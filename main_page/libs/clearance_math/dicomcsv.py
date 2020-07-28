import csv
import datetime
import os
import pynetdicom

from main_page import models

from main_page.libs import dicomlib
from main_page.libs import dataset_creator
from main_page.libs import server_config
from main_page.libs import log_util

logger = log_util.get_logger(__name__)

def get_history_for_csv(
  user,
  date_bounds                 = (datetime.date(2019,7,1), datetime.date(2100,1,1)),
  clearance_bounds            = (0.,200.),
  clearance_normalized_bounds = (0.,200.),
  thin_fact_bounds            = (0.,25000.),
  standard_bounds             = (0.,100000.),
  injection_weight_bounds     = (0.,2.),
  height_bounds               = (0., 250.),
  weight_bounds               = (0., 250.),
  age_bounds                  = (0., 125),
  cpr_bounds                  = '',
  method_bounds               = [],
  gender_bounds               = ['M','F','O']
  ):
  """
  Retrives all studies and processes them to match up with the following filters

  KWargs:
    date_bounds                 : tuple of date datetime objects, if none, then no filtering will be done on the object
    clearance_bounds            : tuple of floats, removes all studies where tag 0x00231012 not in range of the tuple. First argument is smaller than the secound argument
    clearance_normalized_bounds : tuple of floats, removes all studies where tag 0x00231014 not in range of the tuple. First argument is smaller than the secound argument
    thin_fact_bounds            : tuple of floats, removes all studies where tag 0x00231028 not in range of the tuple. First argument is smaller than the secound argument
    standard_bounds             : tuple of floats, removes all studies where tag 0x00231024 not in range of the tuple. First argument is smaller than the secound argument
    injection_weight_bounds     : tuple of floats, removes all studies where tag 0x0023101A not in range of the tuple. First argument is smaller than the secound argument
    height_bounds               : tuple of floats, removes all studies where tag 0x0023101A not in range of the tuple. First argument is smaller than the secound argument
    weight_bounds               : tuple of floats, removes all studies where tag 0x0023101A not in range of the tuple. First argument is smaller than the secound argument
    age_bounds                  : tuple of floats, removes all studies where tag 0x0023101A not in range of the tuple. First argument is smaller than the secound argument
    cpr_bounds                  : string, filters only a after a specific person, if empty removes test patients
    method_bounds               : string list, removes all studies where tag 0x0008103E is 
    gender_bounds               : char list, removes all studies, where the gender is not on the list. Valid Characters are M and F

  Raises: 
    ValueError : Whenever a keyword tuple first argument is greater than the secound argument 
  """
  #Helper Functions 
  #Check bounds
  def check_bounds(a_tuple):
    if a_tuple[0] > a_tuple[1]:
      raise ValueError('Invalid bounds, secound argument of each tuple must be greater than the first.')

  def in_bounds(a_tuple, a_value):
    return a_tuple[0] <= a_value and a_value <= a_tuple[1]  

  def check_study(study): 
    #
    birthdate = datetime.datetime.strptime(study.PatientBirthDate, '%Y%m%d')
    age_in_years = int((datetime.datetime.now() - birthdate).days / 365)
    study_date = datetime.datetime.strptime(study.StudyDate,'%Y%m%d').date()

    bounds = (
      (date_bounds, study_date),
      (clearance_bounds, study.clearance),
      (clearance_normalized_bounds, study.normClear),
      (thin_fact_bounds, study.thiningfactor),
      (standard_bounds, study.stdcnt),
      (injection_weight_bounds, study.injWeight),
      (height_bounds, study.PatientSize * 100.0),
      (weight_bounds, study.PatientWeight),
      (age_bounds, age_in_years),
    )
    
    # bounds checking
    valid_study = True
    for bound, val in bounds:
      valid_study &= in_bounds(bound, val)

    # Additional bounds checking
    valid_study &= cpr_bounds.replace('-','') == study.PatientID
    valid_study &= study.PatientSex in gender_bounds
    if not method_bounds:
      valid_study &= study.StudyDescription in method_bounds

    return valid_study

  def format_dicom(dicom_object, taglist):
    def helper(ds, tag):
      if tag in ds:
        return str(ds[tag].value)
      else :
        return ''
      
    returnlist = []

    for tag in taglist:
      returnlist.append(helper(dicom_object, tag))
    
    return returnlist

  # End Helper Functions

  AE_title = models.ServerConfiguration.objects.get(id=1).AE_title

  bounds = (
    date_bounds,
    clearance_bounds,
    thin_fact_bounds,
    standard_bounds,
    injection_weight_bounds,
    height_bounds,
    weight_bounds,
    age_bounds,
  )
  
  for bound in bounds:
    check_bounds(bound)

  if None != formatting.check_cpr(cpr_bounds):
    raise ValueError('Invalid CPR number')

  if not(gender_bounds in [['M'], ['F'], ['O'], ['M','F'], ['M','O'], ['F','O'] ,['M','F','O'] ]):
    raise ValueError('Invalid gender')
  # End checking bounds

  find_ae = pynetdicom.AE(ae_title=AE_title)
  move_ae = pynetdicom.AE(ae_title=AE_title)

  # Add different presentation contexts for the AE's
  FINDStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.1'
  MOVEStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2'

  find_ae.add_requested_context(FINDStudyRootQueryRetrieveInformationModel)
  move_ae.add_requested_context(MOVEStudyRootQueryRetrieveInformationModel)

  # Note that due to some unknown bugs, pacs is not happy make the same association handling both move and finds at the same time, thus we make two associations
  if not user.department.config.pacs:
    raise ValueError("No PACS address in configuration")
  
  find_assoc = find_ae.associate(
    user.department.config.pacs.ip,
    int(user.department.config.pacs.port),
    ae_title=AE_title
  )

  move_assoc = move_ae.associate(
    user.department.config.pacs.ip,
    int(user.department.config.pacs.port),
    ae_title=AE_title
  )

  studies = []

  if find_assoc.is_established and move_assoc.is_established:
    find_query_dataset = dataset_creator.create_search_dataset(
      date_from = date_bounds[0].strftime("%Y%m%d"),
      date_to   = date_bounds[1].strftime("%Y%m%d")
    )

    #This retrives all studies from pacs
    find_response = find_assoc.send_c_find(
      find_query_dataset,
      query_model=StudyRootQueryRetrieveInformationModelFind
    )

    for find_status, find_response_dataset in find_response:
      successfull_move = False
      move_response = move_assoc.send_c_move(find_response_dataset, ae_title, query_model=StudyRootQueryRetrieveInformationModelMove)
      for (status, identifier) in move_response:
        if status.Status == 0x0000:
          # Status code for C-move is successful
          logger.info('C-move successful')
          successfull_move = True
        elif status.Status == 0xFF00:
          #We are not done, but shit have not broken down
          pass
        else:
          logger.warn('C-Move move opration failed with Status code:{0}'.format(hex(status.Status)))
      #C-move done for the one response
      file_location = f'{server_config.SEARCH_DIR}/{find_dataset.AccessionNumber}.dcm'
      if successfull_move and os.path.exists(file_location) :
        study = dicomlib.dcmread_wrapper(f'{server_config.SEARCH_DIR}/{find_response_dataset.AccessionNumber}')
        os.remove(file_location)
        try:
          #Here is where the indiviual study handling happens
          if check_study(study):
            studies.append(studies)
          else:
            pass #Study Was not part search critie
        except: #TODO error handling
          logger.error(f'Error in handling:\n {study}')
      else:
        logger.info(f'Could not successfully move {find_response_dataset.AccessionNumber}')

    # Finallize Association
    find_assoc.release()
    move_assoc.release()
  else:
    logger.error('Could not connect to pacs')
    #While unlikely a bug could be there
    if find_assoc.is_established:
      find_assoc.release()
    if move_assoc.is_established:
      move_assoc.release()

  # TODO: Make the below code use the export_dicom function from dicomlib
  #Handling of studies
  #Studies at this point contains all valid studies given by the function input
  #This part is the csv

  today = datetime.datetime.today()
  filename = f'gfr_data_{today.strftime("%Y%m%d")}.csv'
  with open(filename, mode='w', newline = '') as csv_file:
    
    csv_writer = csv.writer(
      csv_file,
      delimiter=',',
      quotechar=''
    )
    
    header_tags = [
      ("Navn",                    0x00100010),
      ("CPR",                     0x00100020),
      ("Alder",                   0x00100010),
      ("Højde",                   0x00101020),
      ("Vægt",                    0x00101030),
      ("Køn",                     0x00100040),
      ("Dato",                    0x00080020),
      ("Krops overfalde metode",  0x00231011),
      ("Clearance",               0x00231012),
      ("Clearance Normalized",    0x00231014),
      ("Injektions Tidspunkt",    0x00231018),
      ("Injektions vægt",         0x0023101A),
      ("Sprøjte Vægt før",        0x0023101B),
      ("Sprøjte Vægt Efter",      0x0023101C),
      ("Standard",                0x00231024),
      ("Thining Factor",          0x00231028),
    ]
    sequnce_header = [
      "Prøve 1 Værdi",  "Prøve 1 tidpunkt",
      "Prøve 2 Værdi",  "Prøve 2 tidpunkt",
      "Prøve 3 Værdi",  "Prøve 3 tidpunkt",
      "Prøve 4 Værdi",  "Prøve 4 tidpunkt",
      "Prøve 5 Værdi",  "Prøve 5 tidpunkt",
      "Prøve 6 Værdi",  "Prøve 6 tidpunkt"
    ]

    sequence_tags = [0x00231021, 0x00231022]

    textrow = [header_tag[0] for header_tag in header_tags] + sequnce_header 
    csv_writer.writerow(textrow)

    taglist = [atuple[1] for atuple in header_tags]
    for study in studies:
      
      datarow = format_dicom(study, taglist)
      seq_strs = []
      if 0x00231020 in study:
        for seq_item in study[0x00231020]:
          strs = format_dicom(seq_item, sequence_tags)
          
          seq_strs += strs

      datarow += seq_strs

      csv_writer.writerow(datarow)          

