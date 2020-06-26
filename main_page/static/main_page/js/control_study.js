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

function checkbox_enter_skips() {
  /*
  Allow uses to hit enter to toggle the current
  */
  helper.disable_enter_form_submit($("#Contorl-study-form"));

  // Get all checkboxes
  let checkboxes = $("input:checkbox");
  let n = checkboxes.length;

  // Focus on first checkbox
  checkboxes[0].focus();

  // Hit enter to toggle and jump to next checkbox
  // Store ids as keys and indexes as values, since the i loop variable will remain the same if used in event function
  var inds = { };

  for (var i = 0; i < n; i++) {
    inds[checkboxes[i].id] = i;

    $("#" + checkboxes[i].id).on("keypress", function(event) {
      if (event.which == 13) { // Enter key pressed
        this.checked = true;

        let next_idx = inds[this.id] + 1;

        if (next_idx != n) {
          // Focus on next checkbox
          checkboxes[next_idx].focus();
        } else {
          // Focus on bamid, after last checkbox
          $("#id_bamID").focus();
        }
      }
    });
  }
}

$(function() {
  let alerter = new FieldAlerter($("#error-message-container"));

  $('#confirm').on('click', {"alerter": alerter}, checkboxes_filled);

  // Enable checkbox "Enter" skipping
  checkbox_enter_skips();

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