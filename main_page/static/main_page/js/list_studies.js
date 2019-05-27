

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
  
  // On click event for accepting the deletion of a study
  $('#delete-modal-accept').on('click', function() {
    let del_accession_number = $('#modal-accession-number').text();
    
    $.post({
      url: '/ajax/delete_study',
      data: {
        'delete_accession_number': del_accession_number,
      },
      success: function() {
        window.location.href = "/list_studies";
      },
      error: function() {
        console.warn("Failed to delete study...");
      }
    });
  });

  // On click event for deletion of a study
  $('.trash-btn').on('click', function() {
    // Get accession number to display in modal
    var parent_tr = $(this).parent().parent();
    let accession_number = parent_tr.children()[3].innerHTML;

    $('#modal-accession-number').text(accession_number);

    // Show the modal
    $('#deleteModal').modal('toggle');
  });

  $('#thining_factor_button').on('click', function(){
    
    var a_thining_factor = $('#id_thin_fac').val()
    
    $.post({
      url:'/ajax/update_thining_factor',
      data:{
        'thining_factor': a_thining_factor
      },
      success: function(){
        window.location.href = '/list_studies'
      },
      error: function(){

      }
    });
  });
});