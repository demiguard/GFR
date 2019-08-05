"""
Handles incoming post requests from views
"""

from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import loader
from django.shortcuts import redirect

from dateutil import parser as date_parser
from pydicom import uid
import datetime, logging
import glob
import os
import pandas
import numpy
import pydicom
import PIL

from .. import forms
from .. import models
from .query_wrappers import ris_query_wrapper as ris
from .query_wrappers import pacs_query_wrapper as pacs
from .clearance_math import clearance_math
from . import server_config
from . import dicomlib
from . import formatting
from main_page.libs.dirmanager import try_mkdir


logger = logging.getLogger()

def fill_study_post(request, rigs_nr, dataset):
  """
  Handles Post request for fill study

  Args:
    Request: The Post request
    rigs_nr: The REGH number for the corosponding examination
    dataset
  """
  #Save Without Redirect

  if 'save' in request.POST:
    return store_form(request, dataset, rigs_nr)

  #Beregn
  if 'calculate' in request.POST:
    logger.info(f"""
      User: {request.user.username}
      calculated GFR on Examination number: {rigs_nr}
      from ip: {request.META['REMOTE_ADDR']}
      """
    )
    dataset = store_form(request, dataset, rigs_nr) 
    # Construct datetime for injection time
    inj_time = request.POST['injection_time']
    inj_date = request.POST['injection_date']
    inj_datetime = date_parser.parse(f"{inj_date} {inj_time}")

    # Construct datetimes for study times
    # Determine study method
    # TODO: Possibly make an Enum in the future
    study_type = int(request.POST['study_type'])
    if study_type == 0:
      method = "En blodprøve, Voksen"
    elif study_type == 1:
      method = "En blodprøve, Barn"
    elif study_type == 2:
      method = "Flere blodprøver"
    else:
      method="INVALID METHOD"

    sample_times = request.POST.getlist('study_time')[:-1]
    sample_dates = request.POST.getlist('study_date')[:-1]
    sample_datetimes = numpy.array([date_parser.parse(f"{date} {time}") 
                          for time, date in zip(sample_times, sample_dates)])

    # Measured tec99 counts
    tec_counts = numpy.array([float(x) for x in request.POST.getlist('test_value')])

    # Compute surface area
    weight = float(request.POST['weight'])
    height = float(request.POST['height'])
    BSA = clearance_math.surface_area(height, weight)

    # Compute dosis
    inj_weight_before = float(request.POST['vial_weight_before'])
    inj_weight_after = float(request.POST['vial_weight_after'])
    inj_weight = inj_weight_before - inj_weight_after

    STD_CNT = float(request.POST['std_cnt_text_box'])
    FACTOR = float(request.POST['thin_fac'])
    dosis = clearance_math.dosis(inj_weight, FACTOR, STD_CNT)

    # Calculate GFR
    clearance, clearance_norm = clearance_math.calc_clearance(
      inj_datetime, 
      sample_datetimes,
      tec_counts,
      BSA,
      dosis,
      method=method
    )
    #Logging
    logger.info(f"""
    Clearance calculation input:
    injection time: {inj_datetime}
    Sample Times: {sample_datetimes}
    Tch99 cnt: {tec_counts}
    Body Surface Area: {BSA}
    Dosis: {dosis}
    Method: {method}
    Result:
      Clearnance: {clearance}
      Clearence Normal: {clearance_norm}"""
    )

    name = request.POST['name']
    cpr = formatting.convert_cpr_to_cpr_number(request.POST['cpr'])
    birthdate = request.POST['birthdate']
    gender = request.POST['sex']

    age = datetime.datetime.strptime(request.POST['birthdate'], '%Y-%m-%d')

    gfr_str, gfr_index = clearance_math.kidney_function(clearance_norm, cpr, birthdate=birthdate, gender=gender)

    history_dates, history_age, history_clrN = pacs.get_history_from_pacs(cpr, age, request.user)
    pixel_data = clearance_math.generate_plot_text(
      weight,
      height,
      BSA,
      clearance,
      clearance_norm,
      gfr_str,
      birthdate,
      gender,
      rigs_nr,
      cpr = cpr,
      index_gfr=gfr_index,
      hosp_dir=request.user.department.hospital.short_name,
      history_age=history_age,
      history_clr_n=history_clrN,
      method = method,
      injection_date=inj_datetime.strftime('%d-%b-%Y'),
      name = name,
      procedure_description=dataset.RequestedProcedureDescription
    )
        
    dicomlib.fill_dicom(
      dataset,
      gfr            = gfr_str,
      clearance      = clearance,
      clearance_norm = clearance_norm,
      pixeldata = pixel_data,
      exam_status = 2
    )

    return dataset


