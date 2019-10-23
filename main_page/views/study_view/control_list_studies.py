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

class ControlListView(LoginRequiredMixin, TemplateView):
  template_name = "main_page/control_list_studies.html"
  
  def get(self, request: Type[WSGIRequest]) -> HttpResponse:
    """
    List all studies that shall be send to Pacs
    """  
    current_hospital = request.user.department.hospital.short_name

    hospital_dir = f'{server_config.CONTROL_STUDIES_DIR}{current_hospital}/'
    try_mkdir(hospital_dir, mk_parents=True)
    datasets = ris.get_studies(hospital_dir)

    datasets = ris.sort_datasets_by_date(datasets)
    #Note that failed dataset should not be able to come here, so we do not need to check if they have failed
    datasets , _ = ris.extract_list_info(datasets)

    context = {
      "title"               : server_config.SERVER_NAME,
      "version"             : server_config.SERVER_VERSION,
      "registered_studies"  : datasets
    }

    return render(request, self.template_name, context)


  
