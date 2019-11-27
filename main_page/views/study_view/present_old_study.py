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