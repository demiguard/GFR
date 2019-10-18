from django.test import TestCase
from main_page.libs import dicomlib, dirmanager
from main_page.libs.query_wrappers import pacs_query_wrapper as pacs
from pydicom import Dataset

import shutil
import pydicom
import unittest 


config = {
  'directory_name' : 'pacs_query_wrapper_tests/'
}

class test_get_history_from_pacs(unittest.TestCase):
  def setUp(self):
    calling_dataset = Dataset() 
    calling_dataset.AccessionNumber   = 'REGH10000000'
    calling_dataset.PatientBirthDate  = '20000101'
    calling_dataset.SOpClassUID       = '1.2.840.10008.5.1.4.1.1.7'
    calling_dataset.SOPInstanceUID    = pydicom.uid.generate_uid(prefix='1.3.', entropy_srcs=[calling_dataset.AccessionNumber, 'SOP'])
    calling_dataset.SeriesInstanceUID = pydicom.uid.generate_uid(prefix='1.3.', entropy_srcs=[calling_dataset.AccessionNumber, 'Series'])
    calling_dataset.StudyInstanceUID  = pydicom.uid.generate_uid(prefix='1.3.', entropy_srcs=[calling_dataset.AccessionNumber, 'Study'])
 
    dirmanager.try_mkdir(f"{config['directory_name']}/{calling_dataset.AccessionNumber}/", mk_parents=True)
    dicomlib.save_dicom(f"{config['directory_name']}/{calling_dataset.AccessionNumber}/{calling_dataset.AccessionNumber}.dcm", calling_dataset)
 
    self.path = config['directory_name']
    self.ds   = calling_dataset
 
  def tearDown(self):
    shutil.rmtree(config['directory_name'])

 
  def __create_datasets(self, amounts_of_datasets: int):
    dicomlib.update_private_tags()
 
    history_datasets = []   
    for history_dataset_index in range(amounts_of_datasets):
      history_dataset = Dataset()
 
      history_dataset.AccessionNumber = f'REGH1000000{history_dataset_index + 1}'
      history_dataset.SOpClassUID       = '1.2.840.10008.5.1.4.1.1.7'
      history_dataset.SOPInstanceUID    = pydicom.uid.generate_uid(prefix='1.3.', entropy_srcs=[history_dataset.AccessionNumber, 'SOP'])
      history_dataset.SeriesInstanceUID = pydicom.uid.generate_uid(prefix='1.3.', entropy_srcs=[history_dataset.AccessionNumber, 'Series'])
      history_dataset.StudyInstanceUID  = pydicom.uid.generate_uid(prefix='1.3.', entropy_srcs=[history_dataset.AccessionNumber, 'Study'])
 
      history_dataset.StudyDate = f'201{history_dataset_index}0101'
      history_dataset.clearance = 160 - history_dataset_index * 10
      history_dataset.normClear = 160 - history_dataset_index * 10
      history_dataset.injTime   = '0000'
      history_dataset.PatientWeight = 75 + history_dataset_index * 2
      history_dataset.PatientSize   = 177
 
      history_test_sequence = []
 
      for variance in range(history_dataset_index + 1):
        seq_elem = Dataset()
 
        seq_elem.cpm = 2000 - variance * 250
        seq_elem.SampleTime = f'201{history_dataset_index}01010{variance}00'
 
        history_test_sequence.append(seq_elem)
 
      history_dataset.ClearTest = pydicom.Sequence(history_test_sequence)
 
      dicomlib.save_dicom(f'{self.path}/{self.ds.AccessionNumber}/{history_dataset.AccessionNumber}.dcm', history_dataset)
       
  def test_case_0_history(self):
    # init
    
    # Run
    date_list, age_list, clearence_list = pacs.get_history_from_pacs(self.ds, self.path)
    # Assert Some stuff
    self.assertEqual(len(date_list) == 0 and len(age_list) == 0 and len(clearence_list) == 0 )
    
  def test_case_1_history(self):
    # init
    self.__create_datasets(1)
    # Run
    date_list, age_list, clearence_list = pacs.get_history_from_pacs(self.ds, self.path)
    # Assert Some stuff
    self.assertEqual(len(date_list) == 0 and len(age_list) == 0 and len(clearence_list) == 0 )
    self.assertIn(0x0023103F, self.ds)
    self.assertEqual(len(self.ds[0x0023103F].value), 1 )


  def test_case_2_history(self):
    # init
    self.__create_datasets(2)
    # Run
    date_list, age_list, clearence_list = pacs.get_history_from_pacs(self.ds, self.path)
    # Assert Some stuff
    self.assertEqual(len(date_list) == 3 and len(age_list) == 3 and len(clearence_list) == 3 )
    self.assertIn(0x0023103F, self.ds)
    self.assertEqual(len(self.ds[0x0023103F].value), 2)

  def test_case_3_history(self):
    # init
    self.__create_datasets(3)
    # Run
    date_list, age_list, clearence_list = pacs.get_history_from_pacs(self.ds, self.path)
    # Assert Some stuff
    self.assertEqual(len(date_list) == 3 and len(age_list) == 3 and len(clearence_list) == 3 )
    self.assertIn(0x0023103F, self.ds)
    self.assertEqual(len(self.ds[0x0023103F].value), 3 )

  def test_case_4_history(self):
    # init
    self.__create_datasets(4)
    # Run
    date_list, age_list, clearence_list = pacs.get_history_from_pacs(self.ds, self.path)
    # Assert Some stuff
    self.assertEqual(len(date_list) == 4 and len(age_list) == 4 and len(clearence_list) == 4 )
    self.assertIn(0x0023103F, self.ds)
    self.assertEqual(len(self.ds[0x0023103F].value), 4 )
   








