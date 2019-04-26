import pynetdicom, pydicom
from pynetdicom.sop_class import SecondaryCaptureImageStorage, VerificationSOPClass, PatientRootQueryRetrieveInformationModelMove
from pynetdicom.presentation import PresentationContext

#Goal of test, store a dicom object on simons server

#File to store
filename = 'REGH13985169.dcm'

#Server Ip
server_ip = '193.3.238.103'
server_port = 11112

# 
server_AE_title = b'TEST_DCM4CHEE'
my_AE_title = b'MY_AE_TITLE'
reciever_AE_title = b'recieve_AE_title'

#
sop_class = '1.2.840.10008.5.1.4.1.1.7'
transfer_context = ['1.2.840.10008.1.2', '1.2.840.10008.1.2.1', '1.2.840.10008.1.2.2']

#Create AE title
ae = pynetdicom.AE(ae_title=my_AE_title, port=server_port)

ds = pydicom.dcmread(filename)

#Create Presentation Context
ae.add_requested_context(sop_class, transfer_syntax=transfer_context)
ae.add_requested_context(VerificationSOPClass)
ae.add_requested_context(PatientRootQueryRetrieveInformationModelMove)

assoc = ae.associate(server_ip, server_port, ae_title=server_AE_title, contexts=None)

if assoc.is_established:
  status = assoc.send_c_store(ds)

  

  assoc.release()
else:
  print('Association rejected, aborted or never connected')
