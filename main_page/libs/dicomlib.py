import pydicom, datetime, logging, csv
from pydicom.values import convert_SQ, convert_string
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.datadict import DicomDictionary, keyword_dict
from pydicom import uid

from pathlib import Path
import numpy as np

from typing import Type, Tuple, List, IO, Any

from main_page import models
from main_page.libs import enums
from .server_config import new_dict_items
from . import server_config
from . import formatting
from main_page import log_util

logger = log_util.get_logger(__name__)


def update_private_tags() -> None:
  # Update DicomDictionary to include our private tags
  DicomDictionary.update(new_dict_items)

  new_names_dirc = dict([(val[4], tag) for tag, val in new_dict_items.items()])
  keyword_dict.update(new_names_dirc)


def get_recovered_date(
  accession_number: str,
  hospital_shortname: str,
  active_studies_dir: str=server_config.FIND_RESPONS_DIR,
  recovered_filename: str=server_config.RECOVERED_FILENAME
  ) -> str:
  """
  Attempts to get the recovery date of a study

  Args:
    accession_number: accession number of study to get recovery date from

  Kwargs:
    active_studies_dir: directory containing currently active studies
    recovered_filename: filename of the recovery file

  Returns:
    string contaning the recovery date of the study, None otherwise
  """
  recover_filepath = Path(
    active_studies_dir,
    hospital_shortname,
    accession_number,
    recovered_filename
  )
  
  try:
    with open(recover_filepath, 'r') as fp:
      return fp.readline()
  except FileNotFoundError:
    return None


def get_study_date(dataset: Type[Dataset]) -> str:
  """
  Attempts to retreieve the study date of a dataset, by check first on StudyDate
  then on ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate

  Args:
    dataset: dataset to get study date from

  Returns:
    The study date if it found one, otherwise None
  """
  try:
    study_date_str = dataset.StudyDate

    if not study_date_str:
      raise ValueError()
  except (AttributeError, ValueError):
    try:
      study_date_str = dataset.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate

      if not study_date_str:
        return None
    except (AttributeError, IndexError):
      return None

  return study_date_str
    

def dcmread_wrapper(filepath: IO[Any], is_little_endian: bool=True, is_implicit_VR: bool=True) -> Type[Dataset]:
  """
  Takes a file path and reads it, update the private tags accordingly

  Args:
  filepath: filepath of file to read from
    is_little_endian: whether or not the obj should be in little endian form
    is_implicit_VR: whether or not the obj should is implicit VR

  Returns:
    The read dicom object with corrected private tags
  """
  if isinstance(filepath, Path):
    filepath = str(filepath) # Convert to string, so pydicom can work with it

  update_private_tags()

  obj = pydicom.dcmread(filepath)
  obj = update_tags(obj, is_little_endian, is_implicit_VR)

  return obj


def update_tags(obj, is_little_endian: bool=True, is_implicit_VR: bool=True):
  """
  Resolves unknown private tags

  Args:
    obj: dataset/dataelement to resolve
    
  Kwargs:
    is_little_endian: whether or not the obj should be in little endian form
    is_implicit_VR: whether or not the obj should is implicit VR

  Returns:
    dataset with resolved unknown tags

  Remarks:
    It should be noted that the function relies on recursion and can possibly
    hit the recurrsion limit of Python

    For more see: https://docs.python.org/3/library/sys.html#sys.getrecursionlimit
  """
  for ds in obj:
    if ds.tag not in new_dict_items and ds.VR != 'SQ':
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


def save_dicom(filepath: IO[Any], ds: Type[Dataset]) -> None:
  """
  Saves a dicom file to a given filepath

  Args:
  filepath: destionation to save dataset to
    ds: dataset to save

  Raises:
    ValueError: No AccessionNumber was available when trying to resolve meta data issues
    ValueError: if the filepath is empty
  """
  if isinstance(filepath, Path):
    filepath = str(filepath) # Convert to string, to allow pydicom to work with it

  ds.is_implicit_VR = True
  ds.is_little_endian = True

  if not filepath:
    raise ValueError("Unable to save dataset, filepath is empty.")

  if 'SOPClassUID' not in ds or 'SOPInstanceUID' not in ds:  # Dataset is incomplete
    if 'AccessionNumber' in ds:
      # Set missing meta data
      fill_dicom(ds, update_dicom=True)
    else:
      raise ValueError('Cannot create SOPInstanceUID without AccessionNumber!')
  
  ds.fix_meta_info()
  logger.info(f'Saving Dicom file at: {filepath}')
  ds.save_as(filepath, write_like_original=False)


