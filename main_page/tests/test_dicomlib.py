from django.test import TestCase
import unittest

from tempfile import TemporaryFile, NamedTemporaryFile
from datetime import datetime
import numpy as np
import pydicom
from pydicom import Dataset, Sequence, uid, values
from pydicom._storage_sopclass_uids import SecondaryCaptureImageStorage
import os

from main_page.libs import dataset_creator
from main_page.libs import enums 
from main_page.libs import dicomlib
from main_page.libs import server_config
from main_page.libs.clearance_math import clearance_math
from main_page import models


def validate_tags(ds, tags):
  """
  Checks if a given set of tags is present with the corret values in the dataset

  Args:
    ds: dataset to check tags for
    tags: set of tuples with tag first followed by its correct value

  Returns:
    True if all tags are present with their correct value, False otherwise.
  """
  for tag, value in tags:
    try:
      if not str(ds[tag].value) == str(value):
        return False
    except KeyError:
      return False

  return True


# --- dcmread_wrapper ---
class DcmreadWrapperTests(unittest.TestCase):
  def setUp(self):
    self.ds = dataset_creator.create_empty_dataset('REGH12345678')
    
  def test_dcmread_wrapper_no_private(self):
    """
    Construct and save dataset without private tags to temp file
    
    Remark:
    This test utilizes NamedTemporaryFile's to allow us to reopen them
    since pydicom might close them
    """
    accession_number = '1234564321'
    self.ds.add_new(0x00100020, 'LO', accession_number)

    tmp_file = NamedTemporaryFile(delete=False)
    self.ds.save_as(tmp_file, write_like_original=False)
    tmp_file.close()

    # Attempt to reload the dataset
    load_ds = dicomlib.dcmread_wrapper(tmp_file.name)
    os.remove(tmp_file.name)

    self.assertEqual(load_ds[0x00100020].value, accession_number)

  def test_dcmread_wrapper_with_private(self):
    """
    Construct and save dataset with private tags to temp file
    
    Remark:
      This test utilizes NamedTemporaryFile's to allow us to reopen them
      since pydicom might close them
    """
    thin_fac = 12345
    self.ds.add_new(0x00231028, 'DS', thin_fac)

    tmp_file = NamedTemporaryFile(delete=False)
    self.ds.save_as(tmp_file, write_like_original=False)
    tmp_file.close()

    # Attempt to reload the dataset
    load_ds = dicomlib.dcmread_wrapper(tmp_file.name)
    os.remove(tmp_file.name)

    self.assertEqual(load_ds[0x00231028].value, thin_fac)


