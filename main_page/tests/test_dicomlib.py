from django.test import TestCase
import unittest

from pydicom import Dataset, Sequence, uid
from datetime import datetime
import numpy as np

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
      (0x00080030, ''),
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
    study_date = '1111-11-11'
    dicomlib.try_update_study_date(self.ds, True, study_date)

    # Assert that everything was set correctly
    expected_study_date = '11111111'
    expected_study_time = datetime.now().strftime('%H%M')

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
    study_date = '1111-11-11'
    dicomlib.try_update_study_date(self.ds, True, study_date)

    # Assert that everything was set correctly
    expected_study_date = '11111111'
    expected_study_time = datetime.now().strftime('%H%M')

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
    pixeldata = clearance_math.generate_plot_text(
      weight = 90.0,
      height = 123.0,
      BSA = 1.838274248431286,
      clearance = -150.831722349846,
      clearance_norm = -141.94774250246337,
      kidney_function = 'Svært nedsat',
      day_of_birth = '1945-02-13',
      sex = 'Kvinde',
      rigs_nr = 'REGH14467067',
      cpr = '1111222233',
      method = 'En blodprøve, Voksen',
      name = 'TEST PERSON',
      history_age = [],
      history_clr_n = [],
      hosp_dir = 'TEST',
      image_height = 10.8,
      image_width = 19.2,
      index_gfr = 312.3350170356323,
      injection_date = '05-Aug-2019',
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
    pass

  def test_fill_dicom_none(self):
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
    ]

    for tag in tags_to_check:
      with self.assertRaises(KeyError):
        self.ds[tag]
