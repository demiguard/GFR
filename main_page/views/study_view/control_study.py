# Python Standard Library
from pathlib import Path
from logging import getLogger
from typing import List, Tuple, Union, Generator, Dict

# Third party packages
from django.forms import formset_factory
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.views.generic import TemplateView


# Clairvoyance packages
from constants import GFR_LOGGER_NAME
from main_page.forms import ConfirmSampleForm
from main_page.forms.base_forms import GrandControlPatient
from main_page.libs import server_config
from main_page.libs.image_generation import get_standard_plot_path
from main_page.models import GFRStudy, StudyStatus, InjectionSample

# Custom type
CsvDataType = Tuple[Generator[List[str], List[List[List[Union[int, float]]]], List[int]], int]

logger = getLogger(GFR_LOGGER_NAME)

class ControlView(LoginRequiredMixin, TemplateView):
  template_name = "main_page/control_study.html"

  def post(self, request: WSGIRequest, AccessionNumber: str) -> HttpResponse:
    try:
      study = GFRStudy.objects.get(AccessionNumber=AccessionNumber)
    except ObjectDoesNotExist:
      return HttpResponseNotFound(request)


  def get(self, request: WSGIRequest, AccessionNumber: str) -> HttpResponse:

    try:
      study = GFRStudy.objects.get(AccessionNumber=AccessionNumber)
    except ObjectDoesNotExist:
      return HttpResponseNotFound(request)

    if study.StudyStatus != StudyStatus.CONTROL:
      return redirect('main_page:fill_study', accession_number=AccessionNumber)

    file_path, _ = get_standard_plot_path(study)
    samples = [
      sample for sample in InjectionSample.objects.filter(Study=study)
    ]

    check_form = GrandControlPatient()

    context = {
      'study' : study,
      'check_form' : check_form,
      'image_path' : file_path,
      'samples' : samples,
      'title'   : server_config.SERVER_NAME,
      'version' : server_config.SERVER_VERSION,
      'AccessionNumber' : AccessionNumber,
    }

    return render(request, self.template_name, context=context)
