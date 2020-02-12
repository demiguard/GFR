import pynetdicom, pydicom, time, logging, datetime
from pynetdicom import StoragePresentationContexts, AE, evt
from pydicom import Dataset

"""
Creates a local SCP server, conects to it and stores it

"""


logging.basicConfig(filename='logfile.log', level=logging.INFO)
from main_page import log_util

logger = log_util.get_logger(__name__)




#Event handlers
def handle_store(dataset, context, info):
  #Does nothing So far
  logger.info(dataset)
  logger.info(context)
  logger.info(info)



  return 0x0000


dcm_file_src = 'REGH13985169.dcm'
dcm_file_dst = 'DEST13985169.dcm'
#init Variables 
test_ip = '127.0.0.1'
test_port = 11112
ae_title_1 = 'title1'
ae_title_2 = 'title2'
ae_title_3 = 'title3'
#init Data string
sop_class = '1.2.840.10008.5.1.4.1.1.7'
ds = pydicom.dcmread(dcm_file_src)

#Create Server
server_ae = AE(ae_title= ae_title_1)
server_ae.on_c_store = handle_store
server_ae.supported_contexts = StoragePresentationContexts

server_instance = server_ae.start_server((test_ip, test_port), block=False)

time.sleep(1)

#Create user
usr_ae = AE(ae_title=ae_title_2)

usr_ae.add_requested_context(sop_class)

assoc = usr_ae.associate(test_ip, test_port)

if assoc.is_established:
  print("assoc established")
  response = assoc.send_c_store(ds)
  logger.info(response)
  assoc.release()
else:
  print("assoc not established")

time.sleep(1)

server_instance.shutdown()