from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import loader
from django.shortcuts import redirect

from . import forms
from .libs.query_wrappers import ris_query_wrapper as ris
from .libs.clearance_math import clearance_math
from .libs import Post_Request_handler as PRH

from dateutil import parser as date_parser
import datetime
import glob
import os
import pandas
import numpy
import pydicom
import PIL

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
    PRH.fill_study_post(request, rigs_nr)
    
    if 'calculate' in request.POST:
      return redirect('main_page:present_study', rigs_nr=rigs_nr) 
    #TODO Simon should look at this
    return HttpResponse("YOU HAVE SAVED SOMETHING")

  else: # GET


    # Specify page template
    template = loader.get_template('main_page/fill_study.html')
    
    exam = ris.get_examination(rigs_nr, './tmp') # './tmp' should be put in a configurable thing...

    test_range = range(6)
    today = datetime.datetime.today()
    date, _ = str(today).split(' ')
    test_form = forms.FillStudyTest(initial = {'study_date' : date})
    for f in test_form:
      f.field.widget.attrs['class'] = 'form-control'

    # Get list of csv files
    csv_files = glob.glob("main_page/static/main_page/csv/*.csv")
    csv_names = [os.path.basename(path).split('.')[0] for path in csv_files]

    # Read required data from each csv file  
    csv_data = []
    csv_present_names = []
    for file in csv_files:
      prestring = "Undersøgelse lavet: "
      
      temp_p = pandas.read_csv(file)
      curr_data = [[] for _ in range(temp_p.shape[0])]

      csv_present_names.append(prestring + temp_p['Measurement date & time'][0])
      for i, row in temp_p.iterrows():
        curr_data[i].append(row['Rack'])
        curr_data[i].append(row['Pos'])
        curr_data[i].append(row['Cr-51 Counts'])
        curr_data[i].append(row['Cr-51 CPM'])

      csv_data.append(curr_data)

    csv_data = zip(csv_present_names, csv_data, csv_names)

    context = {
      'rigsnr': rigs_nr,
      'study_patient_form': forms.Fillpatient_1(initial={
        'cpr': exam.info['cpr'],
        'name': exam.info['name'],
        'sex': exam.info['sex'],
        'age': exam.info['age']
      }),
      'study_patient_form_2': forms.Fillpatient_2(initial={
        'height': exam.info['height'],
        'weight': exam.info['weight'],
      }),
      'study_dosis_form' : forms.Filldosis(),
      'study_examination_form' : forms.Fillexamination(),
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
  
  #Display
  # pixel_arr = exam.info['image']
  # if pixel_arr.shape[0] != 0:
  #   Im = PIL.Image.fromarray(pixel_arr)
  #   Im.save('main_page/static/main_page/images/{0}/{1}.png'.format(hospital, rigs_nr))
  
  # plot_path = 'main_page/images/{0}/{1}.png'.format(hospital,rigs_nr) 

  template = loader.get_template('main_page/present_study.html')
  
  context = {
    'name'  : exam.info['name'],
    'age'   : exam.info['age'],
    'date'  : exam.info['date'],
    'BSA'   : exam.info['BSA'],
    'sex'   : exam.info['sex'],
    'height': exam.info['height'],
    'weight': exam.info['weight'],
    'GFR'   : exam.info['GFR'],
    'GFR_N' : exam.info['GFR_N'],
    'image_path' : exam.info['image'],
    'Nyrefunction' : clearance_math.kidney_function(float(exam.info['GFR_N']), exam.info['CPR'])
  }


  return HttpResponse(template.render(context,request))