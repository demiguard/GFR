import pydicom
from pynetdicom.sop_class import LittleEndainExplicit

def get_data_set(rigs_calling = None)
  """
  Makes a dataset matching Base_search_query

  This mainly a speed upgrade since we do not need to open a file

  Args:
    calling_ae_title : string 
  Returns:
    dataset : Pydicom dataset, matching that of base_rigs_query.dcm
  """
  #Create New dataset
  ds = pydicom.Dataset()
  #Fill it with tags
  ds.add_new(0x00020010, 'UI', '1.2.276.0.7230010.3.1.0.1')
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
  if rigs_calling:
    Sequenceset.add_new(0x00400001, 'AE', rigs_calling)
  else:
    Sequenceset.add_new(0x00400001, 'AE', '')
  
  Sequenceset.add_new(0x00400002, 'DA', '')

  #Done adding Sequence Tags
  ds.add_new(0x00400100, 'SQ', pydicom.Sequence([Sequenceset]))

  #Done adding tags
  return ds

