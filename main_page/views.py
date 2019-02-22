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
from .libs import server_config

from dateutil import parser as date_parser
import datetime
import shutil
import glob
import os
import pandas
import numpy
import pydicom
import PIL
import glob
import pprint # Debug


def index(request):
  if request.method == 'POST':
    print(request.POST)
    login_form = forms.LoginForm(data=request.POST)

    if login_form.is_valid():
      user = authenticate(
        request, 
        username=request.POST['username'], 
        password=request.POST['password']
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
  
  bookings = ris.get_all(request.user)

  for booking in bookings:
    booking.name = booking.info['name']
    booking.date = booking.info['date']
    booking.cpr  = booking.info['cpr']
    booking.ris_nr = booking.info['ris_nr']

  # TODO: Move this into ris query wrapper (v2.0 when ris_query_wrapper is split into a pacs wrapper as well)
  # Fetch all old bookings

  DICOM_directory = '{0}/{1}'.format(
    server_config.FIND_RESPONS_DIR, 
    request.user.hospital
  )

  old_bookings = []
  for dcm_file in glob.glob('./{0}/*.dcm'.format(DICOM_directory)):
    # Delete file if more than one week since procedure start
    
    dcm_dirc, dcm_name = dcm_file.rsplit('/',1)
    dcm_name, _ = dcm_name.rsplit('.',1)
    exam_info = ris.get_examination(request.user, dcm_name, dcm_dirc)
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
  # Specify page template
  template = loader.get_template('main_page/fill_study.html')

  if request.method == 'POST':
    PRH.fill_study_post(request, rigs_nr)
    
    if 'calculate' in request.POST:  
      return redirect('main_page:present_study', rigs_nr=rigs_nr) 

  hospital = request.user.hospital # Hospital of current user

  # Create the directory if not existing
  if not os.path.exists(server_config.FIND_RESPONS_DIR):
    os.mkdir(server_config.FIND_RESPONS_DIR)

  if not os.path.exists('{0}/{1}'.format(server_config.FIND_RESPONS_DIR, hospital)):
    os.mkdir('{0}/{1}'.format(server_config.FIND_RESPONS_DIR, hospital))

  # Get previous information for the study
  exam = ris.get_examination(
    request.user, 
    rigs_nr, 
    './{0}/{1}'.format(server_config.FIND_RESPONS_DIR, hospital)
  ) 

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
  # Specify page template
  template = loader.get_template('main_page/fetch_study.html')

  # Construct new query file
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

  # Set auto fill parameters
  auto_fill_params = { }

  if 'Søg' in request.GET:
    # Extract search parameters
    s_name = request.GET['name']
    s_cpr = request.GET['cpr']
    s_rigs = request.GET['Rigs']
    s_date_from = request.GET['Dato_start']
    s_date_to = request.GET['Dato_finish']

    # Formatting...
    s_date_from = s_date_from.replace('-','')
    s_date_to = s_date_to.replace('-','')

    auto_fill_params = {
      'name': s_name,
      'cpr': s_cpr,
      'Rigs': s_rigs,
      'Dato_start': s_date_from[:4] + '-' + s_date_from[4:6] + '-' + s_date_from[6:],
      'Dato_finish': s_date_to[:4] + '-' + s_date_to[4:6] + '-' + s_date_to[6:],
    }

    # Search by name
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

    # Search by cpr nr.
    if s_cpr:
      s_cpr = s_cpr.replace('-', '')

      sf.PatientID = s_cpr
      print(sf.PatientID)

    # Search by rigs number
    if s_rigs:
      sf.AccessionNumber = s_rigs
    
    # Search by date range
    s_date_range = ''
    
    if s_date_from:
      s_date_range += s_date_from + '-'

    if s_date_to:
      s_date_range += s_date_to
    
    sf.StudyDate = s_date_range
  else:
    # Default case: display the patients from the last week
    now = datetime.datetime.now()
    now_str = now.strftime('%Y%m%d')

    week_delta = datetime.timedelta(days=7)
    week_datetime = now - week_delta
    last_week_str = week_datetime.strftime('%Y%m%d')

    sf.StudyDate = '{0}-{1}'.format(last_week_str, now_str)    

    # Set the dates in the auto fill
    auto_fill_params = {
      'Dato_start': last_week_str[:4] + '-' + last_week_str[4:6] + '-' + last_week_str[6:],
      'Dato_finish': now_str[:4] + '-' + now_str[4:6] + '-' + now_str[6:],
    }

  # Save and execute the current search query file
  sf.save_as(curr_search_file)

  user = request.user

  search_query = [
    server_config.FINDSCU,
    "-S",
    "-aet",
    user.config.pacs_calling,
    "-aec",
    user.config.pacs_aet,
    user.config.pacs_ip,
    user.config.pacs_port,
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

    print("Found patient with name: {0}".format(ds.PatientName))

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

  # Add specific bootstrap class to the form item
  get_study_form = forms.GetStudy(initial=auto_fill_params)
  for item in get_study_form:
    item.field.widget.attrs['class'] = 'form-control'

  context = {
    'getstudy' : get_study_form,
    'responses': rsps,
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
  if request == 'POST':
    PRH.send_to_pacs(request, rigs_nr)
    redirect('mainpage:liststudies') 


  Dicom_base_dirc = 'Active_Dicom_objects'
  hospital = request.user.hospital
  
  DICOM_directory = './{0}/{1}/'.format(Dicom_base_dirc, hospital)

  if not os.path.exists(Dicom_base_dirc):
    os.mkdir(Dicom_base_dirc)

  if not os.path.exists(DICOM_directory):
    os.mkdir(DICOM_directory)

  exam = ris.get_examination(request.user, rigs_nr, DICOM_directory)

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

@login_required(login_url='/')
def config(request):
  return HttpResponse('User configuration page')


def documentation(requet):
  return HttpResponse('Denne side burde redirect til en pdf med dokumentation for de anvendte formler og metoder (sprøg Søren om pdf dokument).')