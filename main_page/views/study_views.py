from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.template import loader
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest

import shutil
import os
import datetime
import logging
import PIL
import glob
from pandas import DataFrame
from typing import Type, List, Tuple, Union, Generator, Dict

from main_page.libs.dirmanager import try_mkdir
from main_page.libs.query_wrappers import pacs_query_wrapper as pacs
from main_page.libs.query_wrappers import ris_query_wrapper as ris
from main_page.libs import post_request_handler as PRH
from main_page.libs import examination_info
from main_page.libs import dataset_creator
from main_page.libs import server_config
from main_page.libs import samba_handler
from main_page.libs import formatting
from main_page.libs import dicomlib
from main_page.libs import enums
from main_page import forms
from main_page import models

# Custom type
CsvDataType = Tuple[Generator[List[str], List[List[List[Union[int, float]]]], List[int]], int]

logger = logging.getLogger()


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
      csv_data.append([[int(rack), int(pos), cnt] for rack, pos, cnt in selected.to_numpy().tolist()])
      
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

    study_patient_form = forms.Fillpatient_1(initial={
      'cpr': exam.cpr,
      'name': exam.name,
      'sex': present_sex,
      'birthdate': formatting.convert_date_to_danish_date(exam.birthdate,sep='-')
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

    return {
      'study_patient_form': study_patient_form,
      'study_type_form': study_type_form,
      'study_examination_form': study_examination_form,
      'get_backup_date_form': get_backup_date_form,
      'study_patient_form_2': study_patient_form_2,
      'study_dosis_form': study_dosis_form,
      'test_form': test_form
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

  def get(self, request: Type[WSGIRequest], ris_nr: str) -> HttpResponse:
    """
    Handles GET requests to the view, i.e. the presentation side

    Args:
      request: the incoming HTTP request
      ris_nr: RIS number for the study
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
    exam = pacs.get_examination(request.user, ris_nr, hospital_dir)

    # Read previously entered samples
    previous_samples = self.get_previous_samples(exam)

    # Resolve field display issues
    self.resolve_zero_fields(exam)

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'rigsnr': ris_nr,
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

  def post(self, request: Type[WSGIRequest], ris_nr: str) -> HttpResponse:
    file_path = f"{server_config.FIND_RESPONS_DIR}{request.user.department.hospital.short_name}/{ris_nr}.dcm"

    dataset = dicomlib.dcmread_wrapper(file_path)
    dataset = PRH.fill_study_post(request, ris_nr, dataset)
    
    dicomlib.save_dicom(file_path, dataset)
    
    if 'calculate' in request.POST:
      return redirect('main_page:present_study', ris_nr=ris_nr) 

    return self.get(request, ris_nr)


class PresentOldStudyView(LoginRequiredMixin, TemplateView):
  """
  Remark:
    Should pull information down from PACS, but not be able to send to it.
    Additionally no button for going back to editing the study should be
    available!
  """
  template_name = 'main_page/present_old_study.html'

  def get(self, request: Type[WSGIRequest], ris_nr: str) -> HttpResponse:
    logger.info(f"Attempting to present old study with accession_number: {ris_nr}")
    current_user = request.user
    hospital = request.user.department.hospital.short_name

    # Search to find patient id - pick field response
    dataset = pacs.move_from_pacs(
      current_user,
      ris_nr
    )

    if dataset == None or not('GFR' in dataset):
      #Query Failed!
      logger.warning(f"""
      Examination unknown to GFR Calc
      
      dataset from query:
      {dataset}
      """)
      error_template = loader.get_template('main_page/present_old_study_error.html')
      error_context  = {
        'AccessionNumber' : ris_nr
      }
      if dataset != None:
        error_context['dataset'] = dataset

      return HttpResponse(error_template.render(error_context,request))

    exam = examination_info.deserialize(dataset)

    # Read in previous samples from examination info
    previous_sample_times = []
    previous_sample_dates = []
    previous_sample_counts = exam.tch_cnt

    for st in exam.sam_t:
      previous_sample_dates.append(st.strftime('%Y-%m-%d'))
      previous_sample_times.append(st.strftime('%H:%M'))
    
    previous_samples = zip(
      previous_sample_dates,
      previous_sample_times,
      previous_sample_counts
    )

    today = datetime.datetime.now()
    inj_time = today.strftime('%H:%M')
    inj_date = today.strftime('%Y-%m-%d')
    if exam.inj_t:

      inj_date = exam.inj_t.strftime('%Y-%m-%d')
      inj_time = exam.inj_t.strftime('%H:%M')

    study_type = 0
    if exam.Method:
      # TODO: The below strings that are checked for are used in multiple places. MOVE these into a config file
      # TODO: or just store the study_type number instead of the entire string in the Dicom obj and exam info
      if exam.Method == 'Et punkt voksen':
        study_type = 0
      elif exam.Method == 'Et punkt Barn':
        study_type = 1
      elif exam.Method == 'Flere prøve Voksen':
        study_type = 2

    # Extract the image
    img_resp_dir = f"{server_config.IMG_RESPONS_DIR}{hospital}/"
    try_mkdir(img_resp_dir)
    
    pixel_arr = exam.image
    if pixel_arr.shape[0] != 0:
      Im = PIL.Image.fromarray(pixel_arr, mode="RGB")
      Im.save(f'{img_resp_dir}{ris_nr}.png')
    
    plot_path = 'main_page/images/{0}/{1}.png'.format(hospital, ris_nr) 
    
    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'name': exam.name,
      'date': exam.date,
      'image_path': plot_path,
      'std_cnt': exam.std_cnt,
      'thin_fac': exam.thin_fact,
      'vial_weight_before': exam.inj_before,
      'vial_weight_after': exam.inj_after,
      'injection_time': inj_time,
      'injection_date': inj_date,
      'study_type': study_type,
      'previous_samples': [previous_samples],
    }

    return render(request, self.template_name, context=context)


class PresentStudyView(LoginRequiredMixin, TemplateView):
  """
  Presenting the end result of an examination

  Args:
    request: The HTTP request
    ris_nr: accession number of the request examination
  """

  template_name = 'main_page/present_study.html'

  def get(self, request: Type[WSGIRequest], ris_nr: str) -> HttpResponse:
    base_resp_dir = server_config.FIND_RESPONS_DIR
    hospital = request.user.department.hospital.short_name
    
    DICOM_directory = f"{base_resp_dir}{hospital}/"
    try_mkdir(DICOM_directory, mk_parents=True)

    exam = pacs.get_examination(request.user, ris_nr, DICOM_directory)
    
    # Determine whether QA plot should be displayable - i.e. the study has multiple
    # test values
    show_QA_button = (len(exam.tch_cnt) > 1)

    # Display
    img_resp_dir = f"{server_config.IMG_RESPONS_DIR}{hospital}/"
    try_mkdir(img_resp_dir)
    
    pixel_arr = exam.image
    if pixel_arr.shape[0] != 0:
      Im = PIL.Image.fromarray(pixel_arr)
      Im.save(f'{img_resp_dir}{ris_nr}.png')
    
    plot_path = f"main_page/images/{hospital}/{ris_nr}.png" 
    
    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'name': exam.name,
      'date': exam.date,
      'ris_nr': ris_nr,
      'image_path': plot_path,
      'show_QA_button': show_QA_button,
    }

    return render(request, self.template_name, context=context)

  def post(self, request: Type[WSGIRequest], ris_nr: str) -> HttpResponse:
    # Send information to PACS
    obj_dir     = f"{server_config.FIND_RESPONS_DIR}{request.user.department.hospital.short_name}/{ris_nr}/"
    obj_path    = f"{obj_dir}{ris_nr}.dcm"
    image_path  = f"{server_config.IMG_RESPONS_DIR}{request.user.department.hospital.short_name}/{ris_nr}.png"

    dicom_object = dicomlib.dcmread_wrapper(obj_path)

    logger.info(f"User:{request.user.username} has finished examination: {ris_nr}")
    success_rate, error_message = pacs.store_dicom_pacs(dicom_object, request.user)
    logger.info(f"User:{request.user.username} has stored {ris_nr} in PACS")
    if success_rate:
      # Remove the file + history
      try:
        shutil.rmtree(obj_dir)
      except OSError as error:
        logger.error(f'Could not remove directory: {obj_dir}')
      try:
        os.remove(image_path)
      except:
        logger.warn(f'Could not delete image: {image_path}')
      # Store the RIS number in the HandleExaminations table
      HE = models.HandledExaminations(accession_number=ris_nr)
      HE.save()
    else:
      # Try again?
      # Redirect to informative site, telling the user that the connection to PACS is down
      logger.warn(f'Failed to store {ris_nr} in pacs, because:{error_message}')
    
    return redirect('main_page:list_studies')
