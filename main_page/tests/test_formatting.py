from django.test import TestCase

import main_page.libs.formatting as formatting


class LibsFormattingTestCase(TestCase):
  def setUp(self):
    pass

  """Test formatting of dates"""
  def test_format_date(self):
    expected = "01/01-2019"
    
    out = formatting.format_date("20190101")
    
    self.assertEqual(out, expected)


  def test_format_date_short(self):
    with self.assertRaises(ValueError):
      formatting.format_date("1234")


  def test_format_date_long(self):
    with self.assertRaises(ValueError):
      formatting.format_date("123456789")
    

  def test_format_characters(self):
    with self.assertRaises(ValueError):
      formatting.format_date("something which should throw an exception")


  """Test formatting of cpr numbers"""
  def test_format_cpr(self):
    expected = "010101-0101"

    out = formatting.format_cpr("0101010101")

    self.assertEqual(out, expected)


  def test_format_cpr_non_numeric(self):
    expected = "QP-3859995"

    out = formatting.format_cpr("QP-3859995")

    self.assertEqual(out, expected)


  def test_format_cpr_single_dash(self):
    with self.assertRaises(ValueError):
      formatting.format_cpr("-")


  def test_format_cpr_with_dash(self):
    expected = "010101-0101"

    out = formatting.format_cpr("010101-0101")

    self.assertEqual(out, expected)


  def test_format_cpr_with_multiple_dash(self):
    with self.assertRaises(ValueError):
      formatting.format_cpr("010101--0101")


  def test_format_cpr_with_dash_wrong_idx(self):
    with self.assertRaises(ValueError):
      formatting.format_cpr("01-01010101")


  def test_format_cpr_special_chars(self):
    with self.assertRaises(ValueError):
      formatting.format_cpr("$!?/¤%#¤")


  def test_format_cpr_empty(self):
    with self.assertRaises(ValueError):
      formatting.format_cpr("")