# --- update_tags tests ---
class UpdateTagsTests(unittest.TestCase):
  def setUp(self):
    self.ds = Dataset()
    
    # Keywords to remove from the DicomDictionary
    # These must be removed to ensure that pydicom reads the private tags as VR 'UN' (unknown)
    self.kw_dict = {
      0x00231020,
      0x00231012,
      0x00231001
    }

    for kw in self.kw_dict:
      try:
        del pydicom.datadict.DicomDictionary[kw]
      except KeyError:
        pass

  def test_update_tags_one_unknown(self):
    self.ds.add_new(0x00231012, 'UN', '123'.encode())

    self.ds = dicomlib.update_tags(self.ds)

    self.assertEqual(self.ds[0x00231012].value, 123)
    self.assertEqual(self.ds[0x00231012].VR, 'DS')

  def test_update_tags_unknown_string(self):
    self.ds.add_new(0x00231001, 'UN', 'Normal'.encode())

    self.ds = dicomlib.update_tags(self.ds)

    self.assertEqual(self.ds[0x00231001].value, 'Normal')
    self.assertEqual(self.ds[0x00231001].VR, 'LO')    

  def test_update_tags_unknown_sequence(self):
    # Unknown sequence with known tags
    self.ds = dataset_creator.create_empty_dataset('REGH12345678')
    
    test_seq_data = Dataset()
    test_seq_data.add_new(0x00100020, 'LO', '1234564321')
    test_seq = Sequence([test_seq_data])

    self.ds.add_new(0x00231020, 'SQ', test_seq)

    # Save dataset to make sequence bytes
    tmp_file = NamedTemporaryFile(delete=False)
    dicomlib.save_dicom(tmp_file, self.ds)
    tmp_file.close()

    load_ds = pydicom.dcmread(tmp_file.name)
    os.remove(tmp_file.name)

    load_ds = dicomlib.update_tags(load_ds)

    self.assertEqual(len(load_ds[0x00231020].value), 1)
    self.assertEqual(load_ds[0x00231020].VR, 'SQ')
    self.assertEqual(load_ds[0x00231020][0][0x00100020].VR, 'LO')
    self.assertEqual(load_ds[0x00231020][0][0x00100020].value, '1234564321')

  def test_update_tags_sequence_with(self):
    # Unknown sequence with unknown tags
    self.ds = dataset_creator.create_empty_dataset('REGH12345678')

    test_seq_data1 = Dataset()
    test_seq_data1.add_new(0x00231001, 'UN', 'Normal'.encode())
    
    test_seq_data2 = Dataset()
    test_seq_data2.add_new(0x00231028, 'UN', '35000'.encode())
    
    test_seq_data3 = Dataset()
    test_seq_data3.add_new(0x00231011, 'UN', 'Haycock'.encode())
    
    test_seq = Sequence([test_seq_data1, test_seq_data2, test_seq_data3])

    self.ds.add_new(0x00231020, 'SQ', test_seq)

    # Save dataset to make sequence bytes
    tmp_file = NamedTemporaryFile(delete=False)
    dicomlib.save_dicom(tmp_file, self.ds)
    tmp_file.close()

    load_ds = pydicom.dcmread(tmp_file.name)
    os.remove(tmp_file.name)

    load_ds = dicomlib.update_tags(load_ds)

    self.assertEqual(len(load_ds[0x00231020].value), 3)
    self.assertEqual(load_ds[0x00231020].VR, 'SQ')
    self.assertEqual(load_ds[0x00231020][0][0x00231001].VR, 'LO')
    self.assertEqual(load_ds[0x00231020][0][0x00231001].value, 'Normal')
    self.assertEqual(load_ds[0x00231020][1][0x00231028].VR, 'DS')
    self.assertEqual(load_ds[0x00231020][1][0x00231028].value, 35000)
    self.assertEqual(load_ds[0x00231020][2][0x00231011].VR, 'LO')
    self.assertEqual(load_ds[0x00231020][2][0x00231011].value, 'Haycock')

  def test_update_tags_recurrsion_depth(self):
    """
    Tests that the function can handle multiple layers of sequences within
    sequences
    """
    self.ds = dataset_creator.create_empty_dataset('REGH12345678')

    test_seq_data = Dataset()
    seq_datas = [Dataset() for _ in range(69)]
    
    # Add something which is not a sequence to the last one
    seq_datas[-1].add_new(0x00231001, 'UN', 'Normal'.encode())

    # Add sequences to sequences
    rev_cnt = -1
    for seq_data in reversed(seq_datas[:-1]):
      seq_data.add_new(0x00231020, 'SQ', Sequence([seq_datas[rev_cnt]]))
      rev_cnt -= 1

    # Add main sequence to datas
    test_seq_data.add_new(0x00231020, 'SQ', Sequence([seq_datas[0]]))
    test_seq = Sequence([test_seq_data])

    self.ds.add_new(0x00231020, 'SQ', test_seq)

    # Save dataset to make sequence bytes
    tmp_file = NamedTemporaryFile(delete=False)
    dicomlib.save_dicom(tmp_file, self.ds)
    tmp_file.close()

    load_ds = pydicom.dcmread(tmp_file.name)
    os.remove(tmp_file.name)
    
    load_ds = dicomlib.update_tags(load_ds)
    
    def recurse_assert(elem):
      # Recursively assert that every sequence has another sequence within
      if elem.VR == 'SQ':
        self.assertEqual(elem.VR, 'SQ')
        self.assertEqual(len(elem.value), 1)

        try:
          recurse_assert(elem.value[0][0x00231020])
        except:
          recurse_assert(elem.value[0][0x00231001])
      else:
        self.assertEqual(elem.VR, 'LO')
        self.assertEqual(elem.value, 'Normal')
        
    recurse_assert(load_ds[0x00231020])

  def test_update_tags_known_sequence(self):
    # Known sequence with unknown tags
    self.ds = dataset_creator.create_empty_dataset('REGH12345678')
    
    test_seq_data = Dataset()
    test_seq_data.add_new(0x00231001, 'UN', 'Normal'.encode())
    test_seq = Sequence([test_seq_data])

    self.ds.add_new(0x00400100, 'SQ', test_seq)

    # Save dataset
    tmp_file = NamedTemporaryFile(delete=False)
    dicomlib.save_dicom(tmp_file, self.ds)
    tmp_file.close()

    load_ds = pydicom.dcmread(tmp_file.name)
    os.remove(tmp_file.name)

    load_ds = dicomlib.update_tags(load_ds)

    self.assertEqual(len(load_ds[0x00400100].value), 1)
    self.assertEqual(load_ds[0x00400100].VR, 'SQ')
    self.assertEqual(load_ds[0x00400100][0][0x00231001].VR, 'LO')
    self.assertEqual(load_ds[0x00400100][0][0x00231001].value, 'Normal')

    
