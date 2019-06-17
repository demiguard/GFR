from django.shortcuts import render
from django.http import HttpResponse, FileResponse, JsonResponse, Http404
from django.template import loader
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.log import DEFAULT_LOGGING

from . import forms
from . import models

from .libs.query_wrappers import ris_query_wrapper as ris
from .libs.query_wrappers import pacs_query_wrapper as pacs
from .libs.clearance_math import clearance_math
from .libs.examination_info import ExaminationInfo
from .libs import examination_info
from .libs import formatting
from .libs import post_request_handler as PRH
from .libs import server_config
from .libs import samba_handler
from .libs import dicomlib
from .libs import dataset_creator

from dateutil import parser as date_parser
import datetime
import time
import logging
import shutil
import glob
import os
import pandas
import numpy
import pydicom
import PIL
import glob

logger = logging.getLogger()

class IndexView(TemplateView):
  """
  Index page - also serves as the login page
  """
  template_name = 'main_page/index.html'

  def get(self, request):
    context = {
      'login_form': forms.LoginForm()
    }

    return render(request, self.template_name, context)


class AjaxLogin(TemplateView):
  """
  Handles processing of login requests from javascript
  """
  def post(self, request):
    signed_in = False
    
    login_form = forms.LoginForm(data=request.POST)

    if login_form.is_valid():
      user = authenticate(
        request, 
        username=request.POST['username'], 
        password=request.POST['password']
      )

      if user:
        login(request, user)
        logger.info('User: {0} logged in successful'.format(request.user.username))

        if user.is_authenticated:
          signed_in = True
      else:
        logger.warning('User: {0} Failed to log in'.format(request.POST['username']))

    data = {
      'signed_in': signed_in,
    }
    resp = JsonResponse(data)

    if not signed_in:
      resp.status_code = 403

    return resp


class AjaxDeleteStudy(TemplateView):
  def post(self, request):
    delete_status = True

    user_hosp = request.user.hospital

    delete_accession_number = request.POST['delete_accession_number']

    logger.info(f"Attempting to delete study: {delete_accession_number}")

    # Create deleted studies directory if doesn't exist
    if not os.path.exists(server_config.DELETED_STUDIES_DIR):
      os.mkdir(server_config.DELETED_STUDIES_DIR)

    inner_hosp_dir = f"{server_config.DELETED_STUDIES_DIR}{user_hosp}"
    if not os.path.exists(inner_hosp_dir):
      os.mkdir(inner_hosp_dir)

    move_src = f"{server_config.FIND_RESPONS_DIR}{user_hosp}/{delete_accession_number}.dcm"

    if not os.path.exists(move_src):
      delete_status = False

    if delete_status:
      move_dst = f"{server_config.DELETED_STUDIES_DIR}{user_hosp}/{delete_accession_number}.dcm"
      
      # Reset modification time
      del_time = time.mktime(datetime.datetime.now().timetuple())
      os.utime(move_src, (del_time, del_time))

      # Move to deletion directory
      shutil.move(move_src, move_dst)

      logger.info(f"Successfully deleted study: {delete_accession_number}")

    data = { }
    resp = JsonResponse(data)

    if not delete_status:
      resp.status_code = 403

    return resp


class AjaxRestoreStudy(TemplateView):
  def post(self, request):
    recover_status = True

    user_hosp = request.user.hospital

    recover_accession_number = request.POST['recover_accession_number']

    logger.info(f"Attempting to recover study: {recover_accession_number}")

    # Create deleted studies directory if doesn't exist
    if not os.path.exists(server_config.FIND_RESPONS_DIR):
      os.mkdir(server_config.FIND_RESPONS_DIR)

    inner_hosp_dir = f"{server_config.FIND_RESPONS_DIR}{user_hosp}"
    if not os.path.exists(inner_hosp_dir):
      os.mkdir(inner_hosp_dir)

    move_src = f"{server_config.DELETED_STUDIES_DIR}{user_hosp}/{recover_accession_number}.dcm"

    if not os.path.exists(move_src):
      recover_status = False

    if recover_status:
      move_dst = f"{server_config.FIND_RESPONS_DIR}{user_hosp}/{recover_accession_number}.dcm"
      
      # Move to deletion directory
      shutil.move(move_src, move_dst)

      logger.info(f"Successfully recovered study: {recover_accession_number}")

    data = { }
    resp = JsonResponse(data)

    if not recover_status:
      resp.status_code = 403

    return resp


