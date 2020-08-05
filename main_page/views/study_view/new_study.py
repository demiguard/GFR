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
from main_page.libs import dataset_creator
from main_page.libs import server_config
from main_page.libs import samba_handler
from main_page.libs import formatting
from main_page.libs import dicomlib
from main_page.libs import enums
from main_page.libs import ae_controller
from main_page.forms import base_forms
from main_page import models


from main_page import log_util

logger = log_util.get_logger(__name__)

def handle_find(dataset, *args, **kwargs ):
  # This function is handling the response from a find send to pacs
  #Check
  if 'logger' in kwargs:
    logger = kwargs['logger']
  if 'pacs_move_association' in kwargs:
    pacs_move_association = kwargs['pacs_move_association']
  else:
    raise Exception('handlefind requires a pacs_move_association as a kwarg')
  if 'serverConfig' in kwargs:
    serverConfig = kwargs['serverConfig']
  else:
    raise Exception('handlefind requires a serverConfig as a kwarg')
  if 'study_directory' in kwargs:
    study_directory = kwargs['study_directory']
  else:
    raise Exception('handlefind requires a study_directory as a kwarg')

  accession_number = dataset.AccessionNumber
  ae_controller.send_move(
    pacs_move_association,
    serverConfig.AE_title,
    dataset,
    handle_move,
    logger=logger,
    study_directory=study_directory,
    accession_number=accession_number
  )


def handle_move(dataset, *args, **kwargs):
  if 'logger' in kwargs:
    logger = kwargs['logger']
  if 'study_directory' in kwargs:
    study_directory = kwargs['study_directory']
  else:
    raise Exception('handlefind requires a study_directory as a kwarg')
  if 'hospital_sn' in kwargs:
    hospital_sn = kwargs['hospital_sn']
  else:
    raise Exception('handlefind requires a hospital_sn as a kwargs')
  if 'accession_number' in kwargs:
    accession_number = kwargs['accession_number']

  target_file = f"{server_config.SEARCH_DIR}{accession_number}.dcm"
  destination = f"{study_directory}{accession_number}.dcm"
  shutil.move(target_file, destination)


class NewStudyView(LoginRequiredMixin, TemplateView):
  template_name = 'main_page/new_study.html'

  def get(self, request: Type[WSGIRequest]) -> HttpResponse:
    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'study_form': base_forms.NewStudy(initial={
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

    new_study_form = base_forms.NewStudy(initial={
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
      
      # Get history from pacs if PACS address is present
      user_config = request.user.department.config

      if user_config.pacs:
        #CPR is valid, so we can retrieve history from pacs
        # So there's a serverConfig(database entry) and server_config(file)
        # See models for explination
        serverConfig = models.ServerConfiguration.objects.get(id=1)
        pacs_find_association = ae_controller.connect(
          user_config.pacs.ip,
          user_config.pacs.port,
          serverConfig.AE_title, #This should be changed to serverConfig.AE_title
          user_config.pacs.ae_title,
          ae_controller.FINDStudyRootQueryRetrieveInformationModel,
          logger=logger
        )
        
        failed_connection = False

        if not pacs_find_association:
          logger.info(f"Unable to create pacs_find_association for retreiving new study history.")
          failed_connection |= True

          pacs_move_association = ae_controller.connect(
            user_config.pacs.ip,
            user_config.pacs.port,
            serverConfig.AE_title, #This should be changed to serverConfig.AE_title
            user_config.pacs.ae_title,
            ae_controller.MOVEStudyRootQueryRetrieveInformationModel,
            logger=logger
          )

          if not pacs_move_association:
            logger.info(f"Unable to create pacs_move_association for retreiving new study history.")
            failed_connection |= True

          if not failed_connection: # Only send find if connection was established
            find_query_dataset = dataset_creator.create_search_dataset(
              '',
              cpr,
              '',
              '',
              ''
            )
            ae_controller.send_find(
              pacs_find_association,
              find_query_dataset, 
              handle_find,
              logger=logger,
              pacs_move_association=pacs_move_association,
              serverConfig=serverConfig,
              study_directory=study_directory,
            )

            pacs_find_association.release()
            pacs_move_association.release()
      else:
        # Error Message should be handled by front end
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


