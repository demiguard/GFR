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
from pydicom import Dataset
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
from main_page.forms import base_forms
from main_page import models

# Custom type
CsvDataType = Tuple[Generator[List[str], List[List[List[Union[int, float]]]], List[int]], int]

from main_page import log_util

logger = log_util.get_logger(__name__)

class ControlView(LoginRequiredMixin, TemplateView):
  template_name = "main_page/control_study.html"

  def init_forms(self, PatientDataset : Dataset) -> Dict:

    #GrandControlPatient Initiation
    if PatientDataset.PatientSex == 'M':
      present_sex = 0
    else:
      present_sex = 1
      
    injeciton_date, injeciton_time = formatting.splitDateTimeStr( PatientDataset.injTime )

    method =  PatientDataset.GFRMethod
    if(method == 'En blodprøve, Voksen' ):
      methodVal = 0
    elif (method == 'En blodprøve, Børn'):
      methodVal = 1
    elif (method == 'Flere blodprøver'):
      methodVal = 2
    else:
      raise AttributeError()
  
    GrandForm = base_forms.GrandControlPatient(initial={
      'cpr'                 : formatting.format_cpr(PatientDataset.PatientID),
      'name'                : formatting.person_name_to_name(str(PatientDataset.PatientName)),
      'sex'                 : present_sex,
      'birthdate'           : formatting.convert_date_to_danish_date(PatientDataset.PatientBirthDate, sep='-'),
      'height'              : PatientDataset.PatientSize * 100,
      'weight'              : PatientDataset.PatientWeight,
      'vial_weight_before'  : PatientDataset.injbefore,      
      'vial_weight_after'   : PatientDataset.injafter,      
      'injection_time'      : injeciton_time,      
      'injection_date'      : injeciton_date,
      'thin_fac'            : PatientDataset.thiningfactor,
      'study_type'          : methodVal,
      'stdCnt'              : PatientDataset.stdcnt
    })

    #ControlPatient6 
    FormSamples = []
    for sample in PatientDataset.ClearTest:
      sample_date, sample_time = formatting.splitDateTimeStr(sample.SampleTime)
      FormSample = base_forms.ControlPatient6({
        'sample_time' : sample_time,
        'sample_date' : sample_date,
        'sample_cnt'  : sample.cpm
      })
      FormSamples.append(FormSample)

    return {
      'GrandForm'    : GrandForm,
      'Samples'      : FormSamples,
    }

  def post(self, request, AccessionNumber):

    post_req = request.POST
    hopital_sn = request.user.department.hospital.short_name
    dir_path =f'{server_config.CONTROL_STUDIES_DIR}{hopital_sn}/{AccessionNumber}/'
    file_path = f'{dir_path}{AccessionNumber}.dcm'

    if(post_req['control'] == 'Afvis'):
      fill_study_dir = f'{server_config.FIND_RESPONS_DIR}{hopital_sn}/{AccessionNumber}'
      shutil.move(dir_path, fill_study_dir)

      return redirect('main_page:fill_study', accession_number = AccessionNumber)
    elif (post_req['control'] == 'Godkend'):
      print(post_req)

      file_path = f'{dir_path}{AccessionNumber}.dcm'
      dataset = dicomlib.dcmread_wrapper(file_path)
      bamid = post_req['bamID'].lower().swapcase()

      dicomlib.fill_dicom(dataset, bamid=bamid)
      dicomlib.save_dicom(file_path, dataset)

      return redirect('main_page:final_present', AccessionNumber=AccessionNumber)

    else:
      logger.error(f'Invalid Post request for control Study {AccessionNumber}!')
    



    context = {
      'title'   : server_config.SERVER_NAME,
      'version' : server_config.SERVER_VERSION,
      'AccessionNumber' : AccessionNumber

    }
    context.update(self.init_forms(dataset))

    return render(request, self.template_name, context=context)

  def get(self, request, AccessionNumber):
    
    hopital_sn = request.user.department.hospital.short_name

    filepath = f'{server_config.CONTROL_STUDIES_DIR}{hopital_sn}/{AccessionNumber}/{AccessionNumber}.dcm'
    dataset = dicomlib.dcmread_wrapper(filepath)

    context = {
      'title'   : server_config.SERVER_NAME,
      'version' : server_config.SERVER_VERSION,
      'AccessionNumber' : AccessionNumber
    }
    context.update(self.init_forms(dataset))


    return render(request, self.template_name, context=context)
