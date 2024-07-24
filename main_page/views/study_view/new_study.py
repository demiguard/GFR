# Python standard library
import datetime
import logging

# Third party packages
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest

from pydicom.uid import generate_uid

# Clairvoyance Packages
from constants import GFR_LOGGER_NAME
from main_page.libs import server_config
from main_page.forms import base_forms
from main_page import models

logger = logging.getLogger(GFR_LOGGER_NAME)

class NewStudyView(LoginRequiredMixin, TemplateView):
  template_name = 'main_page/new_study.html'

  def get(self, request: WSGIRequest) -> HttpResponse:
    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'study_form': base_forms.NewStudy(initial={
          'study_date': datetime.date.today().strftime('%d-%m-%Y')
        }
      )
    }

    return render(request, self.template_name, context)

  def post(self, request: WSGIRequest) -> HttpResponse:
    user: models.User = request.user

    if user.department is None:
      raise Exception

    # Create and store dicom object for new study
    new_study_form = base_forms.NewStudy(request.POST)

    if new_study_form.is_valid():
      models.GFRStudy.objects.create(
        StudyUID=generate_uid,
        StudyStatus=models.StudyStatus.INITIAL,
        AccessionNumber=new_study_form.cleaned_data['rigs_nr'],
        StudyID=new_study_form.cleaned_data['rigs_nr'],
        StationName=user.department.config.ris_calling,
        PatientName=new_study_form.cleaned_data['name'],
        PatientBirthDate=None,
        PatientID=new_study_form.cleaned_data['cpr'],
        StudyDateTime=new_study_form.cleaned_data['study_date'],
        StudyDescription='GFR NØD OPRETTET',
        Department=user.department,
      )
      return redirect('main_page:fill_study', accession_number=new_study_form.cleaned_data['rigs_nr'])
    else:
      print("INVALID!")

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'study_form': new_study_form,
      'error_message' : ''
    }
