from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import loader
from django.shortcuts import redirect

from .. import forms
from .query_wrappers import ris_query_wrapper as ris
from .clearance_math import clearance_math

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
    weight = float(request.POST['weight'])
    height = float(request.POST['height'])
    BSA = clearance_math.surface_area(height, weight)

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
    clearence, clearence_norm = clearance_math.calc_clearance(
      inj_datetime, 
      sample_datetimes,
      tec_counts,
      BSA,
      dosis,
      method=method
    )

    cpr = request.POST['cpr']
    gfr = clearance_math.kidney_function(clearence_norm, cpr)


    plot_path = clearance_math.generate_plot_text(
      weight,
      height,
      BSA,
      clearence,
      clearence_norm,
      gfr,
      cpr,
      rigs_nr
    )

    Dicom_base_dirc = 'Active_Dicom_objects'
    hospital     = request.user.hospital
    img_path     = 'main_page/static/main_page/images'

    if not os.path.exists(Dicom_base_dirc):
      os.mkdir(Dicom_base_dirc)

    if not os.path.exists('{0}/{1}'.format(Dicom_base_dirc, hospital)):
      os.mkdir('{0}/{1}'.format(Dicom_base_dirc, hospital))

    if not os.path.exists('{0}/{1}'.format(img_path, hospital)):
      os.mkdir('{0}/{1}'.format(img_path, hospital))

    dcm_obj_path = '.{0}/{1}/{2}.dcm'.format(Dicom_base_dirc ,request.user.hospital, rigs_nr)

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

    ris.store_dicom(
      dcm_obj_path,
      gfr            = gfr,
      clearence      = clearence,
      clearence_norm = clearence_norm,
      series_instance_uid= img_obj.SeriesInstanceUID,
      sop_class_uid= img_obj.SOPClassUID,
      sop_instance_uid= img_obj.SOPInstanceUID,
      pixeldata = img_obj.PixelData 
      )
    


def store_form(request, rigs_nr):
#Input indicating if something have been typed
  
  Dicom_base_dirc = 'Active_Dicom_objects'
  hospital = request.user.hospital

  if not os.path.exists(Dicom_base_dirc):
    os.mkdir(Dicom_base_dirc)

  if not os.path.exists('{0}/{1}'.format(Dicom_base_dirc, hospital)):
    os.mkdir('{0}/{1}'.format(Dicom_base_dirc, hospital))
  
  DICOM_dirc = '{0}/{1}'.format(Dicom_base_dirc, hospital)

  dicom_path = '{0}/{1}.dcm'.format(DICOM_dirc, rigs_nr)  

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
  elif study_type == 3:
    study_str = 'Flere prøve Barn'
  elif study_type == 4:
    study_str = '24 Timer Voksen'
  elif study_type == 5:
    study_str = '24 Timer Barn'

  #Store Study
  ris.store_dicom(
    dicom_path,
    gfr_type=study_str
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

  bsa_method = 'Du Bois'
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
  print(sample_dates)
  #There's Data to put in
  if len(sample_dates) > 0:
    #If thining factor have been inputed    
    thin_factor = 0
    if len(request.POST['thin_fac']) > 0 :
      thin_factor = float(request.POST['thin_fac'])
    std_cnt = 0
    if len(request.POST['std_cnt']) > 0 :
      std_cnt = float(request.POST['std_cnt'])

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
      rigs_nr: The accession number for the examination

  """
  #Extract Information about the 



  # Send information to pacs


  # Remove study from directory
  pass
