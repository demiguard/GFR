from django.test import TestCase
from pydicom import Dataset, uid

from main_page.libs import dicomlib
from main_page.libs import server_config
from main_page import models


# TODO: Split each function into it's own TestCase class. Not just the entire module...

class LibsDicomlibTestCase(TestCase):
  def setUp(self):
    self.ds = Dataset()

  @classmethod
  def setUpTestData(self):
    # Set up data for the whole TestCase
    self.hospital = models.Hospital(id=1, name='test_name', short_name='tn', address='test_address')
    self.department = models.Department(id=1, name='test_department', hospital=self.hospital)


  def __validate_tags(self, tags):
    """
    Checks if a given set of tags is present with the corret values in the dataset

    Args:
      tags: set of tuples with tag first followed by its value

    Returns:
      True if all tags are present with their correct value, False otherwise.
    """
    for tag, value in tags:
      try:
        if not str(self.ds[tag].value) == str(value):
          return False
      except KeyError:
        return False
  
    return True

  # --- try_add_new tests ---
  def test_try_add_new(self):
    study_id_tag = 0x00200010
    study_id = 'REGH12345678'

    dicomlib.try_add_new(self.ds, study_id_tag, 'SH', study_id)
  
    self.assertEqual(self.ds.StudyID, study_id)
  
  def test_try_add_empty(self):
    study_id_tag = 0x00200010
    study_id = ''

    dicomlib.try_add_new(self.ds, study_id_tag, 'SH', study_id)
    with self.assertRaises(AttributeError):
      self.ds.StudyID

  def test_try_add_new_none(self):
    study_id_tag = 0x00200010
    study_id = None

    dicomlib.try_add_new(self.ds, study_id_tag, 'SH', study_id)
    with self.assertRaises(AttributeError):
      self.ds.StudyID
    
  def test_try_add_exists(self):
    # Tag already has a value in the dataset
    study_id_tag = 0x00200010
    old_study_id = 'REGH12345678'
    new_study_id = 'REGH87654321'

    self.ds.StudyID = old_study_id
    self.assertEqual(self.ds.StudyID, old_study_id)

    dicomlib.try_add_new(self.ds, study_id_tag, 'SH', new_study_id)
    
    self.assertEqual(self.ds.StudyID, new_study_id)


  # --- try_update_exam_meta_data tests ---
  def __validate_meta_data_tags(self):
    validation_tags = (
      (0x00080060, 'OT'),
      (0x00080064, 'SYN'),
      (0x00230010, 'Clearance - Denmark - Region Hovedstaden'),
      (0x00080030, ''),
      (0x00080090, ''),
      (0x00200010, 'GFR#' + self.ds.AccessionNumber[4:]),
      (0x00200013, '1'),
      (0x00181020, f'{server_config.SERVER_NAME} - {server_config.SERVER_VERSION}'),
      (0x00080016, '1.2.840.10008.5.1.4.1.1.7'),
      (0x00080018, uid.generate_uid(prefix='1.3.', entropy_srcs=[self.ds.AccessionNumber, 'SOP'])),
      (0x0020000E, uid.generate_uid(prefix='1.3.', entropy_srcs=[self.ds.AccessionNumber, 'Series'])),
    )

    return self.__validate_tags(validation_tags)

  def test_try_update_exam_meta_data(self):
    self.ds.AccessionNumber = "REGH12345678"

    dicomlib.try_update_exam_meta_data(self.ds, True)

    self.assertEqual(self.__validate_meta_data_tags(), True)

  def test_try_update_exam_meta_data_false(self):
    # Run the function with update_dicom=False
    self.ds.AccessionNumber = "REGH12345678"

    dicomlib.try_update_exam_meta_data(self.ds, False)

    self.assertEqual(self.__validate_meta_data_tags(), False)

  def test_try_update_exam_meta_data_existing(self):
    # Try updating a dataset which already contains some meta data
    self.ds.AccessionNumber = "REGH12345678"
    
    tags = (
      (0x00080060, 'CS', 'something'),
      (0x00080064, 'CS', 'something'),
      (0x00230010, 'LO', 'something'),
      (0x00080030, 'TM', 'something'),
      (0x00080090, 'PN', 'something'),
      (0x00200010, 'SH', 'something'),
      (0x00200013, 'IS', 123),
      (0x00181020, 'LO', 'something'),
      (0x00080016, 'UI', 'something'),
      (0x00080018, 'UI', 'something'),
      (0x0020000E, 'UI', 'something'),
    )

    for tag, VR, value in tags:
      self.ds.add_new(tag, VR, value)

    dicomlib.try_update_exam_meta_data(self.ds, True)

    self.assertEqual(self.__validate_meta_data_tags(), True)


  # --- try_add_department tests ---
  def __validate_department_tags(self):
    validation_tags = (
     (0x00080080, self.department.hospital.name),
     (0x00080081, self.department.hospital.address),
     (0x00081040, self.department.name),
    )

    return self.__validate_tags(validation_tags)

  def test_try_add_department(self):
    dicomlib.try_add_department(self.ds, self.department)

    self.assertEqual(self.__validate_department_tags(), True)

  def test_try_add_department_none(self):
    dicomlib.try_add_department(self.ds, None)

    self.assertEqual(self.__validate_department_tags(), False)


  # --- try_update_study_date tests ---



  # --- try_update_scheduled_procedure_step_sequence tests ---



  # --- try_add_exam_status tests ---



  # --- try_add_age tests ---



  # --- try_add_gender tests ---



  # --- try_add_sample_sequence tests ---



  # --- try_add_pixeldata tests ---



  # --- fill_dicom tests ---


