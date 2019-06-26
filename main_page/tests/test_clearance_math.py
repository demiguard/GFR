from django.test import TestCase

from main_page.libs.clearance_math import clearance_math

class ClearanceMathTestCase(TestCase):
  def setUp(self):
    pass


  def test_age_converter_for_cpr_2011932625(self):
    pass

  def test_age_converter_for_cpr_030607Dash5136(self):
    #Failed in Production
    functioninput = '030607-5136'
    
    expected = 12
     
    out = clearance_math.calculate_age(functioninput)

    self.assertEqual(out,expected)

  def test_age_converter_for_cpr_0306075136(self):
    #Failed in Production
    functioninput = '0306075136'
    
    expected = 12
     
    out = clearance_math.calculate_age(functioninput)

    self.assertEqual(out,expected)

