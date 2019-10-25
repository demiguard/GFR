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

class ControlView(LoginRequiredMixin, TemplateView):
  template_name = "main_page/control_study.html"

  def init_forms(self, PatientDataset : Dataset) -> Dict:

    #ControlPatient1
    if PatientDataset.PatientSex == 'M':
      present_sex = 0
    else:
      present_sex = 1



    FormPersonalInfo = forms.ControlPatient1(initial={
      'cpr'       : formatting.format_cpr(PatientDataset.PatientID),
      'name'      : 'Bob',
      'sex'       : present_sex,
      'birthdate' : formatting.convert_date_to_danish_date(PatientDataset.PatientBirthDate, sep='-')
    })
  

    #ControlPatient2  
    FormPatientSize = forms.ControlPatient2(initial={})
    
    #ControlPatient3  
    FormSampleInit = forms.ControlPatient3(initial={
      'vial_weight_before' : PatientDataset.injbefore,      
      'vial_weight_after' : PatientDataset.injafter,      
      'injection_time' : '00:00',      
      'injection_date' : '12-23-2001'   
    })
    
    #ControlPatient4  
    FormThinMethod = forms.ControlPatient4(initial={})
    
    #ControlPatient5  
    FormStdCnt = forms.ControlPatient5(initial={})
    
    #ControlPatient6 
    FormSamples = forms.ControlPatient6(initial={})
    
    #ControlPatientConfirm
    FormBamID = forms.ControlPatientConfirm(initial={})

    return {
      'PersonalInfo' : FormPersonalInfo,
      'PatientSize'  : FormPatientSize,      
      'SampleInit'   : FormSampleInit,
      'ThinMethod'   : FormThinMethod,
      'StdCnt'       : FormStdCnt,
      'Samples'      : FormSamples,
      'BamID'        : FormBamID 
    }

  def post(self, request, AccessionNumber):
    hopital_sn = request.user.department.hospital.short_name

    filepath = f'{server_config.CONTROL_STUDIES_DIR}{hopital_sn}/{AccessionNumber}/{AccessionNumber}.dcm'
    dataset = dicomlib.dcmread_wrapper(filepath)

    context = {
      'title'   : server_config.SERVER_NAME,
      'version' : server_config.SERVER_VERSION,

    }
    #context.update(self.init_forms(dataset))

    return render(request, self.template_name, context=context)

  def get(self, request, AccessionNumber):
    
    hopital_sn = request.user.department.hospital.short_name

    filepath = f'{server_config.CONTROL_STUDIES_DIR}{hopital_sn}/{AccessionNumber}/{AccessionNumber}.dcm'
    dataset = dicomlib.dcmread_wrapper(filepath)

    context = {
      'title'   : server_config.SERVER_NAME,
      'version' : server_config.SERVER_VERSION,

    }
    context.update(self.init_forms(dataset))


    return render(request, self.template_name, context=context)
