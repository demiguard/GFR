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
      sample_times = clearance_math.compute_times(inj_datetime, sample_datetimes)
      data_points1 = numpy.array([sample_times, tec_counts])
    else:
      data_points1 = numpy.array([[], []])
      
    age = int(request.POST['age'])
    data_points2 = numpy.array([[age], [gfr_norm]])

    # plot_path = clearance_math.generate_plot(
    #   data_points1,
    #   data_points2,
    #   rigs_nr
    # )

    cpr = request.POST['cpr']

    plot_path = clearance_math.generate_plot_text(
      weight,
      height,
      BSA,
      gfr,
      gfr_norm,
      clearance_math.kidney_function(gfr_norm, cpr),
      cpr,
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
      plot_path,                    # Input location of image
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
      '11112',                        # Port of PACS server
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