class AjaxSearch(LoginRequiredMixin, TemplateView):
  """
  Handles ajax search requests
  """
  def get(self, request):  
    # Extract search parameters
    search_name = request.GET['name']
    search_cpr = request.GET['cpr']
    search_rigs_nr = request.GET['rigs_nr']
    search_date_from = request.GET['date_from']
    search_date_to = request.GET['date_to']

    print(request.GET)

    search_resp = pacs.search_query_pacs(
      request.user,
      name=search_name,
      cpr=search_cpr,
      accession_number=search_rigs_nr,
      date_from=search_date_from,
      date_to=search_date_to,
    )

    # Serialize search results; i.e. turn ExaminationInfo objects into dicts.
    serialized_results = []
    for res in search_resp:
      serialized_results.append({
        'rigs_nr': res.rigs_nr,
        'name': res.name,
        'cpr': res.cpr,
        'date': res.date
      })

    data = {
      'search_results': serialized_results
    }

    return JsonResponse(data) 



class AjaxUpdateThiningFactor(TemplateView):
  def post(self, request):
    """
      Ajax from list_studies, called from list_studies.js

      Handles and updates thining factor 
    """
    logger.info(f"{request.user.username} Updated thining factor to {request.POST['thining_factor']}")
    request.user.department.thining_factor = float(request.POST['thining_factor'])
    request.user.department.thining_factor_change_date = datetime.date.today()
    request.user.department.save()

    return JsonResponse({})


class LogoutView(LoginRequiredMixin, TemplateView):
  """
  Logouts out the current user from the session.
  (either through a GET or POST request)
  """
  def logout_current_user(self, request):
    logger.info('User - {0} logged out from ip: {1}'.format(
      request.user.username,
      request.META['REMOTE_ADDR']
    ))

    logout(request)
    return redirect('main_page:index')

  def get(self, request):
    return self.logout_current_user(request)

  def post(self, request):
    return self.logout_current_user(request)
  

class NewStudyView(LoginRequiredMixin, TemplateView):
  template_name = 'main_page/new_study.html'

  def get(self, request):
    context = {
      'study_form': forms.NewStudy(initial={'study_date': datetime.date.today})
    }

    return render(request, self.template_name, context)

  def post(self, request):

    # Create and store dicom object for new study
    cpr = request.POST['cpr']
    name = request.POST['name']
    study_date = request.POST['study_date']
    rigs_nr = request.POST['rigs_nr']

    new_study_form = forms.NewStudy(initial={
      'cpr': cpr,
      'name': name,
      'study_date': study_date,
      'rigs_nr': rigs_nr
    })

    context = {
      'study_form': new_study_form,
      'error_msg' : ''
    }

    success, error_msgs = formatting.is_valid_study(cpr, name, study_date, rigs_nr)

    if success:
      #new_destination = '{0}{1}/{2}.dcm'.format(server_config.FIND_RESPONS_DIR, request.user.hospital, rigs_nr)
      #shutil.copyfile(server_config.BLANK_DICOM_FILE, new_destination, follow_symlinks=False)  
      
      dataset = dataset_creator.get_blank(
        cpr,
        name,
        study_date,
        rigs_nr,
        request.user.hospital
      )
      dicomlib.save_dicom('{0}{1}/{2}.dcm'.format(
          server_config.FIND_RESPONS_DIR,
          request.user.hospital,
          rigs_nr
        ), 
        dataset
      )

      # redirect to fill_study/rigs_nr 
      return redirect('main_page:fill_study', rigs_nr=rigs_nr)
    else:
      context['error_msgs'] = error_msgs
      return render(request, self.template_name, context)


class ListStudiesView(LoginRequiredMixin, TemplateView):
  template_name = 'main_page/list_studies.html'

  def get(self, request):
    dicom_objs, error_message = ris.get_patients_from_rigs(request.user)
    
    bookings = examination_info.mass_deserialize(dicom_objs)
  
    def date_sort(item):
      item_time = datetime.datetime.strptime(item.date, "%d/%m-%Y")
      return int(item_time.strftime("%Y%m%d"))

    bookings = list(sorted(bookings, key=date_sort, reverse=True))

    department_thin_fact = request.user.department.thining_factor
    department_changed_date = request.user.department.thining_factor_change_date

    if department_changed_date == datetime.date.today():
      input_thin_factor = department_thin_fact
    else:
      input_thin_factor = 0.0


    #Note that error message is not implimented yet
    context = {
      'thin_fac_form' : forms.FillThiningFactor(initial={'thin_fac': input_thin_factor}),
      'bookings': bookings,
      'error_message' : error_message
    }

    return render(request, self.template_name, context)


