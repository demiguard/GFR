import pynetdicom
import pydicom
from pydicom import Sequence
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind
from pydicom import uid
from pydicom import Dataset
datasets = []

from datetime import date

rigs_calling = 'HIKFARGFR13'
rigs_aet     = 'VICIM' #RIS
rigs_ip      = '10.143.128.247'
rigs_port    = 3320

ae = pynetdicom.AE(ae_title=rigs_calling)
def generate_ris_query_dataset(ris_calling: str=''):
  """
  Generates a dataset for quering RIS

  Args:
    ris_calling: AET for RIS station to retreive studies from, e.g. RH_EDTA, EDTA_GLO, etc.

  Returns:
    Generated dataset used to query rigs
  """
  # Create new dataset
  ds = Dataset()
  
  # Fill required tags, empty tags will be filled out by RIS
  # Non-empty tags with be used as search parameters
  ds.add_new(0x00080016, 'UI', '')      # SOPClassUID These values may be discarded
  ds.add_new(0x00080018, 'UI', '')      # SOPInstanceUID These values may be discarded
  ds.add_new(0x00080020, 'DA', '')      # Study date
  ds.add_new(0x00080050, 'SH', '')      # Accession Number
  ds.add_new(0x00080052, 'CS', 'STUDY') # Root SOP Class level
  ds.add_new(0x00081110, 'SQ', '')      # ReferencedStudySequence
  ds.add_new(0x00100010, 'PN', '')      # Patitent name
  ds.add_new(0x00100020, 'LO', '')      # PatientID / CPR NUMBER
  ds.add_new(0x00100030, 'DA', '')      # Patient Birthday #Why? do we query this, it's in CPR Number?
  ds.add_new(0x0020000D, 'UI', '')      # StudyInstanceUID
  ds.add_new(0x0020000E, 'UI', '')      # SeriesInstanceUID
  ds.add_new(0x00321060, 'LO', '')      # RequestedProcedureDescription

  # Create ScheduledProcedureStepSequence
  Sequenceset = Dataset() 
  
  Sequenceset.add_new(0x00080060, 'CS', 'OT')           # Modality
  Sequenceset.add_new(0x00400001, 'AE', ris_calling) # ScheduledStationAETitle
  Sequenceset.add_new(0x00400002, 'DA', '')           # ScheduledProcedureStepStartDate
  Sequenceset.add_new(0x00400003, 'TM', '')           # ScheduledProcedureStepStartTime
  Sequenceset.add_new(0x00400007, 'LO', '')           # ScheduledProcedureStepDescription
  Sequenceset.add_new(0x00400009, 'SH', '')           # ScheduledProcedureStepID
  Sequenceset.add_new(0x00400010, 'SH', '')           # ScheduledStationName
  Sequenceset.add_new(0x00400011, 'SH', '')           # ScheduledProcedureStepLocation

  ds.add_new(0x00400100, 'SQ', Sequence([Sequenceset])) # ScheduledProcedureStepSequence

  return ds


ds2 = generate_ris_query_dataset(rigs_calling)


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
Sequenceset.add_new(0x00400001, 'AE', 'HIKFARGFR13')
Sequenceset.add_new(0x00400002, 'DA', '')

Sequenceset.add_new(0x00400006, 'PN', '')
Sequenceset.add_new(0x00400009, 'LO', '')
Sequenceset.add_new(0x00400011, 'SH','')

#Done adding Sequence Tags
ds.add_new(0x00400100, 'SQ', pydicom.Sequence([Sequenceset]))

ae.add_requested_context('1.2.840.10008.5.1.4.1.2.2.1')

assoc = ae.associate(rigs_ip,rigs_port, ae_title=rigs_aet)

print(ds)
print(ds2)

if assoc.is_established:
  #NOTE: Response is a generator, not a interator
  response = assoc.send_c_find(ds, query_model=StudyRootQueryRetrieveInformationModelFind)
  print('Connection Successful')
  for (status, dataset_from_rigs) in response:
    #Show Status
    if dataset_from_rigs != None:
      print(dataset_from_rigs)
      print('')
  assoc.release()
else:
  print(assoc.is_established)
