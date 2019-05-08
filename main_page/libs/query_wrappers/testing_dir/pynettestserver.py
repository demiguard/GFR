import pynetdicom, pydicom, logging
from pynetdicom import AE, StoragePresentationContexts, evt

logging.basicConfig(filename='testlogfile.log', level = logging.DEBUG)


def on_store(dataset, context, info):
  logger = logging.getLogger()

  logger.info('\n')  
  logger.info(dataset)
  logger.info('\n')
  logger.info(context)
  logger.info('\n')
  logger.info(info)
  logger.info('\n')
  
  return 0x0000

def on_move(dataset, move_aet, context, info):
  """



  """
  logger = logging.getLogger()

  logger.info('\n')
  logger.info(dataset)
  logger.info('\n')
  logger.info(move_aet)
  logger.info('\n')
  logger.info(context)
  logger.info('\n')
  logger.info(info)
  logger.info('\n')

  return 0xA801

def log_event(event):
  logger = logging.getLogger()

  logger.info('\n New Event Logged!\n')
  logger.info(event.name)
  logger.info(event.description)
  logger.info(event.assoc)


handlers = [
    (evt.EVT_ASYNC_OPS, log_event),
    (evt.EVT_SOP_COMMON, log_event),
    (evt.EVT_SOP_EXTENDED, log_event),
    (evt.EVT_USER_ID, log_event), 
    # No Response
    (evt.EVT_ABORTED, log_event),
    (evt.EVT_CONN_OPEN, log_event),
    (evt.EVT_REQUESTED, log_event), ]



server_ae = AE(ae_title='HVHFBERGHK7')

server_ae.supported_contexts = StoragePresentationContexts
server_ae.on_c_move = on_move
server_ae.on_c_store = on_store

logger = logging.getLogger()
logger.info('Starting Server!')
server_instance = server_ae.start_server(('', 104), evt_handlers=handlers)





