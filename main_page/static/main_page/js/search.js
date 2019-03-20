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
    
    $('#search-table-body').prop('disabled', true);
  }

  // Set readonly to false on search fields
  let enable_search_fields = function() {
    $('#id_name').attr('readonly', false);
    $('#id_cpr').attr('readonly', false);
    $('#id_Rigs').attr('readonly', false);
    $('#id_Dato_start').attr('readonly', false);
    $('#id_Dato_finish').attr('readonly', false);

    $('#search-table-body').prop('disabled', false);
  }

  // Sends an ajax GET request with the entered search parameters
  let ajax_search = function() {
    // Remove all previous search results
    $('#search-table-body').empty();

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
        search_results = data.search_results;

        for (var i = 0; i < search_results.length; i++) {
          // Create elements for table entry
          var trow = document.createElement('tr');
          trow.setAttribute('id', search_results[i].rigs_nr);

          var td_name = document.createElement('td');
          td_name.innerHTML = search_results[i].name;

          var td_cpr = document.createElement('td');
          td_cpr.innerHTML = search_results[i].cpr;

          var td_date = document.createElement('td');
          td_date.innerHTML = search_results[i].date;

          var td_rigs_nr = document.createElement('td');
          td_rigs_nr.innerHTML = search_results[i].rigs_nr;

          // Insert table entry into the table
          trow.appendChild(td_name);
          trow.appendChild(td_cpr);
          trow.appendChild(td_date);
          trow.appendChild(td_rigs_nr);
          $('#search-table-body').append(trow);

          // Make rows redirect to present_old_study page on click
          $('#' + search_results[i].rigs_nr).on('click', function() {
            document.location = '/present_old_study/' + $(this).attr('id');
          });
        }

        enable_search_fields();
      },
      error: function(data) {
        var err_text = "";
        if (data.statusText == 'timeout') {
          err_text = "Fejl: Kunne ikke forbinde til PACS (timeout).";
        } else {
          err_text = "Fejl: Kunne ikke forbinde til PACS";
        }
        
        // Display appropriate error message
        var error_msg = document.createElement('p');
        error_msg.innerHTML = err_text;
        error_msg.style.color = 'lightcoral';
        $('#error-message-container').append(error_msg);

        enable_search_fields();
      },
      timeout: 60000
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