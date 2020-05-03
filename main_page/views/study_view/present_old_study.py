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
import pydicom
from typing import Type, List, Tuple, Union, Generator, Dict
import numpy as np

from main_page.libs.dirmanager import try_mkdir
from main_page.libs.query_wrappers import pacs_query_wrapper as pacs
from main_page.libs.query_wrappers import ris_query_wrapper as ris
from main_page.libs import dataset_creator
from main_page.libs import server_config
from main_page.libs import samba_handler
from main_page.libs import formatting
from main_page.libs import dicomlib
from main_page.libs import enums
from main_page.libs.clearance_math import clearance_math
from main_page import models
from main_page import log_util

# Custom type
CsvDataType = Tuple[Generator[List[str], List[List[List[Union[int, float]]]], List[int]], int]

logger = log_util.get_logger(__name__)


class PresentOldStudyView(LoginRequiredMixin, TemplateView):
  """
  Remark:
    Should pull information down from PACS, but not be able to send to it.
    Additionally no button for going back to editing the study should be
    available!
  """
  template_name = 'main_page/present_old_study.html'

  def get(self, request: Type[WSGIRequest], accession_number: str) -> HttpResponse:
    logger.info(f"Attempting to present old study with accession_number: {accession_number}")
    current_user = request.user
    hospital = request.user.department.hospital.short_name

    # Search to find patient id - pick field response
    dataset = pacs.move_from_pacs(
      current_user,
      accession_number
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
        'AccessionNumber' : accession_number
      }
      if dataset != None:
        error_context['dataset'] = dataset

      return HttpResponse(error_template.render(error_context,request))

    # Read in previous samples from examination info
    previous_sample_times  = []
    previous_sample_dates  = []
    previous_sample_counts = []
    previous_datetime_injections = [] #Used for generating QA plot

    if 'ClearTest' in dataset:
      for test in dataset.ClearTest:

        injection_datetime = datetime.datetime.strptime(test.SampleTime, '%Y%m%d%H%M')
        previous_datetime_injections.append(injection_datetime)
        previous_sample_dates.append(injection_datetime.strftime('%d-%m-%Y'))
        previous_sample_times.append(injection_datetime.strftime('%H:%M'))
        previous_sample_counts.append(test.cpm)

    previous_samples = zip(
      previous_sample_dates,
      previous_sample_times,
      previous_sample_counts
    )

    # Extract study data to present
    study_date = dataset.StudyDate
    study_time = dataset.StudyTime.split('.')[0] #This is a bug
    study_datetime = datetime.datetime.strptime(f"{study_date}{study_time}", "%Y%m%d%H%M%S")

    birthdate_str = dataset.PatientBirthDate
    birthdate = formatting.convert_date_to_danish_date(birthdate_str, sep='-')

    if dataset.PatientSex == 'M':
      present_sex = 0
    else:
      present_sex = 1

    operators = dataset.get("OperatorsName")
    if isinstance(operators, pydicom.valuerep.PersonName3):
      operators = str(operators)
    elif isinstance(operators, pydicom.multival.MultiValue):
      operators = ', '.join([str(x) for x in operators])
    elif not operators:
      operators = ""

    patient_height = formatting.float_dec_to_comma(dataset.PatientSize * 100)
    patient_weight = formatting.float_dec_to_comma(dataset.PatientWeight)
    inj_weight_before = formatting.float_dec_to_comma(dataset.injbefore)
    inj_weight_after = formatting.float_dec_to_comma(dataset.injafter)

    if dataset.GFRMethod == enums.STUDY_TYPE_NAMES[2]:  # "Flere blodprøver"
      #Generate QA plot for Study
      # Get injection time
      qa_inj_time = datetime.datetime.strptime(dataset.injTime, '%Y%m%d%H%M') 
    
      # Get Thining Factor
      thin_fact = dataset.thiningfactor

      # Create list of timedeltas from timedates
      delta_times = [(time - qa_inj_time).seconds / 60 + 86400 * (time - qa_inj_time).days for time in previous_datetime_injections]
    
      qa_image_bytes = clearance_math.generate_QA_plot(delta_times, previous_sample_counts, thin_fact, accession_number)
      qa_plot_path = f"main_page/images/{hospital}/QA_{accession_number}.png"
      qa_image = PIL.Image.frombytes('RGB', (1920,1080), qa_image_bytes)
      qa_image.save(qa_plot_path)


    study_data = [
      ('CPR:', formatting.format_cpr(dataset.PatientID)),
      ('Navn:', formatting.person_name_to_name(str(dataset.PatientName))),
      ('Køn:', enums.GENDER_NAMINGS[present_sex]),
      ('Fødselsdagdato:', birthdate),
      ('Højde:', f"{patient_height} cm"),
      ('Vægt:', f"{patient_weight} kg"),
      ('Sprøjtevægt før inj:', f"{inj_weight_before} g"),
      ('Sprøjtevægt efter inj:', f"{inj_weight_after} g"),
      ('Injektion Tidspunkt:', study_datetime.strftime("%H:%M")),
      ('Injektion Dato:', study_datetime.strftime("%d-%m-%Y")),
      ('Fortyndingsfaktor:', formatting.float_dec_to_comma(dataset.thiningfactor)),
      ('Standardtælletal:', formatting.float_dec_to_comma(dataset.stdcnt)),
      ('Undersøgelses type:', dataset.GFRMethod),
      ('Operatør:', operators)
    ]


    # Extract the image
    img_resp_dir = f"{server_config.IMG_RESPONS_DIR}{hospital}/"
    try_mkdir(img_resp_dir)
    
    if 'PixelData' in dataset:
      # Reads DICOM conformant image to PIL displayable image
      pixel_arr = np.frombuffer(dataset.PixelData, dtype=np.uint8)
      pixel_arr = np.reshape(pixel_arr, (1080, 1920, 3))
 
      Im = PIL.Image.fromarray(pixel_arr, mode="RGB")
      Im.save(f'{img_resp_dir}{accession_number}.png')
    
    plot_path = f'main_page/images/{hospital}/{accession_number}.png'

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'image_path': plot_path,
      'previous_samples': [previous_samples],
      'accession_number': accession_number,
      'study_data': study_data,
    }
    if qa_plot_path:
      context['qa_plot_path'] = qa_plot_path

    return render(request, self.template_name, context=context)

  def post(self, request: Type[WSGIRequest], accession_number: str) -> HttpResponse:
    """
      This function provides the functionality of creating a dicom file, from the already existing files

      Retrieves dicom object Updates the dicom files:
        Series Number
        SeriesUID

      To Do:
        [] Assign a the correct Series number at getting them from RIS
        [x] Write this function
        [] Ensure that Series number is not edited by other functions incorrecly 
          {} dicomlib.fill_dicom
          {} fillstudy.Post
        [] Ensure that other functions can handle, existance of multiple studies
          {} pacs_query_wrapper.move_from_pacs
  
      Returns:
        Redirects to fill_study for matching accession Number
    """ 
    current_user = request.user
    hospital_sn  = current_user.department.hospital.short_name
    study_directory = f'{server_config.FIND_RESPONS_DIR}{hospital_sn}/{accession_number}'
    try_mkdir(study_directory)
    #Retrives Dicom object
    dataset = pacs.move_from_pacs(
      current_user,
      accession_number
    )  
    
    #Updates Tags
    dicomlib.fill_dicom(
      dataset,
      series_number=dataset.SeriesNumber
      #New UID maybe, could build it into Series Number function
      )
    dicomlib.save_dicom(f'{study_directory}/{dataset.AccessionNumber}.dcm', dataset)
    #Retrives History
    for study in dataset.clearancehistory:
      study_dataset = pacs.move_from_pacs(current_user, dataset.AccessionNumber)
      dicomlib.save_dicom(f'{study_directory}/{dataset.AccessionNumber}.dcm', study_dataset)

    return redirect('main_page:fill_study', accession_number = accession_number)
