import pynetdicom
from pydicom import Dataset

import logging
from typing import Type, Union, Callable
from pynetdicom import AE
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind, StudyRootQueryRetrieveInformationModelMove, ModalityWorklistInformationFind 
from main_page.libs.status_codes import DATASET_AVAILABLE, TRANSFER_COMPLETE
from main_page.libs.dirmanager import try_mkdir


ae_logger = logging.getLogger('GFRLogger')



MOVEStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2.2'


#Dev notes: Sooo a pretty major flaw with using this is that send_xxx doesn't return anything

def establish_assoc(AE : AE, ip: str, port: Union[int, str], aet: str, logger: logging.Logger):
  """
    From an AE establish an connection.

    This is mostly a log wrapper for AE.associate and error handling for it

  """
  if isinstance(port, str):
    port = int(port)
  try:
    assoc = AE.associate(
      ip,
      port,
      ae_title=aet
    )
  except TypeError:
    logger.error(f"""
      Could not establish connection to
      IP:     {ip}
      Port:   {port}
      my aet: {AE.ae_title}
      Ris ae: {aet}
      """)
    return None
  except RuntimeError:
    logger.error(f"The context for {AE.ae_title} is {AE.requested_contexts} is invalid")
    return None

  if not(assoc.is_established):
    logger.error(f"""
      Could not establish connection to
      IP:     {ip}
      Port:   {port}
      my aet: {AE.ae_title}
      Ris ae: {aet}
      """)
    return None

  return assoc



def connect(ip: str, port: Union[int, str], calling_aet: str, aet: str, context: str, *args, **kwargs):
  """
  Establish a connection to an AET

  Args:
    ip: IPv4 address of AET to connect to
    port: port to connect over
    calling_aet: your AET
    aet: AET to connect to
    context: context of the connection

  Returns:
    The establish association, None if unable to connect

  Remark:
    This function doesn't handle releasing of the associations, this must be
    done by the caller.
    This have been made obsolitte and is no longer used, I vote to remove this function
  """
  if 'logger' in kwargs:
    logger: logging.Logger = kwargs['logger']
  else:
    logger = ae_logger


  # Handle both integer and string ports
  if isinstance(port, str):
    port = int(port)

  try:
    ae = AE(ae_title=calling_aet)
  except ValueError:
    # If AET is empty then a ValueError is thrown by pynetdicom
    logger.info(f"Failed to create AE with calling aet: '{calling_aet}'")
    return None

  ae.add_requested_context(context)

  try:
    association = ae.associate(ip, port, ae_title=aet)
  except TypeError:
    # Invalid IPv4 address, port and/or AET
    logger.info(
      f"""Failed to associate with parameters:
          IP: '{ip}'
          port: '{port}'
          calling AET: '{calling_aet}'
          AET: '{aet}'""")
    return None
  except RuntimeError:
    logger.info(f"Got no or invalid context: '{context}'")
    return None

  if not association.is_established:
    logger.info(
      f"""Failed to establish connection with parameters:
          IP: '{ip}'
          port: '{port}'
          calling AET: '{calling_aet}'
          AET: '{aet}'""")
    return None

  logger.info(
    f"""Successfully established connection with parameters:
        IP: '{ip}'
        port: '{port}'
        calling AET: '{calling_aet}'
        AET: '{aet}'""")
  return association


def create_find_AE_worklist(ae_title: str) -> AE:
  """
    Creates an pynetdicom.AE object with the find Context, ready to send a find
  """
  ae = AE(ae_title=ae_title)
  ae.add_requested_context(ModalityWorklistInformationFind)

  return ae

def create_find_AE_study(ae_title: str) -> AE:
  ae = AE(ae_title=ae_title)
  ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)

  return ae



def create_move_AE(ae_title: str) -> AE:
  """
    Creates an pynetdicom.AE object with the find Context, ready to send a move
  """
  ae = AE(ae_title=ae_title)
  ae.add_requested_context(StudyRootQueryRetrieveInformationModelMove)

  return ae


