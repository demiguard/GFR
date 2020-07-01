import pynetdicom, logging
import pydicom
from pydicom import uid, tag
datasets = []

rigs_calling = 'HVHFBERGHK7'
rigs_aet     = 'VIPDICOM'
rigs_ip      = '10.143.128.234'
rigs_port    = 104

ae = pynetdicom.AE(ae_title=rigs_calling)



logging.basicConfig(filename='Seriesfind.log', level=logging.DEBUG)
from main_page import log_util

logger = log_util.get_logger(__name__)
logger.debug('initlogger')

AccessionNumber = 'REGH14154196'
UID = uid.generate_uid(prefix='1.3.', entropy_srcs=[ AccessionNumber , 'Series'])

#'1.2.276.0.7230010.3.1.0.1'
ds = pydicom.Dataset()
#Fill it with tags
ds.add_new(0x00080020, 'DA', '') #Study date
ds.add_new(0x00080050, 'SH', '') #Accession Number
ds.add_new(0x00080052, 'CS', 'SERIES') #Root SOP Class level
ds.add_new(0x00080060, 'CS', 'OT') #Modality
ds.add_new(0x00080061, 'CS', 'OT') #Modality
ds.add_new(0x00100010, 'PN', '') #Patitent name
ds.add_new(0x00100020, 'LO', '') #PatientID / CPR NUMBER
ds.add_new(0x0020000D, 'UI', '') # Study Number 
ds.add_new(0x0020000E, 'UI', UID) # Series Number
#Create Sequences
#Sequenceset = pydicom.Dataset() # ScheduledProcedureStepSequence
#Add Sequence Tags
#Sequenceset.add_new(0x00080060, 'CS', '')
#Sequenceset.add_new(0x00400001, 'AE', rigs_calling)
#Sequenceset.add_new(0x00400002, 'DA', '')
#Done adding Sequence Tags
#ds.add_new(0x00400100, 'SQ', pydicom.Sequence([Sequenceset]))

ae.add_requested_context('1.2.840.10008.5.1.4.1.2.2.1')
ae.add_requested_context('1.2.840.10008.5.1.4.1.1.7')


assoc = ae.associate(rigs_ip,rigs_port, ae_title=rigs_aet)

if assoc.is_established:
  #NOTE: Response is a generator, not a interator
  response = assoc.send_c_find(ds, query_model='S')
  
  for (status, dataset_from_pacs) in response:
    #Show Status
    print(status)
    print('')
    #Save dataset
    print(dataset_from_pacs)
    print('')

  assoc.release()
else:
  print(assoc.is_established)
