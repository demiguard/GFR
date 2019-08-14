"""
THIS TEST FILE REQUIRES DRIVERS FOR EACH BROWER TYPE TO BE INSTALLED
AND LOCATED UNDER THE ./main_page/tests/selenium_drivers/ DIRECTORY.
THE DRIVERS CAN BE DOWNLOADED FROM:
https://github.com/SeleniumHQ/selenium/blob/master/py/docs/source/index.rst
"""

from django.test import LiveServerTestCase
from django.conf import settings

from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebDriver
from selenium.webdriver.firefox import options as FirefoxOptions

from main_page import models


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

  def setUp(self):
    settings.DEBUG = True

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

  @classmethod
  def setUpTestData(cls):
    # Ensure that a mock examination file ('from' RIS) is available in the ./active_dicom_objects/TH directory
    # Ensure that a test_user is created and propperly configured (NOTE: don't allow PACS access)
    # Ensure that a study (dicom object) is a available for the test
    # Ensure that a sample file is available on the Samba Share
    # cls.user_group = models.UserGroup.objects.create(id=1, name='user')
    # cls.user_group.save()

    # cls.hospital = models.Hospital.objects.create(id=1, name="test_hospital", short_name="TH")
    # cls.hospital.save()

    # cls.config = models.Config.objects.create(id=1)
    # cls.config.save()

    # cls.department = models.Department.objects.create(id=1, name="test_department", hospital=cls.hospital, config=cls.config)
    # cls.department.save()

    # cls.user = models.User.objects.create(id=1, username='test_user', department=cls.department, user_group=cls.user_group)
    # cls.user.set_password('test_user')
    # cls.user.save()
    pass


  @classmethod
  def tearDownClass(cls):
    # Correctly close and deallocated driver resources once test is done
    cls.driver.quit()
    super().tearDownClass()

  def test_full_study_calculate(self):
    """
    Run a full study through the /fill_study/<RIS_NR page

    Dependencies:
      A sample file located on the Samba Share named: /data/backup/TEST
      (asserts the existance of such a file before performing the test.
      TODO: possibly create this file in the setUpTestData classmethod?...)
      (asserts that the user and user group are both set to "nobody" on the file)

      File placement and location of generated files (TODO: Mock this somehow...)

    Asserts after completion of study (click on beregn):
      The existance of required fields in the corresponding dicom object
      The existance of a generated study image on disk
      That HandledExaminations is updated correctly after the study has successfully completed
    """
    pass

  def test_partial_study_calculate(self):
    # This should assert that (together with other similar tests) that the correct
    # errors are prompted if trying to calculate a partially filled out study
    pass

  def test_full_study_save(self):
    # Ensure that studies are saved correctly in dicom objects for a full study
    pass

  def test_partial_study_save(self):
    # Ensure that partially filled out studies are correctly save in dicom objects 
    # (Should be split over multiple tests for each field on the page)
    pass

  
  # Example code from the Django doc. page: https://docs.djangoproject.com/en/2.2/topics/testing/tools/
  # def test_login(self):
  #   self.selenium.get('%s%s' % (self.live_server_url, '/login/'))
  #   username_input = self.selenium.find_element_by_name("username")
  #   username_input.send_keys('myuser')
  #   password_input = self.selenium.find_element_by_name("password")
  #   password_input.send_keys('secret')
  #   self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()