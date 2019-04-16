var helper = (function() {
  /*
  Checks if a value is within a given threshold

  Args:
    val: value to check on
    min_val: minimum value
    max_val: maximum value

  Returns:
    true if the value is within the bounds, false otherwise
  */
  var is_within_threshold = function(val, min_val, max_val) {
    if (val < min_val || val > max_val) {
      return false;
    }

    return true;
  };

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
  */
  var is_number = function(str) {
    let re_number = /-?\d+\.?\d*/;
    return re_number.test(str);
  };

  // Validates a given time string (format: tt:mm)
  var valid_time_format = function(time_str) {
    let TIME_FORMAT = /^([0-1][0-9]|[2][0-3]):[0-5][0-9]$/;
    return TIME_FORMAT.test(time_str);
  };

  // Validates a given date string (format: YYYY-MM-DD)
  var valid_date_format = function(date_str) {
    let DATE_FORMAT = /^[0-9]{4}-([0][1-9]|[1][0-2])-([0-2][0-9]|[3][0-1])$/;
    return DATE_FORMAT.test(date_str);
  };

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
        
        if (number_of_chars === n){
          let prev_val = $(this).val();
          $(this).val(prev_val + c);
        }
      }
    });
  };

  return {
    is_within_threshold: is_within_threshold,
    round_to: round_to,
    is_number: is_number,
    valid_time_format: valid_time_format,
    valid_date_format: valid_date_format,
    auto_char: auto_char
  };
})();