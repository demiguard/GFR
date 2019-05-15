import pynetdicom, pydicom


pacs_ip = '10.143.128.234'
pacs_port = 104
pacs_calling = 'HVHFBERGHK7'
pacs_AET = 'VIPDICOM'

ae = pynetdicom.AE(ae_title=pacs_calling)

ae.add_requested_context('1.2.840.10008.5.1.4.1.1.7') #SecondaryImageCaptureStorage

assoc = ae.associate(pacs_ip, pacs_port, ae_title=pacs_AET)

if assoc.is_established:
  ds = pydicom.dcmread('test.dcm')
  response = assoc.send_c_store(ds)

  print(response)

  assoc.release() 