from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import loader

from . import forms
from .libs import ris_query_wrapper as ris
from .libs.clearance_math import clearance_math

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
    'study_form': forms.NewStudy(initial={'study_date': datetime.date.today}),
    'error_msg' : ''
  }

  # Handle POST requests
  if request.method == 'POST':
    # Create and store dicom object for new study
    cpr = request.POST['cpr']
    name = request.POST['name']
    study_date = request.POST['study_date']
    ris_nr = request.POST['ris_nr']

    print(request.POST)
    print(cpr)
    print(name)
    print(study_date)
    print(ris_nr)

    success, error_msg = ris.is_valid_study(cpr, name, study_date, ris_nr)

    print(success)
    print(error_msg)

    if success:
      ris.store_study(cpr, name, study_date, ris_nr)
      #TODO redirect to fill_study/ris_nr 
    else:
      # Report error messages back to user
      print(error_msg)

      context['error_msg'] = error_msg
      #return HttpResponse(template.render(context, request))

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
  
  exam = ris.get_examination(rigs_nr, './tmp') # './tmp' should be put in a configurable thing...
  exam_info = exam.info

  test_range = range(6)
  test_form = forms.FillStudyTest()

  print("name:", exam_info['name'])

  context = {
    'rigsnr': rigs_nr,
    'study_info_form': forms.FillStudyInfo(initial={
      'name': exam_info['name'],
      'sex': exam_info['sex'],
      'height': exam_info['height'],
      'weight': exam_info['weight'],
      'age': exam_info['age']
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

def present_study(request, rigs_nr, hospital='RH'): #change default value
  """
  Function for presenting the result

  Args:
    request: The HTTP request
    rigs_nr: The number 
  returns:
  
  """

  DICOM_directory = "./tmp"

  exam = ris.get_examination(rigs_nr, DICOM_directory)
  #MATH


  #Display
  plot_path = clearance_math.generate_plot([],[], rigs_nr,hospital)
  plot_path = plot_path[17:] # #hacky

  template = loader.get_template('main_page/present_study.html')
  
  context = {
    'name'  : exam.info['name'],
    'age'   : exam.info['age'],
    'date'  : exam.info['date'],
    'BSA'   : exam.info['BSA'],
    'sex'   : exam.info['sex'],
    'GFR'   : exam.info['GFR'],
    'GFR_N' : exam.info['GFR_N'],
    'image_path' : plot_path,
    'Nyrefunction' : ''
  }


  return HttpResponse(template.render(context,request))