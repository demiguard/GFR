from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import loader
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from . import forms
from .libs.query_wrappers import ris_query_wrapper as ris
from .libs.clearance_math import clearance_math
from .libs import Post_Request_handler as PRH

from dateutil import parser as date_parser
import datetime
import glob
import os
import shutil
import pandas
import numpy
import pydicom
import PIL
import glob
import pprint


def index(request):
  if request.method == 'POST':
    print(request.POST)
    login_form = forms.LoginForm(data=request.POST)

    if login_form.is_valid():
      user = authenticate(
        request, 
        username=request.POST['username'], 
        password=request.POST['password'],
        hosp=request.POST['hospital']
      )

      if user:
        login(request, user)

        if user.is_authenticated:
          return redirect('main_page:list_studies')
    
    return redirect('main_page:index')
  else:
    # Specify page template
    template = loader.get_template('main_page/index.html')

    context = {
      'login_form': forms.LoginForm()
    }

    return HttpResponse(template.render(context, request))


@login_required(login_url='/')
def logout_page(request):
  logout(request)
  return redirect('main_page:index')


@login_required(login_url='/')
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


@login_required(login_url='/')
def list_studies(request):
  """
    1. get studies from RIGS (Using wrapper functions)
    2. display studies
  """
  # Specify page template
  template = loader.get_template('main_page/list_studies.html')

  bookings = ris.get_all('RH_EDTA')

  for booking in bookings:
    booking.name = booking.info['name']
    booking.date = booking.info['date']
    booking.cpr  = booking.info['cpr']
    booking.ris_nr = booking.info['ris_nr']

  # TODO: Move this into ris query wrapper (v2.0 when ris_query_wrapper is split into a pacs wrapper as well)
  # Fetch all old bookings
  old_bookings = []
  for dcm_file in glob.glob('./tmp/*.dcm'):
    # Delete file if more than one week since procedure start
    
    dcm_dirc, dcm_name = dcm_file.rsplit('/',1)
    dcm_name, _ = dcm_name.rsplit('.',1)
    exam_info = ris.get_examination(dcm_name, dcm_dirc)
    procedure_date = datetime.datetime.strptime(exam_info.info['date'], '%d/%m-%Y')

    now = datetime.datetime.now()
    time_diff = now - procedure_date
    days_diff = time_diff.days
    
    DAYS_THRESHOLD = 7

    if days_diff >= DAYS_THRESHOLD:
      os.remove(dcm_file)
      continue

    # read additional contents
    
    exam_info.name = exam_info.info['name']
    exam_info.date = exam_info.info['date']
    exam_info.cpr = exam_info.info['cpr']
    exam_info.ris_nr = exam_info.info['ris_nr']

    old_bookings.append(exam_info)

  
  context = {
    'bookings': bookings,
    'old_bookings': reversed(sorted(old_bookings, key=lambda x: x.info['date']))
  }

  return HttpResponse(template.render(context, request))


@login_required(login_url='/')
def fill_study(request, rigs_nr):
  if request.method == 'POST':
    print(request.POST)
    PRH.fill_study_post(request, rigs_nr)
    
    if 'calculate' in request.POST:
      return redirect('main_page:present_study', rigs_nr=rigs_nr) 
    #TODO Simon should look at this

  # Specify page template
  template = loader.get_template('main_page/fill_study.html')
  
  exam = ris.get_examination(rigs_nr, './tmp') # TODO: './tmp' should be put in a configurable thing...

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

  inj_time = today.strftime('%H:%M')
  inj_date = today.strftime('%Y-%m-%d')
  if exam.info['inj_t'] != datetime.datetime(2000,1,1,0,0):
    inj_date = exam.info['inj_t'].strftime('%Y-%m-%d')
    inj_time = exam.info['inj_t'].strftime('%H:%M')

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
    'study_dosis_form' : forms.Filldosis( initial={
      'std_cnt' : 0,
      'thin_fac' : 0
    }),
    'study_examination_form'  : forms.Fillexamination(initial={
      'vial_weight_before'    : exam.info['inj_before'],
      'vial_weight_after'     : exam.info['inj_after'],
      'injection_time'        : inj_time,
      'injection_date'        : inj_date
    }),
    'study_type_form': forms.FillStudyType({'study_type': 0}), # Default: 'Et punkt voksen'
    'test_context': {
      'test_range': test_range,
      'test_form': test_form
    },
    'csv_data': csv_data
  }

  return HttpResponse(template.render(context, request))


