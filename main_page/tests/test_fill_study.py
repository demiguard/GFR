"""
THIS TEST FILE REQUIRES DRIVERS FOR EACH BROWSER TYPE TO BE INSTALLED
AND LOCATED UNDER THE ./main_page/tests/selenium_drivers/ DIRECTORY.
THE DRIVERS CAN BE DOWNLOADED FROM:
https://github.com/SeleniumHQ/selenium/blob/master/py/docs/source/index.rst
"""

from django.test import LiveServerTestCase
from django.conf import settings

from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebDriver
from selenium.webdriver.firefox import options as FirefoxOptions

import datetime
import shutil
import os
from pydicom import Dataset, Sequence

from main_page import models
from main_page.libs import server_config
from main_page.libs.dirmanager import try_mkdir
from main_page.libs import dicomlib
from main_page.libs import dataset_creator


# --- FillStudyView ---
class FillStudyFullTests(LiveServerTestCase):
  """
  Tests the FillStudyView through Firefox using Selenium, 
  i.e. tests which perform automated manual tests
  """
  fixtures = ['test_user.json']

  @classmethod
  def setUpClass(cls):
    # Construct Selenium Firefox driver
    super().setUpClass()

    DRIVER_PATH = "./main_page/tests/selenium_drivers/geckodriver-0-24-0-x64"
    options = FirefoxOptions.Options()
    options.headless = False

    cls.driver = FirefoxWebDriver(
      executable_path=DRIVER_PATH,
      options=options
    )
    
    # Set the implict wait time (https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webdriver.html?highlight=wait#selenium.webdriver.remote.webdriver.WebDriver.implicitly_wait)
    cls.driver.implicitly_wait(10)
    cls.is_logged_in = False

    # Enable debugging mode for all tests
    settings.DEBUG = True

  @classmethod
  def tearDownClass(cls):
    # Correctly close and deallocated driver resources once test is done
    cls.driver.quit()

    super().tearDownClass()
    pass

  def setUp(self):
    self.test_hospital = models.Hospital.objects.get(pk=1)

    # Login to the site or go to the fill_study page if already logged in
    if not self.is_logged_in:
      self.driver.get(self.live_server_url)
      username_field = self.driver.find_element_by_id('id_username')
      username_field.send_keys("test_user")

      password_field = self.driver.find_element_by_id('id_password')
      password_field.send_keys("test_user")

      login_btn = self.driver.find_element_by_id('login-btn')
      login_btn.click()

      # Ensure correct login
      list_studies_table = self.driver.find_element_by_id('new_studies')
      self.assertEqual(list_studies_table != None, True)

      self.assertEqual(self.driver.current_url, f"{self.live_server_url}/list_studies")

      self.is_logged_in = True
    else:
      pass

  def tearDown(self):
    # Remove generated dicom objects
    # os.remove(self.test_filepath)
    # os.rmdir(f"{server_config.FIND_RESPONS_DIR}{self.test_hospital.short_name}/{self.accession_number}")
    # os.rmdir(f"{server_config.FIND_RESPONS_DIR}{self.test_hospital.short_name}")
    shutil.rmtree(f"{server_config.FIND_RESPONS_DIR}{self.test_hospital.short_name}", ignore_errors=True)

    # Remove any generated images
    shutil.rmtree(f"{server_config.STATIC_DIR}images/UNIT_TEST", ignore_errors=True)

  def test_full_study_calculate(self):
    """
    Run a full study through the /fill_study/<RIS_NR> page

    Dependencies:
      File placement and location of generated files

    Asserts after completion of study (click on beregn):
      The existance of required fields in the corresponding dicom object
      The existance of a generated study image on disk
    """
    # Create testing directory and corresponding dicom datasets and files
    hosp_dir = f"{server_config.FIND_RESPONS_DIR}{self.test_hospital.short_name}"

    cpr = "1206830057"
    name = "test person testerson"
    study_date = datetime.date.today().strftime('%Y-%m-%d')
    accession_number = "REGH12345678"
    hospital_aet = ""

    obj_dir  = f"{hosp_dir}/{accession_number}"
    try_mkdir(obj_dir, mk_parents=True)

    ds = dataset_creator.get_blank(
      cpr,
      name,
      study_date,
      accession_number,
      hospital_aet
    )

    test_filepath = f"{obj_dir}/{accession_number}.dcm"

    dicomlib.save_dicom(
      test_filepath,
      ds
    )

    self.driver.refresh()

    # Click on first table entry - goto fill_study page
    first_table_item = self.driver.find_element_by_css_selector("#new_studies tbody tr:first-child td:first-child")
    first_table_item.click()

    # Fill out each field in study
    field_val_dict = {
      'height': '178',
      'weight': '60',
      'vial_weight_before': '5,2020',
      'vial_weight_after': '3,5100',
      'injection_date': '02-08-2017',
      'injection_time': '10:50',
      'thin_fac': '1242',
      'standcount': '4569',
      'study_date': '02-08-2017',
      'study_time': '14:10',
    }
    
    for field_name, value in field_val_dict.items():
      field = self.driver.find_element_by_name(field_name)
      field.clear()
      field.send_keys(value)

    # Add empty test - click somewhere else on the page before to remove focus from the datepickers
    save_thin_fac_check = self.driver.find_element_by_id("id_thin_fac")
    save_thin_fac_check.click()

    add_empty_btn = self.driver.find_element_by_id("add-empty-value")
    add_empty_btn.click()

    # Unlock test values and fill in test count
    lock_btn = self.driver.find_element_by_id("lock0")
    lock_btn.click()

    count_field = self.driver.find_element_by_name("sample_value")
    count_field.clear()
    count_field.send_keys("175")

    # Fill in "testtest" as the bamid
    bam_id_field = self.driver.find_element_by_id("id_bamID")
    bam_id_field.send_keys("testtest")

    # Click calculate
    calculate_btn = self.driver.find_element_by_id("calculate")
    calculate_btn.click()

    # Assert dicom object fields
    self.assertEqual(os.path.exists(test_filepath), True)
    ds = dicomlib.dcmread_wrapper(test_filepath)
    
    tag_dict = {
      0x00080005: ('CS', 'ISO_IR 100'),
      0x00080016: ('UI', '1.2.840.10008.5.1.4.1.1.7'),
      0x00080018: ('UI', '1.3.110991891537808377320710161154227944576338148545133209878678'),
      0x00080050: ('SH', 'REGH12345678'),
      0x00080060: ('CS', 'OT'),
      0x00080064: ('CS', 'SYN'),
      0x00080090: ('PN', ''),
      0x00081030: ('LO', 'GFR, Tc-99m-DTPA'),
      0x0008103e: ('LO', 'Clearance En blodprøve, Voksen'),
      0x00100010: ('PN', 'testerson^test^person^^'),
      0x00100020: ('LO', '1206830057'),
      0x00100030: ('DA', '19830612'),
      0x00100040: ('CS', 'M'),
      0x00101010: ('AS', '036'),
      0x00101020: ('DS', 1.78),
      0x00101030: ('DS', 60.0),
      0x00181020: ('LO', f"{server_config.SERVER_NAME} - {server_config.SERVER_VERSION}"),
      0x0020000d: ('UI', '1.3.114945357800429515625009469064908297373491801971184852245298'),
      0x0020000e: ('UI', '1.3.189436844292697631030767924811106592584694046171693622243254'),
      0x00200010: ('SH', 'GFR#12345678'),
      0x00200011: ('IS', 1),
      0x00200013: ('IS', 1),
      0x00204000: ('LT', 'GFR summary, generated by GFR-calc'),
      0x00230010: ('LO', 'Clearance - Denmark - Region Hovedstaden'),
      0x00231001: ('LO', 'Normal'),
      0x00231010: ('LO', 'En blodprøve, Voksen'),
      0x00231011: ('LO', 'Haycock'),
      0x00231012: ('DS', 88.51776585348101),
      0x00231014: ('DS', 89.48289374842932),
      0x00231018: ('DT', '201708021050'),
      0x0023101a: ('DS', 1.6920000000000002),
      0x0023101b: ('DS', 5.202),
      0x0023101c: ('DS', 3.51),
      0x00231024: ('DS', 4569.0),
      0x00231028: ('DS', 1242.0),
      0x00231032: ('US', 2),
      0x00280002: ('US', 3),
      0x00280004: ('CS', 'RGB'),
      0x00280006: ('US', 0),
      0x00280010: ('US', 1080),
      0x00280011: ('US', 1920),
      0x00280100: ('US', 8),
      0x00280101: ('US', 8),
      0x00280102: ('US', 7),
      0x00280103: ('US', 0),
      0x0032000a: ('CS', 'STARTED'),
      0x00321060: ('LO', 'GFR, Tc-99m-DTPA'),
    }
    
    for tag, value_tuple in tag_dict.items():
      VR, value = value_tuple
      
      self.assertEqual(ds[tag].VR, VR)
      self.assertEqual(ds[tag].value, value)

    # Pixel data
    self.assertEqual(ds[0x7fe00010].VR, 'OW')
    self.assertEqual(len(ds[0x7fe00010].value), 6220800)
    self.assertEqual(type(ds[0x7fe00010].value), bytes)

    # Scheduled Procedure Step Sequence
    self.assertEqual(ds[0x00400100].VR, 'SQ')
    self.assertEqual(len(ds[0x00400100].value), 1)
    
    self.assertEqual(ds[0x00400100][0][0x00080060].VR, 'CS')
    self.assertEqual(ds[0x00400100][0][0x00080060].value, 'OT')

    self.assertEqual(ds[0x00400100][0][0x00400001].VR, 'AE')
    self.assertEqual(ds[0x00400100][0][0x00400001].value, '')

    self.assertEqual(ds[0x00400100][0][0x00400007].VR, 'LO')
    self.assertEqual(ds[0x00400100][0][0x00400007].value, 'GFR, Tc-99m-DTPA')

    self.assertEqual(ds[0x00400100][0][0x00400010].VR, 'SH')
    self.assertEqual(ds[0x00400100][0][0x00400010].value, '')

    # Sample Sequence
    self.assertEqual(ds[0x00231020].VR, 'SQ')
    self.assertEqual(len(ds[0x00231020].value), 1)

    self.assertEqual(ds[0x00231020][0][0x00231021].VR, 'DT')
    self.assertEqual(ds[0x00231020][0][0x00231021].value, '201708021410')

    self.assertEqual(ds[0x00231020][0][0x00231022].VR, 'DS')
    self.assertEqual(ds[0x00231020][0][0x00231022].value, 175.0)

    # Ensure that an image was generated
    generated_image_path = f"{server_config.STATIC_DIR}images/UNIT_TEST/{accession_number}.png"
    self.assertEqual(os.path.exists(generated_image_path), True)

  def test_loading_saved_study(self):
    # Create dicom object to load
    hosp_dir = f"{server_config.FIND_RESPONS_DIR}{self.test_hospital.short_name}"

    cpr = "0101010101"
    name = "test test test"
    study_date = "2020-01-06"
    accession_number = "REGH87654321"
    hospital_aet = ""

    obj_dir  = f"{hosp_dir}/{accession_number}"
    try_mkdir(obj_dir, mk_parents=True)

    ds = dataset_creator.get_blank(
      cpr,
      name,
      study_date,
      accession_number,
      hospital_aet
    )

    test_filepath = f"{obj_dir}/{accession_number}.dcm"

    ds.add_new(0x00100030, "DA", "19470412")          # PatientBirthDate
    ds.add_new(0x00100040, "CS", "F")                 # PatientSex
    ds.add_new(0x00101010, "AS", "072")               # PatientAge
    ds.add_new(0x00101020, "DS", "1.7")               # PatientSize
    ds.add_new(0x00101030, "DS", "70.0")              # PatientWeight
    ds.add_new(0x0023101B, "DS", "4.142")             # injbefore
    ds.add_new(0x0023101C, "DS", "3.141")             # injafter
    ds.add_new(0x00231018, "DT", "202001060808")      # injTime
    ds.add_new(0x00231028, "DS", "8000.88")           # thiningfactor
    ds.add_new(0x00231024, "DS", "35001.13")          # stdcnt
    ds.add_new(0x00231010, "LO", "Flere blodprøver")  # BSAmethod

    # Insert two samples
    sample_ds1 = Dataset()
    sample_ds1.add_new(0x00231021, "DT", "202001061010")
    sample_ds1.add_new(0x00231022, "DS", "888.88")

    sample_ds2 = Dataset()
    sample_ds2.add_new(0x00231021, "DT", "202001061212")
    sample_ds2.add_new(0x00231022, "DS", "1777.76")

    sample_seq = Sequence([sample_ds1, sample_ds2])

    ds.add_new(0x00231020, 'SQ', sample_seq)

    dicomlib.save_dicom(
      test_filepath,
      ds
    )

    # Ensure that the dicom object was loaded and displayed correctly on the site 
    self.driver.refresh()

    # Click on first table entry - goto fill_study page
    first_table_item = self.driver.find_element_by_css_selector("#new_studies tbody tr:first-child td:first-child")
    first_table_item.click()

    cpr_value = self.driver.find_element_by_id("id_cpr").get_attribute("value")
    name_value = self.driver.find_element_by_id("id_name").get_attribute("value")
    sex_value = self.driver.find_element_by_id("id_sex").get_attribute("value")
    birthdate_value = self.driver.find_element_by_id("id_birthdate").get_attribute("value")
    height_value = self.driver.find_element_by_id("id_height").get_attribute("value")
    weight_value = self.driver.find_element_by_id("id_weight").get_attribute("value")
    vial_before_value = self.driver.find_element_by_id("id_vial_weight_before").get_attribute("value")
    vial_after_value = self.driver.find_element_by_id("id_vial_weight_after").get_attribute("value")
    inj_time_value = self.driver.find_element_by_id("id_injection_time").get_attribute("value")
    inj_date_value = self.driver.find_element_by_id("id_injection_date").get_attribute("value")
    thin_fac_value = self.driver.find_element_by_id("id_thin_fac").get_attribute("value")
    stdcnt_value = self.driver.find_element_by_id("id_standcount").get_attribute("value")

    study_type_value = self.driver.find_elements_by_css_selector("#id_study_type input[type=radio]:checked")[0].get_attribute("value")
    
    sample_container = self.driver.find_element_by_id("test-data-container")
    sample_rows = sample_container.find_elements_by_class_name("form-row")

    samples = [ ]
    for sample_row in sample_rows:
      date = sample_row.find_element_by_name("sample_date").get_attribute("value")
      time = sample_row.find_element_by_name("sample_time").get_attribute("value")
      cnt  = sample_row.find_element_by_name("sample_value").get_attribute("value")

      samples.append((date, time, cnt))

    self.assertEqual(cpr_value, "0101010101")
    self.assertEqual(name_value, "test test test")
    self.assertEqual(sex_value, '1')
    self.assertEqual(birthdate_value, "12-04-1947")
    self.assertEqual(height_value, "170")
    self.assertEqual(weight_value, "70")
    self.assertEqual(vial_before_value, "4,142")
    self.assertEqual(vial_after_value, "3,141")
    self.assertEqual(inj_time_value, "08:08")
    self.assertEqual(inj_date_value, "06-01-2020")
    self.assertEqual(thin_fac_value, "8000")
    self.assertEqual(stdcnt_value, "35001")
    self.assertEqual(study_type_value, '2')
    
    expected_samples = [
      ('06-01-2020', '10:10', '888'), 
      ('06-01-2020', '12:12', '1777')
    ]

    for i, exp_sample in enumerate(expected_samples):
      self.assertEqual(samples[i][0], exp_sample[0]) # Date
      self.assertEqual(samples[i][1], exp_sample[1]) # Time
      self.assertEqual(samples[i][2], exp_sample[2]) # Count

  # def test_partial_study_calculate(self):
  #   # This should assert that (together with other similar tests) that the correct
  #   # errors are prompted if trying to calculate a partially filled out study
  #   pass

  # def test_full_study_save(self):
  #   # Ensure that studies are saved correctly in dicom objects for a full study
  #   pass

  # def test_partial_study_save(self):
  #   # Ensure that partially filled out studies are correctly save in dicom objects 
  #   # (Should be split over multiple tests for each field on the page)
  #   pass
