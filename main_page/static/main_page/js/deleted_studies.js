

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
  
  // On click event for accepting the recovery of a study
  $('#recover-modal-accept').on('click', function() {
    let recover_accession_number = $('#modal-accession-number').text();
    
    $.post({
      url: '/ajax/restore_study',
      data: {
        'recover_accession_number': recover_accession_number,
      },
      success: function() {
        window.location.href = "/deleted_studies";
      },
      error: function() {
        console.warn("Failed to recover study...");
      }
    });
  });

  // On click event for recovering of a study
  $('.restore-btn').on('click', function() {
    // Get accession number to display in modal
    var parent_tr = $(this).parent().parent();
    let accession_number = parent_tr.children()[4].innerHTML;

    $('#modal-accession-number').text(accession_number);

    // Show the modal
    $('#recoverModal').modal('toggle');
  });
});