$(function() {
  // Add datepickers to date fields
  $('#id_Dato_start').datepicker({format: 'yyyy-mm-dd'});
  $('#id_Dato_finish').datepicker({format: 'yyyy-mm-dd'});


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

  // Make search fields readonly 
  let disable_search_fields = function() {
    $('#id_name').attr('readonly', true);
    $('#id_cpr').attr('readonly', true);
    $('#id_Rigs').attr('readonly', true);
    $('#id_Dato_start').attr('readonly', true);
    $('#id_Dato_finish').attr('readonly', true);
  }

  // Set readonly to false on search fields
  let enable_search_fields = function() {
    $('#id_name').attr('readonly', false);
    $('#id_cpr').attr('readonly', false);
    $('#id_Rigs').attr('readonly', false);
    $('#id_Dato_start').attr('readonly', false);
    $('#id_Dato_finish').attr('readonly', false);
  }

  // Sends an ajax GET request with the entered search parameters
  let ajax_search = function() {
    // Remove all previous search results
    

    // Get search parameters
    let name = $('#id_name').val();
    let cpr = $('#id_cpr').val();
    let rigs_nr = $('#id_Rigs').val();
    let date_from = $('#id_Dato_start').val();
    let date_to = $('#id_Dato_finish').val();

    // Display loading element
    disable_search_fields();

    $.get({
      url: 'ajax/search',
      data: {
        'name': name,
        'cpr': cpr,
        'rigs_nr': rigs_nr,
        'date_from': date_from,
        'date_to': date_to
      },
      success: function(data) {
        // Insert search results into table
        console.log(data);

        enable_search_fields();
      },
      error: function(data) {
        // Display appropriate error message


        enable_search_fields();
      }
    });
  }

  // Event handers for click and enter on search fields
  let search_field_enter = function(event) {
    if (event.which == '13') { // Enter key
      ajax_search();
    }
  }

  $('#id_name').on('keypress', search_field_enter);
  $('#id_cpr').on('keypress', search_field_enter);
  $('#id_Rigs').on('keypress', search_field_enter);
  $('#id_Dato_start').on('keypress', search_field_enter);
  $('#id_Dato_finish').on('keypress', search_field_enter);
  $('#search-btn').on('click', ajax_search);
});