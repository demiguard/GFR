var helper = (function() {
  var within_bound = function(val, args) {
    /*
    Checks if given value is with a specified bound
  
    Args:
      val: integer or float value to check against
      args: dict containing arguments "low" and "high"
  
    Returns:
      True, if val is within low and high. False otherwise
    */
    let low  = args["low"];
    let high = args["high"];
  
    return (val >= low && val <= high);
  }

  /*
  Helper function to round of floating point numbers

  Args:
    num: number to round off
    n: how many decimals to round off to
  */
  var round_to = function(num, n) {
    p = Math.pow(10, n);
    return Math.round(num * p) / p;
  };

  /*
  Checks if a string only contains digits or '.' (floats)

  Args:
    str: string to check on

  Returns:
    true if the string is a number, false otherwise.

  TODO: Make this use commas instread of dots (or both?)
  */
  var is_number = function(str) {
    let re_number = /-?\d+\.?\d*/;
    return re_number.test(str);
  };

  // Validates a given time string (format: tt:mm)
  // TODO: Rename to is_iso8601_time
  var valid_time_format = function(time_str) {
    let TIME_FORMAT = /^([0-1][0-9]|[2][0-3]):[0-5][0-9]$/;
    return TIME_FORMAT.test(time_str);
  };

  /*
  Validates if a given date string is in the format: YYYY-MM-DD (ISO 8601)
  
  Args:
    date_str: string to validate against

  Remark:
    For specific information see:
    https://www.iso.org/iso-8601-date-and-time-format.html

  TODO: Rename this to is_iso8601_date
  */
  var valid_date_format = function(date_str) {
    let DATE_FORMAT = /^[0-9]{4}-([0][1-9]|[1][0-2])-([0-2][0-9]|[3][0-1])$/;
    return DATE_FORMAT.test(date_str);
  };

  /*
  Validates if a given date string is in the format: DD-MM-YYYY (danish format)

  Args:
    date_str: string to validate against

  Remarks:
    For specifications see ISO 8601:2005 or the section on
    "Denmark" in the table on:
    https://en.wikipedia.org/wiki/Date_format_by_country
  */
  var is_danish_date = function(date_str) {
    let DATE_FORMAT = /^([0-2][0-9]|[3][0-1])-([0][1-9]|[1][0-2])-[0-9]{4}$/;
    return DATE_FORMAT.test(date_str);
  };


  var convert_date_to_danish_date_format = function(date_str){
    let day = date_str.substr(8,2);
    let month = date_str.substr(5,2);
    let year = date_str.substr(0,4);
    return day + '-' + month + '-' + year;  
  };

  var convert_danish_date_to_date_format = function(date_str){
    let day   = date_str.substr(0,2);
    let month = date_str.substr(3,2);
    let year = date_str.substr(6,4);
    return year + '-' + month + '-' + day;
  }

  /*
  Automatically appends a character after the n'th character is typed.

  Args:
    field: the field to apply the bind on.
    c: character to append
    n: after how many characters should it append

  Remark:
    The function ignores backspaces (the character code 8)
  */
  var auto_char = function(field, c, n) {
    const BACKSPACE_KEY = 8;
    
    field.bind('keypress', function(key) {

      if (key.which !== BACKSPACE_KEY) {
        let number_of_chars = $(this).val().length;
        
        if (number_of_chars === n  && String.fromCharCode(key.which) !== c){
          let prev_val = $(this).val();
          $(this).val(prev_val + c);
        }
      }
    });
  };

  /*
  Disables all enter key form submission if focused on a field
  */
  var disable_enter_form_submit = function() {
    let ENTER_KEYCODE = 13;

    $('input').on('keyup keypress', function(e) {
      var keyCode = e.keyCode || e.which;
      
      if (keyCode === ENTER_KEYCODE) { 
        e.preventDefault();
        return false;
      }
    });
  };

  return {
    within_bound: within_bound,
    round_to: round_to,
    is_number: is_number,
    valid_time_format: valid_time_format,
    valid_date_format: valid_date_format,
    is_danish_date: is_danish_date,
    auto_char: auto_char,
    convert_danish_date_to_date_format: convert_danish_date_to_date_format,
    convert_date_to_danish_date_format: convert_date_to_danish_date_format,
    disable_enter_form_submit: disable_enter_form_submit
  };
})();
