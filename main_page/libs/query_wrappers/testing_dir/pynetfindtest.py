import pynetdicom
import pydicom
from pydicom import uid
datasets = []

rigs_calling = 'RH_EDTA'
rigs_aet     = 'VICIM'
rigs_ip      = '10.143.128.247'
rigs_port    = 3320

ae = pynetdicom.AE(ae_title=rigs_calling)

#'1.2.276.0.7230010.3.1.0.1'
ds = pydicom.Dataset()
#Fill it with tags
ds.add_new(0x00080020, 'DA', '') #Study date
ds.add_new(0x00080050, 'SH', '') #Accession Number
ds.add_new(0x00080052, 'CS', 'STUDY') #Root SOP Class level
ds.add_new(0x00100010, 'PN', '') #Patitent name
ds.add_new(0x00100020, 'LO', '') #PatientID / CPR NUMBER
ds.add_new(0x00100030, 'DA', '') #Patient Birthday #Why? do we query this, it's in CPR Number?
ds.add_new(0x00321060, 'LO', '')
#Create Sequences
Sequenceset = pydicom.Dataset() # ScheduledProcedureStepSequence
#Add Sequence Tags
Sequenceset.add_new(0x00080060, 'CS', '')
Sequenceset.add_new(0x00400001, 'AE', rigs_calling)
Sequenceset.add_new(0x00400002, 'DA', '')
#Done adding Sequence Tags
ds.add_new(0x00400100, 'SQ', pydicom.Sequence([Sequenceset]))

ae.add_requested_context('1.2.840.10008.5.1.4.1.2.2.1')

assoc = ae.associate(rigs_ip,rigs_port, ae_title=rigs_aet)

if assoc.is_established:
  #NOTE: Response is a generator, not a interator
  response = assoc.send_c_find(ds, query_model='S')
  
  for (status, dataset_from_rigs) in response:
    #Show Status
    print(status)
    #Save dataset
    datasets.append(dataset_from_rigs)
  assoc.release()
else:
  print(assoc.is_established)

print(datasets)