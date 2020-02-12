import pynetdicom
import pydicom
import logging
from pydicom import uid

logging.basicConfig(level =logging.DEBUG, filename = 'pacsfindlogfile.log')
from main_page import log_util

logger = log_util.get_logger(__name__)

datasets = []

rigs_calling = 'RHKFANMGFR2'
rigs_aet     = 'VIPDICOM' #PACS
rigs_ip      = '10.143.128.234'
rigs_port    = 104

ae = pynetdicom.AE(ae_title=rigs_calling)

#'1.2.276.0.7230010.3.1.0.1'
ds = pydicom.Dataset()
#Fill it with tags
ds.add_new(0x00080016,'UI','')
ds.add_new(0x00080018,'UI','')
ds.add_new(0x0020000D,'UI','')
ds.add_new(0x0020000E,'UI','')
ds.StudyID = 'GFR*'
ds.add_new(0x00080020, 'DA', '') #Study date
ds.add_new(0x00080050, 'SH', '') #Accession Number
ds.add_new(0x00080060, 'CS' ,'OT')
ds.add_new(0x00080052, 'CS', 'STUDY') #Root SOP Class level
ds.add_new(0x00100010, 'PN', '') #Patitent name
ds.add_new(0x00100020, 'LO', '') #PatientID / CPR NUMBER
ds.add_new(0x00100030, 'DA', '') #Patient Birthday #Why? do we query this, it's in CPR Number?
ds.add_new(0x00321060, 'LO', '')
#Create Sequences
#Add Sequence Tags

#Done adding Sequence Tags

ae.add_requested_context('1.2.840.10008.5.1.4.1.2.2.1')
#ae.add_requested_context('1.2.840.10008.5.1.4.1.2.2.2')

assoc = ae.associate(rigs_ip,rigs_port, ae_title=rigs_aet)

if assoc.is_established:
  #NOTE: Response is a generator, not a interator
  response = assoc.send_c_find(ds, query_model='S')
  
  for (status, dataset_from_rigs) in response:
    #Show Status
    if status.Status == 0xFF00:
      #Save dataset
      print(dataset_from_rigs)  
      #mov_response = assoc.send_c_move(dataset_from_rigs, rigs_calling, query_model='S')

      #for (mov_status, mov_identifyer) in mov_response:
      #  print(mov_status)
  assoc.release()
else:
  print(assoc.is_established)