# --- save_dicom tests ---
class SaveDicomTests(unittest.TestCase):
  def setUp(self):
    self.ds = Dataset()

  def test_save_dicom(self):
    tmp_file = TemporaryFile()

    self.ds.AccessionNumber = 'REGH12345678'

    dicomlib.save_dicom(tmp_file, self.ds)

    tmp_file.seek(0)
    contents = tmp_file.read()
    self.assertEqual(len(contents) > 0, True)

    tmp_file.close()

  def test_save_dicom_empty_filepath(self):
    with self.assertRaises(ValueError):
      dicomlib.save_dicom('', self.ds)

  def test_save_dicom_failed_resolve(self):
    tmp_file = TemporaryFile()

    with self.assertRaises(ValueError):
      dicomlib.save_dicom(tmp_file, self.ds)
    
    tmp_file.close()

# --- try_add_new tests ---
class TryAddTestCase(unittest.TestCase):
  def setUp(self):
    self.ds = Dataset()

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
class ExamMetaDataTests(TestCase):
  def setUp(self):
    self.ds = Dataset()

  @classmethod
  def setUpTestData(self):
    # Set up data for the whole TestCase
    self.hospital = models.Hospital(id=1, name='test_name', short_name='tn', address='test_address')
    self.department = models.Department(id=1, name='test_department', hospital=self.hospital)

  def __validate_meta_data_tags(self):
    validation_tags = (
      (0x00080060, 'OT'),
      (0x00080064, 'SYN'),
      (0x00230010, 'Clearance - Denmark - Region Hovedstaden'),
      (0x00080090, ''),
      (0x00200010, 'GFR#' + self.ds.AccessionNumber[4:]),
      (0x00200013, '1'),
      (0x00181020, f'{server_config.SERVER_NAME} - {server_config.SERVER_VERSION}'),
      (0x00080016, '1.2.840.10008.5.1.4.1.1.7'),
      (0x00080018, uid.generate_uid(prefix='1.3.', entropy_srcs=[self.ds.AccessionNumber, 'SOP'])),
      (0x0020000E, uid.generate_uid(prefix='1.3.', entropy_srcs=[self.ds.AccessionNumber, 'Series'])),
    )

    return validate_tags(self.ds, validation_tags)

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

    return validate_tags(self.ds, validation_tags)

  def test_try_add_department(self):
    dicomlib.try_add_department(self.ds, self.department)

    self.assertEqual(self.__validate_department_tags(), True)

  def test_try_add_department_none(self):
    dicomlib.try_add_department(self.ds, None)

    self.assertEqual(self.__validate_department_tags(), False)


