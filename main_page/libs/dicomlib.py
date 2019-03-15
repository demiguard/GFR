import pydicom
from pydicom.values import convert_SQ, convert_string
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.datadict import DicomDictionary, keyword_dict

from .server_config import new_dict_items


def dcmread_wrapper(filename, is_little_endian=True, is_implicit_VR=True):
  """
    Takes a file path and reads it, update the private tags accordingly

    Supports only VM 1

  """
  DicomDictionary.update(new_dict_items)  
  new_names_dict = dict([(val[4], tag) for tag, val in new_dict_items.items()])
  keyword_dict.update(new_names_dict)

  obj = pydicom.dcmread(filename)
  obj = update_tags(obj, is_little_endian, is_implicit_VR)

  return obj


def update_tags(obj, is_little_endian=True, is_implicit_VR=True):
  for ds in obj:
    if ds.tag not in new_dict_items:
      continue
    if ds.VR == 'UN':
      if new_dict_items[ds.tag][0] == 'SQ':
        ds_sq = convert_SQ(ds.value, is_implicit_VR , is_little_endian)
        seq_list = []
        for sq in ds_sq:
          sq = update_tags(sq,is_little_endian=is_little_endian, is_implicit_VR=is_implicit_VR)
          seq_list.append(sq)
        obj.add_new(ds.tag, new_dict_items[ds.tag][0], Sequence(seq_list)) 
      elif new_dict_items[ds.tag][0] == 'LO':
        new_val = convert_string(ds.value, is_little_endian)
        obj.add_new(ds.tag, new_dict_items[ds.tag][0], new_val)
      else:
        obj.add_new(ds.tag, new_dict_items[ds.tag][0], ds.value)
    elif ds.VR == 'SQ':
      for ds_sq in ds:
        update_tags(ds_sq)


  return obj