@login_required(login_url='/')
def fetch_study(request):
  # Get all patients with "Clearance blodprove 2. gang":
  # findscu -S 127.0.0.1 11112 -aet RH_EDTA -aec TEST_DCM4CHEE -k 0032,1060="Clearance blodprøve 2. gang" -k 0008,0052="STUDY" -k 0008,0020="20190215" -k 0010,0020

  # Name wildcard example:
  # findscu -S 127.0.0.1 11112 -aet RH_EDTA -aec TEST_DCM4CHEE -k 0032,1060="Clearance blodprøve 2. gang" -k 0008,0052="STUDY" -k 0010,0010="*^mi*" -k 0010,0020

  # Date range example (find all patients from 20180101 to 20190101):
  # findscu -S 127.0.0.1 11112 -aet RH_EDTA -aec TEST_DCM4CHEE -k 0032,1060="Clearance blodprøve 2. gang" -k 0008,0052="STUDY" -k 0008,0020="20180101-20190101" -k 0010,0020 -k 0010,0010

  # Specify page template
  template = loader.get_template('main_page/fetch_study.html')

  if 'Søg' in request.GET:
    # Extract search parameters
    s_name = request.GET['name']
    s_cpr = request.GET['cpr']
    s_rigs = request.GET['Rigs']
    s_date_from = request.GET['Dato_start']
    s_date_to = request.GET['Dato_finish']

    # Construct query
    history_dir = './hist_tmp/'
    search_query = 'search_query'
    base_search_file = "{0}base_{1}.dcm".format(history_dir, search_query)

    # Find next number for query file
    search_files = glob.glob('{0}{1}*.dcm'.format(history_dir, search_query))
    
    curr_num = len(search_files)
    curr_search_file = '{0}{1}{2}.dcm'.format(history_dir, search_query, curr_num)
    
    curr_rsp_dir = '{0}rsp{1}/'.format(history_dir, curr_num)
    os.mkdir(curr_rsp_dir)

    # Make a new copy to construct the current query
    shutil.copyfile(base_search_file, curr_search_file)

    sf = pydicom.dcmread(curr_search_file)

    if s_name:
      s_name = s_name.strip()
      name_arr = s_name.split(' ')

      # Format as: "*LASTNAME^FIRSTNAME^MIDDLENAMES^*"
      firstname = name_arr[0]
      lastname = name_arr[-1]
      middlenames = name_arr[1:len(name_arr) - 1]

      # TODO: Shorten this name formatting
      # TODO: Add a lastname field to make life easier
      # If array is one element long
      if firstname == lastname:
        lastname = ''
      
      name_str = "*{0}^{1}^{2}^*".format(
        lastname, 
        firstname, 
        '^'.join(middlenames)
      )

      print(name_str)

      sf.PatientName = name_str

    # if s_cpr:


    # if s_rigs:

    
    # if s_date_from:


    # if s_date_to:


    sf.save_as(curr_search_file)

    search_query = [
      "findscu",
      "-S",
      "-aet",
      "RH_EDTA",
      "-aec",
      "TEST_DCM4CHEE",
      "127.0.0.1",
      "11112",
      curr_search_file,
      '-X',
      '-od',
      curr_rsp_dir
    ]
    
    # TODO: Add error handling
    out = ris.execute_query(search_query)

    # Extract data from responses
    rsps = []

    for rsp_path in glob.glob('{0}*.dcm'.format(curr_rsp_dir)):
      # TODO: Change this to use get_examination from ris_query_wrapper to make christoffer happy, yet still try to keep the querie files short
      # rsp_name = rsp_path.split('.')[0]
      # curr_exam = ris.get_examination(curr_rsp_dir, rsp_name)

      ds = pydicom.dcmread(rsp_path)
      rsp_info = (
        ds.PatientID,
        ds.PatientName,
        ds.StudyDate,
        ds.AccessionNumber,
      )

      # rsp_info = (
      #   curr_exam.info['name'],
      #   curr_exam.info['cpr'],
      #   curr_exam.info['date'],
      #   curr_exam.info['ris_nr'],
      # )

      rsps.append(rsp_info)

    # Remove the search query file
    os.remove(curr_search_file)
    shutil.rmtree(curr_rsp_dir)

  else:
    # Default case: display the patients from today
    # search_file = "./hist_tmp/default_search_query.dcm"
    
    # default_query = [
    #   "FINDSCU",
    #   "-S",
    #   "-aet",
    #   "RH_EDTA",
    #   "-aec",
    #   "TEST_DCM4CHEE",
    #   "127.0.0.1",
    #   "11112",
    #   search_file
    # ]
    rsps = []


  context = {
    'getstudy' : forms.GetStudy(),
    'responses': rsps
  }

  return HttpResponse(template.render(context, request))


@login_required(login_url='/')
def present_study(request, rigs_nr):
  """
  Function for presenting the result

  Args:
    request: The HTTP request
    rigs_nr: The number 

  Returns:
  """
  DICOM_directory = "./tmp"

  hospital = request.user.hospital

  exam = ris.get_examination(rigs_nr, DICOM_directory)

  # Display
  pixel_arr = exam.info['image']
  if pixel_arr.shape[0] != 0:
    Im = PIL.Image.fromarray(pixel_arr)
    Im.save('main_page/static/main_page/images/{0}/{1}.png'.format(hospital, rigs_nr))
  
  plot_path = 'main_page/images/{0}/{1}.png'.format(hospital,rigs_nr) 

  template = loader.get_template('main_page/present_study.html')
  
  context = {
    'name'          : exam.info['name'],
    'date'          : exam.info['date'],
    'rigs_nr'         : rigs_nr,
    'image_path'    : plot_path,
  }


  return HttpResponse(template.render(context,request))