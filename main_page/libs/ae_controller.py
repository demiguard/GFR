import pynetdicom
from pydicom import Dataset

import os
import logging
from typing import Type

from main_page.libs.status_codes import DATASET_AVAILABLE, TRANSFER_COMPLETE
from main_page.libs.dirmanager import try_mkdir
from main_page.libs import dicomlib
from main_page.libs import server_config
from main_page.libs import dataset_creator
from main_page import models

logger = logging.getLogger()


FINDStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2.1'
MOVEStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2.2'


def connect(ip: str, port: int, calling_aet: str, aet: str, context: str):
  """
  Establish a connection to an AET

  Args:
    ip: IPv4 address of AET to connect to
    port: port to connect over
    calling_aet: your AET
    aet: AET to connect to
    context: context of the connection 
            (e.g. FINDStudyRootQueryRetrieveInformationModel, 
            MOVEStudyRootQueryRetrieveInformationModel)

  Returns:
    The establish association, None if unable to connect

  Remark:
    This function doesn't handle releasing of the associations, this must be
    done by the caller.
  """
  try:
    ae = pynetdicom.AE(ae_title=calling_aet)
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
          AET: '{aet}'
      """)
    return None
  except RuntimeError:
    logger.info(f"Got no or invalid context: '{context}'")

  if not association.is_established:
    logger.info(
      f"""Failed to establish connection with parameters:
          IP: '{ip}'
          port: '{port}'
          calling AET: '{calling_aet}'
          AET: '{aet}'
      """)
    return None

  logger.info(
    f"""Successfully established connection with parameters:
        IP: '{ip}'
        port: '{port}'
        calling AET: '{calling_aet}'
        AET: '{aet}'
    """)
  return association


def __handle_find_resp(resp, process, *args, **kwargs):
  """
  Passes each successful response on to the user defined process function

  Args:
    resp: response generator from e.g. C_FIND, C_MOVE, etc.
    process: function for processing successful response identifiers (datasets)
  """
  for status, identifier in resp:
    if status.Status == DATASET_AVAILABLE:
      process(identifier, *args, **kwargs)
    elif status.Status == TRANSFER_COMPLETE:
      pass # Ignore, then release association
    else:
      logger.info(f"Failed to transfer dataset, with status: {status.Status}")


def __handle_move_resp(resp, process, *args, **kwargs):
  """
  Passes each successful response on to the user defined process function

  Args:
    resp: response generator from e.g. C_FIND, C_MOVE, etc.
    process: function for processing successful response identifiers (datasets)
  """
  for status, identifier in resp:
    if status.Status == DATASET_AVAILABLE: #YEAH SO THIS IS CODE FOR FIND NOT MOVE
      pass # C-move, regullary sends small updates about what is going on, these are not really useful
    elif status.Status == TRANSFER_COMPLETE:
      process(identifier, *args, **kwargs) #The file have been moved successfully
    else:
      logger.info(f"Failed to transfer dataset, with status: {status.Status}")



def send_find(association, query_ds, process, query_model='S', *args, **kwargs) -> None:
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
  logger.info("Sending C_FIND query")
  resp = association.send_c_find(query_ds, query_model=query_model)
  __handle_find_resp(resp, process, *args, **kwargs)


def send_move(association, to_aet, query_ds, process: lambda x, y: None, query_model='S', *args, **kwargs) -> None:
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
  logger.info("Sending C_MOVE query")
  resp = association.send_c_move(query_ds, to_aet, query_model=query_model)
  __handle_move_resp(resp, process, *args, **kwargs)
