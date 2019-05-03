import pynetdicom, pydicom, logging
from pynetdicom import AE, StoragePresentationContexts

logging.basicConfig(filename='testlogfile.log', level = logging.INFO)
logger = logging.getLogger()

def on_store(dataset, context, info):

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

server_ae = AE(ae_title='HEHKFARGHOTR05')

server_ae.supported_contexts = StoragePresentationContexts
server_ae.on_c_move = on_move
server_ae.on_c_store = on_store

server_instance = server_ae.start_server(('', 104))





