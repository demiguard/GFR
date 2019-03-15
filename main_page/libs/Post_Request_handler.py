from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import loader
from django.shortcuts import redirect

from .. import forms
from .. import models
from .query_wrappers import ris_query_wrapper as ris
from .clearance_math import clearance_math

from . import server_config
from . import dicomlib

from dateutil import parser as date_parser
import datetime
import glob
import os
import pandas
import numpy
import pydicom
import PIL

#Handles Post Requests for Views

# Fill Study Post Request
def fill_study_post(request, rigs_nr):
  """
  Handles Post request for fill study

  Args:
    Request: The Post request
    rigs_nr: The REGH number for the corosponding examination
  """
  #Save Without Redirect

  if 'save' in request.POST:
    store_form(request,rigs_nr)

  #Beregn
  if 'calculate' in request.POST:
    store_form(request, rigs_nr) 
    # Construct datetime for injection time
    inj_time = request.POST['injection_time']
    inj_date = request.POST['injection_date']
    inj_datetime = date_parser.parse("{0} {1}".format(inj_date, inj_time))

    # Construct datetimes for study times
    sample_dates = request.POST.getlist('study_date')[:-1]
    sample_times = request.POST.getlist('study_time')[:-1]

    sample_datetimes = numpy.array([date_parser.parse("{0} {1}".format(date, time)) 
                          for time, date in zip(sample_times, sample_dates)])

    # Measured tec99 counts
    tec_counts = numpy.array([float(x) for x in request.POST.getlist('test_value')])

    # Compute surface area
    weight = float(request.POST['weight'].split('.')[0])
    height = float(request.POST['height'].split('.')[0])
    BSA = clearance_math.surface_area(height, weight)

    # Compute dosis
    inj_weight_before = float(request.POST['vial_weight_before'])
    inj_weight_after = float(request.POST['vial_weight_after'])
    inj_weight = inj_weight_before - inj_weight_after

    # TODO: CHANGE THE FACTOR AND STANDARD COUNT TO BE ON THE PAGE AS WELL
    STD_CNT = int(request.POST['std_cnt'].split('.')[0])
    FACTOR = int(request.POST['thin_fac'].split('.')[0])
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
    clearance, clearance_norm = clearance_math.calc_clearance(
      inj_datetime, 
      sample_datetimes,
      tec_counts,
      BSA,
      dosis,
      method=method
    )

    cpr = request.POST['cpr']
    age = float(request.POST['age'])
    gender = request.POST['sex']

    gfr = clearance_math.kidney_function(clearance_norm, cpr, age=age, gender=gender)

    plot_path = clearance_math.generate_plot_text(
      weight,
      height,
      BSA,
      clearance,
      clearance_norm,
      gfr,
      age,
      gender,
      rigs_nr,
      hosp_dir=request.user.hospital
    )

    base_resp_dir = server_config.FIND_RESPONS_DIR
    hospital     = request.user.hospital
    img_path     = 'main_page/static/main_page/images'

    if not os.path.exists(base_resp_dir):
      os.mkdir(base_resp_dir)

    if not os.path.exists('{0}/{1}'.format(base_resp_dir, hospital)):
      os.mkdir('{0}/{1}'.format(base_resp_dir, hospital))

    if not os.path.exists('{0}/{1}'.format(img_path, hospital)):
      os.mkdir('{0}/{1}'.format(img_path, hospital))

    dcm_obj_path = '{0}/{1}/{2}.dcm'.format(base_resp_dir, hospital, rigs_nr)

    dcm_img_path = '{0}/{1}/{2}.dcm'.format(img_path, hospital, rigs_nr)

    img2dcm_query = [
      'img2dcm',                    # Path to img2dcm # TODO: Change this to be an absolute path to the program on the production server (rememeber to set the dcm tool kit system variable path)
      plot_path,                    # Input location of image
      dcm_img_path,                 # Output location
      '-sc',                        # Write as secondary capture SOP class
      '-i',                         # Specify input image format
      'BMP'
    ]

    # TODO: Check exit-code of query and handle errors
    ris.execute_query(img2dcm_query)
    img_obj = pydicom.dcmread(dcm_img_path)
  
    # Read StudyInstanceUID from main dicom object, to allow storage of image together with it
    """
    These are handels by store dicom
    study_UID = dcm_obj.StudyInstanceUID

    # Store both dicom objects; main dicom object and image object
    img_obj.StudyInstanceUID = study_UID

    dcm_obj.SeriesInstanceUID = img_obj.SeriesInstanceUID
    dcm_obj.SOPClassUID = img_obj.SOPClassUID
    dcm_obj.SOPInstanceUID = img_obj.SOPInstanceUID

    img_obj.save_as(dcm_img_path)
    dcm_obj.save_as(dcm_obj_path)
    """

    dicomlib.store_dicom(
      dcm_obj_path,
      gfr            = gfr,
      clearance      = clearance,
      clearance_norm = clearance_norm,
      series_instance_uid= img_obj.SeriesInstanceUID,
      sop_class_uid= img_obj.SOPClassUID,
      sop_instance_uid= img_obj.SOPInstanceUID,
      pixeldata = img_obj.PixelData 
    )
    #Remove bmp file and dcm file
    os.remove(plot_path)
    os.remove(dcm_img_path)


