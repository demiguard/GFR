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

class DeletedStudiesView(LoginRequiredMixin, TemplateView):
  """
  Displays deleted studies from 30 days ago.
  Works like a trashcan for files, that deleted studies lie for 30 days until
  they are completly removed.
  """

  template_name = "main_page/deleted_studies.html"

  def get(self, request):
    # Get list of all deleted studies
    user_hosp = request.user.department.hospital.short_name

    deleted_studies = [] # Contains ExaminationInfo objects

    deleted_dir = f"{server_config.DELETED_STUDIES_DIR}{user_hosp}/"
    
    studies =  ris.get_studies(deleted_dir)
    today = datetime.datetime.today()

    for study in studies:
      #Check if Study is old
      if ((today - datetime.datetime.strptime(study.StudyDate,'%Y%m%d')).days > server_config.DAYS_THRESHOLD):
        # Delete the study
        study_dir_path = f'{deleted_dir}{study.AccessionNumber}/'
        shutil.rmtree(study_dir_path)
      else:
        #TODO: Change Jinja templete such that it's a dicom object and not an Examination Info 
        deleted_studies.append(examination_info.deserialize(study))    
    
    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'deleted_studies': deleted_studies,
    }

    return render(request, self.template_name, context)
