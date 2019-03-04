// Wait until document ready
$(function() {

  // On click event for any field on the page, warns the user amount changing the settings
  var warned = false;

  $(".form-control").click(function() {
    // Remove previous success text
    $('#success-msg').remove();

    // Warn the user if they haven't been warned before
    if (!warned) {
      let res = confirm("ADVARSEL!: Ændring af bruger indstillinger kan medføre problemer for forbindelsen til siden.");
      if (res) {
        warned = true; 
      }
    }
  });
});