def store_form(request, dataset, rigs_nr):
  """
  Stores information from the post request in a dicom file with the name
  <rigs_nr>.dcm

  Args:
    rigs_nr: rigs number of the examination to store in
  """
  base_resp_dir = server_config.FIND_RESPONS_DIR
  hospital = request.user.department.hospital.short_name

  try_mkdir(f"{base_resp_dir}{hospital}", mk_parents=True)

  #All Fields to be stored
  birthdate = None
  injection_time = None
  gfr_type = None
  gender = None
  injection_before = None
  injection_after  = None
  injection_weight = None
  weight = None
  height = None
  bsa_method = 'Haycock'
  seq = None

  # Store age
  birthdate_str = request.POST['birthdate']
  
  if birthdate_str:    
    birthdate = datetime.datetime.strptime(birthdate_str, '%Y-%m-%d').date()
    age = (datetime.date.today() - birthdate).days // 365 

  #Injection Date Time information
  if len(request.POST['injection_date']) > 0:
    inj_time = request.POST['injection_time']
    inj_date = request.POST['injection_date']
    inj_datetime = date_parser.parse(f"{inj_date} {inj_time}")
    injection_time = inj_datetime.strftime('%Y%m%d%H%M')

  #Study Always exists
  study_type = int(request.POST['study_type'])
  gfr_type = ''
  if study_type == 0:
    gfr_type = 'Et punkt Voksen'
  elif study_type == 1:
    gfr_type = 'Et punkt Barn'
  elif study_type == 2:
    gfr_type = 'Flere prøve Voksen'

  if request.POST['sex']:
    gender = request.POST['sex']

  if request.POST['vial_weight_before'] and request.POST['vial_weight_after']:
    injection_before = float(request.POST['vial_weight_before'])
    injection_after  = float(request.POST['vial_weight_after'])
    injection_weight = injection_before - injection_after
  elif request.POST['vial_weight_before']:
    injection_before = float(request.POST['vial_weight_before'])
 
  if request.POST['weight']:
    weight = float(request.POST['weight']) 

  if 'save_fac' in request.POST and request.POST['thin_fac']: 
    logger.info(f"{request.user.username} Updated thining factor to {request.POST['thin_fac']}")
    request.user.department.thining_factor = float(request.POST['thin_fac'])
    request.user.department.thining_factor_change_date = datetime.date.today()
    request.user.department.save()

  if request.POST['height']:
    height = float(request.POST['height'])/100.0

  thiningfactor = 0.0
  std_cnt = 0.0
  if request.POST['thin_fac']:
    thiningfactor = float(request.POST['thin_fac'])
  
  if request.POST['std_cnt_text_box']:
    std_cnt= float(request.POST['std_cnt_text_box'])

  sample_dates = request.POST.getlist('study_date')[:-1]
  sample_times = request.POST.getlist('study_time')[:-1]  

  sample_tec99 = numpy.array([float(x) for x in request.POST.getlist('test_value')])
  # There's Data to put in
  if len(sample_tec99) > 0:
    formated_sample_date = [date.replace('-','') for date in sample_dates]
    formated_sample_time = [time.replace(':','') for time in sample_times]
    zip_obj_datetimes = zip(formated_sample_date,formated_sample_time)

    sample_datetimes = [date + time for date,time in zip_obj_datetimes]  
    zip_obj_seq = zip(sample_datetimes, sample_tec99)
    seq = [(datetime, cnt) for datetime, cnt in zip_obj_seq]
  else:
    seq = []

  # If exam_status is already higher than 1, don't change it
  exam_status = 0
  if 'ExamStatus' in dataset:
    if dataset.ExamStatus == 2:
      exam_status = 2
  else:
    exam_status = 1

  dicomlib.fill_dicom(dataset,
    age=age,
    birthday=birthdate,
    update_dicom = True,
    update_date = True,
    injection_time=injection_time,
    gfr_type=gfr_type,
    series_number = rigs_nr[4:],
    station_name = request.user.department.config.ris_calling,
    gender=gender,
    injection_before = injection_before,
    injection_after  = injection_after,
    injection_weight = injection_weight,
    weight=weight,
    height=height,
    bsa_method=bsa_method,
    thiningfactor=thiningfactor,
    std_cnt=std_cnt,
    sample_seq=seq,
    exam_status=exam_status
  )

  return dataset
