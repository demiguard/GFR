$(function() {
  // Send csrf token with on ajax requests 
  $.ajaxSetup({ 
    beforeSend: function(xhr, settings) {
      function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
          var cookies = document.cookie.split(';');
          for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
            }
          }
        }
        return cookieValue;
      }
      
      if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
        // Only send the token to relative URLs i.e. locally.
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
      }
    } 
  });


  // Site loaded
  console.log("Admin panel loaded");
  alerter.init_alerter($('#handled-examination-errors'));


  // Button click handlers for the various forms
  $('#create-user-btn').on('click', function() {
    console.log("CREATE USER");
  });


  $('#delete-handled-btn').on('click', function() {
    // Attempts to delete the requested examination
    alerter.clear_alerts();

    let accession_number = $('#id_accession_number').val();

    if (accession_number == '') {
      alerter.add_alert("Intet accession nummer givet.", 'danger');
      return;
    }

    // Tell backend to delete it
    $('#id_accession_number').attr('readonly', true);

    $.ajax({
      url: 'ajax/handled_examination',
      type: 'DELETE',
      data: {
        'accession_number': accession_number
      },
      success: function(data) {
        $('#id_accession_number').attr('readonly', false);
        alerter.add_alert("Slettede behandlede undersøgelse: '" + data.resp_accession_number + "'", 'success');
      },
      error: function(data) {
        $('#id_accession_number').attr('readonly', false);
        let resp_accession_number = data.responseJSON.resp_accession_number;
        alerter.add_alert("Kunne ikke slette behandlede undersøgelse med accession nummer: '" + resp_accession_number + "'", 'danger');
      }
    });
  });
});