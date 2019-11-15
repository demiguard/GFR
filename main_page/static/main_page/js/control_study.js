function remove_decimal_values(Value){
  var string = Value.split(".")
  return string[0]
}

function replace_dots_with_commas(Value){
  var string = Value.split(".");
  var reeeeeeeee = /0+/;
  if (reeeeeeeee.test(string[1])) {
    return string[0];
  } else {
    return string[0] + "," + string[1];
  }
}


function Check(){
  var is_valid = true;
  var checkboxes = $('input[type=checkbox]');
  //Checks if all checkboxes are checked. I hope concurrency is not a thing in JS
  checkboxes.each(function(){
    is_valid = is_valid && this.checked; 
  });

  var bamID_str = $('#id_bamID').val()
  is_valid = is_valid && (bamID_str.length == 8);

  return is_valid;
}

$(function() {
  $('#confirm').on('click', Check);

  //Remove . from Thining Factor, Samples and Standard Counts
  var remove_decimal_fields = ["#id_thin_fac","#id_stdCnt"];
  var remove_decimal_fields_lenght = remove_decimal_fields.length;
  
  for(var i = 0; i < remove_decimal_fields_lenght; i++){
    $(remove_decimal_fields[i]).val(remove_decimal_values($(remove_decimal_fields[i]).val()));
  }

  var samples = $(".sample_count");
  samples.each(function(){
    this.value = remove_decimal_values(this.value);
  })

  //Change .xxxx to ,xxxx or removing it if xxxx = 0
  var fields_comma_removal = ["#id_height","#id_weight","#id_vial_weight_before", "#id_vial_weight_after"]
  var fields_comma_removal_length = fields_comma_removal.length;

  for(var i = 0; i < fields_comma_removal_length; i++){
    $(fields_comma_removal[i]).val(replace_dots_with_commas($(fields_comma_removal[i]).val()));
  }

})