def try_add_new(ds: Type[Dataset], tag: int, VR: str, value, check_val: bool=True) -> None:
  """
  Attempts to add a new value by tag, if the value is not None or empty

  Args:
    ds: dataset to add tag/value too
    tag: tag to add
    VR: Value Representation of the value to add
    value: the value to add for the given tag

  Kwargs:
    check_val: additional boolean to check before trying to add
  """
  if value and check_val:
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
    ds.add_new(0x00230010, 'LO', 'Clearance - Denmark - Region Hovedstaden')  # Our PrivateCreator tag (0x00230010)
    ds.add_new(0x00080090, 'PN', '')  # request.user.name or BAMID.name       # ds.ReferringPhysicianName
    ds.add_new(0x00200010, 'SH', 'GFR#' + ds.AccessionNumber[4:])             # ds.StudyID
    ds.add_new(0x00200013, 'IS', '1')                                         # ds.InstanceNumber
    
    ds.SoftwareVersions = f'{server_config.SERVER_NAME} - {server_config.SERVER_VERSION}'

    ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.7' # Secoundary Image Capture

    # Don't write SOPInstanceUID if already present, as it might be set for new studies created from prior historical ones
    SOPuid = uid.generate_uid(prefix='1.3.', entropy_srcs=[ds.AccessionNumber, 'SOP'])
    if "SOPInstanceUID" not in ds:
      ds.SOPInstanceUID = SOPuid
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


def try_update_study_date(ds: Type[Dataset], update_date: bool, study_datetime: str) -> None:
  """
  Attempts to update the study date for the dataset

  Args:
    ds: dataset to update study date for
    update_date: whether or not to update the study date
    study_datetime: the new study date YYYYMMDDHHMM, if empty will be gotten from the scheduled procedure step sequence
  """
  if update_date:
    if study_datetime:
      date_string = study_datetime[:8]
      time_string = study_datetime[8:]

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
      # TODO: The below will fail if update_date=True, study_date=None and ds has no ScheduledProcedureStepSequence...
      try:
        ds.StudyDate  = ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate
        ds.StudyTime  = ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartTime
        ds.SeriesDate = ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate
        ds.SeriesTime = ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartTime
      except:
        ds.StudyDate  = datetime.datetime.today().strftime('%Y%m%d')
        ds.StudyTime  = '0800'
        ds.SeriesDate  = datetime.datetime.today().strftime('%Y%m%d')
        ds.SeriesTime  = '0800'

def try_update_scheduled_procedure_step_sequence(ds: Type[Dataset]) -> None:
  """
  Attempts to update the scheduled procedure step sequence for the dataset

  Args:
    ds: dataset to update for

  Remark:
    This function assumes ScheduledProcedureStepDescription and Modality is in
    the ScheduledProcedureStepSequence
  """
  if 'ScheduledProcedureStepSequence' in ds:
    ds.StudyDescription = ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepDescription
    ds.Modality = ds.ScheduledProcedureStepSequence[0].Modality


def try_add_bamID(ds: Type[Dataset], bamID: str) -> None:
  """
  Adds Additional bamID to the operators

  """
  if bamID:
    curr_operators = ds.get("OperatorsName")

    if not curr_operators:
      ds.OperatorsName = bamID
    elif isinstance(curr_operators, pydicom.multival.MultiValue):
      if bamID not in curr_operators:
        curr_operators.append(bamID)
    elif isinstance(curr_operators, pydicom.valuerep.PersonName3):
      if str(ds.OperatorsName) != bamID:
        ds.OperatorsName = str(ds.OperatorsName) + f'\\{bamID}'