def store_dicom(dicom_obj_path,
    age                 = None,
    height              = None,
    weight              = None,
    gender              = None,
    gfr                 = None,
    gfr_type            = None,
    injection_time      = None,
    injection_weight    = None,
    injection_before    = None,
    injection_after     = None,
    bsa_method          = None,
    clearance           = None,
    clearance_norm      = None,
    series_instance_uid = None,
    sop_class_uid       = None,
    sop_instance_uid    = None,
    sample_seq          = [],
    pixeldata           = []
  ):
  """
  Saves information in dicom object, overwriting previous data, with no checks

  Args:
    dicom_obj_path  : string, path to the object where you wish information to stored

  Optional Args:
    age             : int, Age of the patient
    height          : float, Height of patient wished to be stored
    weight          : float, Weight of patient wished to be stored
    gfr             : string, either 'Normal', 'Moderat Nedsat', 'Nedsat', 'Stærkt nedsat' 
    gfr_type        : string, Method used to calculate GFR
    injection_time  : string on format 'YYYYMMDDHHMM', Describing when a sample was injected
    injection_weight: float, Weight of injection
    injection_before: float, Weight of Vial Before injection
    injection_after : float, Weight of Vial After Injection
    bsa_method      : string, Method used to calculate Body Surface area
    clearance       : float, Clearance Value
    clearance_norm  : float, Clearance Value Normalized to 1.73m²
    sample_seq      : list of lists where every list is on the format: 
      *List_elem_1  : string on format 'YYYYMMDDHHMM', describing sample taken time
      *List_elem_2  : float, cpm of sample
      *List_elem_3  : float, stdcnt of the sample
      *List_elem_4  : float, Thining Factor of Sample. In most sane cases these are the same throught the list

  Remarks
    It's only possible to store the predefined args with this function
  """
  DicomDictionary.update(new_dict_items)

  new_names_dirc = dict([(val[4], tag) for tag, val in new_dict_items.items()])
  keyword_dict.update(new_names_dirc)

  ds = dcmread_wrapper(dicom_obj_path)
  ds.add_new(0x00230010, 'LO', 'Clearance - Denmark - Region Hovedstaden')
  ds.add_new(0x00080080, 'LO', 'Rigshospitalet')
  ds.add_new(0x00080081, 'ST', 'Blegdamsvej 9, 2100 København')
  ds.add_new(0x00081040, 'LO', 'Klin. Fys.')
  ds.add_new(0x00080064, 'CS', 'SYN')
  ds.Modality =  ds.ScheduledProcedureStepSequence[0].Modality
  #ds.add_new(0x00080070, 'LO', 'GFR-calc') #Manufactorer 
  #Number twos
  ds.add_new(0x00080030, 'TM', '')
  ds.add_new(0x00080090, 'PN', '')  #request.user.name or BAMID.name
  ds.add_new(0x00200010, 'SH', '')
  ds.add_new(0x00200013, 'IS', '1')


  # Set StudyDate
  ds.StudyDate = ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate

  if series_instance_uid:
    ds.SeriesInstanceUID = series_instance_uid

  if sop_class_uid:
    ds.SOPClassUID = sop_class_uid

  if sop_instance_uid:
    ds.SOPInstanceUID = sop_instance_uid

  if age:
    ds.PatientAge = age

  if height:
    ds.PatientSize = height

  if weight:
    ds.PatientWeight = weight

  if gender:
    if gender in ['Male', 'MALE', 'm', 'M', 'Mand', 'mand', 'MAND']:
      ds.PatientSex = 'M'
    if gender in ['Kvinde', 'KVINDE', 'd', 'D', 'k', 'K', 'woman', 'Woman','WOMAN', 'Dame', 'dame', 'DAME', 'female', 'Female', 'FEMALE']:
      ds.PatientSex = 'F'

  # PRIVATE TAGS START
  if gfr:
    # ds.GFR = gfr
    # ds.GFRVersion = 'Version 1.0'
    ds.add_new(0x00231001, 'LO', gfr)
    ds.add_new(0x00231002, 'LO', 'Version 1.0')

  if gfr_type:
    # ds.GFRMethod = gfr_type
    ds.add_new(0x00231010, 'LO', gfr_type)
    ds.add_new(0x0008103E, 'LO', 'Clearance ' + gfr_type)

  if injection_time:
    # ds.injTime = injection_time
    ds.add_new(0x00231018, 'DT', injection_time)

  if injection_weight:
    # ds.injWeight = injection_weight
    ds.add_new(0x0023101A, 'DS', injection_weight)
  
  if injection_before:
    # ds.injbefore = injection_before
    ds.add_new(0x0023101B, 'DS', injection_before)
  
  if injection_after:
    # ds.injafter = injection_after
    ds.add_new(0x0023101C, 'DS', injection_after)

  if bsa_method:
    # ds.BSAmethod = bsa_method
    ds.add_new(0x00231011, 'LO', bsa_method)

  if clearance:
    # ds.clearance = clearance
    ds.add_new(0x00231012, 'DS', clearance)

  if clearance_norm:
    # ds.normClear = clearance_norm
    ds.add_new(0x00231014, 'DS', clearance_norm)

  if sample_seq:
    seq_list = []
    #Add Information About the Sample
    for sample in sample_seq:
      seq_elem = Dataset()
      seq_elem.add_new(0x00231021, 'DT', sample[0])
      seq_elem.add_new(0x00231022, 'DS', sample[1])
      seq_elem.add_new(0x00231024, 'DS', sample[2])
      seq_elem.add_new(0x00231028, 'DS', sample[3])
      
      # seq_elem.SampleTime    = sample[0]
      # seq_elem.cpm           = sample[1]
      # seq_elem.stdcnt        = sample[2]
      # seq_elem.thiningfactor = sample[3]

      seq_list.append(seq_elem)
    # ds.ClearTest = Sequence(seq_list)
    ds.add_new(0x00231020, 'SQ', Sequence(seq_list))

  # PRIVATE TAGS END

  if pixeldata:
    ds.SamplesPerPixel = 3
    ds.PhotometricInterpretation = 'RGB'
    ds.PlanarConfiguration = 0
    ds.Rows = 1080
    ds.Columns = 1920
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.PixelData = pixeldata
    ds.ImageComments = 'GFR summary, generated by GFR-calc'

  ds.fix_meta_info()
  ds.save_as(dicom_obj_path)
