from django.test import TestCase

import main_page.libs.formatting as formatting


class LibsFormattingTestCase(TestCase):
  def setUp(self):
    pass

  """Test formatting of dicom dates"""
  def test_format_date(self):
    expected = "01/01-2019"
    
    out = formatting.format_date("20190101")
    
    self.assertEqual(out, expected)


  """Test formatting of cpr numbers"""
  def test_format_cpr(self):
    expected = "010101-0101"

    out = formatting.format_cpr("0101010101")

    self.assertEqual(out, expected)


  def test_format_cpr_non_numeric(self):
    expected = "QP-3859995"

    out = formatting.format_cpr("QP-3859995")

    self.assertEqual(out, expected)


  def test_format_cpr_with_dash(self):
    expected = "010101-0101"

    out = formatting.format_cpr("010101-0101")

    self.assertEqual(out, expected)