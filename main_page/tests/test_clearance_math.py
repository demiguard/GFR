from django.test import TestCase
from main_page.libs.clearance_math import clearance_math
from datetime import datetime

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
    #Failed in Production
    functioninput = '0306075136'
    #Preprocessing
    birthday = datetime(2007,6,3)
    now = datetime.now()
    expected = int((now - birthday).days / 365)
    #Test
    out = clearance_math.calculate_age(functioninput)

    self.assertEqual(out,expected)

