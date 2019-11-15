


var bad_input_handler = (function() {
  const BACKSPACE_KEY = 8;

  var remove_decimal_values = function (Value){
    var string = Value.split(".")
    return string[0]
  }
  

  var replace_dots_with_commas = function (Value){
    var string = Value.split(".");
    var reeeeeeeee = /^0+$/;
    if (reeeeeeeee.test(string[1]) || string.length == 1) {
      return string[0];
    } else {
      return string[0] + "," + string[1];
    }
  }


  var number = function(field){
    field.bind('keyup', function(key){
      var char = String.fromCharCode(key.which);
      var txt = field.val();
      field.val(txt.replace(/[^0-9\,]/g,''));
    })
  }


  var  convert_comma_to_float = function (number_str){
    return parseFloat(number_str.replace(',','.'));
  }

  var convert_float_to_comma = function(float_val){
    return float_val.toString().replace('.',',');
  }


  return {
    convert_comma_to_float    : convert_comma_to_float,
    convert_float_to_comma    : convert_float_to_comma,
    number                    : number,
    remove_decimal_values     : remove_decimal_values,
    replace_dots_with_commas  : replace_dots_with_commas
    }
})();