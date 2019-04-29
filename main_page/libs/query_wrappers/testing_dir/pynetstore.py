import pynetdicom, pydicom


pacs_ip = '193.3.238.103'
pacs_port = 104
pacs_calling = 'RH_EDTA'
pacs_AET = 'TEST_DCM4CHEE'

ae = pynetdicom.AE(ae_title=pacs_calling)

ae.add_requested_context('1.2.840.10008.5.1.4.1.1.7') #SecondaryImageCaptureStorage

assoc = ae.associate(pacs_ip, pacs_port, ae_title=pacs_AET)

if assoc.is_established:
  ds = pydicom.dcmread('REGH13985169.dcm')
  assoc.send_c_store(ds)

  assoc.release()