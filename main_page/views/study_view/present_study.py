"""This view is showing the user the result they have just calculated"""

# Python Standard library
from logging import getLogger
from pathlib import Path
import shutil
from typing import Type, List, Tuple, Union, Generator


# Third Party Packages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.handlers.wsgi import WSGIRequest
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.views.generic import TemplateView

# Clairvoyance Packages
from constants import GFR_LOGGER_NAME
from main_page.models import GFRStudy, InjectionSample, StudyStatus
from main_page.libs.image_generation import generate_standard_plot
from main_page.libs import server_config





# Custom type
CsvDataType = Tuple[Generator[List[str], List[List[List[Union[int, float]]]], List[int]], int]

logger = getLogger(GFR_LOGGER_NAME)


class PresentStudyView(LoginRequiredMixin, TemplateView):
  """
  Presenting the end result of an examination

  Args:
    request: The HTTP request
    accession_number: accession number of the request examination
  """

  template_name = 'main_page/present_study.html'

  def get(self, request: WSGIRequest, accession_number: str) -> HttpResponse:
    try:
      study = GFRStudy.objects.get(AccessionNumber=accession_number)
    except ObjectDoesNotExist:
      return HttpResponseNotFound()

    samples = [sample for sample in InjectionSample.objects.filter(Study=study)]

    try:
      plot_path = generate_standard_plot(
        study,
        samples
      )
    except ValueError:
      logger.error(f"Could not generate an image for {accession_number}")
      return redirect('main_page:fill_study', accession_number=accession_number)

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'name': study.PatientName,
      'date': study.StudyDateTime,
      'accession_number': accession_number,
      'image_path': plot_path,
    }

    return render(request, self.template_name, context=context)

  def post(self, request: WSGIRequest, accession_number: str) -> HttpResponse:
    try:
      study = GFRStudy.objects.get(AccessionNumber=accession_number)
    except ObjectDoesNotExist:
      return HttpResponseNotFound()

    if 'control' in request.POST:
      study.StudyStatus = StudyStatus.CONTROL
      study.save()
      return redirect('main_page:list_studies')

    samples = [sample for sample in InjectionSample.objects.filter(Study=study)]

    try:
      plot_path = generate_standard_plot(
        study,
        samples
      )
    except ValueError:
      logger.error(f"Could not generate an image for {accession_number}")
      return redirect('main_page:fill_study', accession_number=accession_number)

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'name': study.PatientName,
      'date': study.StudyDateTime,
      'accession_number': accession_number,
      'image_path': plot_path,
    }

    return render(request, self.template_name, context=context)