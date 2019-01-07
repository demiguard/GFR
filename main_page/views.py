from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import loader

from . import forms
from .libs import ris_query_wrapper as ris

import datetime

# Create your views here.
def index(request):
  # Specify page template
  template = loader.get_template('main_page/index.html')

  context = {
    'login_form': forms.LoginForm()
  }

  return HttpResponse(template.render(context, request))


def new_study(request):
  # Specify page template
  template = loader.get_template('main_page/new_study.html')

  context = {
    'study_form': forms.NewStudy(initial={'study_date': datetime.date.today})
  }

  return HttpResponse(template.render(context, request))


def list_studies(request):
  """
    1. get studies from RIGS (Using wrapper functions)
    2. display studies
  """
  # Specify page template
  template = loader.get_template('main_page/list_studies.html')

  bookings = ris.get_all('RH_EDTA')

  context = {
    'bookings': bookings
  }

  return HttpResponse(template.render(context, request))

def fill_study(request, rigs_nr):
  # Specify page template
  template = loader.get_template('main_page/fill_study.html')
  
  exam_info = ris.get_examination(rigs_nr, './tmp') # './tmp' should be put in a configurable thing...

  test_range = range(6)
  test_form = forms.FillStudyTest()

  context = {
    'rigsnr': rigs_nr,
    'study_info_form': forms.FillStudyInfo(initial={
      'name': exam_info.name,
      'sex': exam_info.sex,
      'height': exam_info.height,
      'weight': exam_info.weight,
      'age': exam_info.age
    }),
    'study_type_form': forms.FillStudyType({'study_type': 0}), # Default: 'Et punkt voksen'
    'test_context': {
      'test_range': test_range,
      'test_form': test_form
    }
  }

  return HttpResponse(template.render(context, request))


def fetch_study(request):
  # Specify page template
  template = loader.get_template('main_page/fetch_study.html')

  context = {

  }

  return HttpResponse(template.render(context, request))