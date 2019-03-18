from django.shortcuts import render
from django.http import HttpResponse, FileResponse, JsonResponse, Http404
from django.template import loader
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.log import DEFAULT_LOGGING

from . import forms
from . import models

from .libs.query_wrappers import ris_query_wrapper as ris
from .libs.query_wrappers import pacs_query_wrapper as pacs
from .libs.clearance_math import clearance_math
from .libs.examination_info import ExaminationInfo
from .libs import formatting
from .libs import post_request_handler as PRH
from .libs import server_config
from .libs import samba_handler
from .libs import dicomlib

from dateutil import parser as date_parser
import logging
import datetime
import shutil
import glob
import os
import pandas
import numpy
import pydicom
import PIL
import glob


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

    success, error_msgs = formatting.is_valid_study(cpr, name, study_date, rigs_nr)

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
  
  bookings = []
  for booking in ris.get_all(request.user):
    # Remove all booking previously sent to PACS
    sent_to_pacs = models.HandledExaminations.objects.filter(rigs_nr=booking.rigs_nr).exists()
    if not sent_to_pacs:
      bookings.append(booking)

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

    exam = pacs.get_examination(request.user, dcm_name, dcm_dirc)
    procedure_date = datetime.datetime.strptime(exam.date, '%d/%m-%Y')

    now = datetime.datetime.now()
    time_diff = now - procedure_date
    days_diff = time_diff.days
    
    DAYS_THRESHOLD = 7

    if days_diff >= DAYS_THRESHOLD:
      os.remove(dcm_file)
      continue

    # read additional contents    
    exam.name = exam.name
    exam.date = exam.date
    exam.cpr = exam.cpr
    exam.rigs_nr = exam.rigs_nr

    # checks if a user already exists
    def existing_user(rigs_nr):
      for booking in bookings:
        if booking.rigs_nr == rigs_nr:
          return True
      return False

    if not existing_user(exam.rigs_nr): 
      old_bookings.append(exam)

  context = {
    'bookings': bookings,
    'old_bookings': reversed(sorted(old_bookings, key=lambda x: x.date))
  }

  return HttpResponse(template.render(context, request))


@login_required(login_url='/')
def fill_study(request, rigs_nr):
  # Specify page template
  print(request.POST)
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
  exam = pacs.get_examination(
    request.user, 
    rigs_nr, 
    '{0}{1}'.format(server_config.FIND_RESPONS_DIR, hospital)
  )

  today = datetime.datetime.today()
  date, _ = str(today).split(' ')
  test_form = forms.FillStudyTest(initial = {'study_date' : date})
  for f in test_form:
    f.field.widget.attrs['class'] = 'form-control'

  # Return a list of Panda objects
  csv_data = []
  csv_present_names = []
  data_names = []
  error_message = 'Der er ikke lavet nogen prøver de sidste 24 timer'
  
  try: 
    data_files = samba_handler.smb_get_csv(request.user.hospital, timeout=10)

    # Read required data from each csv file  
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
  except:
    error_message = 'Hjemmesiden kunne ikke få kontakt til serveren med prøve resultater.\n Kontakt din lokale IT-ansvarlige \n Server kan ikke få kontakt til sit Samba-share.'

  inj_time = today.strftime('%H:%M')
  inj_date = today.strftime('%Y-%m-%d')
  if exam.inj_t:
    inj_date = exam.inj_t.strftime('%Y-%m-%d')
    inj_time = exam.inj_t.strftime('%H:%M')

  # Read in previous samples from examination info
  previous_sample_times = []
  previous_sample_dates = []
  previous_sample_counts = exam.tch_cnt

  for st in exam.sam_t:
    previous_sample_dates.append(st.strftime('%Y-%m-%d'))
    previous_sample_times.append(st.strftime('%H:%M'))
  
  previous_samples = zip(
    previous_sample_dates,
    previous_sample_times,
    previous_sample_counts
  )

  study_type = 0
  if exam.Method:
    # TODO: The below strings that are checked for are used in multiple places. MOVE these into a config file
    # TODO: or just store the study_type number instead of the entire string in the Dicom obj and exam info
    if exam.Method == 'Et punkt voksen':
      study_type = 0
    elif exam.Method == 'Et punkt Barn':
      study_type = 1
    elif exam.Method == 'Flere prøve Voksen':
      study_type = 2

  context = {
    'rigsnr': rigs_nr,
    'study_patient_form': forms.Fillpatient_1(initial={
      'cpr': exam.cpr,
      'name': exam.name,
      'sex': exam.sex,
      'age': exam.age
    }),
    'study_patient_form_2': forms.Fillpatient_2(initial={
      'height': exam.height,
      'weight': exam.weight,
    }),
    'study_dosis_form' : forms.Filldosis( initial={
      'thin_fac' : exam.thin_fact
    }),
    'study_examination_form': forms.Fillexamination(initial={
      'vial_weight_before': exam.inj_before,
      'vial_weight_after': exam.inj_after,
      'injection_time': inj_time,
      'injection_date': inj_date
    }),
    'study_type_form': forms.FillStudyType(initial={
      'study_type': study_type # Default: 'Et punkt voksen'
    }),
    'test_context': {
      'test_form': test_form
    },
    'previous_samples': previous_samples,
    'csv_data': csv_data,
    'csv_data_len': len(data_files),
    'error_message' : error_message,
    'standart_count' : exam.std_cnt,
  }

  return HttpResponse(template.render(context, request))


