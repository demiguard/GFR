MODEL_URL_MAPPINGS = {
  'users': '/api/user',
  'hospitals': '/api/hospital',
  'departments': '/api/department',
  'handled_examinations': '/api/handled_examination',
  'configs': '/api/config'
};

MODEL_NAME_MAPPINGS = {
  'users': 'bruger',
  'hospitals': 'hospital',
  'departments': 'afdeling',
  'handled_examinations': 'behandlede undersøgelse',
  'configs': 'konfiguration'
};

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

function create_button(iconic_class_name, btn_class) {
  var edit_button = document.createElement('button');
  edit_button.classList.add('btn');
  edit_button.classList.add('btn-link');
  edit_button.classList.add(btn_class);
  
  var edit_span = document.createElement('span');
  edit_span.title = 'Slet';
  edit_span.classList.add('oi');
  edit_span.classList.add('oi-' + iconic_class_name);
  
  edit_button.appendChild(edit_span);

  return edit_button;
}

function init_action_button_event_handlers() {
  // Edit button event handlers
  $('.edit-btn').each(function() {
    $(this).on('click', function() {
      // Which model is being editted
      var selected_model = $('#model-selector').val();
      selected_model = selected_model.substring(0, selected_model.length - 1); // Remove last 's'

      // Which specific model instance is being editted
      let obj_id = $(this).parent().parent().children()[0].innerText;
      
      // Redirect
      let redirect_url = "/admin_panel/edit/" + selected_model + "/" + obj_id;
      window.location.href = redirect_url;
    });
  });

  // Delete button event handlers
  $('.delete-btn').each(function() {
    $(this).on('click', function() {
      let selected_model = $('#model-selector').val();

      let entry_id = $(this).parent().parent().children()[0].innerText;
      let api_url = MODEL_URL_MAPPINGS[selected_model] + "/" + entry_id;

      if (confirm('Er du sikker på du ønsker at slette ' + MODEL_NAME_MAPPINGS[selected_model] + ' med id: ' + entry_id)) { 
        $.ajax({
          url: api_url,
          type: 'DELETE',
          success: function(data) {
            console.log(data);
            
            show_model();
          },
          error: function(data) {
            console.log(data);
          }
        });
      }
    });
  });
}

// TODO: Just make a function for creating a single button, given a iconic button class.
// Then use this to implement an edit and remove, button
function init_action_buttons() {
  // Create additional spacing in header
  var action_header = document.createElement('th');
  $('#admin-table-head').append(action_header);
  
  // Create the action buttons
  
  $('#admin-table-body tr').each(function() {
    var edit_td = document.createElement('td');
    var edit_button = create_button('pencil', 'edit-btn');
    var delete_button = create_button('trash', 'delete-btn');

    var divider_div = document.createElement('div');
    divider_div.classList.add('divider');

    edit_td.appendChild(edit_button);
    edit_td.appendChild(divider_div);
    edit_td.appendChild(delete_button);

    $(this).append(edit_td);
  });
}

function show_model() { 
  clear_table_headers();
  clear_table_entries();
  alerter.clear_alerts();

  let selected_model = $('#model-selector').val();

  $.ajax({
    url: MODEL_URL_MAPPINGS[selected_model],
    type: 'GET',
    success: function(data) {
      console.log(data);
      let vals = Object.values(data)[0];
      if (vals.length != 0) {
        let headers = Object.keys(vals[0]);
        init_table_headers(headers);
  
        init_table_entries(Object.values(data)[0]);
  
        init_action_buttons();
        init_action_button_event_handlers();
      } else {
        alerter.add_alert('Ingen indgang fundet.', 'warning');
      }
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
  // Site loaded
  console.log("Admin panel loaded");
  alerter.init_alerter($('#error-container'));

  show_model();

  $('#model-selector').on('change', show_model);

  $('#add-btn').on('click', function() {
    console.log("clicked add-btn");
    // Which model is being added
    var selected_model = $('#model-selector').val();
    selected_model = selected_model.substring(0, selected_model.length - 1); // Remove last 's'

    let add_url = "/admin_panel/add/" + selected_model;
    window.location.href = add_url;
  });
});
