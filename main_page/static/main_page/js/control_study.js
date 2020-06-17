function remove_decimal_values(number){
  var string = number.split(".")
  return string[0]
}

function replace_dots_with_commas(Value){
  var string = Value.split(".");
  var zero_test = /^0+$/;
  if (zero_test.test(string[1])) {
    return string[0];
  } else {
    return string[0] + "," + string[1];
  }
}

function checkboxes_filled(event) {
  /*
  Ensure that all checkboxes are filled out before allowing submission of POST request for "Godkend og send til PACS"
  */
  // Get alerter object from eventData
  let alerter = event.data.alerter;
  
  // Remove prior alerts
  alerter.remove_all_alerts();
  alerter.show_alerts();

  // Check if all checkboxes are checked
  var is_valid = true;

  var checkboxes = $('input[type=checkbox]');
  checkboxes.each(function() {
    is_valid = is_valid && this.checked; 
  });

  if (!is_valid) {
    alerter.add_alert("failed_checkbox", "Et eller flere felter er ikke blevet godkendt", "danger");
    alerter.show_alerts();
    return false;
  }

  // Check BamID
  var bamID_str = $('#id_bamID').val()
  is_valid = is_valid && (bamID_str.length == 8);

  if (!is_valid) {
    alerter.add_alert("failed_bamid", "Bam ID er ikke blevet udfyldt", "danger");
    alerter.show_alerts();
    return false;
  }

  return true;
}

$(function() {
  let alerter = new FieldAlerter($("#error-message-container"));

  $('#confirm').on('click', {"alerter": alerter}, checkboxes_filled);

  //Remove . from Thining Factor, Samples and Standard Counts
  var samples = $(".sample_count");
  samples.each(function(){
    this.value = remove_decimal_values(this.value);
  })
  var Deviations = $(".Deviation");
  Deviations.each(function(){
    this.value = replace_dots_with_commas(this.value);
  })
})