# --- try_update_study_date tests ---
class StudyDateTests(unittest.TestCase):
  def setUp(self):
    self.ds = Dataset()

  def test_try_update_study_date(self):
    # Construct the ScheduledProcedureStepSequence
    init_date = '00000000'
    init_time = '0000'
    
    test_seq_data = Dataset()

    test_seq_data.add_new(0x00400002, 'DA', init_date) # ScheduledProcedureStepStartDate
    test_seq_data.add_new(0x00400003, 'TM', init_time)     # ScheduledProcedureStepStartTime

    test_seq = Sequence([test_seq_data])

    self.ds.add_new(0x00400100, 'SQ', test_seq)

    self.ds.StudyDate = init_date
    self.ds.SeriesDate = init_date
    self.ds.StudyTime = init_time
    self.ds.SeriesTime = init_time

    # Attempt update
    study_date = '111111110808'
    dicomlib.try_update_study_date(self.ds, True, study_date)

    # Assert that everything was set correctly
    expected_study_date = '11111111'
    expected_study_time = '0808'

    validation_tags = (
      (0x00080020, expected_study_date), # StudyDate
      (0x00080021, expected_study_date), # SeriesDate
      (0x00080030, expected_study_time), # StudyTime
      (0x00080031, expected_study_time), # SeriesTime
    )

    self.assertEqual(validate_tags(self.ds, validation_tags), True)

    self.assertEqual(self.ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate, expected_study_date)
    self.assertEqual(self.ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartTime, expected_study_time)

  def test_try_update_study_date_false(self):
    # Sets update_date to False
    
    # Construct the ScheduledProcedureStepSequence
    init_date = '00000000'
    init_time = '0000'
    
    test_seq_data = Dataset()

    test_seq_data.add_new(0x00400002, 'DA', init_date) # ScheduledProcedureStepStartDate
    test_seq_data.add_new(0x00400003, 'TM', init_time) # ScheduledProcedureStepStartTime

    test_seq = Sequence([test_seq_data])

    self.ds.add_new(0x00400100, 'SQ', test_seq)

    # Don't perform any update
    dicomlib.try_update_study_date(self.ds, False, '')
    dicomlib.try_update_study_date(self.ds, False, '1111-11-11')

    # Assert that everything was set correctly
    expected_study_date = '00000000'
    expected_study_time = '0000'

    self.assertEqual(self.ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate, expected_study_date)
    self.assertEqual(self.ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartTime, expected_study_time)

  def test_try_update_study_date_empty(self):
    # Sets study_date to an empty string to attempt to get the date and times
    # from the ScheduledProcedureStepSequence
    
    # Construct the ScheduledProcedureStepSequence
    init_date = '00000000'
    init_time = '0000'
    
    test_seq_data = Dataset()

    test_seq_data.add_new(0x00400002, 'DA', init_date) # ScheduledProcedureStepStartDate
    test_seq_data.add_new(0x00400003, 'TM', init_time) # ScheduledProcedureStepStartTime

    test_seq = Sequence([test_seq_data])

    self.ds.add_new(0x00400100, 'SQ', test_seq)

    # Attempt to set StudyDate, StudyTime, SeriesDate and SeriesTime through the ScheduledProcedureStepSequence
    dicomlib.try_update_study_date(self.ds, True, '')

    # Assert that everything was set correctly
    expected_study_date = '00000000'
    expected_study_time = '0000'

    validation_tags = (
      (0x00080020, expected_study_date), # StudyDate
      (0x00080021, expected_study_date), # SeriesDate
      (0x00080030, expected_study_time), # StudyTime
      (0x00080031, expected_study_time), # SeriesTime
    )

    self.assertEqual(validate_tags(self.ds, validation_tags), True)

  def test_try_update_study_date_no_step_sequence(self):
    # Fail the try exception when setting the ScheduledProcedureStepStartDate
    # and ScheduledProcedureStepStartTime
    
    # Construct the ScheduledProcedureStepSequence
    init_date = '00000000'
    init_time = '0000'

    self.ds.StudyDate = init_date
    self.ds.SeriesDate = init_date
    self.ds.StudyTime = init_time
    self.ds.SeriesTime = init_time

    # Attempt update
    study_date = '111111110808'
    dicomlib.try_update_study_date(self.ds, True, study_date)

    # Assert that everything was set correctly
    expected_study_date = '11111111'
    expected_study_time = '0808'

    validation_tags = (
      (0x00080020, expected_study_date), # StudyDate
      (0x00080021, expected_study_date), # SeriesDate
      (0x00080030, expected_study_time), # StudyTime
      (0x00080031, expected_study_time), # SeriesTime
    )

    self.assertEqual(validate_tags(self.ds, validation_tags), True)

    self.assertEqual(self.ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate, expected_study_date)
    self.assertEqual(self.ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartTime, expected_study_time)


  # --- try_update_scheduled_procedure_step_sequence tests ---
  def test_try_update_scheduled_procedure_step_sequence(self):
    # Construct required ScheduledProcedureStepSequence
    test_seq_data = Dataset()

    modality = 'OT'
    sch_descp = 'some description of the study'

    test_seq_data.add_new(0x00080060, 'CS', modality)  # ScheduledProcedureSteSequence[0].modality
    test_seq_data.add_new(0x00400007, 'LO', sch_descp) # ScheduledProcedureSteSequence[0].ScheduledProcedureStepDescription

    test_seq = Sequence([test_seq_data])

    self.ds.add_new(0x00400100, 'SQ', test_seq)

    # Attempt to update scheduled procedure step sequence
    dicomlib.try_update_scheduled_procedure_step_sequence(self.ds)

    # Assertion
    self.assertEqual(self.ds.Modality, modality)
    self.assertEqual(self.ds.StudyDescription, sch_descp)

  def test_try_update_scheduled_procedure_step_sequence_no_sequence(self):
    dicomlib.try_update_scheduled_procedure_step_sequence(self.ds)

    with self.assertRaises(AttributeError):
      self.ds.StudyDescription

    with self.assertRaises(AttributeError):
      self.ds.Modality


