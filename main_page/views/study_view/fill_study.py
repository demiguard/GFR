from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.template import loader
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.core.handlers.wsgi import WSGIRequest

import shutil
import os
import datetime
import logging
import PIL
import glob
from pandas import DataFrame
from dateutil import parser as date_parser
import pydicom
from pydicom import uid
import pandas
import numpy as np
from pathlib import Path

from typing import Type, List, Tuple, Union, Generator, Dict
# Custom type - for csv files
CsvDataType = Tuple[Generator[List[str], List[List[List[Union[int, float]]]], List[int]], int]


from main_page.libs.dirmanager import try_mkdir
from main_page.libs.query_wrappers import pacs_query_wrapper as pacs
from main_page.libs.query_wrappers import ris_query_wrapper as ris
from main_page.libs import examination_info
from main_page.libs import dataset_creator
from main_page.libs import server_config
from main_page.libs import samba_handler
from main_page.libs import formatting
from main_page.libs import dicomlib
from main_page.libs import enums
from main_page import forms
from main_page import models
from main_page.libs.clearance_math import clearance_math

logger = logging.getLogger()

REQUEST_PARAMETER_TYPES = { 
  'cpr': str,
  'name': str,
  'sex': int,
  'birthdate': str,
  'height': float,
  'weight': float,
  'vial_weight_before': float,
  'vial_weight_after': float,
  'injection_time': str,
  'injection_date': str,
  'thin_fac': float,
  'study_type': int,
  'std_cnt_text_box': float,
  'sample_date': (list, str),
  'sample_time': (list, str),
  'sample_value': (list, float),
  'study_date': str,
  'study_time': str,
  'bamID': str,
  'dateofmessurement': str,
}


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

  sample_dates = request.POST.getlist('sample_date')
  sample_dates = map(formatting.reverse_format_date, sample_dates) # could oneline this

  sample_times = request.POST.getlist('sample_time')

  sample_tec99 = np.array([float(x) for x in request.POST.getlist('sample_value')])
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
    department=request.user.department,
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


