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
})