# --- try_add_exam_status tests ---
class ExamStatusTests(unittest.TestCase):
  def setUp(self):
    self.ds = Dataset()

  def test_add_exam_status(self):
    dicomlib.update_private_tags()

    self.ds.ExamStatus = 1

    dicomlib.try_add_exam_status(self.ds, 2)

    self.assertEqual(self.ds.ExamStatus, 2)

  def test_add_exam_status_no_exam_status(self):
    dicomlib.try_add_exam_status(self.ds, 0)

    with self.assertRaises(AttributeError):
      self.ds.ExamStatus

  def test_add_exam_status_equal(self):
    dicomlib.update_private_tags()

    self.ds.ExamStatus = 2

    dicomlib.try_add_exam_status(self.ds, 2)

    self.assertEqual(self.ds.ExamStatus, 2)

  def test_add_exam_status_lower(self):
    dicomlib.update_private_tags()

    self.ds.ExamStatus = 3

    dicomlib.try_add_exam_status(self.ds, 1)

    self.assertEqual(self.ds.ExamStatus, 3)

  def test_add_exam_status_none(self):
    dicomlib.update_private_tags()

    self.ds.ExamStatus = 3

    dicomlib.try_add_exam_status(self.ds, None)

    self.assertEqual(self.ds.ExamStatus, 3)


