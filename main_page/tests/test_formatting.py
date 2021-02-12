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

######## ---------------- Test of function convert_date_to_danish_date --------------- ########
# Success full tests
  def test_convert_date_to_danish_date_no_extra_characters(self):
    function_input = '19931120'

    expected_output = '20111993'
    
    function_output = formatting.convert_date_to_danish_date(function_input) 

    self.assertEqual(expected_output, function_output)

  def test_convert_date_to_danish_date_slash_characters(self):
    function_input = '1993/11/20'

    expected_output = '20111993'

    function_output = formatting.convert_date_to_danish_date(function_input) 

    self.assertEqual(expected_output, function_output)

  def test_convert_date_to_danish_date_dash_characters(self):
    function_input = '1993-11-20'

    expected_output = '20111993'

    function_output = formatting.convert_date_to_danish_date(function_input) 

    self.assertEqual(expected_output, function_output)
  # ### Check for leap year
  def test_convert_date_to_danish_date_leap_year(self):
    function_input = '19920229'

    expected_output = '29021992'

    function_output = formatting.convert_date_to_danish_date(function_input) 

    self.assertEqual(expected_output, function_output)

  def test_convert_date_to_danish_date_leap_year_special_rule_2(self):
    function_input = '20000229'

    expected_output = '29022000'

    function_output = formatting.convert_date_to_danish_date(function_input) 

    self.assertEqual(expected_output, function_output)

  # Error Tests

  # ### Invalid dates years
  def test_convert_date_to_danish_date_invalid_date_no_extra_characters(self):
    function_input = '32112000'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)


  def test_convert_date_to_danish_date_invalid_date_dash_characters(self):
    function_input = '32-11-2000'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_invalid_date_backslash_characters(self):
    function_input = '32/11/2000'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_not_leap_year(self):
    function_input = '29022019'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_leap_year_special_rule_1(self):
    function_input = '29022100'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  # ### Typoes / formatting
  def test_convert_date_to_danish_date_len_too_long_error(self):
    function_input = '290221100'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_len_too_short_error(self):
    function_input = '2902211'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)


  def test_convert_date_to_danish_date_character(self):
    function_input = '2a022110'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_stupid_format(self):
    function_input = '12312000'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_spaces_format(self):
    function_input = '31 12 2000'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)


  def test_convert_date_to_danish_date_backslash_format(self):
    function_input = '31\\12\\2000'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_dot_format(self):
    function_input = '31.12.2000'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_6_digit_format(self):
    function_input = '311200'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_6_digit_slash_format(self):
    function_input = '31/12/00'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_6_digit_dash_format(self):
    function_input = '31-12-00'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_month_name_format(self):
    function_input = '31-Dec-2000'

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_no_leading_zero(self):
    function_input = '112000' #01012000

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_no_leading_dashes_zero(self):
    function_input = '1-1-2000' #01-01-2000

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_no_leading_slashes_zero(self):
    function_input = '1/1/2000' #01/01/2000

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_inconsistance_seperators_1(self):
    function_input = '01/01-2000' #01012000

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  def test_convert_date_to_danish_date_inconsistance_seperators_2(self):
    function_input = '01-01/2000' #01012000

    with self.assertRaises(ValueError):
      formatting.convert_date_to_danish_date(function_input)

  # Production test
  # If a test case comes up in production put it in here

  # End testing for convert_date_to_danish_date

  """Test check cpr"""
  def test_check_cpr_no_dash(self):
    function_input = '1212960000'

    expected_output = None

    function_output = formatting.check_cpr(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_cpr_with_dash(self):
    function_input = '121296-0000'

    expected_output = None

    function_output = formatting.check_cpr(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_cpr_no_dash_len_too_short_error(self):
    function_input = '121295000'

    expected_output = "Forkert formattering af cpr nr."

    function_output = formatting.check_cpr(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_cpr_with_dash_len_too_short_error(self):
    function_input = '121295-000'

    expected_output = "Forkert formattering af cpr nr."

    function_output = formatting.check_cpr(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_cpr_no_dash_len_too_long_error(self):
    function_input = '12129500001'

    expected_output = "Forkert formattering af cpr nr."

    function_output = formatting.check_cpr(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_cpr_with_dash_len_too_long_error(self):
    function_input = '121295-00001'

    expected_output = "Forkert formattering af cpr nr."

    function_output = formatting.check_cpr(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_cpr_no_dash_invalid_checksum_error(self):
    function_input = '1212950000'

    expected_output = "Forkert formattering af cpr nr."

    function_output = formatting.check_cpr(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_cpr_with_dash_invalid_checksum_error(self):
    function_input = '121295-0000'

    expected_output = "Forkert formattering af cpr nr."

    function_output = formatting.check_cpr(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_cpr_no_dash_nonsense_error(self):
    function_input = 'nonsense'

    expected_output = "Forkert formattering af cpr nr."

    function_output = formatting.check_cpr(function_input)

    self.assertEqual(expected_output, function_output)

  """Test check name"""
  def test_check_name(self):
    function_input = 'John Doe'

    expected_output = None

    function_output = formatting.check_name(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_name_middlenames(self):
    function_input = 'John Jane Doe Doe'

    expected_output = None

    function_output = formatting.check_name(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_name_empty(self):
    function_input = ''

    expected_output = "Intet navn angivet"

    function_output = formatting.check_name(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_name_no_space(self):
    function_input = 'JohnDoe'

    expected_output = "Fornavn og efternavn skal udfyldes"

    function_output = formatting.check_name(function_input)

    self.assertEqual(expected_output, function_output)

  """Test check date"""
  def test_check_date_no_dash(self):
    function_input = '11110111'

    expected_output = None

    function_output = formatting.check_date(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_date_with_dash(self):
    function_input = '1111-01-11'

    expected_output = None

    function_output = formatting.check_date(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_date_no_dash_len_too_long_error(self):
    function_input = '111101111'

    expected_output = "Forkert formattering af dato."

    function_output = formatting.check_date(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_date_with_dash_len_too_long_error(self):
    function_input = '1111-01-111'

    expected_output = "Forkert formattering af dato."

    function_output = formatting.check_date(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_date_no_dash_len_too_short_error(self):
    function_input = '1111011'

    expected_output = "Forkert formattering af dato."

    function_output = formatting.check_date(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_date_with_dash_len_too_short_error(self):
    function_input = '1111-01-1'

    expected_output = "Forkert formattering af dato."

    function_output = formatting.check_date(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_date_no_dash_non_digits_error(self):
    function_input = '1111ae1o'

    expected_output = "Dato må kun indeholde heltal og '-'."

    function_output = formatting.check_date(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_date_with_dash_non_digits_error(self):
    function_input = '1111-ae-1o'

    expected_output = "Dato må kun indeholde heltal og '-'."

    function_output = formatting.check_date(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_date_no_dash_invalid_month_error(self):
    function_input = '11119911'

    expected_output = "Fejlagtig måned i dato."

    function_output = formatting.check_date(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_date_with_dash_invalid_month_error(self):
    function_input = '1111-99-11'

    expected_output = "Fejlagtig måned i dato."

    function_output = formatting.check_date(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_date_no_dash_invalid_day_error(self):
    function_input = '11110199'

    expected_output = "Fejlagtig dag i dato."

    function_output = formatting.check_date(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_date_with_dash_invalid_day_error(self):
    function_input = '1111-01-99'

    expected_output = "Fejlagtig dag i dato."

    function_output = formatting.check_date(function_input)

    self.assertEqual(expected_output, function_output)

  """Test check rigs nr"""
  def test_check_rigs_nr(self):
    function_input = 'REGH12345678'

    expected_output = None
    
    function_output = formatting.check_rigs_nr(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_rigs_nr_2(self):
    function_input = 'REGH1'

    expected_output = None
    
    function_output = formatting.check_rigs_nr(function_input)

    self.assertEqual(expected_output, function_output)

  def test_check_rigs_nr_no_REGH_at_start_error(self):
    function_input = 'REG12345678'

    expected_output = "Accession nr. skal starte med 'REGH'."

    function_output = formatting.check_rigs_nr(function_input)

    self.assertEqual(expected_output, function_output)

  """Test is valid study"""

  """Test convert cpr to cpr number"""
  def test_convert_cpr_to_cpr_number_no_dash(self):
    function_input = '1111110000'

    expected_output = '1111110000'

    function_output = formatting.convert_cpr_to_cpr_number(function_input)

    self.assertEqual(expected_output, function_output)

  def test_convert_cpr_to_cpr_number_with_dash(self):
    function_input = '111111-0000'

    expected_output = '1111110000'

    function_output = formatting.convert_cpr_to_cpr_number(function_input)

    self.assertEqual(expected_output, function_output)

  def test_convert_cpr_to_cpr_number_wrong_format_error(self):
    function_input = '1111-110000'

    expected_output = '1111-110000'

    function_output = formatting.convert_cpr_to_cpr_number(function_input)

    self.assertEqual(expected_output, function_output)

  def test_convert_cpr_to_cpr_number_nonsense_error(self):
    function_input = 'nonsens-e'

    expected_output = 'nonsens-e'

    function_output = formatting.convert_cpr_to_cpr_number(function_input)

    self.assertEqual(expected_output, function_output)

  """Test convert american date to reasonable date format (fejl)"""
  def test_convert_american_date_to_reasonable_date_format(self):
    function_input = '05/12/2020 12:15'

    expected_output = '2020-05-12 12:15'

    function_output = formatting.convert_american_date_to_reasonable_date_format(function_input)

    self.assertEqual(expected_output, function_output)

  def test_convert_american_date_to_reasonable_date_format_month_with_letters_format(self):
    function_input = 'May/12/2020 12:15'

    expected_output = '2020-May-12 12:15'

    function_output = formatting.convert_american_date_to_reasonable_date_format(function_input)

    self.assertEqual(expected_output, function_output)

  def test_convert_american_date_to_reasonable_date_format_no_zero_in_month_format(self):
    function_input = '5/12/2020 12:15'

    expected_output = '2020-5-12 12:15'

    function_output = formatting.convert_american_date_to_reasonable_date_format(function_input)

    self.assertEqual(expected_output, function_output)

  def test_convert_american_date_to_reasonable_date_format_inconsistent_seperators_1(self):
    function_input = '05/12-2020 12:15'

    with self.assertRaises(ValueError):
      formatting.convert_american_date_to_reasonable_date_format(function_input)

  def test_convert_american_date_to_reasonable_date_format_inconsistent_seperators_2(self):
    function_input = '05-12/2020 12:15'

    with self.assertRaises(ValueError):
      formatting.convert_american_date_to_reasonable_date_format(function_input)

  def test_convert_american_date_to_reasonable_date_format_inconsistent_seperators_3(self):
    function_input = '05/12/2020 12/15'

    with self.assertRaises(ValueError):
      formatting.convert_american_date_to_reasonable_date_format(function_input)

  def test_convert_american_date_to_reasonable_date_format_wrong_order_error(self):
    function_input = '12:15 05/12/2020'

    with self.assertRaises(ValueError):
      formatting.convert_american_date_to_reasonable_date_format(function_input)

  def test_convert_american_date_to_reasonable_date_format_month_with_letters_format(self):
    function_input = 'May/12/2020 12:15'

    with self.assertRaises(ValueError):
      formatting.convert_american_date_to_reasonable_date_format(function_input)

  def test_convert_american_date_to_reasonable_date_format_no_zeroes_in_month_format(self):
    function_input = '5/12/2020 12:15'

    with self.assertRaises(ValueError):
      formatting.convert_american_date_to_reasonable_date_format(function_input)
  
  def test_convert_american_date_to_reasonable_date_format_wrong_nonsense_error(self):
    function_input = 'nonsense 12:15'

    with self.assertRaises(ValueError):
      formatting.convert_american_date_to_reasonable_date_format(function_input)

  def test_convert_american_date_to_reasonable_date_format_backslash_format(self):
    function_input = '05\12\2020 12:15'

    with self.assertRaises(ValueError):
      formatting.convert_american_date_to_reasonable_date_format(function_input)

  def test_convert_american_date_to_reasonable_date_format_spaces_format(self):
    function_input = '05 12 2020 12 15'

    with self.assertRaises(ValueError):
      formatting.convert_american_date_to_reasonable_date_format(function_input)

  def test_convert_american_date_to_reasonable_date_format_double_slash_format(self):
    function_input = '05//12//2020 12:15'

    with self.assertRaises(ValueError):
      formatting.convert_american_date_to_reasonable_date_format(function_input)
    
  """Test xstr"""
  def test_xstr_None_input(self):
    function_input = None

    expected_output = ''

    function_output = formatting.xstr(function_input)

    self.assertEqual(function_output, expected_output)

  def test_xstr_string_input(self):
    function_input = 'string'

    expected_output = 'string'

    function_output = formatting.xstr(function_input)

    self.assertEqual(function_output, expected_output)

  def test_xstr_int_input(self):
    function_input = 112

    expected_output = '112'

    function_output = formatting.xstr(function_input)

    self.assertEqual(function_output, expected_output)




