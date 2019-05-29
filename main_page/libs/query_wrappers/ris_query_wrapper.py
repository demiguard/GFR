import glob
import os
import datetime
import random
import shutil
import pydicom, pynetdicom
import logging


from ... import models

from .. import dirmanager
from .. import dataset_creator
from .. import dicomlib
from .. import server_config
from ..clearance_math import clearance_math
from .. import examination_info
from ..examination_info import ExaminationInfo
from .query_executer import execute_query

logger = logging.getLogger()

def parse_bookings(resp_dir):
  """
  Get dicom objects for all responses

  Args:
    resp_dir: path to directory containing dicom responses from findscu

  Returns:
    dict of dicom objects for all responses
  """
  ret = {}

  # Loop all responses
  for dcm_path in glob.glob('{0}/rsp*.dcm'.format(resp_dir)):
    ret[dcm_path] = dicomlib.dcmread_wrapper(dcm_path)

  return ret


def is_old_dcm_obj(obj_path):
  """
  Determines whether a dicom object is too old (i.e. it should be removed)

  Args:
    obj_path: path to the dicom obj to check

  Returns:
    True, the dicom object was to old and has been removed.
    False, the dicom object was NOT to old and still remains

  Remark:
    Only accepts valid dicom objects
  """
  obj = dicomlib.dcmread_wrapper(obj_path)
  
  exam = examination_info.deserialize(obj)

  # If more then 3 days old remove it
  procedure_date = datetime.datetime.strptime(exam.date, '%d/%m-%Y')

  now = datetime.datetime.now()
  time_diff = now - procedure_date
  days_diff = time_diff.days
  
  if days_diff >= server_config.DAYS_THRESHOLD:
    os.remove(obj_path)
    return True

  return False


def get_patients_from_rigs(user):
  """

  Args:
    user : Django User model who is making the call to rigs
  Returns:
    pydicom Dataset List : with all patients availble to the server  
    Error message : If an error happens it's described here, if no error happened, returns an empty string
  Raises:
    
  NOTE: This function is not thread safe
  
  """

  def complicated_and_statement(dataset, accession_numbers, accepted_procedures): 
    fst_truth_val = not dataset.AccessionNumber in accession_numbers
    snd_truth_val = (dataset.ScheduledProcedureStepSequence[0].ScheduledProcedureStepDescription in accepted_procedures) or (accepted_procedures == [''])
    thr_truth_val = not models.HandledExaminations.objects.filter(rigs_nr=dataset.AccessionNumber).exists()

    logger.info(f"\nDoes already exists on the server:{fst_truth_val}\nIs rejected from the handled procedures - {accepted_procedures}:{snd_truth_val}\nHave already been handled:{thr_truth_val}")

    return fst_truth_val and snd_truth_val and thr_truth_val

  returnlist = []
  accession_numbers = []
  ErrorMessage = ''
  #First Find all Dicom Objects

  dirmanager.check_combined_and_create(server_config.FIND_RESPONS_DIR , user.hospital)

  dcm_file_paths = glob.glob('{0}{1}/*.dcm'.format(
    server_config.FIND_RESPONS_DIR,
    user.hospital
  ))
  
  today = datetime.datetime.now()
  for dcm_file_path in dcm_file_paths:
    dataset = dicomlib.dcmread_wrapper(dcm_file_path)
    date_string = dataset.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate
    date_of_examination = datetime.datetime.strptime(date_string,'%Y%m%d')
    if (today - date_of_examination).days <= server_config.DAYS_THRESHOLD:
      returnlist.append(dataset)
      accession_numbers.append(dataset.AccessionNumber)
    else:
      #TODO: Move to recycle bin
      logger.info('Old file Detected Moving {0}.dcm to recycle bin'.format(
        dataset.AccessionNumber
      ))
      
  #Make a Querry up to Ris
  ae = pynetdicom.AE(ae_title=user.config.rigs_calling)
  
  FINDStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2.1'

  ae.add_requested_context(FINDStudyRootQueryRetrieveInformationModel)
  #If the object is not created, then Create an new object else add it to return list 
  assocation = ae.associate(
    user.config.rigs_ip,
    int(user.config.rigs_port), #Portnumbers should be shorts or ints! bad database 
    ae_title=user.config.rigs_aet
  )

  if assocation.is_established:
    logger.info('connected to Rigs with:\nIP:{0}\nPort:{1}\nMy ae Title:{2}\nCalling AE title:{3}'.format(
      user.config.rigs_ip,
      user.config.rigs_port,
      user.config.rigs_calling,
      user.config.rigs_aet))

    #Create query file
    query_ds = dataset_creator.get_rigs_base(rigs_calling=user.config.rigs_calling)
    accepted_procedures = user.config.accepted_procedures.split('^')
    logger.info(f'User:{user.username} is making a C-FIND')
    response = assocation.send_c_find(query_ds, query_model='S')

    for (status, dataset) in response:
      if status.Status == 0xFF00 :
        logger.info(f'Recieved Dataset:{dataset.AccessionNumber}')
        #0x0000 is code for no more files available
        #0xFF00 is code for dataset availble
        #Succes, I have a dataset
        if complicated_and_statement(dataset, accession_numbers, accepted_procedures):
          #Dataset is valid
          dicomlib.save_dicom(f'{server_config.FIND_RESPONS_DIR}{user.hospital}/{dataset.AccessionNumber}.dcm',
            dataset
          )
          returnlist.append(dataset)
          accession_numbers.append(dataset.AccessionNumber)
        else:
          pass #Discard the value
      elif status.Status == 0x0000:
        #Query Complete with no Errors
        pass
      else:
        logger.warn('Status code:{0}'.format(hex(status.Status)))
    #Clean up after we are done
    assocation.release()
  else:
    #Error Messages to 
    logger.warn(f'Could not connect to Rigs with:\nIP:{user.config.rigs_ip}\nPort:{user.config.rigs_port}\nMy ae Title:{user.config.rigs_calling}\nCalling AE title:{user.config.rigs_aet}')
    ErrorMessage += 'Kunne ikke forbinde til Rigs, der mangler måske nye undersøgelser'

  return returnlist, ErrorMessage

