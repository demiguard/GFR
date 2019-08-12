import unittest

import pydicom
from pydicom import Dataset

from main_page.libs import dataset_creator


# --- create_empty_dataset ---
class EmptyDatasetTests(unittest.TestCase):  
  def test_create_empty_dataset(self):
    accession_number = "REGH12345678"
    ds = dataset_creator.create_empty_dataset(accession_number)

    self.assertEqual(isinstance(ds, Dataset), True)

    # Assert that meta data is in dataset
    self.assertEqual(ds.is_little_endian, True)
    self.assertEqual(ds.is_implicit_VR, True)
    self.assertEqual(ds[0x00080005].VR, 'CS')
    self.assertEqual(ds[0x00080005].value, 'ISO_IR 100')
    self.assertEqual(ds.SOPClassUID, '1.2.840.10008.5.1.4.1.1.7')
    self.assertEqual(ds.SOPInstanceUID, '1.3.110991891537808377320710161154227944576338148545133209878678') # Generated UID for the accession number

    # Assert that corresponding meta data is in file_meta
    self.assertEqual(ds.file_meta[0x00020002].value, '1.2.840.10008.5.1.4.1.1.7')
    self.assertEqual(ds.file_meta[0x00020002].VR, 'UI')
    self.assertEqual(ds.file_meta[0x00020003].value, '1.3.110991891537808377320710161154227944576338148545133209878678')
    self.assertEqual(ds.file_meta[0x00020003].VR, 'UI')
    self.assertEqual(ds.file_meta[0x00020010].value, '1.2.840.10008.1.2') # Implicit VR Little Endian
    self.assertEqual(ds.file_meta[0x00020010].VR, 'UI')
    self.assertEqual(ds.file_meta[0x00020012].value, '1.2.826.0.1.3680043.8.498.1')
    self.assertEqual(ds.file_meta[0x00020012].VR, 'UI')
    self.assertEqual(ds.file_meta[0x00020013].value, f'PYDICOM {pydicom.__version__}')
    self.assertEqual(ds.file_meta[0x00020013].VR, 'SH')

  def test_create_empty_dataset_none(self):
    with self.assertRaises(ValueError):
      dataset_creator.create_empty_dataset(None)

# --- get_blank ---
class GetBlankTests(unittest.TestCase):
  def setUp(self):
    self.cpr = '1234564321'
    self.name = 'test t. testerson'
    self.study_date = '2019-01-01'
    self.accession_number = 'REGH12345678'
    self.hospital_ae_title = 'TEST_AET'
  
  def test_get_blank(self):
    ds = dataset_creator.get_blank(
      self.cpr, 
      self.name, 
      self.study_date, 
      self.accession_number, 
      self.hospital_ae_title
    )

    self.assertEqual(isinstance(ds, Dataset), True)

    # Required examination data
    self.assertEqual(ds[0x0020000d].value, '1.3.114945357800429515625009469064908297373491801971184852245298')
    self.assertEqual(ds[0x0020000d].VR, 'UI')

    self.assertEqual(ds[0x0032000a].value, 'STARTED')
    self.assertEqual(ds[0x0032000a].VR, 'CS')
    self.assertEqual(ds[0x00321060].value, 'GFR, Tc-99m-DTPA')
    self.assertEqual(ds[0x00321060].VR, 'LO')

    # ScheduledProcedureStepSequence
    self.assertEqual(len(ds[0x00400100].value), 1)
    self.assertEqual(ds[0x00400100].VR, 'SQ')
    self.assertEqual(ds[0x00400100][0][0x00080060].value, 'OT')
    self.assertEqual(ds[0x00400100][0][0x00080060].VR, 'CS')
    self.assertEqual(ds[0x00400100][0][0x00400001].value, self.hospital_ae_title)
    self.assertEqual(ds[0x00400100][0][0x00400001].VR, 'AE')
    self.assertEqual(ds[0x00400100][0][0x00400002].value, '20190101')
    self.assertEqual(ds[0x00400100][0][0x00400002].VR, 'DA')
    self.assertEqual(ds[0x00400100][0][0x00400007].value, 'GFR, Tc-99m-DTPA')
    self.assertEqual(ds[0x00400100][0][0x00400007].VR, 'SH')
    self.assertEqual(ds[0x00400100][0][0x00400010].value, self.hospital_ae_title)
    self.assertEqual(ds[0x00400100][0][0x00400010].VR, 'SH')

  def test_get_blank_none(self):
    # cpr = None
    with self.assertRaises(ValueError):
      dataset_creator.get_blank(None, self.name, self.study_date, self.accession_number, self.hospital_ae_title)

    # name = None
    with self.assertRaises(ValueError):
      dataset_creator.get_blank(self.cpr, None, self.study_date, self.accession_number, self.hospital_ae_title)

    # study_date = None
    with self.assertRaises(ValueError):
      dataset_creator.get_blank(self.cpr, self.name, None, self.accession_number, self.hospital_ae_title)

    # accession_number = None
    with self.assertRaises(ValueError):
      dataset_creator.get_blank(self.cpr, self.name, self.study_date, None, self.hospital_ae_title)
    
    # hospital_ae_title = None
    with self.assertRaises(ValueError):
      dataset_creator.get_blank(self.cpr, self.name, self.study_date, self.accession_number, None)


