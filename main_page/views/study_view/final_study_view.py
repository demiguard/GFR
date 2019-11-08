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
    ris_nr: accession number of the request examination
  """

  template_name = 'main_page/final_study.html'

  def get(self, request: Type[WSGIRequest], AccessionNumber: str) -> HttpResponse:
    """
      Note that this code doesn't use the Examination obejects


    """
    hospital = request.user.department.hospital.short_name
    object_path = f'{server_config.CONTROL_STUDIES_DIR}/{hospital}/{AccessionNumber}/{AccessionNumber}.dcm'


    try:
      dicom_object = dicomlib.dcmread_wrapper(object_path)
    except expression as identifier:
      logger.error(f'Could not find {object_path}')
      return redirect('main_page:control_list_studies')
     
    #Check if Study is confirmed?
    # if not ( '' in dicom_object):
    #   return redirect('main_page:control_study', AccessionNumber=AccessionNumber)

    # Display
    img_resp_dir = f"{server_config.IMG_RESPONS_DIR}{hospital}/"
    try_mkdir(img_resp_dir)
    
    pixel_arr = np.frombuffer(dicom_obj.PixelData, dtype=np.uint8)
    pixel_arr = np.reshape(pixel_arr, (1920, 1080, 3))
    pixel_arr = np.reshape(pixel_arr, (1080, 1920, 3))


    if pixel_arr.shape[0] != 0:
      Im = PIL.Image.fromarray(pixel_arr)
      Im.save(f'{img_resp_dir}{AccessionNumber}.png')
    
    plot_path = f"main_page/images/{hospital}/{AccessionNumber}.png" 
    
    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'image_path': plot_path
    }

    return render(request, self.template_name, context=context)

  def post(self, request: Type[WSGIRequest], AccessionNumber: str) -> HttpResponse:
    
    hosp_sn = request.user.department.hospital.short_name
    obj_dir     = f"{server_config.CONTROL_STUDIES_DIR}{hosp_sn}/{AccessionNumber}/"
    obj_path    = f"{obj_dir}{AccessionNumber}.dcm"
    image_path  = f"{server_config.IMG_RESPONS_DIR}{hosp_sn}/{AccessionNumber}.png"
    dicom_object = dicomlib.dcmread_wrapper(obj_path)

    # We assume there's no threads on the network, we have a Great Firewall, that the hackers paid for!

    # Send information to PACS
    success_rate, error_message = pacs.store_dicom_pacs(dicom_object, request.user)
    logger.info(f"User:{request.user.username} has stored {AccessionNumber} in PACS")
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
      HE = models.HandledExaminations(accession_number=AccessionNumber)
      HE.save()
    else:
      # Try again?
      # Redirect to informative site, telling the user that the connection to PACS is down
      logger.warn(f'Failed to store {AccessionNumber} in pacs, because:{error_message}')
    
    return redirect('main_page:control_list_studies')