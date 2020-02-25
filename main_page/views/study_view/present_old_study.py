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

    if 'ClearTest' in dataset:
      for test in dataset.ClearTest:

        injection_datetime = datetime.datetime.strptime(test.SampleTime, '%Y%m%d%H%M')
        previous_sample_dates.append(injection_datetime.strftime('%Y-%m-%d'))
        previous_sample_times.append(injection_datetime.strftime('%H:%M'))
        previous_sample_counts.append(test.cpm)

    previous_samples = zip(
      previous_sample_dates,
      previous_sample_times,
      previous_sample_counts
    )

    # Extract study data to present
    study_date = dataset.StudyDate
    study_time = dataset.StudyTime
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
      print("ENTERED HERE!")
      operators = ', '.join([str(x) for x in operators])
    elif not operators:
      operators = ""

    patient_height = formatting.float_dec_to_comma(dataset.PatientSize * 100)
    patient_weight = formatting.float_dec_to_comma(dataset.PatientWeight)
    inj_weight_before = formatting.float_dec_to_comma(dataset.injbefore)
    inj_weight_after = formatting.float_dec_to_comma(dataset.injafter)

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

    return render(request, self.template_name, context=context)
