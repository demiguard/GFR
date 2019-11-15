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

class PresentStudyView(LoginRequiredMixin, TemplateView):
  """
  Presenting the end result of an examination

  Args:
    request: The HTTP request
    accession_number: accession number of the request examination
  """

  template_name = 'main_page/present_study.html'

  def get(self, request: Type[WSGIRequest], accession_number: str) -> HttpResponse:
    base_resp_dir = server_config.FIND_RESPONS_DIR
    hospital = request.user.department.hospital.short_name
    
    DICOM_directory = f"{base_resp_dir}{hospital}/"
    try_mkdir(DICOM_directory, mk_parents=True)

    exam = pacs.get_examination(request.user, accession_number, DICOM_directory)
    
    # Determine whether QA plot should be displayable - i.e. the study has multiple
    # test values
    show_QA_button = (len(exam.tch_cnt) > 1)

    # Display
    img_resp_dir = f"{server_config.IMG_RESPONS_DIR}{hospital}/"
    try_mkdir(img_resp_dir)
    
    pixel_arr = exam.image
    if pixel_arr.shape[0] != 0:
      Im = PIL.Image.fromarray(pixel_arr)
      Im.save(f'{img_resp_dir}{accession_number}.png')
    
    plot_path = f"main_page/images/{hospital}/{accession_number}.png" 
    
    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'name': exam.name,
      'date': exam.date,
      'ris_nr': accession_number,
      'image_path': plot_path,
      'show_QA_button': show_QA_button,
    }

    return render(request, self.template_name, context=context)

  def post(self, request: Type[WSGIRequest], accession_number: str) -> HttpResponse:
    # Send information to PACS
    hosp_sn = request.user.department.hospital.short_name

    control_dir = f"{server_config.CONTROL_STUDIES_DIR}{hosp_sn}/{accession_number}/"
    obj_dir     = f"{server_config.FIND_RESPONS_DIR}{hosp_sn}/{accession_number}/"
    
    # Remove the file + history
    try:
      shutil.move(obj_dir, control_dir)
      logger.debug(f"Successfully moved {obj_dir} to {control_dir}")
    except OSError as error:
      logger.error(f'Could not remove directory: {obj_dir} to {control_dir}')
  
    return redirect('main_page:list_studies')