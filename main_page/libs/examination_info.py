import datetime
import numpy as np


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
    inj_t       = datetime.datetime(2000,1,1,0,0), # Injection time of examination
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
  """
  