def try_add_exam_status(ds: Type[Dataset], exam_status: str) -> None:
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


def try_add_gender(ds: Type[Dataset], gender: enums.Gender) -> None:
  """
  Attempts to add the gender to the dataset

  Args:
    ds: dataset to add to
    gender: gender to add if present
  """
  if gender:
    # Save first character (either 'M' or 'F')
    ds.PatientSex = enums.GENDER_SHORT_NAMES[gender.value]


def try_add_sample_sequence(ds: Type[Dataset], sample_seq: List[Tuple[datetime.datetime, float]]) -> None:
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

def try_add_dicom_history(ds: Type[Dataset], dicom_history):
  if dicom_history:
    ds.clearancehistory = Sequence(dicom_history)


def try_add_pixeldata(ds: Type[Dataset], pixeldata: bytes) -> None:
  """
  Attempts to add the pixeldata to the dataset

  Args:
    ds: dataset to add to
    pixeldata: pixeldata to add if present

  Remark:
    This function assumes the pixeldata was generated through generate_gfr_plot
    function from clearance_math.py

    The dicom dataset should have TransferSyntax to Little Endian Explicit
    to avoid any corruption of the pixeldata.
    
    During development of previous versions we've found that when TransferSyntax
    is set to Little Endian Implicit, that the pixeldata gets distorted with a
    blue/greenish tint when uploaded to PACS.
  """
  if pixeldata:
    # Save in DICOM pixel data encoding format
    pixeldata = np.frombuffer(pixeldata, dtype=np.uint8) # Reads byte array to 1D numpy array
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


