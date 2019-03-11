from django.shortcuts import render
from django.http import HttpResponse, FileResponse, JsonResponse, Http404
from django.template import loader
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.log import DEFAULT_LOGGING
import logging

from . import forms
from .libs.query_wrappers import ris_query_wrapper as ris
from .libs.clearance_math import clearance_math
from .libs import Post_Request_handler as PRH
from .libs import server_config
from .libs import samba_handler

from . import models


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

#Setting up logging 

logger = logging.getLogger(__name__)


def index(request):
  template = loader.get_template('main_page/index.html')

  context = {
    'login_form': forms.LoginForm()
  }

  return HttpResponse(template.render(context, request))


def ajax_login(request):
  signed_in = False
  
  if request.method == 'POST':
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
          signed_in = True

  data = {
    'signed_in': signed_in,
  }
  resp = JsonResponse(data)

  if not signed_in:
    resp.status_code = 403

  return resp


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
    rigs_nr = request.POST['rigs_nr']

    success, error_msgs = ris.is_valid_study(cpr, name, study_date, rigs_nr)

    if success:
        
      
      # redirect to fill_study/rigs_nr 
      return redirect('main_page:fill_study', rigs_nr=rigs_nr)
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

  tmp_arr = []
  for booking in bookings:
    # Remove all booking previously sent to PACS
    sent_to_pacs = models.HandledExaminations.objects.filter(rigs_nr=booking.info['rigs_nr']).exists()
    if not sent_to_pacs:
      booking.name = booking.info['name']
      booking.date = booking.info['date']
      booking.cpr  = booking.info['cpr']
      booking.rigs_nr = booking.info['rigs_nr']
      tmp_arr.append(booking)
  bookings = tmp_arr

  # TODO: Move this into ris query wrapper (v2.0 when ris_query_wrapper is split into a pacs wrapper as well)
  # Fetch all old bookings
  DICOM_directory = '{0}/{1}'.format(
    server_config.FIND_RESPONS_DIR, 
    request.user.hospital
  )

  old_bookings = []
  for dcm_file in glob.glob('{0}/*.dcm'.format(DICOM_directory)):
    # Delete file if more than one week since procedure start
    dcm_name = os.path.basename(dcm_file).split('.')[0]
    dcm_dirc = os.path.dirname(dcm_file)

    # Don't display old booking which have already been sent to PACS
    sent_to_pacs = models.HandledExaminations.objects.filter(rigs_nr=dcm_name).exists()
    if sent_to_pacs:
      continue

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
    exam_info.rigs_nr = exam_info.info['rigs_nr']

    def existing_user(rigs_nr):
      """
        checks if a user already exists
      """
      for booking in bookings:
        if booking.rigs_nr == rigs_nr:
          return True
      return False

    if not existing_user(exam_info.rigs_nr): 
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
    '{0}{1}'.format(server_config.FIND_RESPONS_DIR, hospital)
  )

  test_range = range(6)
  today = datetime.datetime.today()
  date, _ = str(today).split(' ')
  test_form = forms.FillStudyTest(initial = {'study_date' : date})
  for f in test_form:
    f.field.widget.attrs['class'] = 'form-control'

  # Return a list of Panda objects
  data_files = samba_handler.smb_get_csv(request.user.hospital)

  # Read required data from each csv file  
  csv_data = []
  csv_present_names = []
  data_names = []
  for data_file in list(reversed(data_files)):
    prestring = "Undersøgelse lavet: "
    
    curr_data = [[] for _ in range(data_file.shape[0])]

    csv_present_names.append(prestring + data_file['Measurement date & time'][0])
    for i, row in data_file.iterrows():
      curr_data[i].append(row['Rack'])
      curr_data[i].append(row['Pos'])
      curr_data[i].append(row['Tc-99m Counts'])
      curr_data[i].append(row['Tc-99m CPM'])
      data_names.append(i)

    csv_data.append(curr_data)

  csv_data = zip(csv_present_names, csv_data, data_names)

  inj_time = today.strftime('%H:%M')
  inj_date = today.strftime('%Y-%m-%d')
  if exam.info['inj_t'] != datetime.datetime(2000,1,1,0,0):
    inj_date = exam.info['inj_t'].strftime('%Y-%m-%d')
    inj_time = exam.info['inj_t'].strftime('%H:%M')

  # Read in previous samples from examination info
  previous_sample_times = []
  previous_sample_dates = []
  previous_sample_counts = exam.info['tch_cnt']

  for st in exam.info['sam_t']:
    previous_sample_dates.append(st.strftime('%Y-%m-%d'))
    previous_sample_times.append(st.strftime('%H:%M'))
  
  previous_samples = zip(
    previous_sample_dates,
    previous_sample_times,
    previous_sample_counts
  )

  study_type = 0
  if exam.info['Method']:
    # TODO: The below strings that are checked for are used in multiple places. MOVE these into a config file
    # TODO: or just store the study_type number instead of the entire string in the Dicom obj and exam info
    if exam.info['Method'] == 'Et punkt voksen':
      study_type = 0
    elif exam.info['Method'] == 'Et punkt Barn':
      study_type = 1
    elif exam.info['Method'] == 'Flere prøve Voksen':
      study_type = 2

  print("Exam info from fill_study: {0}".format(exam.info))

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
      'std_cnt' : exam.info['std_cnt'],
      'thin_fac' : exam.info['thin_fact']
    }),
    'study_examination_form'  : forms.Fillexamination(initial={
      'vial_weight_before'    : exam.info['inj_before'],
      'vial_weight_after'     : exam.info['inj_after'],
      'injection_time'        : inj_time,
      'injection_date'        : inj_date
    }),
    'study_type_form': forms.FillStudyType(initial={
      'study_type': study_type # Default: 'Et punkt voksen'
    }),
    'test_context': {
      'test_range': test_range,
      'test_form': test_form
    },
    'previous_samples': previous_samples,
    'csv_data': csv_data,
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
    "-v", # TODO: Remove this line since it's debugging
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
  print("Executed query: {0}".format(search_query))
  print("Output: {0}".format(out))

  # Extract data from responses
  rsps = []

  for rsp_path in glob.glob('{0}*.dcm'.format(curr_rsp_dir)):
    # TODO: Change this to use get_examination from ris_query_wrapper to make christoffer happy, yet still try to keep the querie files short
    # rsp_name = rsp_path.split('.')[0]
    # curr_exam = ris.get_examination(curr_rsp_dir, rsp_name)

    ds = pydicom.dcmread(rsp_path)
    rsp_info = (
      ris.format_cpr(ds.PatientID),
      ris.format_name(ds.PatientName),
      ris.format_date(ds.StudyDate),
      ds.AccessionNumber,
    )

    print("Found patient with name: {0}".format(ds.PatientName))

    # rsp_info = (
    #   curr_exam.info['name'],
    #   curr_exam.info['cpr'],
    #   curr_exam.info['date'],
    #   curr_exam.info['rigs_nr'],
    # )

    rsps.append(rsp_info)

  # Remove the search query file
  # os.remove(curr_search_file)
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
def present_old_study(request, rigs_nr):
  """list(reversed(

  Remark:
    Should pull information down from PACS, but not be able to send to it.
    Additionally no button for going back to editing the study should be
    available!
  """
  template = loader.get_template('main_page/present_old_study.html')

  if request.method == 'POST':
    PRH.send_to_pacs(request, rigs_nr)
    redirect('main_page:list_studies')

  base_resp_dir = server_config.FIND_RESPONS_DIR
  hospital = request.user.hospital
  
  DICOM_directory = '{0}{1}/'.format(base_resp_dir, hospital)

  if not os.path.exists(base_resp_dir):
    os.mkdir(base_resp_dir)

  if not os.path.exists(DICOM_directory):
    os.mkdir(DICOM_directory)

  exam = ris.get_examination(request.user, rigs_nr, DICOM_directory)
  print(exam.info)

  # Read in previous samples from examination info
  previous_sample_times = []
  previous_sample_dates = []
  previous_sample_counts = exam.info['tch_cnt']

  for st in exam.info['sam_t']:
    previous_sample_dates.append(st.strftime('%Y-%m-%d'))
    previous_sample_times.append(st.strftime('%H:%M'))
  
  previous_samples = zip(
    previous_sample_dates,
    previous_sample_times,
    previous_sample_counts
  )

  today = datetime.datetime.today()
  inj_time = today.strftime('%H:%M')
  inj_date = today.strftime('%Y-%m-%d')
  if exam.info['inj_t'] != datetime.datetime(2000,1,1,0,0):
    inj_date = exam.info['inj_t'].strftime('%Y-%m-%d')
    inj_time = exam.info['inj_t'].strftime('%H:%M')

  study_type = 0
  if exam.info['Method']:
    # TODO: The below strings that are checked for are used in multiple places. MOVE these into a config file
    # TODO: or just store the study_type number instead of the entire string in the Dicom obj and exam info
    if exam.info['Method'] == 'Et punkt voksen':
      study_type = 0
    elif exam.info['Method'] == 'Et punkt Barn':
      study_type = 1
    elif exam.info['Method'] == 'Flere prøve Voksen':
      study_type = 2

  # Extract the image
  img_resp_dir = "{0}{1}/".format(server_config.IMG_RESPONS_DIR, hospital)
  if not os.path.exists(img_resp_dir):
    os.mkdir(img_resp_dir)
  
  pixel_arr = exam.info['image']
  if pixel_arr.shape[0] != 0:
    Im = PIL.Image.fromarray(pixel_arr)
    Im.save('{0}{1}.png'.format(img_resp_dir, rigs_nr))
  
  plot_path = 'main_page/images/{0}/{1}.png'.format(hospital,rigs_nr) 
  
  context = {
    'name': exam.info['name'],
    'date': exam.info['date'],
    'rigs_nr': rigs_nr,
    'image_path': plot_path,
    'std_cnt': exam.info['std_cnt'],
    'thin_fac': exam.info['thin_fact'],
    'vial_weight_before': exam.info['inj_before'],
    'vial_weight_after': exam.info['inj_after'],
    'injection_time': inj_time,
    'injection_date': inj_date,
    'study_type': study_type,
    'previous_samples': [previous_samples],
  }

  return HttpResponse(template.render(context,request))


