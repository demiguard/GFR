from django.test import TestCase
import unittest

from datetime import datetime

from main_page.libs.clearance_math import clearance_math
from main_page.libs import enums


class ClearanceMathTestCase(TestCase):
  def setUp(self):
    pass


  def test_age_converter_for_cpr_2011932625(self):
    pass

  def test_age_converter_for_cpr_030607dash5136(self):
    #Failed in Production
    functioninput = '030607-5136'
    #Preprocessing
    birthday = datetime(2007,6,3)
    now = datetime.now()
    expected = int((now - birthday).days / 365)
    #Test
    out = clearance_math.calculate_age(functioninput)

    self.assertEqual(out,expected)

  def test_age_converter_for_cpr_0306075136(self):
    # Failed in Production
    functioninput = '0306075136'
    # Preprocessing
    birthday = datetime(2007,6,3)
    now = datetime.now()
    expected = int((now - birthday).days / 365)
    # Test
    out = clearance_math.calculate_age(functioninput)

    self.assertEqual(out,expected)


  def test_calculate_birthday_valid(self):
    functioninput = '0606500149'

    expected = '1950-06-06'
    # Test
    self.assertEqual(expected, clearance_math.calculate_birthdate(functioninput))


class TestKidneyFunction(unittest.TestCase):
  def test_kidney_function_production_fail_1(self):
    """
    This test showcases a test of an old patient from 2017 from production at 
    Glostrup which reported a kidney function of "Moderat nedsat" in the side
    description when the corresponding graph showed a kidney function of "Normal"
    """
    clearance_norm = 73.6
    birthdate = "1952-10-21"
    gender = enums.Gender.MALE

    res_text, _ = clearance_math.kidney_function(clearance_norm, birthdate, gender)

    self.assertEqual(res_text, 'Normal')
