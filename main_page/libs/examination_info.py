import datetime
import numpy as np

from main_page.libs import formatting
from main_page.libs.clearance_math import clearance_math


class ExaminationInfo:
  def __init__(self):
    self.age         = ''       # Age of patient
    self.birthdate   = None
    self.BSA         = 0.0      # Body surface area of the patient
    self.clearance   = 0.0      # Computed clearance
    self.cpr         = ''       # Cpr number of patient
    self.clearance_N = 0.0      # Normalized clearance
    self.date        = ''       # Scheduled data of examination
    self.dosis       = 0        # Derived value from standard count, thinning factor and weight difference between vials
    self.exam_type   = ''
    self.gfr         = ''       # GFR result (e.g. 'normal', 'svært nedsat', etc.)
    self.height      = None      # Height of patient
    self.image       = np.array([]) # pixeldata, contains the resulting image stored in PACS
    self.inj_after   = None      # Weight of vial after examination
    self.inj_before  = None      # Weight of vial before examination
    self.inj_t       = None     # Injection time of examination (Datetime object, default=None)
    self.inj_weight  = 0.0      # Weight difference between vials
    self.Method      = ''       # Method of the examination (e.g. 'et punkts, 'flere punkts', etc.)
    self.name        = ''       # Name of patient
    self.procedure   = ''       # The procedure of the examination
    self.rigs_nr     = ''       # Rigs number of the examination
    self.sam_t       = np.array([]) # Datetime list - sample times for the examination
    self.sex         = ''       # Sex of patient
    self.std_cnt     = None      # Standard count
    self.tch_cnt     = np.array([]) # list of technetium counts
    self.thin_fact   = None      # Thinning factor
    self.weight      = None      # Weight of patient
    self.exam_status      = 0         # Status of examination: 0 = unedited, 1 = contains saved data, 2 = ready to send to pacs


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
  exam.name = formatting.person_name_to_name(str(dicom_obj.PatientName))
  
  try:
    exam.date = formatting.format_date(dicom_obj.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate)
  except AttributeError:
    exam.date = formatting.format_date(dicom_obj.StudyDate)

  if 'RequestedProcedureDescription' in dicom_obj:
    exam.procedure = dicom_obj.RequestedProcedureDescription
  else:
    try:
      if 'RequestedProcedureDescription' in dicom_obj.ScheduledProcedureStepSequence[0].ScheduledProcedureStepDescription:
        exam.procedure = dicom_obj.ScheduledProcedureStepSequence[0].ScheduledProcedureStepDescription
    except AttributeError:
      exam.procedure = ""

  # Depermine patient sex based on cpr nr. if not able to retreive it
  if 'PatientSex' in dicom_obj:
    exam.sex = dicom_obj.PatientSex
  else:
    exam.sex = clearance_math.calculate_sex(exam.cpr)

  if 'PatientWeight' in dicom_obj:
    exam.weight = dicom_obj.PatientWeight
  
  if 'PatientSize' in dicom_obj:
    exam.height = dicom_obj.PatientSize * 100
  
  if 'PatientAge' in dicom_obj:
    exam.age = dicom_obj.PatientAge
  else:
    exam.age = clearance_math.calculate_age(exam.cpr)

  if 'PatientBirthDate' in dicom_obj:
    birthday_str = dicom_obj.PatientBirthDate[0:4] + '-' + dicom_obj.PatientBirthDate[4:6] + '-' + dicom_obj.PatientBirthDate[6:8]
    exam.birthdate = birthday_str
  else:
    try:
      exam.birthdate = clearance_math.calculate_birthdate(exam.cpr)
    except:
      exam.birthdate = '2000-01-01'

  if 'clearance' in dicom_obj:
    exam.clearance = dicom_obj.clearance
  
  if 'RequestedProcedureDescription' in dicom_obj:
    exam.exam_type = dicom_obj.RequestedProcedureDescription

  if 'clearance_N' in dicom_obj:
    exam.clearance_N = dicom_obj.clearance_N

  if 'GFR' in dicom_obj:
    exam.gfr = dicom_obj.GFR
  
  if 'injbefore' in dicom_obj:
    exam.inj_before = dicom_obj.injbefore

  if 'injafter' in dicom_obj:
    exam.inj_after = dicom_obj.injafter

  if 'thiningfactor' in dicom_obj:
    exam.thin_fact = dicom_obj.thiningfactor
  if 'stdcnt' in dicom_obj:
    exam.std_cnt = dicom_obj.stdcnt
  
  if 'ClearTest' in dicom_obj:
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
    exam.BSA = clearance_math.surface_area(dicom_obj.PatientSize * 100.0, dicom_obj.PatientWeight)

  if 'PixelData' in dicom_obj:
    # Reads DICOM conformant image to PIL displayable image
    exam.image = np.frombuffer(dicom_obj.PixelData, dtype=np.uint8)
    exam.image = np.reshape(exam.image, (1920, 1080, 3))
    exam.image = np.reshape(exam.image, (1080, 1920, 3))

  if 'GFRMethod' in dicom_obj:
    exam.Method = dicom_obj.GFRMethod

  if 'ExamStatus' in dicom_obj:
    exam.exam_status = dicom_obj.ExamStatus

  return exam


def mass_deserialize(dicom_objs):
  return [deserialize(obj) for obj in dicom_objs]
