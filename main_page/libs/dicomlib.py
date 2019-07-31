import pydicom, datetime, logging
from pydicom.values import convert_SQ, convert_string
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.datadict import DicomDictionary, keyword_dict
from pydicom import uid

from typing import Type
import numpy as np

from main_page import models
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
          sq = update_tags(sq, is_little_endian=is_little_endian, is_implicit_VR=is_implicit_VR)
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


def save_dicom(file_path, dataset, default_error_handling=True ):
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


def try_add_new(ds: Type[Dataset], tag: int, VR: str, value) -> None:
  """
  Attempts to add a new value by tag, if the value is not None or empty

  Args:
    ds: dataset to add tag/value too
    tag: tag to add
    VR: Value Representation of the value to add
    value: the value to add for the given tag
  """
  if value:
    ds.add_new(tag, VR, value)


def try_update_exam_meta_data(ds: Type[Dataset], update_dicom: bool) -> None:
  """
  Attempts to update meta data for the examination

  Args:
    ds: dataset to update meta data for
    update_dicom: whether or not to update the meta data
  
  Remark:
    This function assumes the AccessionNumber is already set in the dataset
    and that it's atleast 4 characters long
  """
  if update_dicom:
    ds.Modality = 'OT'
    #ds.add_new(0x00080070, 'LO', 'GFR-calc') # Manufacturer                  # ds.Manufacturer
    ds.add_new(0x00080064, 'CS', 'SYN')                                       # ds.ConversionType
    ds.add_new(0x00230010, 'LO', 'Clearance - Denmark - Region Hovedstaden')  # TODO: Figure out what this tag is...
    ds.add_new(0x00080030, 'TM', '')                                          # ds.StudyTime
    ds.add_new(0x00080090, 'PN', '')  # request.user.name or BAMID.name       # ds.ReferringPhysicianName
    ds.add_new(0x00200010, 'SH', 'GFR#' + ds.AccessionNumber[4:])             # ds.StudyID
    ds.add_new(0x00200013, 'IS', '1')                                         # ds.InstanceNumber
    
    ds.SoftwareVersions = f'{server_config.SERVER_NAME} - {server_config.SERVER_VERSION}'

    ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.7' # Secoundary Image Capture
    ds.SOPInstanceUID = uid.generate_uid(prefix='1.3.', entropy_srcs=[ds.AccessionNumber, 'SOP'])
    #ds.StudyInstanceUID = uid.generate_uid(prefix='1.3.', entropy_srcs=[ds.AccessionNumber, 'Study'])
    ds.SeriesInstanceUID = uid.generate_uid(prefix='1.3.', entropy_srcs=[ds.AccessionNumber, 'Series'])


def try_add_department(ds: Type[Dataset], department: Type[models.Department]) -> None:
  """
  Attempts to add department information to the dataset

  Args:
    ds: dataset to add to
    department: if present adds the required information
  """
  if department:
    ds.InstitutionName = department.hospital.name
    ds.InstitutionAddress = department.hospital.address
    ds.InstitutionalDepartmentName = department.name


def try_update_study_date(ds: Type[Dataset], update_date: bool, study_date: str) -> None:
  """
  Attempts to update the study date for the dataset

  Args:
    ds: dataset to update study date for
    update_date: whether or not to update the study date
    study_date: the new study date (YYYY-MM-DD), if empty will be gotten from the scheduled procedure step sequence
  """
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
      except AttributeError:
        # The ScheduledProcedureStepSequence was not present in the dataset, create it
        seq_data = Dataset()
        seq_data.add_new(0x00400002, 'DA', date_string) # ScheduledProcedureStepStartDate
        seq_data.add_new(0x00400003, 'TM', time_string) # ScheduledProcedureStepStartTime
        ds.add_new(0x00400100, 'SQ', Sequence([seq_data]))
    else:
      ds.StudyDate = ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate
      ds.StudyTime = ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartTime
      ds.SeriesDate = ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate
      ds.SeriesTime = ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartTime


