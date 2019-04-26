from pydicom import Dataset, Sequence, uid
from . import dicomlib

def get_blank(
    cpr,
    name,
    study_date,
    accession_number,
    hospital_ae_title):
  
  ds = Dataset()

  method_str = 'GFR, Tc-99m-DTPA'

  
  ds.add_new(0x00080005, 'CS', 'ISO_IR 100')
  ds.add_new(0x0020000d, 'UI', 
    uid.generate_uid(
      prefix='1.3.',
      entropy_srcs=[accession_number,'Study'])
    )
  ds.add_new(0x0032000a, 'CS', 'STARTED')
  ds.add_new(0x00321060, 'LO',  method_str)


  ds_seq = Dataset()
  ds_seq.add_new(0x00080060, 'CS', 'OT')
  ds_seq.add_new(0x00400001, 'AE', hospital_ae_title)
  ds_seq.add_new(0x00400007, 'SH' ,method_str)
  ds_seq.add_new(0x00400010, 'SH', hospital_ae_title)

  ds.add_new(0x004001000, 'SQ', Sequence([ds_seq]))



  dicomlib.fill_dicom(
    ds,
    update_dicom=True,
    update_date=True,
    cpr=cpr,
    name=name,
    study_date=study_date,
    rigs_nr = accession_number
    )

  return ds



def get_rigs_base(rigs_calling = None):
  """
  Makes a dataset matching Base_search_query

  This mainly a speed upgrade since we do not need to open a file

  Args:
    calling_ae_title : string 
  Returns:
    dataset : Pydicom dataset, matching that of base_rigs_query.dcm
  """
  #Create New dataset
  ds = Dataset()
  #Fill it with tags
  ds.add_new(0x00020010, 'UI', '1.2.276.0.7230010.3.1.0.1') #Transfer Syntax
  ds.add_new(0x00080020, 'DA', '') #Study date
  ds.add_new(0x00080050, 'SH', '') #Accession Number
  ds.add_new(0x00080052, 'CS', 'STUDY') #Root SOP Class level
  ds.add_new(0x00100010, 'PN', '') #Patitent name
  ds.add_new(0x00100020, 'LO', '') #PatientID / CPR NUMBER
  ds.add_new(0x00100030, 'DA', '') #Patient Birthday #Why? do we query this, it's in CPR Number?
  ds.add_new(0x00321060, 'LO', '')
  #Create Sequences
  Sequenceset = Dataset() # ScheduledProcedureStepSequence
  #Add Sequence Tags
  Sequenceset.add_new(0x00080060, 'CS', '')
  if rigs_calling:
    Sequenceset.add_new(0x00400001, 'AE', rigs_calling)
  else:
    Sequenceset.add_new(0x00400001, 'AE', '')
  
  Sequenceset.add_new(0x00400002, 'DA', '')

  #Done adding Sequence Tags
  ds.add_new(0x00400100, 'SQ', Sequence([Sequenceset]))

  #Done adding tags
  return ds