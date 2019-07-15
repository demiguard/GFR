function clear_table_headers() {
  $('#admin-table-head').empty();
}

function clear_table_entries() {
  $('#admin-table-body').empty();
}

function init_table_headers(headers) {
  for (var i = 0; i < headers.length; i++) {
    var curr_th = document.createElement('th');
    curr_th.innerText = headers[i];

    $('#admin-table-head').append(curr_th);
  }
}

function init_table_entries(entries) {
  for (var i = 0; i < entries.length; i++) {
    entry_values = Object.values(entries[i]);
    
    curr_tr = document.createElement('tr');

    for (var j = 0; j < entry_values.length; j++) {
      var curr_td = document.createElement('td');
      curr_td.innerText = entry_values[j];
      curr_tr.appendChild(curr_td);
    }

    $('#admin-table-body').append(curr_tr);
  }
}

function init_action_buttons() {
  
}

function show_model() {
  MODEL_URL_MAPPINGS = {
    'users': '/api/user',
    'hospitals': '/api/hospital',
    'departments': 'api/department',
    'handled_examinations': 'api/handled_examinations'
  };
 
  clear_table_headers();
  clear_table_entries();

  let selected_model = $('#model-selector').val();
  console.log(selected_model);
  console.log(MODEL_URL_MAPPINGS[selected_model]);
  $.ajax({
    url: MODEL_URL_MAPPINGS[selected_model],
    type: 'GET',
    success: function(data) {
      console.log(data);

      let headers = Object.keys(data.users[0]);
      init_table_headers(headers);

      init_table_entries(data.users);
    },
    error: function(data) {
      console.log(data);
      // $('#id_accession_number').attr('readonly', false);
      // let resp_accession_number = data.responseJSON.resp_accession_number;
      // alerter.add_alert("Kunne ikke slette behandlede undersøgelse med accession nummer: '" + resp_accession_number + "'", 'danger');
    }
  });
}

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

  show_model();

  $('#model-selector').on('change', show_model);

  // // Button click handlers for the various forms
  // $('#create-user-btn').on('click', function() {
  //   console.log("CREATE USER");
  // });


  // $('#delete-handled-btn').on('click', function() {
  //   // Attempts to delete the requested examination
  //   alerter.clear_alerts();

  //   let accession_number = $('#id_accession_number').val();

  //   if (accession_number == '') {
  //     alerter.add_alert("Intet accession nummer givet.", 'danger');
  //     return;
  //   }

  //   // Tell backend to delete it
  //   $('#id_accession_number').attr('readonly', true);

  //   $.ajax({
  //     url: 'ajax/handled_examination',
  //     type: 'DELETE',
  //     data: {
  //       'accession_number': accession_number
  //     },
  //     success: function(data) {
  //       $('#id_accession_number').attr('readonly', false);
  //       alerter.add_alert("Slettede behandlede undersøgelse: '" + data.resp_accession_number + "'", 'success');
  //     },
  //     error: function(data) {
  //       $('#id_accession_number').attr('readonly', false);
  //       let resp_accession_number = data.responseJSON.resp_accession_number;
  //       alerter.add_alert("Kunne ikke slette behandlede undersøgelse med accession nummer: '" + resp_accession_number + "'", 'danger');
  //     }
  //   });
  // });
});