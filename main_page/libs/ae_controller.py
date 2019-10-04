import pynetdicom
from pydicom import Dataset
from typing import Type

import logging

logger = logging.getLogger()


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


SUCCESS = 0x0000
CONTINUING = 0xFF00

def __handle_resp(resp, process):
  """
  Passes each successful response on to the user defined process function

  Args:
    resp: response generator from e.g. C_FIND, C_MOVE, etc.
    process: function for processing successful response identifiers (datasets)

  Returns:
    True if any single response was successful, False otherwise
  """
  any_succeeded = False

  for status, identifier in resp:
    if status.Status == SUCCESS:
      any_succeeded = True
      process(identifier)
    elif status.Status == CONTINUING:
      continue
    else:
      logger.warn(
        f"""Operation failed for 
            status code: {status.Status}
            identifier: {identifier}
        """)

  return any_succeeded


def send_find(association, query_model, query_ds, process) -> None:
  """
  Sends a C_FIND query request to an association using the supplied dataset

  Args:
    association: an established association
    query_model: which level to query one (e.g. 'S' for study level)
    query_ds: pydicom dataset containing the query parameters
    process: function for processing incoming response identifiers (datasets)

  Raises:
    RuntimeError: if the association is not an established association
    ValueError: if the query dataset fails to encode in the underlying
                query request

  Returns:
    True if any single response was successful, False otherwise
  """
  logger.info("Sending C_FIND query")
  resp = association.send_c_find(query_ds, query_model=query_model)
  return __handle_resp(resp, process)


def send_move(association, to_aet, query_model, query_ds, process: lambda x: None) -> None:
  """
  Sends a C_FIND query request to an association using the supplied dataset

  Args:
    association: an established association
    to_aet: AET of where to send responses
    query_ds: pydicom dataset containing the query parameters
    process: function for processing incoming response identifiers

  Raises:
    RuntimeError: if the association is not an established association
    ValueError: if the query dataset fails to encode in the underlying
                query request
  
  Returns:
    True if any single response was successful, False otherwise
  """
  logger.info("Sending C_MOVE query")
  resp = association.send_c_move(query_ds, to_aet, query_model=query_model)
  return __handle_resp(resp, process)
