from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.template import loader
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest

import numpy as np
from pathlib import Path
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
    hospital = request.user.department.hospital.short_name

    dataset = dicomlib.dcmread_wrapper(Path(
      server_config.FIND_RESPONS_DIR,
      hospital,
      accession_number,
      f"{accession_number}.dcm"
    ))

    # Determine whether QA plot should be displayable - i.e. the study has multiple
    # test values
    n_len = lambda obj: 0 if not obj else len(obj) # Helper function which asigns length 0 to None objects

    show_QA_button = (n_len(dataset.get("ClearTest")) > 1)

    # Display
    img_resp_dir = f"{server_config.IMG_RESPONS_DIR}{hospital}/"
    try_mkdir(img_resp_dir)
    
    pixel_data = dataset.get("PixelData")
    if pixel_data:
      pixel_data = np.frombuffer(dataset.PixelData, dtype=np.uint8)
      pixel_data = np.reshape(pixel_data, (1080, 1920, 3)) # Reshape to presentable shape

      img = PIL.Image.fromarray(pixel_data)
      img.save(Path(
        img_resp_dir,
        f"{accession_number}.png"
      ))

    plot_path = f"main_page/images/{hospital}/{accession_number}.png" 
    
    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'name': dataset.get("PatientName"),
      'date': dataset.get("StudyDate"),
      'accession_number': accession_number,
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