def store_form(request, rigs_nr):
#Input indicating if something have been typed
  
  base_resp_dir = server_config.FIND_RESPONS_DIR
  hospital = request.user.hospital

  if not os.path.exists(base_resp_dir):
    os.mkdir(base_resp_dir)

  if not os.path.exists('{0}{1}'.format(base_resp_dir, hospital)):
    os.mkdir('{0}{1}'.format(base_resp_dir, hospital))
  
  DICOM_dirc = '{0}{1}/'.format(base_resp_dir, hospital)

  dicom_path = '{0}{1}.dcm'.format(DICOM_dirc, rigs_nr)  

  # Store age
  if request.POST['age']:    
    ris.store_dicom(
      dicom_path,
      age=request.POST['age']
    )

  #Injection Date Time information
  if len(request.POST['injection_date']) > 0:
    inj_time = request.POST['injection_time']
    inj_date = request.POST['injection_date']
    inj_datetime = date_parser.parse("{0} {1}".format(inj_date, inj_time))

    ris.store_dicom(
      dicom_path,
      injection_time = inj_datetime.strftime('%Y%m%d%H%M')
    )

  #Study Always exists
  study_type = int(request.POST['study_type'])
  study_str = ''
  if study_type == 0:
    study_str = 'Et punkt Voksen'
  elif study_type == 1:
    study_str = 'Et punkt Barn'
  elif study_type == 2:
    study_str = 'Flere prøve Voksen'

  #Store Study
  ris.store_dicom(
    dicom_path,
    gfr_type=study_str
  )

  if len(request.POST['sex']) > 0:
    ris.store_dicom(
      dicom_path,
      gender=request.POST['sex']
    )

  if (len(request.POST['vial_weight_before']) > 0) and (len(request.POST['vial_weight_after']) > 0):
    vial_weight_before = float(request.POST['vial_weight_before'])
    vial_weight_after = float(request.POST['vial_weight_after'])
    vial_weight_inj   = vial_weight_before - vial_weight_after

    ris.store_dicom(
      dicom_path,
      injection_before = vial_weight_before,
      injection_after  = vial_weight_after,
      injection_weight = vial_weight_inj 
      )

  elif len(request.POST['vial_weight_before']) > 0:
    vial_weight_before = float(request.POST['vial_weight_before'])
    ris.store_dicom(
      dicom_path,
      injection_before= vial_weight_before
    )

  bsa_method = 'Haycock'
  if (len(request.POST['weight']) > 0):
    ris.store_dicom(
      dicom_path,
      weight     = float(request.POST['weight']) 
    ) 
  if (len(request.POST['height']) > 0):
    ris.store_dicom(
      dicom_path,
      height     = float(request.POST['height']),
      bsa_method = bsa_method 
    )

  sample_dates = request.POST.getlist('study_date')[:-1]
  sample_times = request.POST.getlist('study_time')[:-1]
  sample_tec99 = numpy.array([float(x) for x in request.POST.getlist('test_value')])

  #There's Data to put in
  if sample_dates:
    #If thining factor have been inputed
    if request.POST['thin_fac']:
      thin_factor = float(request.POST['thin_fac'])
    if request.POST['std_cnt_text_box']:
      std_cnt = float(request.POST['std_cnt_text_box'])

    formated_sample_date = [date.replace('-','') for date in sample_dates]
    formated_sample_time = [time.replace(':','') for time in sample_times]
    zip_obj_datetimes = zip(formated_sample_date,formated_sample_time)

    sample_datetimes = [date + time for date,time in zip_obj_datetimes]  
    
    zip_obj_seq = zip(sample_datetimes, sample_tec99)
    seq = [(datetime, cnt, std_cnt, thin_factor) for datetime, cnt in zip_obj_seq]
    
    ris.store_dicom(
      dicom_path,
      sample_seq = seq
    )

def send_to_pacs(request, rigs_nr):
  """
  Handles the Post request, when there's a complete study, and it needs to be send back to pacs 

  Args:
    request: The Post Request
    rigs_nr: The accession number for the examination to store
  """
  # Send information to PACS
  obj_path = "{0}{1}/{2}.dcm".format(
    server_config.FIND_RESPONS_DIR,
    request.user.hospital,
    rigs_nr
  )

  if ris.store_in_pacs(request.user, obj_path):
    # Remove the file
    os.remove(obj_path)

    # Store the RIGS number in the HandleExaminations table
    HE = models.HandledExaminations(rigs_nr=rigs_nr)
    HE.save()
  else:
    # Try again?
    # Redirect to informative site, telling the user that the connection to PACS is down
    print("Failed to store in pacs")