@login_required(login_url='/')
def present_study(request, rigs_nr):
  """
  Function for presenting the result

  Args:
    request: The HTTP request
    rigs_nr: The number 

  Remark:
    Should not pull information down from PACS
  """
  template = loader.get_template('main_page/present_study.html')

  if request.method == 'POST':
    PRH.send_to_pacs(request, rigs_nr)
    return redirect('main_page:list_studies')

  base_resp_dir = server_config.FIND_RESPONS_DIR
  hospital = request.user.hospital
  
  DICOM_directory = '{0}{1}/'.format(base_resp_dir, hospital)

  if not os.path.exists(base_resp_dir):
    os.mkdir(base_resp_dir)

  if not os.path.exists(DICOM_directory):
    os.mkdir(DICOM_directory)

  exam = ris.get_examination(request.user, rigs_nr, DICOM_directory)
  
  # Display
  img_resp_dir = "{0}{1}/".format(server_config.IMG_RESPONS_DIR, hospital)
  if not os.path.exists(img_resp_dir):
    os.mkdir(img_resp_dir)
  
  pixel_arr = exam.info['image']
  if pixel_arr.shape[0] != 0:
    Im = PIL.Image.fromarray(pixel_arr)
    Im.save('{0}{1}.png'.format(img_resp_dir, rigs_nr))
  
  plot_path = 'main_page/images/{0}/{1}.png'.format(hospital,rigs_nr) 
  
  context = {
    'name'          : exam.info['name'],
    'date'          : exam.info['date'],
    'rigs_nr'         : rigs_nr,
    'image_path'    : plot_path,
  }

  return HttpResponse(template.render(context,request))

@login_required(login_url='/')
def settings(request):
  template = loader.get_template('main_page/settings.html')

  saved = False

  if request.method == 'POST':
    instance = models.Config.objects.get(pk=request.user.config.config_id)
    form = forms.SettingsForm(request.POST, instance=instance)
    if form.is_valid():
      form.save()
      request.user.config = instance

      saved = True

  context = {
    'settings_form': forms.SettingsForm(instance=request.user.config),
    'saved': saved,
  }

  return HttpResponse(template.render(context, request))


def documentation(requet):
  print("Test")

  return FileResponse(
    open('main_page/static/main_page/pdf/GFR_Tc-DTPA-harmonisering_20190223.pdf', 'rb'),
    content_type='application/pdf'
  )

  #return HttpResponse('Denne side burde redirect til en pdf med dokumentation for de anvendte formler og metoder (sprøg Søren om pdf dokument).')