# --- try_add_age tests ---
class AgeTests(unittest.TestCase):
  def setUp(self):
    self.ds = Dataset()

  def test_tr_add_age_one(self):
    dicomlib.try_add_age(self.ds, 1)

    self.assertEqual(self.ds.PatientAge, '001')

  def test_tr_add_age_two(self):
    dicomlib.try_add_age(self.ds, 11)

    self.assertEqual(self.ds.PatientAge, '011')

  def test_tr_add_age_three(self):
    dicomlib.try_add_age(self.ds, 111)

    self.assertEqual(self.ds.PatientAge, '111')

  def test_tr_add_age_none(self):
    dicomlib.try_add_age(self.ds, None)

    with self.assertRaises(AttributeError):
      self.ds.PatientAge


# --- try_add_gender tests ---
class GenderTests(unittest.TestCase):
  def setUp(self):
    self.ds = Dataset()

  def test_try_add_gender_male(self):
    dicomlib.try_add_gender(self.ds, enums.Gender(0))

    self.assertEqual(self.ds.PatientSex, 'M')

  def test_try_add_gender_female(self):
    dicomlib.try_add_gender(self.ds, enums.Gender(1))

    self.assertEqual(self.ds.PatientSex, 'F')

  def test_try_add_gender_none(self):
    dicomlib.try_add_gender(self.ds, None)

    self.assertEqual('PatientSex' in self.ds, False)


# --- try_add_sample_sequence tests ---
class SampleTests(unittest.TestCase):
  def setUp(self):
    self.ds = Dataset()

  def test_add_samples(self):
    now = datetime.now()
    samples = [(now, x * 0.1) for x in range(1, 6)]

    dicomlib.try_add_sample_sequence(self.ds, samples)

    for i, sample in enumerate(self.ds[0x00231020]):
      sample_date = sample[0x00231021].value
      sample_cnt = sample[0x00231022].value

      self.assertEqual(sample_date, now)
      self.assertAlmostEqual(sample_cnt, samples[i][1])

  def test_add_samples_cleartest(self):
    dicomlib.update_private_tags()

    # Add samples to ds
    now = datetime.now()
    samples = [(now, x * 0.1) for x in range(1, 6)]

    dicomlib.try_add_sample_sequence(self.ds, samples)
    
    for i, sample in enumerate(self.ds[0x00231020]):
      sample_date = sample[0x00231021].value
      sample_cnt = sample[0x00231022].value

      self.assertEqual(sample_date, now)
      self.assertAlmostEqual(sample_cnt, samples[i][1])

    # Try to add empty list of samples (i.e. remove the existing ones)
    empty_samples = [ ]

    dicomlib.try_add_sample_sequence(self.ds, empty_samples)

    # Assert that they where removed
    self.assertEqual('ClearTest' in self.ds, False)

  def test_add_samples_none(self):
    empty_samples = [ ]

    dicomlib.try_add_sample_sequence(self.ds, empty_samples)

    self.assertEqual('ClearTest' in self.ds, False)


# --- try_add_pixeldata tests ---
class PixelDataTests(unittest.TestCase):
  def setUp(self):
    self.ds = Dataset()

  def test_add_pixeldata(self):
    # NOTE: The following input data has been randomly picked, and doesn't
    # and doesn't represent an actual study that took place.
    pixeldata = clearance_math.generate_plot_text(
      weight = 90.0,
      height = 123.0,
      BSA = 1.838274248431286,
      clearance = -150.831722349846,
      clearance_norm = -141.94774250246337,
      kidney_function = 'Svært nedsat',
      day_of_birth = '1945-02-13',
      gender = 'Kvinde',
      rigs_nr = 'REGH14461234',
      cpr = '1111222233',
      method = 'En blodprøve, Voksen',
      name = 'TEST PERSON',
      history_age = [],
      history_clr_n = [],
      hosp_dir = 'TEST',
      hospital_name="Test Hospital",
      image_height = 10.8,
      image_width = 19.2,
      index_gfr = 312.3350170356323,
      injection_date = '12-Sep-2019',
      procedure_description = 'Clearance blodprøve 2. gang',
    )

    dicomlib.try_add_pixeldata(self.ds, pixeldata)

    # Reshape accordingly
    pixeldata = np.frombuffer(pixeldata, dtype=np.uint8)
    pixeldata = np.reshape(pixeldata, (1080, 1920, 3))
    pixeldata = np.reshape(pixeldata, (1920, 1080, 3))

    self.assertEqual(self.ds.SamplesPerPixel, 3)
    self.assertEqual(self.ds.PhotometricInterpretation, 'RGB')
    self.assertEqual(self.ds.PlanarConfiguration, 0)
    self.assertEqual(self.ds.Rows, 1080)
    self.assertEqual(self.ds.Columns, 1920)
    self.assertEqual(self.ds.BitsAllocated, 8)
    self.assertEqual(self.ds.BitsStored, 8)
    self.assertEqual(self.ds.HighBit, 7)
    self.assertEqual(self.ds.PixelRepresentation, 0)
    self.assertEqual(self.ds.PixelData, pixeldata.tobytes())
    self.assertEqual(self.ds.ImageComments, 'GFR summary, generated by GFR-calc')


  def test_add_pixeldata_none(self):
    dicomlib.try_add_pixeldata(self.ds, None)

    self.assertEqual('PixelData' in self.ds, False)


