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
import math
from pandas import DataFrame
from dateutil import parser as date_parser
import pydicom
from pydicom import uid
import pandas
import numpy as np
from pathlib import Path

from typing import Type, List, Tuple, Union, Generator, Dict
# Custom type - for representation of csv files to be loaded on to page
CsvDataType = Tuple[Generator[List[str], List[List[List[Union[int, float]]]], List[int]], int]


from main_page.libs.dirmanager import try_mkdir
from main_page.libs.query_wrappers import pacs_query_wrapper as pacs
from main_page.libs.query_wrappers import ris_query_wrapper as ris
from main_page.libs import dataset_creator
from main_page.libs import server_config
from main_page.libs import samba_handler
from main_page.libs import formatting
from main_page.libs import dicomlib
from main_page.libs import dicomio
from main_page.libs import enums
from main_page.forms import base_forms
from main_page import models
from main_page.libs.clearance_math import clearance_math
from main_page.libs.clearance_math import plotting
from main_page import log_util

logger = log_util.get_logger('GFRLogger')

# Dict. used for extraction of large request parameters in fill_study.post
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
  'save_fac': bool,
  'study_type': int,
  'standcount': float,
  'sample_date': (list, str),
  'sample_time': (list, str),
  'sample_value': (list, float),
  'sample_deviation': (list, float),
  'comment_field' : str,
  'study_date': str,
  'study_time': str,
  'bamID': str,
  'vial_number': int,
  'dateofmessurement': str,
}