def fill_dicom(ds,
    age                 = None,
    birthday            = None,
    bamid               = None,
    bsa_method          = None,
    clearance           = None,
    clearance_norm      = None,
    cpr                 = None,
    department          = None,
    dicom_history       = None,
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
    study_datetime      = None,
    std_cnt             = None,
    thiningfactor       = None,
    update_date         = False,
    update_dicom        = False,
    update_version      = False,
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
    dicom_history       : list[class:pydicom:dataset], contains the history of the patient
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
    pixeldata           : image represented as byte-string
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
    study_datetime      : string, on format YYYYMMDD, describing study date
    std_cnt             : standard count for the study
    thiningfactor       : thinning factor of the day
    update_date         : whether or not to update the StudyDate
    update_dicom        : whether or not to update dicom meta data
    update_version      : whether or not to update the software version
    weight              : float, Weight of patient wished to be stored

  Remarks
    This function assumes input is correctly formatted for the corresponding
    VRs for each input argument, e.g. birthday must be in format YYYYMMDD
  """
  """
  TODO: Check if the updating of the DicomDictionary can be achieved through the
        new datadict.add_private_dict_entry or datadict.add_private_dict_entries
        from pydicom 1.3.0.

        For more details see:
          https://pydicom.github.io/pydicom/stable/release-notes.html
          or
          https://github.com/pydicom/pydicom/issues/799
  
  TODO: Move all formatting out of this function, it should be handled by higher level functions
  """
  update_private_tags()
  
  # Dictionary defining which arguments to run through __try_add_new
  try_adds_dict = {
    0x00080050 : ('SH', ris_nr),                                              # ds.AccessionNumber
    0x00100030 : ('DA', birthday),                                            # ds.PatientBirthDate
    0x00100020 : ('LO', cpr),                                                 # ds.PatientId
    0x00100010 : ('PN', formatting.name_to_person_name(name)),                # ds.PatientName
    0x00200011 : ('IS', series_number),                                       # ds.SeriesNumber
    0x00081010 : ('SH', station_name),                                        # ds.StationName
    0x00101020 : ('DS', height),                                              # ds.PatientSize
    0x00101030 : ('DS', weight),                                              # ds.PatientWeight
    0x0008103E : ('LO', 'Clearance ' + formatting.xstr(gfr_type), gfr_type),  # ds.SeriesDescription
                                                                              # ### PRIVATE TAGS START ###
    0x00231001 : ('LO', gfr),                                                 # ds.GFR
    0x00231002 : ('LO', server_config.SERVER_VERSION, update_version),        # ds.GFRVersion
    0x00231010 : ('LO', gfr_type),                                            # ds.GFRMethod
    0x00231018 : ('DT', injection_time),                                      # ds.injTime
    0x0023101A : ('DS', injection_weight),                                    # ds.injWeight
    0x0023101B : ('DS', injection_before),                                    # ds.injbefore
    0x0023101C : ('DS', injection_after),                                     # ds.injafter
    0x00231011 : ('LO', bsa_method),                                          # ds.BSAmethod
    0x00231012 : ('DS', clearance),                                           # ds.clearance
    0x00231014 : ('DS', clearance_norm),                                      # ds.normClear
    0x00231024 : ('DS', std_cnt),                                             # ds.stdcnt
    0x00231028 : ('DS', thiningfactor)                                        # ds.thiningfactor
  }
  
  for tag, args in try_adds_dict.items():
    VR, value = args[:2]
    
    # Get check_val if available
    check_val = True
    if len(args) == 3:
      check_val = args[2]
    
    try_add_new(ds, tag, VR, value, check_val=check_val)

  # Dictionary defining custom functions and corresponding arguments for more
  # complicated values to set on the dataset
  custom_try_adds = {
    try_update_exam_meta_data: [update_dicom],
    try_add_department: [department],
    try_update_study_date: [update_date, study_datetime],
    try_update_scheduled_procedure_step_sequence: [ ],
    try_add_exam_status: [exam_status],
    try_add_age: [age],
    try_add_gender: [gender],
    try_add_pixeldata: [pixeldata],
    # ### PRIVATE TAGS START ###
    try_add_sample_sequence: [sample_seq],
    try_add_dicom_history: [dicom_history],
    try_add_bamID: [bamid]
  }

  for try_func, args in custom_try_adds.items():
    # Args is 'unpacked' to allow for functions with none or multiple required arguments
    try_func(ds, *args)

def export_dicom(ds, file_path):
  """
    converts a dicom file to csv file and saves it at 'file_path'
    Note that this csv file doesn't contain any patient history

    args:
      ds: Pydicom dataset, data to be saved
      file_path: str, the file destination for the csv
    Throws:
      Attribute Error: if the ds do not have the following tags
        [0x00100010]
  """
  try:
    # Get initial header and data row
    column_dict = {
      'CPR':                       ds.PatientID,
      'Navn':                      formatting.person_name_to_name(str(ds.PatientName)),
      'Study Date':                ds.StudyDate,
      'Height':                    ds.PatientSize * 100,
      'Weight':                    ds.PatientWeight,
      'Body Surface Area Method':  ds.BSAmethod,
      'Standard count':            ds.stdcnt,
      'Thining Factor':            ds.thiningfactor,
      'Injection Weight':          ds.injWeight,
      'Injection Time':            ds.injTime,
      'Clearance':                 ds.clearance,
      'Clearance Normalized':      ds.normClear
    }

    header_row = list(column_dict.keys())
    data_row   = list(column_dict.values())
  except AttributeError as e: # Misssing attribute in dicom object
    logger.info(f'Error in writing to CSV: {e}')
    return 'Incomplete dicom 1'

  # Add samples to header and data row
  for i in range(1, 7):
    header_row.append(f"Sample Value {i}")
    header_row.append(f"Sample Time {i}")
  
  try:
    for sample_ds in ds.ClearTest:
      data_row.append(sample_ds[0x00231022].value)
      data_row.append(sample_ds.SampleTime)
  except AttributeError as e: # Missing attribute in dicom object
    logger.info(f'Error in writing to CSV: {e}')
    return 'Incomplete Dicom 2'
  
  # Write header and data row to the csv file
  with open(file_path, mode='w', newline='') as csv_file:
    csv_writer = csv.writer(
      csv_file,
      delimiter=',',
      quotechar='"'     
    )

    csv_writer.writerow(header_row)
    csv_writer.writerow(data_row)

  return 'OK'