# --- fill_dicom tests ---
# I.e. integration test of all the above unit tests
class FillDicomTests(TestCase):
  def setUp(self):
    self.ds = Dataset()

  @classmethod
  def setUpTestData(self):
    # Set up data for the whole TestCase
    self.hospital = models.Hospital(id=1, name='test_name', short_name='tn', address='test_address')
    self.department = models.Department(id=1, name='test_department', hospital=self.hospital)

  def test_fill_dicom(self):
    # Everything is filled out or True
    dicomlib.update_private_tags()

    # Set Modality and ScheduledProcedureStepDescription in the ScheduledProcedureStepSequence    
    test_seq_data = Dataset()

    test_seq_data.add_new(0x00400007, 'LO', 'TEST DESCRIPTION') # ScheduledProcedureStepDescription
    test_seq_data.add_new(0x00080060, 'CS', 'OT')               # Modality

    test_seq = Sequence([test_seq_data])

    self.ds.add_new(0x00400100, 'SQ', test_seq)

    # NOTE: The following input data has been randomly picked, and doesn't
    # and doesn't represent an actual study that took place.
    PIXELDATA_BYTES_LEN = 6220800
    test_pixeldata = ''.join(['0' for _ in range(PIXELDATA_BYTES_LEN)]).encode()

    now = datetime.now()
    test_samples = [(now, i * 0.25) for i in range(10)]

    dicomlib.fill_dicom(
      ds                  = self.ds,
      age                 = 12,
      birthday            = '18880102',
      bsa_method          = 'Haycock',
      clearance           = 129.11,
      clearance_norm      = 100.23,
      cpr                 = '0808081232',
      department          = self.department,
      exam_status         = '0',
      gender              = enums.Gender(0),
      gfr                 = 'Normal',
      gfr_type            = 'En blodprøve, Voksen',
      height              = 1.43,
      injection_after     = 3.21,
      injection_before    = 5.43,
      injection_time      = '201908070946',
      injection_weight    = 1.23,
      name                = 'TEST PERSON TESTERSON',
      pixeldata           = test_pixeldata,
      ris_nr              = 'REGH12345678',
      sample_seq          = test_samples,
      # series_instance_uid = ,
      series_number       = '123',
      # sop_instance_uid    = ,
      station_name        = 'RH_EDTA',
      study_datetime        = '100102030809',
      std_cnt             = 12345,
      thiningfactor       = 54321,
      update_date         = True,
      update_dicom        = True,
      update_version      = True,
      weight              = 95.5
    )

    validation_dict = {
      # try_add_new tags
      0x00080050: 'REGH12345678',
      0x00100030: '18880102',
      0x00100020: '0808081232',
      0x00100010: 'TESTERSON^TEST^PERSON^^',
      0x00200011: 123,
      0x00081010: 'RH_EDTA',
      0x00101020: 1.43,
      0x00101030: 95.5,
      0x0008103E: 'Clearance En blodprøve, Voksen', 
      0x00231001: 'Normal', 
      0x00231002: server_config.SERVER_VERSION, 
      0x00231010: 'En blodprøve, Voksen',
      0x00231018: '201908070946',
      0x0023101A: 1.23,
      0x0023101B: 5.43,
      0x0023101C: 3.21, 
      0x00231011: 'Haycock', 
      0x00231012: 129.11,
      0x00231014: 100.23, 
      0x00231024: 12345, 
      0x00231028: 54321,
      # Pixel data tags
      0x00280002: 3, 
      0x00280004: 'RGB', 
      0x00280006: 0, 
      0x00280010: 1080, 
      0x00280011: 1920, 
      0x00280100: 8,
      0x00280101: 8, 
      0x00280102: 7, 
      0x00280103: 0, 
      0x7FE00010: test_pixeldata, 
      0x00204000: 'GFR summary, generated by GFR-calc',
      # Gender tags
      0x00100040: 'M',
      # Age tags,
      0x00101010: '012',
      # Exam status tags
      0x00231032: '0',
      # Study date tags
      0x00080020: '10010203',
      0x00080021: '10010203',
      0x00080030: '0809',
      0x00080031: '0809',
      # Department tags
      0x00080080: self.hospital.name, 
      0x00080081: self.hospital.address, 
      0x00081040: self.department.name,
      # Exam meta data tags
      0x00080064: 'SYN', 
      0x00230010: 'Clearance - Denmark - Region Hovedstaden',
      0x00080090: '', 
      0x00200010: 'GFR#12345678', 
      0x00200013: 1,
      0x00181020: f"{server_config.SERVER_NAME} - {server_config.SERVER_VERSION}",
      0x00080016: '1.2.840.10008.5.1.4.1.1.7',
      # Try Update Scheduled Procedure Step Sequence tags
      0x00081030: 'TEST DESCRIPTION',
      0x00080060: 'OT',
    }

    for tag, value in validation_dict.items():
      self.assertEqual(self.ds[tag].value, value)

    # Sample sequence tags
    for i, item in enumerate(self.ds[0x00231020]):
      self.assertEqual(item[0x00231021].value, test_samples[i][0])
      self.assertEqual(item[0x00231022].value, test_samples[i][1])

  def test_fill_dicom_none(self):
    dicomlib.update_private_tags()
    dicomlib.fill_dicom(ds=self.ds)

    # Everything is either None or False
    tags_to_check = [
      # try_add_new tags
      0x00080050, 0x00100030, 0x00100020, 0x00100010, 0x00200011, 0x00081010,
      0x00101020, 0x00101030, 0x0008103E, 0x00231001, 0x00231002, 0x00231010,
      0x00231018, 0x0023101A, 0x0023101B, 0x0023101C, 0x00231011, 0x00231012,
      0x00231014, 0x00231024, 0x00231028,
      # Pixel data tags
      0x00280002, 0x00280004, 0x00280006, 0x00280010, 0x00280011, 0x00280100,
      0x00280101, 0x00280102, 0x00280103, 0x7FE00010, 0x00204000,
      # Sample sequence tags
      0x00231020,
      # Gender tags
      0x00100040,
      # Age tags,
      0x00101010,
      # Exam status tags
      0x00231032,
      # Schedule procedure tags
      0x00400100,
      # Study date tags
      0x00080020, 0x00080021, 0x00080030, 0x00080031,
      # Department tags
      0x00080080, 0x00080081, 0x00081040,
      # Exam meta data tags
      0x00080064, 0x00230010, 0x00080030, 0x00080090, 0x00200010, 0x00200013,
      # Try Update Scheduled Procedure Step Sequence tags
      0x00400007, 0x00080060,
    ]

    for tag in tags_to_check:
      with self.assertRaises(KeyError):
        self.ds[tag]
