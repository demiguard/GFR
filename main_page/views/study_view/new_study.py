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

class NewStudyView(LoginRequiredMixin, TemplateView):
  template_name = 'main_page/new_study.html'

  def get(self, request: Type[WSGIRequest]) -> HttpResponse:
    context = {
      'study_form': forms.NewStudy(initial={
          'study_date': datetime.date.today().strftime('%d-%m-%Y')
        }
      )
    }

    return render(request, self.template_name, context)

  def post(self, request: Type[WSGIRequest]) -> HttpResponse:
    # Create and store dicom object for new study
    cpr = request.POST['cpr'].strip()
    name = request.POST['name'].strip()
    study_date = request.POST['study_date'].strip()
    ris_nr = request.POST['rigs_nr'].strip()

    new_study_form = forms.NewStudy(initial={
      'cpr': cpr,
      'name': name,
      'study_date': study_date,
      'rigs_nr': ris_nr
    })

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'study_form': new_study_form,
      'error_message' : ''
    }

    # Ensure validity of study
    validation_status, error_messages = formatting.is_valid_study(
      cpr, name, study_date, ris_nr)

    if validation_status:
      study_date = datetime.datetime.strptime(study_date, '%d-%m-%Y').strftime('%Y%m%d')
      
      hospital_sn = request.user.department.hospital.short_name
      study_directory = f'{server_config.FIND_RESPONS_DIR}{hospital_sn}/{ris_nr}/'
      try_mkdir(study_directory, mk_parents=True)

      dataset = dataset_creator.get_blank(
        cpr,
        name,
        study_date,
        ris_nr,
        hospital_sn
      )
      
      # Get history from pacs
      if formatting.check_cpr(cpr):
        #CPR is valid, so we can retrieve history from pacs
        #TODO: Get history from pacs
        pass
      else:
        #Error
        pass

      dicomlib.save_dicom( 
        f'{study_directory}{ris_nr}.dcm',
        dataset
      )

      # redirect to fill_study/ris_nr
      return redirect('main_page:fill_study', accession_number=ris_nr)
    else:
      context['error_messages'] = error_messages
      return render(request, self.template_name, context)


