function remove_decimal_values(number){
  var string = number.split(".")
  return string[0]
}

function replace_dots_with_commas(Value){
  var string = Value.split(".");
  var reeeeeeeee = /^0+$/;
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
  var samples = $(".sample_count");
  samples.each(function(){
    this.value = remove_decimal_values(this.value);
  })
})