def try_update_scheduled_procedure_step_sequence(ds: Type[Dataset]) -> None:
  """
  Attempts to update the scheduled procedure step sequence for the dataset

  Args:
    ds: dataset to update for
  """
  if 'ScheduledProcedureStepSequence' in ds:  
    Schedule = ds.ScheduledProcedureStepSequence[0]
    ds.StudyDescription = Schedule.ScheduledProcedureStepDescription
    ds.Modality = Schedule.Modality


def try_add_exam_status(ds: Type[Dataset], exam_status: int) -> None:
  """
  Attempts to add the exam status to the dataset

  Args:
    ds: dataset to add to
    exam_status: exam status to add if present
  """
  if exam_status:
    if 'ExamStatus' in ds:
      if ds.ExamStatus < exam_status:
        ds.ExamStatus = exam_status
    else:
      ds.ExamStatus = exam_status


def try_add_age(ds: Type[Dataset], age: int) -> None:
  """
  Attempts to add the age to the dataset

  Args:
    ds: dataset to add to
    age: age to add if present
  """
  if age:
    ds.PatientAge = f"{age:03d}"


def try_add_gender(ds: Type[Dataset], gender: str) -> None:
  """
  Attempts to add the gender to the dataset

  Args:
    ds: dataset to add to
    gender: gender to add if present
  """
  if gender:
    gender = gender.lower()
    if gender in ['male', 'm', 'mand', 'dreng']:
      ds.PatientSex = 'M'
    if gender in ['kvinde', 'd', 'k', 'pige', 'woman', 'dame', 'female' ]:
      ds.PatientSex = 'F'


def try_add_sample_sequence(ds: Type[Dataset], sample_seq) -> None:
  """
  Attempts to add the sample sequence to the dataset

  Args:
    ds: dataset to add to
    sample_seq: sample sequence to add if present
  """
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


def try_add_pixeldata(ds: Type[Dataset], pixeldata) -> None:
  """
  Attempts to add the pixeldata to the dataset

  Args:
    ds: dataset to add to
    pixeldata: pixeldata to add if present

  Remark:
    The dicom dataset should have TransferSyntax to Little Endian Explicit
    to avoid any corruption of the pixeldata.
    
    During development of previous versions we've found that when TransferSyntax
    is set to Little Endian Implicit, that the pixeldata gets distorted with a
    blue/greenish tint when uploaded to PACS.
  """
  if pixeldata:
    # Save in DICOM pixel data encoding format
    pixeldata = np.frombuffer(pixeldata, dtype=np.uint8) # Reads byte array to 1D numpy array
    pixeldata = np.reshape(pixeldata, (1080, 1920, 3))   # Reshapes to PIL displayable image - current format of byte string
    pixeldata = np.reshape(pixeldata, (1920, 1080, 3))   # Reshapes to DICOM conformat pixel data encoding (for more details see: https://dicom.innolitics.com/ciods/segmentation/image-pixel/7fe00010)

    # Set additional meta data about the image
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


