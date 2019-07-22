from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.template import loader
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

import os
import datetime
import logging
import PIL
import glob

from main_page.libs.query_wrappers import pacs_query_wrapper as pacs
from main_page.libs.query_wrappers import ris_query_wrapper as ris
from main_page.libs import post_request_handler as PRH
from main_page.libs import examination_info
from main_page.libs import dataset_creator
from main_page.libs import server_config
from main_page.libs import samba_handler
from main_page.libs import formatting
from main_page.libs import dicomlib
from main_page import forms


logger = logging.getLogger()


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
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'study_form': new_study_form,
      'error_msg' : ''
    }

    success, error_msgs = formatting.is_valid_study(cpr, name, study_date, rigs_nr)

    if success:
      #new_destination = '{0}{1}/{2}.dcm'.format(server_config.FIND_RESPONS_DIR, request.user.department.hospital, rigs_nr)
      #shutil.copyfile(server_config.BLANK_DICOM_FILE, new_destination, follow_symlinks=False)  
      
      dataset = dataset_creator.get_blank(
        cpr,
        name,
        study_date,
        rigs_nr,
        request.user.department.hospital
      )
      dicomlib.save_dicom('{0}{1}/{2}.dcm'.format(
          server_config.FIND_RESPONS_DIR,
          request.user.department.hospital,
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

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'bookings': bookings,
      'error_message' : error_message
    }

    return render(request, self.template_name, context)


@login_required()
def fill_study(request, rigs_nr):
  # Specify page template
  template = loader.get_template('main_page/fill_study.html')

  if request.method == 'POST':
    file_path = f"{server_config.FIND_RESPONS_DIR}{request.user.department.hospital.short_name}/{rigs_nr}.dcm"

    dataset = dicomlib.dcmread_wrapper(file_path)
    dataset = PRH.fill_study_post(request, rigs_nr, dataset)
    
    dicomlib.save_dicom(file_path, dataset)

    if 'calculate' in request.POST:  
      return redirect('main_page:present_study', rigs_nr=rigs_nr) 

  hospital = request.user.department.hospital.short_name # Hospital of current user

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
    data_files = samba_handler.smb_get_csv(request.user.department.hospital.short_name, timeout=10)
    
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
  except Exception as E:
    logger.warning(f'SMB Connection Failed:{E}')
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

  thin_fac_save_inital = True
  if exam.thin_fact == 0.0 or exam.thin_fact == None:
    if request.user.department.thining_factor_change_date == datetime.date.today() and request.user.department.thining_factor != 0:
      exam.thin_fact = request.user.department.thining_factor
      thin_fac_save_inital = False
    else:
      exam.thin_fact = None

  if exam.std_cnt == 0.0:
    exam.std_cnt = None

  context = {
    'title'     : server_config.SERVER_NAME,
    'version'   : server_config.SERVER_VERSION,
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
      'thin_fac' : exam.thin_fact,
      'save_fac' : thin_fac_save_inital
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
    'GetBackupDate' : forms.GetBackupDate(initial={
      'dateofmessurement' : datetime.date.today()
    }),
    'previous_samples': previous_samples,
    'csv_data': csv_data,
    'csv_data_len': len(data_names),
    'error_message' : error_message,
    'standard_count' : exam.std_cnt,
  }

  return HttpResponse(template.render(context, request))


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
  hospital = request.user.department.hospital

  # Search to find patient id - pick field response
  
  dataset = pacs.move_from_pacs(
    current_user,
    rigs_nr
  )

  if dataset == None or not('GFR' in dataset):
    #Query Failed!
    logger.warning(f"""
    Examination unknown to GFR Calc
    
    dataset from query:
    {dataset}
    """)
    error_template = loader.get_template('main_page/present_old_study_error.html')
    error_context  = {
      'AccessionNumber' : rigs_nr
    }
    if dataset != None:
      error_context['dataset'] = dataset

    return HttpResponse(error_template.render(error_context,request))

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
    'title'     : server_config.SERVER_NAME,
    'version'   : server_config.SERVER_VERSION,
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
  hospital = request.user.department.hospital.short_name
  
  DICOM_directory = '{0}{1}/'.format(base_resp_dir, hospital)

  if not os.path.exists(base_resp_dir):
    os.mkdir(base_resp_dir)

  if not os.path.exists(DICOM_directory):
    os.mkdir(DICOM_directory)

  exam = pacs.get_examination(request.user, rigs_nr, DICOM_directory)
  
  # Determine whether QA plot should be displayable - i.e. the study has multiple
  # test values
  show_QA_button = (len(exam.tch_cnt) > 1)

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
    'title'     : server_config.SERVER_NAME,
    'version'   : server_config.SERVER_VERSION,
    'name': exam.name,
    'date': exam.date,
    'rigs_nr': rigs_nr,
    'image_path': plot_path,
    'show_QA_button': show_QA_button,
  }

  return HttpResponse(template.render(context,request))


class DeletedStudiesView(LoginRequiredMixin, TemplateView):
  """
  Displays deleted studies from 30 days ago.
  Works like a trashcan for files, that deleted studies lie for 30 days until
  they are completly removed.
  """

  template_name = "main_page/deleted_studies.html"

  def get(self, request):
    # Get list of all deleted studies
    user_hosp = request.user.department.hospital

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
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'deleted_studies': deleted_studies,
    }

    return render(request, self.template_name, context)