@login_required(login_url='/')
def search(request):
  # Specify page template
  template = loader.get_template('main_page/search.html')

  search_resp = []
  auto_fill_params = { }

  if 'Søg' in request.GET:    
    # Extract search parameters
    search_name = request.GET['name']
    search_cpr = request.GET['cpr']
    search_rigs_nr = request.GET['Rigs']
    search_date_from = request.GET['Dato_start']
    search_date_to = request.GET['Dato_finish']

    search_resp = pacs.search_pacs(
      request.user,
      name=search_name,
      cpr=search_cpr,
      rigs_nr=search_rigs_nr,
      date_from=search_date_from,
      date_to=search_date_to,
    )

    auto_fill_params = {
      'name': search_name,
      'cpr': search_cpr,
      'Rigs': search_rigs_nr,
      'Dato_start': search_date_from[:4] + '-' + search_date_from[4:6] + '-' + search_date_from[6:],
      'Dato_finish': search_date_to[:4] + '-' + search_date_to[4:6] + '-' + search_date_to[6:],
    }

  # Add specific bootstrap class to the form item and previous search parameters
  get_study_form = forms.GetStudy(initial=auto_fill_params)
  for item in get_study_form:
    item.field.widget.attrs['class'] = 'form-control'

  context = {
    'getstudy' : get_study_form,
    'responses': search_resp,
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

  base_resp_dir = server_config.FIND_RESPONS_DIR
  hospital = request.user.hospital
  
  DICOM_directory = '{0}{1}/'.format(base_resp_dir, hospital)

  if not os.path.exists(base_resp_dir):
    os.mkdir(base_resp_dir)

  if not os.path.exists(DICOM_directory):
    os.mkdir(DICOM_directory)

  exam = pacs.get_examination(request.user, rigs_nr, DICOM_directory)

  # Read in previous samples from examination info
  previous_sample_times = []
  previous_sample_dates = []
  previous_sample_counts = exam.tch_cnt

  for st in exam.sam_t:
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
  if exam.inj_t:
    inj_date = exam.inj_t.strftime('%Y-%m-%d')
    inj_time = exam.inj_t.strftime('%H:%M')

  study_type = 0
  if exam.Method:
    # TODO: The below strings that are checked for are used in multiple places. MOVE these into a config file
    # TODO: or just store the study_type number instead of the entire string in the Dicom obj and exam info
    if exam.Method == 'Et punkt voksen':
      study_type = 0
    elif exam.Method == 'Et punkt Barn':
      study_type = 1
    elif exam.Method == 'Flere prøve Voksen':
      study_type = 2

  # Extract the image
  img_resp_dir = "{0}{1}/".format(server_config.IMG_RESPONS_DIR, hospital)
  if not os.path.exists(img_resp_dir):
    os.mkdir(img_resp_dir)
  
  pixel_arr = exam.image
  if pixel_arr.shape[0] != 0:
    Im = PIL.Image.fromarray(pixel_arr)
    Im.save('{0}{1}.png'.format(img_resp_dir, rigs_nr))
  
  plot_path = 'main_page/images/{0}/{1}.png'.format(hospital,rigs_nr) 
  
  context = {
    'name': exam.name,
    'date': exam.date,
    'rigs_nr': rigs_nr,
    'image_path': plot_path,
    'std_cnt': exam.std_cnt,
    'thin_fac': exam.thin_fact,
    'vial_weight_before': exam.inj_before,
    'vial_weight_after': exam.inj_after,
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
    PRH.present_study_post(request, rigs_nr)
    return redirect('main_page:list_studies')

  base_resp_dir = server_config.FIND_RESPONS_DIR
  hospital = request.user.hospital
  
  DICOM_directory = '{0}{1}/'.format(base_resp_dir, hospital)

  if not os.path.exists(base_resp_dir):
    os.mkdir(base_resp_dir)

  if not os.path.exists(DICOM_directory):
    os.mkdir(DICOM_directory)

  exam = pacs.get_examination(request.user, rigs_nr, DICOM_directory)
  
  # Display
  img_resp_dir = "{0}{1}/".format(server_config.IMG_RESPONS_DIR, hospital)
  if not os.path.exists(img_resp_dir):
    os.mkdir(img_resp_dir)
  
  pixel_arr = exam.image
  if pixel_arr.shape[0] != 0:
    Im = PIL.Image.fromarray(pixel_arr)
    Im.save('{0}{1}.png'.format(img_resp_dir, rigs_nr))
  
  plot_path = 'main_page/images/{0}/{1}.png'.format(hospital,rigs_nr) 
  
  context = {
    'name': exam.name,
    'date': exam.date,
    'rigs_nr': rigs_nr,
    'image_path': plot_path,
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


def documentation(request):
  """
  Generates the file response for the documentation page
  """
  return FileResponse(
    open('main_page/static/main_page/pdf/GFR_Tc-DTPA-harmonisering_20190223.pdf', 'rb'),
    content_type='application/pdf'
  )
