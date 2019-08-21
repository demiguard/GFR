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
from main_page.libs import enums


logger = logging.getLogger()

"""
TODO: The two function below; fill_study_post and store_form both perform 
      extraction and type conversion of the same fields in the POST request.
      Meaning that as fill_study_post calls store_form this happends twice.
      Fix this... i.e. move the type conversion to an external function which
      performs the necessary conversions just ONCE.
"""


def fill_study_post(request, rigs_nr, dataset):
  """
  Handles Post request for fill study

  Args:
    Request: The Post request
    rigs_nr: The REGH number for the corosponding examination
    dataset

  TODO: This function should be split into smaller functions and moved under
        it corresponding views post request handler.
        Write a function which can resolve the types of the request.POST content
  """
  #NOTE: The comment just below is code that doesn't run be cause the directory request.POST is immuate therefore we cannot this.
  #There probbally is a smarter way to do this. 

  #Because we have a wierd date format, here we change the different times s.t they follow logical date format
  #request.POST['injection_date'] = formatting.reverse_format_date(request.POST['injection_date'], sep='-')
  #request.POST['birthday'] = formatting.reverse_format_date(request.POST['birthday'], sep='-')
  #Study date is left out because it's a list and it's not clear how to overwrite that. 

  # The below print statements are therefore debugging the requets and it's POST body,
  # so we can be begin to start making the below code better instead of having complicated type casts
  # print("##### START REQUEST #####")
  # print(request)
  # print("##### END REQUEST #####")
  # print("##### START REQUEST POST #####")
  # print(request.POST)
  # print("##### END REQUEST POST #####")

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
    inj_date = formatting.reverse_format_date(request.POST['injection_date'], sep='-')
    inj_datetime = date_parser.parse(f"{inj_date} {inj_time}")

    # Construct datetimes for study times
    # Determine study type
    study_type = enums.StudyType(int(request.POST['study_type']))
    study_type_name = enums.STUDY_TYPE_NAMES[study_type.value]

    sample_times = request.POST.getlist('study_time')[:-1]
    sample_dates = request.POST.getlist('study_date')[:-1]
    sample_dates = map(formatting.reverse_format_date, sample_dates)
    sample_datetimes = numpy.array([date_parser.parse(f"{date} {time}") 
                          for time, date in zip(sample_times, sample_dates)])

    # Measured tec99 counts
    tec_counts = numpy.array([float(x) for x in request.POST.getlist('test_value')])

    weight = float(request.POST['weight'])
    height = float(request.POST['height'])
    
    # Compute surface area
    BSA = clearance_math.surface_area(height, weight)

    inj_weight_before = float(request.POST['vial_weight_before'])
    inj_weight_after = float(request.POST['vial_weight_after'])
    inj_weight = inj_weight_before - inj_weight_after

    STD_CNT = float(request.POST['std_cnt_text_box'])
    FACTOR = float(request.POST['thin_fac'])
    
    # Compute dosis
    dosis = clearance_math.dosis(inj_weight, FACTOR, STD_CNT)

    logger.info(f"""
      Clearance calculation input:
      injection time: {inj_datetime}
      Sample Times: {sample_datetimes}
      Tch99 cnt: {tec_counts}
      Body Surface Area: {BSA}
      Dosis: {dosis}
      Method: {study_type_name}
    """)

    # Compute clearance and normalized clearance
    clearance, clearance_norm = clearance_math.calc_clearance(
      inj_datetime,
      sample_datetimes,
      tec_counts,
      BSA,
      dosis,
      study_type
    )

    logger.info(f"""
    Clearance calculation result:
      Clearnance: {clearance}
      Clearence Normal: {clearance_norm}"""
    )

    name = request.POST['name']
    cpr = formatting.convert_cpr_to_cpr_number(request.POST['cpr'])
    birthdate = formatting.reverse_format_date(request.POST['birthdate'], sep='-')
    
    gender_num = int(request.POST['sex'])
    gender = enums.Gender(gender_num)
    gender_name = enums.GENDER_NAMINGS[gender.value]

    # Determine new kidney function
    gfr_str, gfr_index = clearance_math.kidney_function(clearance_norm, birthdate, gender)

    # Get historical data from PACS
    history_dates, history_age, history_clrN = pacs.get_history_from_pacs(cpr, birthdate, request.user)
    
    # Generate plot to display
    pixel_data = clearance_math.generate_plot_text(
      weight,
      height,
      BSA,
      clearance,
      clearance_norm,
      gfr_str,
      birthdate,
      gender_name,
      rigs_nr,
      cpr = cpr,
      index_gfr=gfr_index,
      hosp_dir=request.user.department.hospital.short_name,
      history_age=history_age,
      history_clr_n=history_clrN,
      method = study_type_name,
      injection_date=inj_datetime.strftime('%d-%b-%Y'),
      name = name,
      procedure_description=dataset.RequestedProcedureDescription
    )
        
    # Insert plot (as byte string) into dicom object
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
  gender = None
  injection_before = None
  injection_after  = None
  injection_weight = None
  weight = None
  height = None
  bsa_method = 'Haycock'
  seq = None

  # Store age
  birthdate_str = formatting.reverse_format_date(request.POST['birthdate'], sep='-')
  
  if birthdate_str:    
    birthdate = datetime.datetime.strptime(birthdate_str, '%Y-%m-%d').date()
    age = (datetime.date.today() - birthdate).days // 365 

  #Injection Date Time information
  if len(request.POST['injection_date']) > 0:
    inj_time = request.POST['injection_time']
    inj_date = formatting.reverse_format_date(request.POST['injection_date'], sep='-')
    inj_datetime = date_parser.parse(f"{inj_date} {inj_time}")
    injection_time = inj_datetime.strftime('%Y%m%d%H%M')

  #Study Always exists
  study_type = enums.StudyType(int(request.POST['study_type']))
  study_type_name = enums.STUDY_TYPE_NAMES[study_type.value]

  if request.POST['sex']:
    gender_num = request.POST['sex']
    gender = enums.Gender(int(gender_num))

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
  sample_dates = map(formatting.reverse_format_date, sample_dates) # could oneline this

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
    gfr_type=study_type_name,
    series_number = 1,
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