def store_form(post_req: dict, dataset: pydicom.Dataset) -> pydicom.Dataset:
  """
  Stores form information from a post request into a dicom object

  Args:
    post_req: dictionary of extracted and formatted post request content
    dataset: dicom object to store information in
  """
  # Get birthdate and compute the age to store
  cpr = post_req.get("cpr")
  birthdate = post_req.get("birthdate")

  if cpr:
    age = clearance_math.calculate_age(cpr)
  else:
    age = None

  # Get and format injection time and date to match required format for dicom object
  vial_number = post_req.get('vial_number')
  inj_time = post_req.get("injection_time")
  inj_date = post_req.get("injection_date")

  if inj_time and inj_date:
    tmp = datetime.datetime.strptime(
      f"{inj_date} {inj_time}",
      "%d-%m-%Y %H:%M"
    )
    injection_datetime = tmp.strftime("%Y%m%d%H%M")
  else:
    injection_datetime = None

  # Get study type
  study_type_name = enums.STUDY_TYPE_NAMES[post_req["study_type"]]

  # Get gender
  post_sex = post_req.get("sex")
  gender = enums.Gender(post_sex)

  # Get weights before and after injection and difference between
  inj_before = post_req.get("vial_weight_before")
  inj_after = post_req.get("vial_weight_after")

  if inj_before and inj_after:
    inj_weight = inj_before - inj_after
  else:
    inj_weight = None

  # Get weight and height
  weight = post_req.get("weight")
  height = post_req.get("height")
  if height:
    height = height / 100.0

  # Get thinning factor and standard count
  thin_fac = post_req.get("thin_fac")
  if not thin_fac:
    thin_fac = 0.0

  std_cnt = post_req.get("standcount")
  if not std_cnt:
    std_cnt = 0.0

  # If exam_status is already higher than 1, don't change it
  exam_status = 0
  if 'ExamStatus' in dataset:
    if dataset.ExamStatus == 2:
      exam_status = 2
  else:
    exam_status = 1

  # Get sample data
  seq = [ ]
  sample_dates = post_req.get("sample_date")
  sample_times = post_req.get("sample_time")
  sample_values = post_req.get("sample_value")
  sample_deviations = post_req.get("sample_deviation")

  #These if statements seams fishy
  if sample_dates and sample_times and sample_values and sample_deviations:
    # Resize to fit min., if shapes don't match to avoid problems with zip
    dates_cnt = len(sample_dates)
    times_cnt = len(sample_times)
    values_cnt = len(sample_values)
    deviation_cnt = len(sample_deviations)

    if dates_cnt != times_cnt or dates_cnt != values_cnt:
      min_len = min(dates_cnt, times_cnt, values_cnt)
      sample_dates = sample_dates[:min_len]
      sample_times = sample_times[:min_len]
      sample_values = sample_values[:min_len]
      sample_deviations = sample_deviations[:min_len]

    # Combine dates and times to %Y%m%d%H%M format
    for date, time, value, deviation in zip(sample_dates, sample_times, sample_values, sample_deviations):
      date_tmp = datetime.datetime.strptime(
        f"{date} {time}", "%d-%m-%Y %H:%M"
      ).strftime("%Y%m%d%H%M")

      seq.append((date_tmp, value, deviation))

  # Store everything into dicom object
  dicomlib.fill_dicom(
    dataset,
    age=age,
    birthday=formatting.convert_to_dicom_date(birthdate),
    bsa_method="Haycock", # There is no way to change this from fill_study, so just fill in default value
    exam_status=exam_status,
    gender=gender,
    gfr_type=study_type_name,
    injection_time=injection_datetime,
    injection_before=inj_before,
    injection_after=inj_after,
    injection_weight=inj_weight,
    height=height,
    sample_seq=seq,
    series_number=1,
    image_comment=post_req.get('comment_field'),
    std_cnt=std_cnt,
    thiningfactor=thin_fac,
    update_date = True,
    update_dicom = True,
    vial_number=vial_number,
    weight=weight
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
      server_configuration = models.ServerConfiguration.objects.get(id=1)

      data_files, error_messages = samba_handler.smb_get_all_csv(hospital, server_configuration, timeout=10)
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
        [[int(rack), int(pos), int(cnt)]
          for rack, pos, cnt in selected.to_numpy().tolist()]
        )

      data_indicies.append(selected.index.tolist())

    # Flatten list of lists
    data_indicies = [idx for sublist in data_indicies for idx in sublist]

    return zip(csv_present_names, csv_data, data_indicies), len(data_indicies), error_messages

  def initialize_forms(self, request, dataset: pydicom.Dataset) -> Dict:
    """
    Initializes all the required forms for this view.
    There's 3 forms on fill study:
      Grandfrom: This form is a merged serveral old forms
      test_forms: This form is for Samples. Since you can have multiple samples per study,
                    we need to replicate the sample form, else where
      backup_form: This form is used by getting backup samples, and have nothing to do with the study.

    Returns:
      Dict containing the initialized forms
    """
    # Grand form Initial
    try:
      study_type = enums.STUDY_TYPE_NAMES.index(dataset.get("GFRMethod"))
    except (ValueError, AttributeError):
      # Default to StudyType(0)
      study_type = 0

    cpr = dataset.get("PatientID")
    patient_sex = dataset.get("PatientSex")
    vial_number = dataset.get("VialNumber")
    if patient_sex:
      present_sex = enums.GENDER_SHORT_NAMES.index(patient_sex)
    else:
      # Only attempt to determine sex from cpr nr. if nothing about sex is present in the dicom dataset 
      try:
        present_sex = enums.GENDER_SHORT_NAMES.index(
          clearance_math.calculate_sex(cpr))
      except ValueError: # Failed to cast cpr nr. to int, i.e. weird cpr nr.
        present_sex = 1

    # Get patient birthdate
    try:
      birthdate = dataset.get("PatientBirthDate")

      try:
        patient_birthday = formatting.convert_date_to_danish_date(birthdate, sep='-')
      except (ValueError, TypeError):
        patient_birthday = birthdate

      if not patient_birthday: # If birthday is not found
        try:
          patient_birthday = formatting.convert_date_to_danish_date(clearance_math.calculate_birthdate(dataset.get("PatientID")), sep='-')
        except:
          patient_birthday = "00-00-0000"
    except ValueError:
      patient_birthday = "00-00-0000"

    today = datetime.date.today()
    inj_date = today.strftime('%d-%m-%Y')
    inj_time = None

    ds_inj_time = dataset.get("injTime")
    if ds_inj_time:
      ds_inj_datetime = datetime.datetime.strptime(
        ds_inj_time, "%Y%m%d%H%M"
      )
      inj_date = ds_inj_datetime.strftime('%d-%m-%Y')
      inj_time = ds_inj_datetime.strftime('%H:%M')
    else:
      inj_date = today.strftime('%d-%m-%Y')
      inj_time = None

    thin_fac_save_inital = True
    ds_thin_fac = dataset.get("thiningfactor")
    department_thin_fac = request.user.department.thining_factor

    if ds_thin_fac:
      thin_fac_save_inital = False
    elif request.user.department.thining_factor_change_date == today and department_thin_fac != 0:
      ds_thin_fac = department_thin_fac
      thin_fac_save_inital = False

    # Check to avoid resetting the thining factor when clicking 'beregn'

    # Get patient height
    height = dataset.get("PatientSize")
    if height:
      height = math.ceil(math.floor(height * 10000) / 100)
      """
      we use:
        height = height * 1000 / 10
      as opposed to
        height *= 100
      As Python does some weird things with floating-point numbers in specific
      cases, e.g. if height = 1.16, then
      height = height * 1000 / 10, becomes:
      height = 1.16 * 1000 / 10 = 1160.0 / 10 = 116.0
      whilst, height *= 100, becomes:
      height = 1.16 * 100 = 115.99999999999999

      The multiplication has to be done as the DICOM standard and pydicom
      expects PatientSize to be stored in meters.

      For details on the floating-point issue see:
      https://docs.python.org/3.6/tutorial/floatingpoint.html
      """

    # Get patient name
    name = dataset.get("PatientName")
    if name:
      name = formatting.person_name_to_name(name)

    comment = dataset.get('ClearenceComment')
    if not(comment):
      comment = dataset.get('ImageComments')


    grand_form = base_forms.FillStudyGrandForm(initial={
      'cpr'               : formatting.format_cpr(cpr),
      'height'            : height,
      'birthdate'         : patient_birthday,
      'injection_date'    : inj_date,
      'injection_time'    : inj_time,
      'vial_number'       : vial_number,
      'name'              : name,
      'save_fac'          : thin_fac_save_inital,
      'sex'               : present_sex,
      'standcount'        : dataset.get("stdcnt"),
      'study_type'        : study_type,
      'thin_fac'          : ds_thin_fac,
      'vial_weight_after' : dataset.get("injafter"),
      'vial_weight_before': dataset.get("injbefore"),
      'weight'            : dataset.get("PatientWeight"),
      'comment_field'     : comment
    })

    # Samples Form
    test_form = base_forms.FillStudyTest(initial={
      'study_date': today.strftime('%d-%m-%Y')
    })

    # Backup
    get_backup_date_form = base_forms.GetBackupDateForm(initial={
      'dateofmessurement' : today.strftime('%d-%m-%Y')
    })

    return {
      'grand_form'            : grand_form,
      'get_backup_date_form'  : get_backup_date_form,
      'test_form'             : test_form
    }

  def get_previous_samples(self,
    dataset: pydicom.Dataset
  ) -> List[Tuple[str, str, float, float]]:
    """
    Retrieves the previous entered samples for study

    Args:
      dataset: pydicom Dataset contaning previous study samples

    Returns:
      list of the previous sample data
    """
    previous_samples = [ ]
    if "ClearTest" in dataset:
      for sample in dataset.ClearTest:
        sample_datetime = datetime.datetime.strptime(
          sample.SampleTime,
          "%Y%m%d%H%M"
        )
        sample_date = sample_datetime.strftime("%d-%m-%Y")
        sample_time = sample_datetime.strftime("%H:%M")
        sample_cnt  = sample.cpm
        #Legacy Support
        if 'Deviation' in sample:
          sample_devi = float(sample.Deviation)
        else:
          sample_devi = 0.0

        previous_samples.append((
          sample_date,
          sample_time,
          sample_cnt,
          sample_devi
        ))

    return previous_samples


  def get(self, request: Type[WSGIRequest], accession_number: str) -> HttpResponse:
    """
    Handles GET requests to the view, i.e. the presentation side

    Args:
      request: the incoming HTTP request
      accession_number: RIS number for the study
    """
    hospital = request.user.department.hospital.short_name # type: ignore #failure ensured by login required
    hospital_dir = f"{server_config.FIND_RESPONS_DIR}{hospital}/"

    logger.info(f"Accessing study with accession_number: {accession_number}")

    # Retrieve counter data to display from Samba Share
    error_message = "Der er ikke lavet nogen prøver de sidste 24 timer"
    try:
      csv_data, csv_data_len, error_messages = self.get_counter_data(hospital)
    except ConnectionError as conn_err:
      csv_data, csv_data_len = [], 0
      error_message = conn_err

    obj_filepath = Path(
      hospital_dir,
      accession_number,
      f"{accession_number}.dcm"
    )

    dataset = dicomlib.dcmread_wrapper(obj_filepath)

    # Get previous information for the study
    previous_samples = self.get_previous_samples(dataset)

    # Read previously entered samples
    view_forms = self.initialize_forms(request, dataset)

    # Initialize forms - concat forms into the context

    # Get History
    historic_studies = [study.split('/')[-1].split('.')[0] for study in glob.glob(f'{hospital_dir}/{accession_number}/*') if server_config.RECOVERED_FILENAME not in study]
    historic_studies = list(filter(lambda study: not(study == accession_number), historic_studies))
    historic_studies = ", ".join(historic_studies)

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'rigsnr': accession_number,
      'previous_samples': previous_samples,
      'historic_studies': historic_studies,
      'csv_data': csv_data,
      'csv_data_len': csv_data_len,
      'error_message' : error_message
    }
    context.update(view_forms)

    return render(request, self.template_name, context=context)

  def post(self, request: Type[WSGIRequest], accession_number: str) -> HttpResponse:
    """
      This function handles the post request of /fill_study/accession_number

      The purpose of the post request is the study have been made or is being saved
      In other words the responsiblity for this function is:
        Updating Department based thining factor
        Handling different POST-request methods

    """
    hospital_shortname = request.user.department.hospital.short_name # type: ignore
    department = request.user.department # type: ignore

    # Load in dataset to work with based on accession number
    dataset_filepath = Path(
      server_config.FIND_RESPONS_DIR,
      hospital_shortname,
      accession_number,
      f"{accession_number}.dcm"
    )

    dataset = dicomlib.dcmread_wrapper(dataset_filepath)

    # Extract POST request parameters with safer handling of special characters
    try:
      post_req = formatting.extract_request_parameters(
        request.POST,
        REQUEST_PARAMETER_TYPES
      )
    except ValueError as E: # Handle edge cases where e.g. as user typed two commas in a float field and/or somehow got text into it
      return HttpResponse("Server fejl: Et eller flere felter var ikke formateret korrekt!")

    # Store form information in dataset regardless of submission type
    dataset = store_form(post_req, dataset)

    # Update department thinning factor if neccessary
    if 'save_fac' in post_req and 'thin_fac' in post_req:
      thin_fac = post_req['thin_fac']
      if thin_fac:
        logger.info(f"User: '{request.user}', updated thining factor to {thin_fac}")
        department.thining_factor = thin_fac
        department.thining_factor_change_date = datetime.date.today()
        department.save()

    dicomlib.fill_dicom(
      dataset,
      department=department,
      station_name=department.config.ris_calling
    )

    # Use parameters fillout in store_form to compute GFR of patient
    if "calculate" in request.POST:
      # Comupute body surface area
      height = math.ceil(math.floor(dataset.PatientSize * 10000) / 100)
      """
      we use: math.floor(height * 10000) / 100, as height * 100 results in floating-point
      errors, due to weird Python behavior
      (for details see: https://docs.python.org/3.6/tutorial/floatingpoint.html)
      """

      weight = dataset.PatientWeight
      BSA = clearance_math.surface_area(height, weight)

      # Compute dosis
      inj_weight = dataset.injWeight
      thin_fac = dataset.thiningfactor
      std_cnt = dataset.stdcnt
      vial_num = dataset.VialNumber
      dosis = clearance_math.dosis(inj_weight, thin_fac, std_cnt)

      # Compute clearance and normalized clearance
      inj_datetime = datetime.datetime.strptime(
        dataset.injTime,
        "%Y%m%d%H%M",
      )

      sample_datetimes = [ ]
      tec_counts = [ ]
      if 'ClearTest' in dataset: 
        for sample in dataset.ClearTest:
          tmp_date = datetime.datetime.strptime(
            sample.SampleTime,
            "%Y%m%d%H%M"
          )
          sample_datetimes.append(tmp_date)
          tec_counts.append(sample.cpm)

      study_type = enums.StudyType(post_req["study_type"])

      clearance, clearance_norm = clearance_math.calc_clearance(
        inj_datetime,
        sample_datetimes,
        tec_counts,
        BSA,
        dosis,
        study_type
      )

      # Compute kidney function
      birthdate = datetime.datetime.strptime(dataset.PatientBirthDate,"%Y%m%d")
      gender_num = post_req["sex"]
      gender = enums.Gender(gender_num)
      gender_name = enums.GENDER_NAMINGS[gender.value]

      gfr_str, gfr_index = clearance_math.kidney_function(
        clearance_norm,
        birthdate,
        gender
      )

      # Get historical data from PACS
      try:
        # Side effect this function saves the history in the dataset as well
        history_dates, history_age, history_clrN = dicomio.get_history(dataset, hospital_shortname)
      except ValueError as E: # Handle empty AET for PACS connection
        logger.error(f'Value error detected {E}')
        print(f'Value error detected {E}')
        history_age = [ ]
        history_clrN = [ ]
        history_dates = [ ]


      dicomlib.fill_dicom(
        dataset,
        gfr            = gfr_str,
        clearance      = clearance,
        clearance_norm = clearance_norm,
        exam_status    = 2,

      )

      pixel_data = plotting.generate_plot_from_dataset(dataset)

      # Insert plot (as byte string) into dicom object
      dicomlib.fill_dicom(
        dataset,
        pixeldata      = pixel_data
      )
    # end "calculate" if

    # Save the filled out dataset
    dicomlib.save_dicom(dataset_filepath, dataset)
    # Redirect to correct site based on which action was performed
    if "calculate" in request.POST:
      return redirect('main_page:present_study', accession_number=accession_number)
    else:
      return redirect('main_page:list_studies')

    return self.get(request, accession_number)
