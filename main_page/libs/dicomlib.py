import pydicom, datetime, logging
from pydicom.values import convert_SQ, convert_string
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.datadict import DicomDictionary, keyword_dict
from pydicom import uid

import numpy as np

from .server_config import new_dict_items
from . import server_config
from . import formatting

logger = logging.getLogger()


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

def save_dicom(file_path, dataset, default_error_handling = True ):
  """
  Saves a dicom file to a selected file path

  Args:
    file_path : String, desination for file to be saved
    dataset

  kwargs:
    no_error: With default dicom handling
  Raises
    Attribute Error: Incomplete Dicom, without default errorhandling
    Value Error: No given AccessionNumber
  """
  
  dataset.is_implicit_VR = True
  dataset.is_little_endian = True
  if (not 'SOPClassUID' in dataset) or (not 'SOPInstanceUID' in dataset):  #Dicom is incomplete
    if default_error_handling: 
      if 'AccessionNumber' in dataset:
        dataset.SOPClassUID = '1.2.840.10008.5.1.4.1.1.7' #Secondary Image Capture
        dataset.SOPInstanceUID = uid.generate_uid(prefix='1.3.', entropy_srcs=[dataset.AccessionNumber, 'SOP'])
      else:
        raise ValueError('default Error handling for saving dicom failed!\nCannot create SOPInstanceUID without AccessionNumber!')
    else: 
      raise AttributeError('Incomplete Dicom Required Tags are SOPClassUID and SOPInstanceUID')
  
  dataset.fix_meta_info()
  logger.info('Saving Dicom file at:{0}'.format(file_path))
  dataset.save_as(file_path, write_like_original = False)

