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
      formatting.format_date("")


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


  def test_format_cpr_special_case1(self):
    # This case failed in production
    expected = "2905500HM1"

    out = formatting.format_cpr("2905500HM1")

    self.assertEqual(out, expected)


  """
  Test person name to name
  
  The tests are mainly based on the examples at:
  http://dicom.nema.org/dicom/2013/output/chtml/part05/sect_6.2.html#sect_6.2.1.1
  """
  def test_person_name_no_middlename_two_suffix(self):
    expected = "Rev. John Robert Quincy Adams, B.A. M.Div."

    out = formatting.person_name_to_name("Adams^John Robert Quincy^^Rev.^B.A. M.Div.")

    self.assertEqual(out, expected)


  def test_person_name_one_given_name(self):
    expected = "Susan Morrison-Jones, Ph.D., Chief Executive Officer"

    out = formatting.person_name_to_name("Morrison-Jones^Susan^^^Ph.D., Chief Executive Officer")

    self.assertEqual(out, expected)


  def test_person_name_one_given_family(self):
    expected = "John Doe"

    out = formatting.person_name_to_name("Doe^John")

    self.assertEqual(out, expected)


  def test_person_name_full(self):
    expected = "Rev. John Robert Quincy Someoneson Adams, B.A. M.Div."

    out = formatting.person_name_to_name("Adams^John Robert Quincy^Someoneson^Rev.^B.A. M.Div.")

    self.assertEqual(out, expected)
    

  def test_person_name_empty(self):
    expected = ""

    out = formatting.person_name_to_name("^")

    self.assertEqual(out, expected)


  def test_person_name_wildcard(self):
    with self.assertRaises(ValueError):
      formatting.person_name_to_name('*')


  def test_person_name_cat(self):
    expected = "Fluffy Smith"

    out = formatting.person_name_to_name("Smith^Fluffy")

    self.assertEqual(out, expected)
    
  
  def test_person_name_horse(self):
    expected = "Running on Water ABC Farms"

    out = formatting.person_name_to_name("ABC Farms^Running on Water")

    self.assertEqual(out, expected)


  """Test name to person name"""
  def test_name_empty(self):
    expected = ''

    out = formatting.name_to_person_name('')

    self.assertEqual(out, expected)


  def test_name_no_middlename(self):
    expected = 'someoneson^someone^^^'

    out = formatting.name_to_person_name('someone someoneson')

    self.assertEqual(out, expected)


  def test_name_middlenames(self):
    expected = 'someoneson^someone^1 2 3^^'

    out = formatting.name_to_person_name('someone 1 2 3 someoneson')

    self.assertEqual(out, expected)

######## ---------------- Test of function reverse_format_date --------------- ########
# Success full tests
def test_reverse_format_date_no_extra_characters(self):
  function_input = '20111993'

  expected_output = '19931120'

  function_output = formatting.reverse_format_date(function_input) 

  self.assertEqual(expected_output, function_input)

def test_reverse_format_date_slash_characters(self):
  function_input = '20/11/1993'

  expected_output = '19931120'

  function_output = formatting.reverse_format_date(function_input) 

  self.assertEqual(expected_output, function_input)

def test_reverse_format_date_dash_characters(self):
  function_input = '20-11-1993'

  expected_output = '19931120'

  function_output = formatting.reverse_format_date(function_input) 

  self.assertEqual(expected_output, function_input)
# ### Check for leap year
def test_reverse_format_date_leap_year(self):
  function_input = '29021992'

  expected_output = '19920229'

  function_output = formatting.reverse_format_date(function_input) 

  self.assertEqual(expected_output, function_input)

def test_reverse_format_date_leap_year_special_rule_2(self):
  function_input = '29022000'

  expected_output = '20000229'

  function_output = formatting.reverse_format_date(function_input) 

  self.assertEqual(expected_output, function_input)

# Error Tests

# ### Invalid dates years
def test_reverse_format_date_invalid_date_no_extra_characters(self):
  function_input = '32112000'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)


def test_reverse_format_date_invalid_date_dash_characters(self):
  function_input = '32-11-2000'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_invalid_date_dash_characters(self):
  function_input = '32/11/2000'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_not_leap_year(self):
  function_input = '29022019'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)
  
def test_reverse_format_date_leap_year_special_rule_1(self):
  function_input = '29022100'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

# ### Typoes / formatting
def test_reverse_format_date_len_too_long_error(self):
  function_input = '290221100'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_len_too_short_error(self):
  function_input = '2902211'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)


def test_reverse_format_date_character(self):
  function_input = '2a022110'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_stupid_format(self):
  function_input = '12312000'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_spaces_format(self):
  function_input = '31 12 2000'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)


def test_reverse_format_date_backslash_format(self):
  function_input = '31\\12\\2000'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_backslash_format(self):
  function_input = '31.12.2000'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_6_digit_format(self):
  function_input = '311200'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_6_digit_slash_format(self):
  function_input = '31/12/00'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_6_digit_dash_format(self):
  function_input = '31-12-00'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_month_name_format(self):
  function_input = '31-Dec-2000'

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_no_leading_zero(self):
  function_input = '112000' #01012000

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_no_leading_dashes_zero(self):
  function_input = '1-1-2000' #01-01-2000

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_no_leading_slashes_zero(self):
  function_input = '1/1/2000' #01/01/2000

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_inconsistance_seperators_1(self):
  function_input = '01/01-2000' #01012000

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)

def test_reverse_format_date_inconsistance_seperators_2(self):
  function_input = '01-01/2000' #01012000

  with self.assertRaises(ValueError):
    formatting.reverse_format_date(function_input)




# Production test
# If a test case comes up in production put it in here

# End testing for reverse_format_date