def get_all(user):
  """
  RETRIED FUNCTION use get_patients_from_rigs instead!

  Get registed examinations from a specific hospital, using a user

  Args:
    user: the currently logged in user object

  Returns:
    Ordered list, based on names, of ExaminationInfo instances containing infomation 
    about examinations registed at the specified hospital.
  """
  # Create query file
  base_query_file = server_config.BASE_RIGS_QUERY

  query_file = '{0}_{1}.dcm'.format(
    base_query_file.split('.')[0],
    random.getrandbits(128)
  )

  shutil.copy(base_query_file, query_file)

  qf_obj = pydicom.dcmread(query_file)
  qf_obj.ScheduledProcedureStepSequence[0].ScheduledStationAETitle = user.config.rigs_calling
  qf_obj.save_as(query_file)

  base_resp_dir = server_config.FIND_RESPONS_DIR
  resp_dir = '{0}{1}/'.format(base_resp_dir, user.hospital)

  if not os.path.exists(base_resp_dir):
    os.mkdir(base_resp_dir)

  if not os.path.exists(resp_dir):
    os.mkdir(resp_dir)

  # Construct query and execute
  query_arr = [
    server_config.FINDSCU,
    '-aet', # Set calling AET
    user.config.rigs_calling,
    '-aec', # Set AET to call
    user.config.rigs_aet,
    user.config.rigs_ip,
    user.config.rigs_port,
    query_file,
    '-X',  # Extract responses
    '-od', # Output dir to extract into
    resp_dir
  ]

  exe_out = execute_query(query_arr)

  if exe_out != '':
    pass # TODO: Error handling for failed findscu execution

  # Remove the query file after execution
  os.remove(query_file)

  dcm_objs = parse_bookings(resp_dir)
  ret = []

  # Add previous examinations to return list
  for obj_path in glob.glob('{0}REGH*.dcm'.format(resp_dir)):
    if not is_old_dcm_obj(obj_path):
      obj = dicomlib.dcmread_wrapper(obj_path)
      ret.append(examination_info.deserialize(obj))

  # Add new examinations to return list
  accepted_procedures = user.config.accepted_procedures.split('^')

  for obj_path, obj in dcm_objs.items():
    if obj.RequestedProcedureDescription in accepted_procedures:
      # Save to file if not already retreived
      if not os.path.exists('{0}{1}.dcm'.format(resp_dir, obj.AccessionNumber)):
        exam = examination_info.deserialize(obj)
        obj.save_as('{0}{1}.dcm'.format(resp_dir, obj.AccessionNumber))
        ret.append(exam)

    # Remove the response file
    os.remove(obj_path)
  
  # Filter out examinations previously sent to PACS
  def sent_to_pacs(ex):
    return not models.HandledExaminations.objects.filter(rigs_nr=ex.rigs_nr).exists()
  
  ret = list(filter(sent_to_pacs, ret))
  
  return list(sorted(ret, key=lambda x: x.name))