def fill_dicom(ds,
    age                 = None,
    birthday            = None,
    bsa_method          = None,
    clearance           = None,
    clearance_norm      = None,
    cpr                 = None,
    department          = None,
    exam_status         = None,
    gender              = None,
    gfr                 = None,
    gfr_type            = None,
    height              = None,
    injection_after     = None,
    injection_before    = None,
    injection_time      = None,
    injection_weight    = None,
    name                = None,
    pixeldata           = None,
    rigs_nr             = None,
    sample_seq          = None,
    series_instance_uid = None,
    series_number       = None,
    sop_instance_uid    = None,
    station_name        = None,
    study_date          = None,
    std_cnt             = None,
    thiningfactor       = None,
    update_date         = False,
    update_dicom        = False,
    weight              = None
  ):
  """
  Saves information in dicom object, overwriting previous data, with no checks

  Args:
    dicom_obj_path  : string, path to the object where you wish information to stored

  Optional Args:
    cpr             : string, CPR number
    name            : string, Name on format Firstname<1 space>Middlenames sperated by 1 space<1 space>Lastname
    rigs_nr         : string, Accession number
    study_date      : string, on format YYYYMMDDHHMM, describing study date
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

  if rigs_nr:
    ds.AccessionNumber = rigs_nr
  if update_dicom:
    ds.Modality = 'OT'
    #ds.add_new(0x00080070, 'LO', 'GFR-calc') #Manufactorer 
    #Number twos
    #Basic Information
    ds.add_new(0x00080064, 'CS', 'SYN')
    ds.add_new(0x00230010, 'LO', 'Clearance - Denmark - Region Hovedstaden')
    ds.add_new(0x00080030, 'TM', '')
    ds.add_new(0x00080090, 'PN', '')  #request.user.name or BAMID.name
    ds.add_new(0x00200010, 'SH', 'GFR#' + ds.AccessionNumber[4:])  #Study ID
    ds.add_new(0x00200013, 'IS', '1')
    
    ds.SoftwareVersions = f'{server_config.SERVER_NAME} - {server_config.SERVER_VERSION}'

    ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.7' #Secoundary Image Capture
    ds.SOPInstanceUID = uid.generate_uid(prefix='1.3.', entropy_srcs=[ds.AccessionNumber, 'SOP'])
    #ds.StudyInstanceUID = uid.generate_uid(prefix='1.3.', entropy_srcs=[ds.AccessionNumber, 'Study'])
    ds.SeriesInstanceUID = uid.generate_uid(prefix='1.3.', entropy_srcs=[ds.AccessionNumber, 'Series'])

  if department:
    ds.InstitutionName = department.hospital_Name
    ds.InstitutionAddress = department.address
    ds.InstitutionalDepartmentName = department.department

  # Set StudyDate
  if update_date:
    if study_date:
      date_string = study_date.replace('-','')
      time_string = datetime.datetime.now().strftime('%H%M')

      ds.StudyDate = date_string
      ds.SeriesDate = date_string
      ds.StudyTime = time_string
      ds.SeriesTime = time_string
      try:
        ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate = date_string
        ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartTime = time_string
      except:
        pass #TODO: make ScheduledProcedureStepSequence
    else:
      ds.StudyDate = ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate
      ds.StudyTime = ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartTime
      ds.SeriesDate = ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate
      ds.SeriesTime = ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartTime

  if 'ScheduledProcedureStepSequence' in ds:  
    Schedule = ds.ScheduledProcedureStepSequence[0]
    ds.StudyDescription = Schedule.ScheduledProcedureStepDescription
    ds.Modality = Schedule.Modality


  if birthday:
    ds.PatientBirthDate = birthday.replace('-','')

  if cpr:
    ds.PatientID = cpr.replace('-','')

  if name:
    PN = formatting.name_to_person_name(name)
    ds.PatientName = PN  

  if series_number:
    ds.add_new(0x00200011, 'IS', series_number)

  if station_name:
    ds.StationName = station_name

  if exam_status:
    if 'Examstatus' in ds:
      if ds.ExamStatus < exam_status:
        ds.ExamStatus = exam_status
    else:
      ds.ExamStatus = exam_status

  if age:
    ds.PatientAge = age

  if height:
    ds.PatientSize = height

  if weight:
    ds.PatientWeight = weight

  if gender:
    gender = gender.lower()
    if gender in ['male', 'm', 'mand', 'dreng']:
      ds.PatientSex = 'M'
    if gender in ['kvinde', 'd', 'k', 'pige', 'woman', 'dame', 'female' ]:
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

  if std_cnt:
    ds.add_new(0x00231024, 'DS', std_cnt)
  if thiningfactor:
    ds.add_new(0x00231028, 'DS', thiningfactor)

  if sample_seq:
    logger.info('adding Seqence:{0}'.format(sample_seq))
    seq_list = []
    
    # Add Information About the Sample
    for sample in sample_seq:
      seq_elem = Dataset()
      seq_elem.add_new(0x00231021, 'DT', sample[0])
      seq_elem.add_new(0x00231022, 'DS', sample[1])
      seq_list.append(seq_elem)
    
    ds.add_new(0x00231020, 'SQ', Sequence(seq_list))
  elif sample_seq == [] and 'ClearTest' in ds:
    logger.info('Removing Seqence')
    del ds[0x00231020]

  # PRIVATE TAGS END

  if pixeldata:
    # Save in DICOM pixel data encoding format ()
    pixeldata = np.frombuffer(pixeldata, dtype=np.uint8) # Reads byte array to 1D numpy array
    pixeldata = np.reshape(pixeldata, (1080, 1920, 3))   # Reshapes to PIL displayable image - current format of byte string
    pixeldata = np.reshape(pixeldata, (1920, 1080, 3))   # Reshapes to DICOM conformat pixel data encoding (for more details see: https://dicom.innolitics.com/ciods/segmentation/image-pixel/7fe00010)

    ds.SamplesPerPixel = 3
    ds.PhotometricInterpretation = 'RGB'
    ds.PlanarConfiguration = 0
    ds.Rows = 1080
    ds.Columns = 1920
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.PixelData = pixeldata.tobytes()
    ds.ImageComments = 'GFR summary, generated by GFR-calc'