def __handle_find_resp(resp, process: Callable, *args, **kwargs):
  """
  Passes each successful response on to the user defined process function

  Args:
    resp: response generator from e.g. C_FIND, C_MOVE, etc.
    process: function for processing successful response identifiers (datasets)

  Remarks:
    TRANSFER_COMPLETE is the last thing received from a C-FIND,
    since it's empty we can just ignore it and
    release the association if no futher queries are to be made.
  """
  if 'logger' in kwargs:
    logger = kwargs['logger']
  else:
    logger = ae_logger

  for status, identifier in resp:
    if 'Status' in status:
      if status.Status == DATASET_AVAILABLE:
        process(identifier, *args, **kwargs)
      elif status.Status == TRANSFER_COMPLETE:
        pass
      else:
        logger.info(f"Failed to transfer dataset, with status: {status.Status}")
    else:
      logger.error(f'Dataset does not have status attribute\n Status:\n{status}')


def __handle_move_resp(resp, process, *args, **kwargs):
  """
  Passes each successful response on to the user defined process function

  Args:
    resp: response generator from e.g. C_FIND, C_MOVE, etc.
    process: function for processing successful response identifiers (datasets)

  Remarks:
    C-move, regullary sends small updates about what is going on
    this is processed under DATASET_AVAILABLE. Thus we just ignore them.

    Once a TRANSFER_COMPLETE is received the file has been moved successfully
  """
  if 'logger' in kwargs:
    logger = kwargs['logger']
  else:
    logger = ae_logger

  for status, identifier in resp:
    if 'Status' in status:
      if status.Status == DATASET_AVAILABLE:
        pass
      elif status.Status == TRANSFER_COMPLETE:
        process(identifier, *args, **kwargs)
      else:
        logger.info(f"Failed to transfer dataset, with status: {hex(status.Status)}")
    else:
      logger.error(f'Dataset does not have status attribute\n Status:\n{status}')


def send_find(association, query_ds, process, query_model=StudyRootQueryRetrieveInformationModelFind, *args, **kwargs) -> None:
  """
  Sends a C_FIND query request to an association using the supplied dataset

  Args:
    association: an established association
    query_ds: pydicom dataset containing the query parameters
    process: function for processing incoming response identifiers (datasets).
             *args and **kwargs will be passed on to this function

  Kwargs:
    query_model: which query model to use (see DICOM standard for specifics)
                 (Default='S' for Study level)

  Raises:
    RuntimeError: if the association is not an established association
    ValueError: if the query dataset fails to encode in the underlying
                query request
  """
  # Handle None as association
  if not association:
    raise ValueError("'association' cannot be NoneType object when making a send_find call")

  # Retrieve logger if given
  if 'logger' in kwargs:
    logger = kwargs['logger']
  else:
    logger = ae_logger

  # Perform query
  logger.info(f"Sending C_FIND query to {association.acceptor.ae_title}")
  resp = association.send_c_find(query_ds, query_model=query_model)
  __handle_find_resp(resp, process, *args, **kwargs)


def send_move(association, to_aet, query_ds, process: Callable, query_model=StudyRootQueryRetrieveInformationModelMove, *args, **kwargs) -> None:
  """
  Sends a C_FIND query request to an association using the supplied dataset

  Args:
    association: an established association
    to_aet: AET of where to send responses
    query_ds: pydicom dataset containing the query parameters
    process: function for processing incoming response identifiers (datasets).
             *args and **kwargs will be passed on to this function

  Kwargs:
    query_model: which query model to use (see DICOM standard for specifics)
                 (Default='S' for Study level)

  Raises:
    RuntimeError: if the association is not an established association
    ValueError: if the query dataset fails to encode in the underlying
                query request
  """
  # Handle None as association
  if not association:
    raise ValueError("'association' cannot be NoneType object when making a send_move call")

  # Retrieve logger if given
  if 'logger' in kwargs:
    logger = kwargs['logger']
  else:
    logger = ae_logger

  # Perform query
  logger.info(f"Sending C_MOVE query to {association.acceptor.ae_title}")
  resp = association.send_c_move(query_ds, to_aet, query_model=query_model)
  __handle_move_resp(resp, process, *args, **kwargs)
