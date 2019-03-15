import datetime
import numpy as np

from . import formatting
from .clearance_math import clearance_math


class ExaminationInfo:
  def __init__(self):
    rigs_nr     = '',       # Rigs number of the examination
    name        = '',       # Name of patient
    cpr         = '',       # Cpr number of patient
    age         = '',       # Age of patient
    date        = '',       # Scheduled data of examination
    sex         = '',       # Sex of patient
    gfr         = '',       # GFR result (e.g. 'normal', 'svært nedsat', etc.)
    height      = 0.0,      # Height of patient
    weight      = 0.0,      # Weight of patient
    BSA         = 0.0,      # Body surface area of the patient
    clearance   = 0.0,      # Computed clearance
    clearance_N = 0.0,      # Normalized clearance
    Method      = '',       # Method of the examination (e.g. 'et punkts, 'flere punkts', etc.)
    inj_t       = None,     # Injection time of examination (Datetime object, default=None)
    inj_weight  = 0.0,      # Weight difference between vials
    inj_before  = 0.0,      # Weight of vial before examination
    inj_after   = 0.0,      # Weight of vial after examination
    thin_fact   = 0.0,      # Thinning factor
    std_cnt     = 0.0,      # Standard count
    sam_t       = np.array([]), # Datetime list - sample times for the examination
    tch_cnt     = np.array([]), # list of technetium counts
    dosis       = 0,        # Derived value from standard count, thinning factor and weight difference between vials
    image       = np.array([]) # pixeldata, contains the resulting image stored in PACS


def deserialize(dicom_obj):
  """
  Deserializes a dicom object, i.e. turns a dicom object into an ExaminationInfo
  object.

  This is to make it easier to work with a standard python class, instead of direct
  dicom objects and their related types
  
  Args:
    dicom_obj: dicom object to deserialize

  Returns:
    An ExaminationInfo instance containing the deserialized values of the dicom object
  """
  exam = ExaminationInfo()

  exam.rigs_nr = dicom_obj.AccessionNumber
  exam.cpr = formatting.format_cpr(dicom_obj.PatientID)
  exam.date = formatting.format_date(dicom_obj.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate)
  exam.name = formatting.format_name(dicom_obj.PatientName)

  # Depermine patient sex based on cpr nr. if not able to retreive it
  if 'PatientSex' in dicom_obj:
    exam.sex = dicom_obj.PatientSex
  else:
    exam.sex = clearance_math.calculate_age(exam.cpr)

  if 'PatientWeight' in dicom_obj:
    exam.weight = dicom_obj.PatientWeight
  
  if 'PatientSize' in dicom_obj:
    exam.height = dicom_obj.PatientSize
  
  if 'PatientAge' in dicom_obj:
    exam.age = dicom_obj.PatientAge
  else:
    exam.age = clearance_math.calculate_age(exam.cpr)

  if 'clearance' in dicom_obj:
    exam.clearance = dicom_obj.clearance
  
  if 'clearance_N' in dicom_obj:
    exam.clearance_N = dicom_obj.clearance_N

  if 'GFR' in dicom_obj:
    exam.gfr = dicom_obj.GFR
  
  if 'inj_before' in dicom_obj:
    exam.inj_befre = dicom_obj.inj_before

  if 'inj_after' in dicom_obj:
    exam.inj_after = dicom_obj.inj_after

  if 'ClearTest' in dicom_obj:
    if 'thiningfactor' in dicom_obj.ClearTest[0]:
      exam.thin_fact = dicom_obj.ClearTest[0].thiningfactor
    if 'stdcnt' in dicom_obj.ClearTest[0]:
      exam.std_cnt = dicom_obj.ClearTest[0].stdcnt

    sample_times = []
    tch99_cnt = []
    for test in dicom_obj.ClearTest:
      if 'SampleTime' in test:
        sample_times.append(datetime.datetime.strptime(test.SampleTime, '%Y%m%d%H%M'))
      if 'cpm' in test:
        tch99_cnt.append(test.cpm)

    exam.sam_t = np.array(sample_times)
    exam.tch_cnt = np.array(tch99_cnt)

  if 'injTime' in dicom_obj:
    exam.inj_t = datetime.datetime.strptime(dicom_obj.injTime, '%Y%m%d%H%M')
    
  if 'PatientSize' in dicom_obj and 'PatientWeight' in dicom_obj:
    exam.BSA = clearance_math.surface_area(dicom_obj.PatientSize, dicom_obj.PatientWeight)

  if 'PixelData' in dicom_obj:
    exam.image = np.array(dicom_obj.pixel_array)

  if 'GFRMethod' in dicom_obj:
    exam.Method = dicom_obj.GFRMethod

  return exam
