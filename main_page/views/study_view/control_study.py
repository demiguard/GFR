from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.template import loader
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest


import pydicom
import shutil
import os
import datetime
import logging
import PIL
import glob
import numpy as np
from pydicom import Dataset
from pandas import DataFrame
from typing import Type, List, Tuple, Union, Generator, Dict
from pathlib import Path

from main_page.libs.dirmanager import try_mkdir
from main_page.libs.query_wrappers import pacs_query_wrapper as pacs
from main_page.libs.query_wrappers import ris_query_wrapper as ris
from main_page.libs import dataset_creator
from main_page.libs import server_config
from main_page.libs import samba_handler
from main_page.libs import formatting
from main_page.libs import dicomlib
from main_page.libs import enums
from main_page.forms import base_forms
from main_page import models
from main_page import log_util

# Custom type
CsvDataType = Tuple[Generator[List[str], List[List[List[Union[int, float]]]], List[int]], int]

logger = log_util.get_logger(__name__)


class ControlView(LoginRequiredMixin, TemplateView):
  template_name = "main_page/control_study.html"

  def init_forms(self, dataset : Dataset) -> Dict:

    #GrandControlPatient Initiation
    GrandForm = base_forms.GrandControlPatient()

    #ControlPatient6 
    FormSamples = []
    for sample in dataset.ClearTest:
      sample_date, sample_time = formatting.splitDateTimeStr(sample.SampleTime)

      if 'Deviation' in sample:
        deviation = sample.Deviation
      else:
        deviation = 0

      FormSample = base_forms.ControlPatient6({
        'sample_time' : sample_time,
        'sample_date' : sample_date,
        'sample_cnt'  : sample.cpm,
        'sample_devi' : deviation
      })
      FormSamples.append(FormSample)

    return {
      'GrandForm'    : GrandForm,
      'Samples'      : FormSamples,
    }

  def post(self, request, AccessionNumber):
    post_req = request.POST
    hopital_sn = request.user.department.hospital.short_name
    dir_path = Path(server_config.CONTROL_STUDIES_DIR,hopital_sn, AccessionNumber)
    file_path = Path(dir_path,f'{AccessionNumber}.dcm')

    if post_req['control'] == 'Afvis':
      fill_study_dir = Path(server_config.FIND_RESPONS_DIR, hopital_sn, AccessionNumber)
      if fill_study_dir.exists():
        shutil.rmtree(fill_study_dir)
      shutil.move(dir_path, fill_study_dir)

      return redirect('main_page:fill_study', accession_number = AccessionNumber)
    elif post_req['control'] == 'Godkend og send til PACS':
      file_path   = Path(dir_path,f'{AccessionNumber}.dcm')
      image_path  = Path(server_config.IMG_RESPONS_DIR,hopital_sn,f"{AccessionNumber}.png")

      dataset = dicomlib.dcmread_wrapper(file_path)
      bamid = post_req['bamID'].lower().swapcase()

      dicomlib.fill_dicom(dataset, bamid=bamid)
      dicomlib.save_dicom(file_path, dataset)

      # Send information to PACS
      success_rate, error_message = pacs.store_dicom_pacs(dataset, request.user)
      logger.info(f"User:{request.user.username} has stored {AccessionNumber} in PACS")
      if success_rate:
        # move the directroy with file + history to cache
        try:
          cache_path = Path(server_config.SEARCH_CACHE_DIR, AccessionNumber)
          shutil.move(dir_path, cache_path)
        except OSError as error:
          logger.error(f'Could not remove directory: {dir_path}')
        # Store the RIS number in the HandleExaminations table
        HE = models.HandledExaminations(accession_number=AccessionNumber)
        HE.save()
      else:
        # Try again?
        # Redirect to informative site, telling the user that the connection to PACS is down
        logger.warn(f'Failed to store {AccessionNumber} in pacs, because:{error_message}')
    else:
      logger.error(f'Invalid Post request for control Study {AccessionNumber}')

    return redirect('main_page:control_list_studies')

  def get(self, request, AccessionNumber):
    hospital   = request.user.department.hospital.short_name
    hopital_sn = request.user.department.hospital.short_name

    filepath = f'{server_config.CONTROL_STUDIES_DIR}{hopital_sn}/{AccessionNumber}/{AccessionNumber}.dcm'
    dataset = dicomlib.dcmread_wrapper(filepath)
    plot_path_full =f'{server_config.IMG_RESPONS_DIR}{hospital}/{AccessionNumber}.png'
    if not os.path.exists(plot_path_full):
      img_resp_dir = f"{server_config.IMG_RESPONS_DIR}{hospital}/"
      try_mkdir(img_resp_dir)
    
      pixel_arr = np.frombuffer(dataset.PixelData, dtype=np.uint8)
      pixel_arr = np.reshape(pixel_arr, (1920, 1080, 3))
      pixel_arr = np.reshape(pixel_arr, (1080, 1920, 3))

      if pixel_arr.shape[0] != 0:
        Im = PIL.Image.fromarray(pixel_arr)
        Im.save(f'{img_resp_dir}{AccessionNumber}.png')
    
    static_path = f'main_page/images/{hospital}/{AccessionNumber}.png'

    if dataset.PatientSex == 'M':
      present_sex = 0
    else:
      present_sex = 1
      
    injeciton_date, injeciton_time = formatting.splitDateTimeStr( dataset.injTime )
  
    image_comments = dataset.get("ImageComments")

    InfoDir = {
      'cpr'                 : formatting.format_cpr(dataset.PatientID),
      'name'                : formatting.person_name_to_name(str(dataset.PatientName)),
      'sex'                 : enums.GENDER_NAMINGS[present_sex],
      'vial_number'         : dataset.VialNumber,
      'height'              : formatting.float_dec_to_comma(dataset.PatientSize * 100),
      'weight'              : formatting.float_dec_to_comma(dataset.PatientWeight),
      'vial_weight_before'  : formatting.float_dec_to_comma(dataset.injbefore),      
      'vial_weight_after'   : formatting.float_dec_to_comma(dataset.injafter),      
      'injection_time'      : injeciton_time,      
      'injection_date'      : injeciton_date,
      'thin_fac'            : formatting.float_dec_to_comma(dataset.thiningfactor),
      'study_type'          : dataset.GFRMethod,
      'comment'             : image_comments,
      'stdCnt'              : formatting.float_dec_to_comma(dataset.stdcnt)
    }

    context = {
      'title'   : server_config.SERVER_NAME,
      'version' : server_config.SERVER_VERSION,
      'info'    : InfoDir,
      'AccessionNumber' : AccessionNumber,
      'static_path'     : static_path
    }
    context.update(self.init_forms(dataset))

    return render(request, self.template_name, context=context)