def update_private_tags():
  # Update DicomDictionary to include our private tags
  DicomDictionary.update(new_dict_items)

  new_names_dirc = dict([(val[4], tag) for tag, val in new_dict_items.items()])
  keyword_dict.update(new_names_dirc)


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
    ris_nr              = None,
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
    ds: dataset to add values to

  Kwargs:
    age                 : int, Age of the patient
    birthday            : 
    bsa_method          : string, Method used to calculate Body Surface area
    clearance           : float, Clearance Value
    clearance_norm      : float, Clearance Value Normalized to 1.73m²
    cpr                 : string, CPR number
    department          :
    exam_status         : int, status of the exam, e.g. to be reviewed, ready to send to packs, etc.
    gender              :
    gfr                 : string, either 'Normal', 'Moderat Nedsat', 'Nedsat', 'Stærkt nedsat' 
    gfr_type            : string, Method used to calculate GFR
    height              : float, Height of patient wished to be stored
    injection_after     : float, Weight of Vial After Injection
    injection_before    : float, Weight of Vial Before injection
    injection_time      : string on format 'YYYYMMDDHHMM', Describing when a sample was injected
    injection_weight    : float, Weight of injection
    name                : string, Name on format Firstname<1 space>Middlenames sperated by 1 space<1 space>Lastname
    pixeldata           :
    ris_nr              : string, Accession number of dataset
    sample_seq          : list of lists where every list is on the format: 
      *List_elem_1      : string on format 'YYYYMMDDHHMM', describing sample taken time
      *List_elem_2      : float, cpm of sample
      *List_elem_3      : float, stdcnt of the sample
      *List_elem_4      : float, Thining Factor of Sample. In most sane cases these are the same throught the list
    series_instance_uid :
    series_number       :
    sop_instance_uid    :
    station_name        :
    study_date          : string, on format YYYYMMDDHHMM, describing study date
    std_cnt             :
    thiningfactor       :
    update_date         :
    update_dicom        :
    weight              : float, Weight of patient wished to be stored

  Remarks
    It's only possible to store the predefined args with this function
  """
  """
  TODO: Check if the updating of the DicomDictionary can be achieved through the
        new datadict.add_private_dict_entry or datadict.add_private_dict_entries
        from pydicom 1.3.0.

        For more details see:
          https://pydicom.github.io/pydicom/stable/release-notes.html
          or
          https://github.com/pydicom/pydicom/issues/799
  """
  update_private_tags()

  # Dictionary defining which arguments to run through __try_add_new
  try_adds_dict = {
    0x00080050 : ('SH', ris_nr),                                  # ds.AccessionNumber
    0x00100030 : ('DA', birthday.replace('-', '')),               # ds.PatientBirthDate
    0x00100020 : ('LO', cpr.replace('-', '')),                    # ds.PatientId
    0x00100010 : ('PM', formatting.name_to_person_name(name)),    # ds.PatientName
    0x00200011 : ('IS', series_number),                           # ds.SeriesNumber
    0x00081010 : ('SH', station_name),                            # ds.StationName
    0x00101020 : ('DS', height),                                  # ds.PatientSize
    0x00101030 : ('DS', weight),                                  # ds.PatientWeight
    0x0008103E : ('LO', 'Clearance ' + gfr_type),                 # ds.SeriesDescription
                                                                  # ### PRIVATE TAGS START ###
    0x00231001 : ('LO', gfr),                                     # ds.GFR
    0x00231002 : ('LO', 'Version 1.0'),                           # ds.GFRVersion
    0x00231010 : ('LO', gfr_type),                                # ds.GFRMethod
    0x00231018 : ('DT', injection_time),                          # ds.injTime
    0x0023101A : ('DS', injection_weight),                        # ds.injWeight
    0x0023101B : ('DS', injection_before),                        # ds.injbefore
    0x0023101C : ('DS', injection_after),                         # ds.injafter
    0x00231011 : ('LO', bsa_method),                              # ds.BSAmethod
    0x00231012 : ('DS', clearance),                               # ds.clearance
    0x00231014 : ('DS', clearance_norm),                          # ds.normClear
    0x00231024 : ('DS', std_cnt),                                 # ds.stdcnt
    0x00231028 : ('DS', thiningfactor)                            # ds.thiningfactor
  }
  
  for tag, value_tuple in try_adds_dict.items():
    VR, value = value_tuple
    try_add_new(ds, tag, VR, value)

  # Dictionary defining custom functions and corresponding arguments for more
  # complicated values to set on the dataset
  custom_try_adds = (
    (try_update_exam_meta_data, update_dicom),
    (try_update_exam_meta_data, update_dicom),
    (try_add_department, department),
    (try_update_study_date, update_date, study_date),
    (try_update_scheduled_procedure_step_sequence),
    (try_add_exam_status, exam_status),
    (try_add_age, age),
    (try_add_gender, gender),
    (try_add_pixeldata, pixeldata),
    # ### PRIVATE TAGS START ###
    (try_add_sample_sequence, sample_seq)
  )

  for item in custom_try_adds:
    try:
      try_func = item[0]
      args = item[1:]
    except TypeError: # i.e. no args supplied
      try_func = item

    try_func(ds, *args)