# --- generate_ris_query_dataset ---
class GenerateRisQueryDatasetTests(unittest.TestCase):
  def test_generate_ris_query_dataset(self):
    ris_calling = 'TEST_AET'

    ds = dataset_creator.generate_ris_query_dataset(ris_calling=ris_calling)

    self.assertEqual(isinstance(ds, Dataset), True)

    self.assertEqual(ds[0x00080016].value, '')
    self.assertEqual(ds[0x00080018].value, '')
    self.assertEqual(ds[0x00080020].value, '')
    self.assertEqual(ds[0x00080050].value, '')
    self.assertEqual(ds[0x00080052].value, 'STUDY')
    self.assertEqual(len(ds[0x00081110].value), 0)
    self.assertEqual(ds[0x00100010].value, '')
    self.assertEqual(ds[0x00100020].value, '')
    self.assertEqual(ds[0x00100030].value, '')
    self.assertEqual(ds[0x0020000D].value, '')
    self.assertEqual(ds[0x0020000E].value, '')
    self.assertEqual(ds[0x00321060].value, '')

    self.assertEqual(ds[0x00080016].VR, 'UI')
    self.assertEqual(ds[0x00080018].VR, 'UI')
    self.assertEqual(ds[0x00080020].VR, 'DA')
    self.assertEqual(ds[0x00080050].VR, 'SH')
    self.assertEqual(ds[0x00080052].VR, 'CS')
    self.assertEqual(ds[0x00081110].VR, 'SQ')
    self.assertEqual(ds[0x00100010].VR, 'PN')
    self.assertEqual(ds[0x00100020].VR, 'LO')
    self.assertEqual(ds[0x00100030].VR, 'DA')
    self.assertEqual(ds[0x0020000D].VR, 'UI')
    self.assertEqual(ds[0x0020000E].VR, 'UI')
    self.assertEqual(ds[0x00321060].VR, 'LO')

    self.assertEqual(len(ds[0x00400100].value), 1)
    self.assertEqual(ds[0x00400100][0][0x00080060].value, '')
    self.assertEqual(ds[0x00400100][0][0x00400001].value, ris_calling)
    self.assertEqual(ds[0x00400100][0][0x00400002].value, '')
    self.assertEqual(ds[0x00400100][0][0x00400003].value, '')
    self.assertEqual(ds[0x00400100][0][0x00400007].value, '')
    self.assertEqual(ds[0x00400100][0][0x00400009].value, '')
    self.assertEqual(ds[0x00400100][0][0x00400010].value, '')
    self.assertEqual(ds[0x00400100][0][0x00400011].value, '')

    self.assertEqual(ds[0x00400100].VR, 'SQ')
    self.assertEqual(ds[0x00400100][0][0x00080060].VR, 'CS')
    self.assertEqual(ds[0x00400100][0][0x00400001].VR, 'AE')
    self.assertEqual(ds[0x00400100][0][0x00400002].VR, 'DA')
    self.assertEqual(ds[0x00400100][0][0x00400003].VR, 'TM')
    self.assertEqual(ds[0x00400100][0][0x00400007].VR, 'LO')
    self.assertEqual(ds[0x00400100][0][0x00400009].VR, 'SH')
    self.assertEqual(ds[0x00400100][0][0x00400010].VR, 'SH')
    self.assertEqual(ds[0x00400100][0][0x00400011].VR, 'SH')

  def test_generate_ris_query_dataset_empty(self):
    ds = dataset_creator.generate_ris_query_dataset()

    self.assertEqual(isinstance(ds, Dataset), True)

    self.assertEqual(ds[0x00400100][0][0x00400001].value, '')


# --- create_search_dataset ---
class CreateSearchDatasetTests(unittest.TestCase):
  def setUp(self):
    self.name = 'test t. testerson'
    self.cpr = '1234564321'
    self.accession_number = 'REGH12345678'
    self.date_from = '2019-01-01'
    self.date_to = '2019-08-01'

  def test_create_search_dataset(self):
    
    ds = dataset_creator.create_search_dataset(
      self.name,
      self.cpr,
      self.date_from,
      self.date_to,
      self.accession_number
    )

    self.assertEqual(isinstance(ds, Dataset), True)

    self.assertEqual(ds[0x00080020].value, '20190101-20190801')
    self.assertEqual(ds[0x00080050].value, self.accession_number)
    self.assertEqual(ds[0x00100020].value, self.cpr)
    self.assertEqual(ds[0x00100010].value, 'testerson^test^t.^^')
    self.assertEqual(ds[0x00080052].value, 'STUDY')
    self.assertEqual(ds[0x00080016].value, '')
    self.assertEqual(ds[0x00080018].value, '')
    self.assertEqual(ds[0x0020000E].value, '')
    self.assertEqual(ds[0x0020000D].value, '')
    self.assertEqual(ds[0x00080060].value, 'OT')
    self.assertEqual(ds[0x00200010].value, 'GFR*')

  def test_create_search_dataset_dates(self):
    def test_dates(date_from, date_to, assert_str):
      ds = dataset_creator.create_search_dataset(
        self.name,
        self.cpr,
        date_from,
        date_to,
        self.accession_number
      )
  
      self.assertEqual(isinstance(ds, Dataset), True)
  
      self.assertEqual(ds[0x00080020].value, assert_str)
    
    test_dates('', '', '')                      # Both dates are empty
    test_dates('', self.date_to, '-20190801')   # date_from is empty
    test_dates(self.date_from, '', '20190101-') # date_to is empty