@login_required()
def fill_study(request, rigs_nr):
  # Specify page template
  template = loader.get_template('main_page/fill_study.html')

  if request.method == 'POST':
    file_path = f"{server_config.FIND_RESPONS_DIR}{request.user.hospital}/{rigs_nr}.dcm"

    dataset = dicomlib.dcmread_wrapper(file_path)
    dataset = PRH.fill_study_post(request, rigs_nr, dataset)
    
    dicomlib.save_dicom(file_path, dataset)

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
    f'{server_config.FIND_RESPONS_DIR}{hospital}/'
  )

  today = datetime.datetime.now()
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
    for data_file in data_files:
      prestring = ""

      curr_data = [[] for _ in range(data_file.shape[0])]

      csv_present_names.append(prestring + data_file['Measurement date & time'][0])
      for i, row in data_file.iterrows():
        curr_data[i].append(row['Rack'])
        curr_data[i].append(row['Pos'])
        curr_data[i].append(row['Tc-99m CPM'])
        data_names.append(i)

      csv_data.append(curr_data)

    csv_data = zip(csv_present_names, csv_data, data_names)
  except:
    logger.warning('SMB Connection Failed')
    error_message = 'Hjemmesiden kunne ikke få kontakt til serveren med prøve resultater.\n Kontakt din lokale IT-ansvarlige \n Server kan ikke få kontakt til sit Samba-share.'

  inj_time = None
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

  if exam.sex == 'M':
    present_sex = 'Mand'
  else:
    present_sex = 'Kvinde'

  #This Code is not approve of the pretty police
  if exam.inj_before == 0.0:
    exam.inj_before = None

  if exam.inj_after == 0.0:
    exam.inj_after = None

  if exam.height == 0.0:
    exam.height = None

  if exam.weight == 0.0:
    exam.weight = None

  if exam.thin_fact == 0.0 or exam.thin_fact == None:
    if request.user.department.thining_factor_change_date == datetime.date.today() and request.user.department.thining_factor != 0:
      exam.thin_fact = request.user.department.thining_factor
    else:
      exam.thin_fact = None

  if exam.std_cnt == 0.0:
    exam.std_cnt = None
  # --- ---

  # TODO: Many of these parameters passed to the template can be simplified by
  # just passing in the exam object
  context = {
    'rigsnr': rigs_nr,
    'study_patient_form': forms.Fillpatient_1(initial={
      'cpr': exam.cpr,
      'name': exam.name,
      'sex': present_sex,
      'birthdate': exam.birthdate
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
    'csv_data_len': len(data_names),
    'error_message' : error_message,
    'standard_count' : exam.std_cnt,
  }


  return HttpResponse(template.render(context, request))


class SearchView(LoginRequiredMixin, TemplateView):
  """
  Search view
  """
  template_name = 'main_page/search.html'
  
  def get(self, request):
    # Default date case: display the patients from the last week
    now = datetime.datetime.now()
    default_date_to = now.strftime('%Y-%m-%d')

    week_delta = datetime.timedelta(days=7)
    week_datetime = now - week_delta
    default_date_from = week_datetime.strftime('%Y-%m-%d')

    # Extract search parameters from url
    if 'name' in request.GET:
      search_name = request.GET['name']
    else:
      search_name = ''

    if 'cpr' in request.GET:
      search_cpr = request.GET['cpr']
    else:
      search_cpr = ''

    if 'Rigs' in request.GET:
      search_rigs_nr = request.GET['Rigs']
    else:
      search_rigs_nr = ''

    date_set = False
    if 'Dato_start' in request.GET:
      search_date_from = request.GET['Dato_start']
      date_set = True
    else:
      search_date_from = ''

    if 'Dato_finish' in request.GET:
      search_date_to = request.GET['Dato_finish']
      date_set = True
    else:
      search_date_to = ''

    if not date_set:
      search_date_from = default_date_from
      search_date_to = default_date_to

    #Removed initial 
  
    search_resp = pacs.search_query_pacs(
      request.user,
      name=search_name,
      cpr=search_cpr,
      accession_number=search_rigs_nr,
      date_from=search_date_from,
      date_to=search_date_to,
    )
    

    logger.info(f"Initial search responses: {search_resp}")

    # Add specific bootstrap class to the form item and previous search parameters
    get_study_form = forms.GetStudy(initial={
      'name': search_name,
      'cpr': search_cpr,
      'Rigs': search_rigs_nr,
      'Dato_start': search_date_from,
      'Dato_finish': search_date_to
    })
    
    for item in get_study_form:
      item.field.widget.attrs['class'] = 'form-control'

    context = {
      'getstudy' : get_study_form,
      'responses': search_resp,
    }

    return render(request, self.template_name, context)





@login_required()
def present_old_study(request, rigs_nr):
  """
  Remark:
    Should pull information down from PACS, but not be able to send to it.
    Additionally no button for going back to editing the study should be
    available!
  """
  template = loader.get_template('main_page/present_old_study.html')

  current_user = request.user
  hospital = request.user.hospital

  # Search to find patient id - pick field response
  search_resp = pacs.search_query_pacs(current_user, accession_number=rigs_nr)
  patient_id = search_resp[0].cpr

  logger.info(f"patient id for present old: {patient_id}")

  #study_id = pydicom.uid.generate_uid(prefix='1.3.', entropy_srcs=[rigs_nr, 'Study'])
  series_id = pydicom.uid.generate_uid(prefix='1.3.', entropy_srcs=[rigs_nr, 'Series'])
  instance_id = pydicom.uid.generate_uid(prefix='1.3.', entropy_srcs=[rigs_nr, 'SOP'])

  dataset = pacs.move_from_pacs(
    current_user,
    rigs_nr,
    patient_id=patient_id,
    series_id=series_id,
    #study_id=study_id,
    instance_id=instance_id
  )

  exam = examination_info.deserialize(dataset)

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

  today = datetime.datetime.now()
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
    Im = PIL.Image.fromarray(pixel_arr, mode="RGB")
    Im.save(f'{img_resp_dir}{rigs_nr}.png')
  
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


@login_required()
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
  img_resp_dir = f"{server_config.IMG_RESPONS_DIR}{hospital}/"
  if not os.path.exists(img_resp_dir):
    os.mkdir(img_resp_dir)
  
  pixel_arr = exam.image
  if pixel_arr.shape[0] != 0:
    Im = PIL.Image.fromarray(pixel_arr)
    Im.save(f'{img_resp_dir}{rigs_nr}.png')
  
  plot_path = f"main_page/images/{hospital}/{rigs_nr}.png" 
  
  context = {
    'name': exam.name,
    'date': exam.date,
    'rigs_nr': rigs_nr,
    'image_path': plot_path,
  }

  return HttpResponse(template.render(context,request))


class SettingsView(LoginRequiredMixin, TemplateView):
  """
  User configuration view
  """
  template_name = 'main_page/settings.html'

  def get(self, request):
    context = {
      'settings_form': forms.SettingsForm(instance=request.user.config)
    }

    return render(request, self.template_name, context)

  def post(self, request):
    saved = False

    instance = models.Config.objects.get(pk=request.user.config.config_id)
    form = forms.SettingsForm(request.POST, instance=instance)
    if form.is_valid():
      form.save()
      request.user.config = instance

      saved = True

    context = {
      'settings_form': forms.SettingsForm(instance=request.user.config),
      'saved': saved
    }

    return render(request, self.template_name, context)


def documentation(request):
  """
  Generates the file response for the documentation page
  """
  return FileResponse(
    open('main_page/static/main_page/pdf/GFR_Tc-DTPA-harmonisering_20190223.pdf', 'rb'),
    content_type='application/pdf'
  )

class DeletedStudiesView(LoginRequiredMixin, TemplateView):
  """
  Displays deleted studies from 30 days ago.
  Works like a trashcan for files, that deleted studies lie for 30 days until
  they are completly removed.
  """

  template_name = "main_page/deleted_studies.html"

  def get(self, request):
    # Get list of all deleted studies
    user_hosp = request.user.hospital

    deleted_studies = [] # Contains ExaminationInfo objects

    deleted_dir = f"{server_config.DELETED_STUDIES_DIR}{user_hosp}/"
    glob_pattern = f"{deleted_dir}*.dcm"
    for filepath in glob.glob(glob_pattern):
      curr_rigs_nr = os.path.basename(filepath).split('.')[0]

      curr_exam = pacs.get_examination(request.user, curr_rigs_nr, deleted_dir)
      
      # Set the deletion date
      deletion_date = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
      curr_exam.deletion_date = deletion_date.strftime('%d/%m-%Y')
      
      deleted_studies.append(curr_exam)
    
    context = {
      'deleted_studies': deleted_studies,
    }

    return render(request, self.template_name, context)

  