class FillStudyView(LoginRequiredMixin, TemplateView):
  """
  View for filling out a specific study/examination
  """
  template_name = 'main_page/fill_study.html'

  def get_counter_data(self, hospital: str) -> CsvDataType:
    """
    Tries to retrieve counter data from the Samba Share to display on the site

    Args:
      hospital: short name of the hospital to retrieve data from

    Returns:
      Tuple with the zipped data and the length of the data
    
    Raises:
      ConnectionError: if no connection to the Samba Share can be made
    """
    try:
      data_files = samba_handler.smb_get_all_csv(hospital, timeout=10)
    except Exception as E:
      logger.warning(f'SMB Connection Failed: {E}')
      raise ConnectionError('Hjemmesiden kunne ikke få kontakt til serveren med prøve resultater.\n Kontakt din lokale IT-ansvarlige \n Server kan ikke få kontakt til sit Samba-share.')

    # Read requested data from each csv file  
    csv_present_names = []
    csv_data = []
    data_indicies = []
    
    for data_file in data_files:
      selected = data_file[['Rack', 'Pos', 'Tc-99m CPM']]

      base_name = data_file['Measurement date & time'][0]

      measurement_date, measurement_time = base_name.split(' ') 
      measurement_date = formatting.convert_date_to_danish_date(measurement_date, sep='-')

      csv_present_names.append( f'{measurement_time} - {measurement_date}')
      
      # Cast to int, as to remove dots when presenting on the site
      csv_data.append(
        [[int(rack), int(pos), formatting.convert_number_to_unreasonable_number_format(cnt)] 
          for rack, pos, cnt in selected.to_numpy().tolist()]
        )
      
      data_indicies.append(selected.index.tolist())

    # Flatten list of lists
    data_indicies = [idx for sublist in data_indicies for idx in sublist]

    return zip(csv_present_names, csv_data, data_indicies), len(data_indicies)

  def initialize_forms(self, request, exam: Type[examination_info.ExaminationInfo]) -> Dict:
    """
    Initializes all the required forms for this view

    Returns:
      Dict containing the initialized forms
    """
    try:
      study_type = enums.STUDY_TYPE_NAMES.index(exam.Method)
    except ValueError:
      # Default to StudyType(0)
      study_type = 0

    study_type_form = forms.FillStudyType(initial={
      'study_type': study_type
    })

    if exam.sex == 'M':
      present_sex = 0
    else:
      present_sex = 1

    try:
      patient_birthday = formatting.convert_date_to_danish_date(exam.birthdate, sep='-')
    except ValueError:
      patient_birthday = "00-00-0000"
    
    study_patient_form = forms.Fillpatient_1(initial={
      'cpr': exam.cpr,
      'name': exam.name,
      'sex': present_sex,
      'birthdate': patient_birthday
    })

    today = datetime.date.today()

    inj_time = None
    inj_date = today.strftime('%d-%m-%Y')
    if exam.inj_t:
      inj_date = exam.inj_t.strftime('%d-%m-%Y')
      inj_time = exam.inj_t.strftime('%H:%M')

    study_examination_form = forms.Fillexamination(initial={
      'vial_weight_before': exam.inj_before,
      'vial_weight_after': exam.inj_after,
      'injection_time': inj_time,
      'injection_date': inj_date
    })

    get_backup_date_form = forms.GetBackupDateForm(initial={
      'dateofmessurement' : today.strftime('%d-%m-%Y')
    })

    study_patient_form_2 = forms.Fillpatient_2(initial={
      'height': exam.height,
      'weight': exam.weight,
    })

    thin_fac_save_inital = True
    if exam.thin_fact == 0.0 or exam.thin_fact == None:
      if request.user.department.thining_factor_change_date == today and request.user.department.thining_factor != 0:
        exam.thin_fact = request.user.department.thining_factor
        thin_fac_save_inital = False
      else:
        exam.thin_fact = None

    # Check to avoid resetting the thining factor when clicking 'beregn'
    if exam.thin_fact:
      if exam.thin_fact != request.user.department.thining_factor:
        thin_fac_save_inital = False

    study_dosis_form = forms.Filldosis(initial={
      'thin_fac' : exam.thin_fact,
      'save_fac' : thin_fac_save_inital
    })

    test_form = forms.FillStudyTest(initial={'study_date' : today.strftime('%d-%m-%Y')})

    bamID_form = forms.ControlPatientConfirm()

    return {
      'bamID_form'            : bamID_form,
      'study_patient_form'    : study_patient_form,
      'study_type_form'       : study_type_form,
      'study_examination_form': study_examination_form,
      'get_backup_date_form'  : get_backup_date_form,
      'study_patient_form_2'  : study_patient_form_2,
      'study_dosis_form'      : study_dosis_form,
      'test_form'             : test_form
    }

  def get_previous_samples(self, exam: Type[examination_info.ExaminationInfo]):
    """
    Retrieves the previous entered samples for study

    Args:
      exam: Examination info object for the study
    
    Returns:
      zip of the previous sample data
    """
    previous_sample_times = [st.strftime('%H:%M') for st in exam.sam_t]
    previous_sample_dates = [st.strftime('%d-%m-%Y') for st in exam.sam_t]
    previous_sample_counts = exam.tch_cnt
    
    return zip(
      previous_sample_dates,
      previous_sample_times,
      previous_sample_counts
    )

  def resolve_zero_fields(self, exam):
    """
    Resolve presentation issue for 0.0 values.

    Args:
      exam: Examination info object for the study

    Remarks:
      This is done by setting the value to None, so the field doesn't contain
      any value once the page is displayed to the user.
    """
    FIELDS_TO_RESOLVE = (
      'inj_before',
      'inj_after',
      'height',
      'weight',
      'std_cnt'
    )

    for field in FIELDS_TO_RESOLVE:
      attr_val = getattr(exam, field)

      if attr_val == 0.0:
        setattr(exam, field, None)

  def get(self, request: Type[WSGIRequest], accession_number: str) -> HttpResponse:
    """
    Handles GET requests to the view, i.e. the presentation side

    Args:
      request: the incoming HTTP request
      accession_number: RIS number for the study
    """
    hospital = request.user.department.hospital.short_name
    hospital_dir = f"{server_config.FIND_RESPONS_DIR}{hospital}/"

    # Create dicom file cache directory
    try_mkdir(hospital_dir, mk_parents=True)

    # Retrieve counter data to display from Samba Share
    error_message = 'Der er ikke lavet nogen prøver de sidste 24 timer'
    try:
      csv_data, csv_data_len = self.get_counter_data(hospital)
    except ConnectionError as conn_err:
      csv_data, csv_data_len = [], 0
      error_message = conn_err

    # Get previous information for the study
    exam = pacs.get_examination(request.user, accession_number, hospital_dir)

    # Read previously entered samples
    previous_samples = self.get_previous_samples(exam)

    # Resolve field display issues
    self.resolve_zero_fields(exam)

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'rigsnr': accession_number,
      'previous_samples': previous_samples,
      'csv_data': csv_data,
      'csv_data_len': csv_data_len,
      'error_message' : error_message,
      'standard_count' : exam.std_cnt,
    }

    # Initialize forms - concat forms into the context
    view_forms = self.initialize_forms(request, exam)
    context.update(view_forms)

    return render(request, self.template_name, context=context)

  def post(self, request: Type[WSGIRequest], accession_number: str) -> HttpResponse:
    hospital_shortname = request.user.department.hospital.short_name

    dataset_filepath = Path(
      server_config.FIND_RESPONS_DIR,
      hospital_shortname,
      accession_number,
      f"{accession_number}.dcm"
    )
    #file_path = f"{server_config.FIND_RESPONS_DIR}{request.user.department.hospital.short_name}/{accession_number}/{accession_number}.dcm"
    
    dataset = dicomlib.dcmread_wrapper(dataset_filepath)

    print("##### START REQUEST #####")
    print(request)
    print("##### END REQUEST #####")
    print("##### START REQUEST POST #####")
    print(request.POST)
    print("##### END REQUEST POST #####")
    print("##### START FORMATTED POST #####")
    # Extract POST request parameters with safer handling of special characters
    try:
      post_req = formatting.extract_request_parameters(
        request.POST, 
        REQUEST_PARAMETER_TYPES
      )
    except ValueError as e: # Handle edge cases where e.g. as user typed two commas in a float field and/or somehow got text into it
      return HttpResponse("Server fejl: Et eller flere felter var ikke formateret korrekt!")
    print(post_req)
    print("##### END FORMATTED POST #####")

    #Save Without Redirect
    if 'save' in request.POST:
      return store_form(request, dataset, accession_number)

    #Beregn
    if 'calculate' in request.POST:
      logger.info(f"""
        User: {request.user.username}
        calculated GFR on Examination number: {accession_number}
        from ip: {request.META['REMOTE_ADDR']}
        """
      )
      
      dataset = store_form(request, dataset, accession_number) 
      
      # Construct datetime for injection time
      inj_time = request.POST['injection_time']
      inj_date = formatting.reverse_format_date(request.POST['injection_date'], sep='-')
      inj_datetime = date_parser.parse(f"{inj_date} {inj_time}")

      # Construct datetimes for study times
      # Determine study type
      study_type = enums.StudyType(int(request.POST['study_type']))
      study_type_name = enums.STUDY_TYPE_NAMES[study_type.value]

      # sample_times = request.POST.getlist('study_time')[:-1]
      # sample_dates = request.POST.getlist('study_date')[:-1]
      sample_times = request.POST.getlist('sample_time')
      sample_dates = request.POST.getlist('sample_date')
      sample_dates = map(formatting.reverse_format_date, sample_dates)
      sample_datetimes = np.array([date_parser.parse(f"{date} {time}") 
                            for time, date in zip(sample_times, sample_dates)])

      # Measured tec99 counts
      tec_counts = np.array([float(x) for x in request.POST.getlist('sample_value')])

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
      bamID = request.POST['bamID']
          

      gender_num = int(request.POST['sex'])
      gender = enums.Gender(gender_num)
      gender_name = enums.GENDER_NAMINGS[gender.value]

      # Determine new kidney function
      gfr_str, gfr_index = clearance_math.kidney_function(clearance_norm, birthdate, gender)

      # Get historical data from PACS
      try:
        history_dates, history_age, history_clrN = pacs.get_history_from_pacs(dataset, 
        f'{server_config.FIND_RESPONS_DIR}{request.user.department.hospital.short_name}')
      except ValueError: # Handle empty AET for PACS connection 
        history_age = [ ]
        history_clrN = [ ]
        history_dates = [ ]

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
        accession_number,
        cpr = cpr,
        index_gfr=gfr_index,
        hosp_dir=request.user.department.hospital.short_name,
        hospital_name=request.user.department.hospital.name,
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
        bamid          = bamID,
        gfr            = gfr_str,
        clearance      = clearance,
        clearance_norm = clearance_norm,
        pixeldata      = pixel_data,
        exam_status    = 2
      )
      
    dicomlib.save_dicom(dataset_filepath, dataset)
    
    if 'calculate' in request.POST:
      return redirect('main_page:present_study', accession_number=accession_number) 

    return self.get(request, accession_number)
