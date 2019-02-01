from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import loader
from django.shortcuts import redirect

from . import forms
from .libs import ris_query_wrapper as ris
from .libs.clearance_math import clearance_math

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

    if 'calculate' in request.POST: # 'Bere  exam.info['BSA'],
      # Extract study data 
      # Construct datetime for injection time
      inj_time = request.POST['injection_time']
      inj_date = request.POST['injection_date']
      inj_datetime = date_parser.parse("{0} {1}".format(inj_date, inj_time))

      # Construct datetimes for study times
      sample_dates = request.POST.getlist('test_date')[:-1]
      sample_times = request.POST.getlist('test_time')[:-1]
      
      sample_datetimes = numpy.array([date_parser.parse("{0} {1}".format(date, time)) 
                            for time, date in zip(sample_times, sample_dates)])

      # Measured tec99 counts
      tec_counts = numpy.array([int(x) for x in request.POST.getlist('test_value')[:-1]])

      # Compute surface area
      weight = float(request.POST['weight'])
      height = float(request.POST['height'])
      BSA = clearance_math.surface_area(weight, height)

      # Compute dosis
      inj_weight_before = float(request.POST['vial_weight_before'])
      inj_weight_after = float(request.POST['vial_weight_after'])
      inj_weight = inj_weight_before - inj_weight_after
      
      # TODO: CHANGE THE FACTOR AND STANDARD COUNT TO BE ON THE PAGE AS WELL

      STD_CNT = int(request.POST['std_cnt'])
      FACTOR = int(request.POST['thin_fac'])

      dosis = clearance_math.dosis(inj_weight, FACTOR, STD_CNT)

      # Determine study method
      # TODO: Possibly make an Enum in the future
      study_type = int(request.POST['study_type'])
      if study_type == 0:
        method = "EPV"
      elif study_type == 1:
        method = "EPB"
      elif study_type == 2:
        method = "Multi-4"
      else:
        method="INVALID METHOD"

      # Calculate GFR
      gfr, gfr_norm = clearance_math.calc_clearance(
        inj_datetime, 
        sample_datetimes,
        tec_counts,
        BSA,
        dosis,
        method=method
      )

      # Generate plot
      if study_type >= 1: # Not EPV or EPB
        data_points1 = numpy.array([sample_datetimes, tec_counts])
      else:
        data_points1 = numpy.array([[], []])
      
      age = int(request.POST['age'])
      data_points2 = numpy.array([[age], [gfr_norm]])

      plot_path = clearance_math.generate_plot(
        data_points1,
        data_points2,
        rigs_nr
      )

      # Save GFR and extracted study data to DICOM corresponding DICOM object
      # TODO: Update these to the ones Flemming found
      BSA_TAG = (0x0017, 0x0017)
      GFR_TAG = (0xDEAD, 0xBEEF)
      GFR_NORM_TAG = (0xDEAD, 0xBEFF)
      INJ_WEIGHT_DIFF_TAG = (0xCAAF, 0x0001)
      INJ_WEIGHT_BEFORE_TAG = (0xCAAF, 0x8085)
      INJ_WEIGHT_AFTER_TAG = (0xCAAF, 0x0807)
      INJ_DATETIME_TAG = (0xCAAF, 0xABCD)
      METHOD_TAG = (0x0667, 0x0667)
      WEIGHT_TAG = (0x0010, 0x1030)
      HEIGHT_TAG = (0x0010, 0x1020)

      BSA_REP = "FL"
      GFR_REP = "FL"
      GFR_NORM_REP = "FL" 
      INJ_WEIGHT_DIFF_REP = "FL"
      INJ_WEIGHT_BEFORE_REP = "FL"
      INJ_WEIGHT_AFTER_REP = "FL"
      INJ_DATETIME_REP = "DT"
      METHOD_REP = "ST"
      WEIGHT_REP = "DS"
      HEIGHT_REP = "DS"
      
      # Tag location for where to store
      store_tags = [
        BSA_TAG,
        GFR_TAG,
        GFR_NORM_TAG,
        INJ_WEIGHT_DIFF_TAG,
        INJ_WEIGHT_BEFORE_TAG,
        INJ_WEIGHT_AFTER_TAG,
        INJ_DATETIME_TAG,
        METHOD_TAG,
        WEIGHT_TAG,
        HEIGHT_TAG
      ]

      # Values to store
      store_values = [
        BSA,
        gfr,
        gfr_norm,
        inj_weight,
        inj_weight_before,
        inj_weight_after,
        inj_datetime,
        method,
        weight,
        height
      ]

      # Dicom value representations for each element
      store_value_reps = [
        BSA_REP,
        GFR_REP,
        GFR_NORM_REP,
        INJ_WEIGHT_DIFF_REP,
        INJ_WEIGHT_BEFORE_REP,
        INJ_WEIGHT_AFTER_REP,
        INJ_DATETIME_REP,
        METHOD_REP,
        WEIGHT_REP,
        HEIGHT_REP
      ]

      dcm_obj_path = './tmp/{0}.dcm'.format(rigs_nr)
      ris.store_dicom(dcm_obj_path, store_tags, store_values, store_value_reps)

      print(rigs_nr)

      # Store dicom object in PACS
      # TODO: SET ADDRESS FOR PACS INSTEAD OF TESTING SERVER
      dcm_img_path = 'main_page/static/main_page/images/RH/{0}.dcm'.format(rigs_nr)
      
      img2dcm_query = [
        'img2dcm',                    # Path to img2dcm # TODO: Change this to be an absolute path to the program on the production server (rememeber to set the dcm tool kit system variable path)
        'main_page/static/main_page/images/RH/{0}.bmp'.format(rigs_nr),    # Input location
        dcm_img_path,                 # Output location
        '-sc',                        # Write as secondary capture SOP class
        '-i',                         # Specify input image format
        'BMP'
      ]

      # TODO: Check exit-code of query and handle errors
      ris.execute_query(img2dcm_query)

      # Read StudyInstanceUID from main dicom object, to allow storage of image together with it
      dcm_obj = pydicom.dcmread(dcm_obj_path)
      study_UID = dcm_obj.StudyInstanceUID

      # Store both dicom objects; main dicom object and image object
      img_obj = pydicom.dcmread(dcm_img_path)
      img_obj.StudyInstanceUID = study_UID

      dcm_obj.SeriesInstanceUID = img_obj.SeriesInstanceUID
      dcm_obj.SOPClassUID = img_obj.SOPClassUID
      dcm_obj.SOPInstanceUID = img_obj.SOPInstanceUID

      img_obj.save_as(dcm_img_path)
      dcm_obj.save_as(dcm_obj_path)

      # Execute store query
      store_query = [
        'storescu',                   # Path to storescu # TODO: Change to absolute path, see above img2dcm
        '-aet',                       # Set source arguments
        ris.CALLING_AET,              # Calling AET (our own AET)
        '-aec',                       # Set destination arguments
        ris.PACS_AET,                 # Valid AET on PACS server
        ris.PACS_IP,                  # IP of PACS server
        ris.PACS_PORT,                # Port of PACS server
        dcm_obj_path,                 # Store both obj and img
        dcm_img_path
      ]

      # TODO: Check exit-code of query and handle errors
      ris.execute_query(store_query)

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
  
  #Display
  pixel_arr = exam.info['image']
  if pixel_arr.shape[0] != 0:
    Im = PIL.Image.fromarray(pixel_arr)
    Im.save('main_page/static/main_page/images/{0}/{1}.png'.format(hospital, rigs_nr))
  
  plot_path = 'main_page/images/{0}/{1}.png'.format(hospital,rigs_nr) 

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
    'image_path' : plot_path,
    'Nyrefunction' : ''
  }


  return HttpResponse(template.render(context,request))