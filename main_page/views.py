from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import loader
from django.shortcuts import redirect

from . import forms
from .libs import ris_query_wrapper as ris
from .libs.clearance_math import clearance_math

import datetime
import glob
import os
import pandas
import numpy

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

    success, error_msgs = ris.is_valid_study(cpr, name, study_date, ris_nr)

    if success:
      #ris.store_study(cpr, name, study_date, ris_nr)
      
      # redirect to fill_study/ris_nr 
      return redirect('main_page:fill_study', rigs_nr=ris_nr)
    else:
      context['error_msgs'] = error_msgs

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
  if request.method == 'POST':
    print(request.POST)

    if 'calculate' in request.POST: # 'Bere  exam.info['BSA'],
   
      print("Calculate")

      # Redirect to study presentation page  exam.info['BSA'],
    

    elif 'calculate-nodb' in request.POST: # 'Beregn udenom databasen' clicked
      print("Calcuate around database")

      # Redirect to study presentation page, without saving to database

    elif 'save' in request.POST: # 'Gem' clicked - save in temp database
      print("Save in database")

      # Redirect back to list_studies

    elif 'cancel' in request.POST: # 'Afbryd' clicked
      print("Cancel filling out parient info")

      # Discard form info and redirect back to list_studies


  # Specify page template
  template = loader.get_template('main_page/fill_study.html')
  
  exam = ris.get_examination(rigs_nr, './tmp') # './tmp' should be put in a configurable thing...
  exam_info = exam.info

  test_range = range(6)
  test_form = forms.FillStudyTest()
  for f in test_form:
    f.field.widget.attrs['class'] = 'form-control'

  # Get list of csv files
  csv_files = glob.glob("main_page/static/main_page/csv/*.csv")
  csv_names = [os.path.basename(path).split('.')[0] for path in csv_files]

  # Read required data from each csv file  
  csv_data = []
  for file in csv_files:
    temp_p = pandas.read_csv(file)
    curr_data = [[] for _ in range(temp_p.shape[0])]

    for i, row in temp_p.iterrows():
      curr_data[i].append(row['Rack'])
      curr_data[i].append(row['Pos'])
      curr_data[i].append(row['Cr-51 Counts'])
      curr_data[i].append(row['Cr-51 CPM'])

    csv_data.append(curr_data)

  csv_data = zip(csv_names, csv_data)

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
    },
    'csv_data': csv_data
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
  #Compute Body surface area
  height = float(exam.info['height'])
  weight = float(exam.info['weight'])

  print(type(height), type(weight))

  Body_surface_area = clearance_math.surface_area(height, weight)
  exam.info['BSA'] = str(Body_surface_area)

  # GFR, GFR_N = clearance_math.calc_clearance(
    # exam.info['inj_time'],
    # exam.info['sam_t'],
    # exam.info['tch_cnt'], 
    # exam.info['BSA'],
    # exam.info['dosis'],
    # method=exam.info['method']
  # )


  #Display
  plot_path = clearance_math.generate_plot(
    numpy.array([[],[]]),
    numpy.array([[],[]]),
    rigs_nr,hospital
  )
  plot_path = plot_path[17:] # #hacky
  #Write to Dicom object

  #

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