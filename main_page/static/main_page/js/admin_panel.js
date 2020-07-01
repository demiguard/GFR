// Endpoint to access the model through
MODEL_URL_MAPPINGS = {
  'users'               : '/api/user',
  'hospitals'           : '/api/hospital',
  'departments'         : '/api/department',
  'handled_examinations': '/api/handled_examination',
  'configs'             : '/api/config',
  'procedures'          : '/api/proceduretype',
  'procedure_mapping'   : '/api/procedure_mapping',
  'address'             : '/api/address' ,
  'server_config'       : '/api/server_config'
};

// Names to display to the user
MODEL_NAME_MAPPINGS = {
  'users': 'bruger',
  'hospitals': 'hospital',
  'departments': 'afdeling',
  'handled_examinations': 'behandlede undersøgelse',
  'configs': 'konfiguration',
  'procedures' : 'proceduretype',
  'procedure_mapping': 'procedure filter',
  'address' : 'addresse',
  'server_config' : 'server konfiguration'
};

// Name of the underlying model
SELECTED_MODEL_NAMES = {
  'users'               : 'user',
  'hospitals'           : 'hospital',
  'departments'         : 'department',
  'handled_examinations': 'handled_examination',
  'configs'             : 'config',
  'procedures'          : 'proceduretype',
  'procedure_mapping'   : 'procedure_mapping',
  'address'             : 'address',
  'server_config'       : 'server_config'
}

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

function create_button(iconic_class_name, btn_class, tooltip) {
  var edit_button = document.createElement('button');
  edit_button.classList.add('btn');
  edit_button.classList.add('btn-link');
  edit_button.classList.add(btn_class);
  
  var edit_span = document.createElement('span');
  edit_span.title = tooltip;
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
      let selected_model_value = $('#model-selector').val();
      let selected_model_name = SELECTED_MODEL_NAMES[selected_model_value];

      // Which specific model instance is being editted
      let obj_id = $(this).parent().parent().children()[0].innerText;
      
      // Redirect
      let redirect_url = "/admin_panel/edit/" + selected_model_name + "/" + obj_id;
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
            // console.log(data);
            
            show_model();
          },
          error: function(data) {
            // console.log(data);
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
    var edit_button = create_button('pencil', 'edit-btn', 'Rediger');
    var delete_button = create_button('trash', 'delete-btn', 'Slet');

    var divider_div = document.createElement('div');
    divider_div.classList.add('divider');

    let selected_model_value = $('#model-selector').val();
    if (selected_model_value.indexOf('procedure_mapping') == -1) { // Excluded edit button from procedure_mappings
      edit_td.appendChild(edit_button);
    }
    
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
  // console.log(selected_model);
  $.ajax({
    url: MODEL_URL_MAPPINGS[selected_model],
    type: 'GET',
    success: function(data) {
      // console.log(data);
      let vals = Object.values(data)[0];
      if (vals.length != 0) {
        let headers = Object.keys(vals[0]);
        init_table_headers(headers);
  
        init_table_entries(Object.values(data)[0]);
  
        init_action_buttons();
        init_action_button_event_handlers();

        // Add sort_table function to all table headers
        $('#admin-table-head th').each(function() {
          let th_val = $(this).text();

          if (th_val !== "") {
            $(this).on('click', function() {
              sort_table($(this).index(), 'admin-table');
            });
          }
        });

      } else {
        alerter.add_alert('Ingen indgang fundet.', 'warning');
      }
    },
    error: function(data) {
      console.warn(data);
      // $('#id_accession_number').attr('readonly', false);
      // let resp_accession_number = data.responseJSON.resp_accession_number;
      // alerter.add_alert("Kunne ikke slette behandlede undersøgelse med accession nummer: '" + resp_accession_number + "'", 'danger');
    }
  });
}

function remove_all_studies() {
  let hospital_shortname = $('#id_l_hospital').val();
  let bam_id = $('#id_l_bamID').val();

  $.ajax({
    url: '/api/list',
    type: 'DELETE',
    data: {
      'list_studies': '',
      'hospital_shortname': hospital_shortname,
      'bam_id': bam_id,
    },
    success: function(data) {
      console.debug(data);
      window.location.replace("/admin_panel");
    },
    error: function(data) {
      console.debug("Failed to delete all list_studies");
    }
  });
}

function remove_all_deleted_studies() {
  let hospital_shortname = $('#id_d_hospital').val();
  let bam_id = $('#id_l_bamID').val();

  $.ajax({
    url: '/api/list',
    type: 'DELETE',
    data: {
      'deleted_studies': '',
      'hospital_shortname': hospital_shortname,
      'bam_id': bam_id,
    },
    success: function(data) {
      console.debug(data);
      window.location.replace("/admin_panel");
    },
    error: function(data) {
      console.debug("Failed to delete all deleted_studies");
    }
  });
}

function deleted_check_toggle_remove() {
  let hosp = $('#id_d_hospital').val();
  let bam_id = $('#id_d_bamID').val();

  var should_toggle = true;

  if (bam_id.length != 8) {
    should_toggle = false;
  }

  if (!hosp) {
    should_toggle = false;
  }

  if (should_toggle) {
    $('#nukeDS-modal-accept').attr('disabled', false);
  } else {
    $('#nukeDS-modal-accept').attr('disabled', true);
  }
}

function list_check_toggle_remove() {
  let hosp = $('#id_l_hospital').val();
  let bam_id = $('#id_l_bamID').val();

  var should_toggle = true;

  if (bam_id.length != 8) {
    should_toggle = false;
  }

  if (!hosp) {
    should_toggle = false;
  }

  if (should_toggle) {
    $('#nukeLS-modal-accept').attr('disabled', false);
  } else {
    $('#nukeLS-modal-accept').attr('disabled', true);
  }
}

$(function() {
  // Site loaded
  alerter.init_alerter($('#error-container'));

  show_model();

  $('#model-selector').on('change', show_model);

  $('#add-btn').on('click', function() {
    // Determine which model is being added, so the correct api endpoint can be reached 
    let selected_model_value = $('#model-selector').val();
    let selected_model_name = SELECTED_MODEL_NAMES[selected_model_value];

    let add_url = "/admin_panel/add/" + selected_model_name;
    window.location.href = add_url;
  });

  /* Event listeners for remove all studies buttons */
  $('#nukeLS-modal-accept').attr('disabled', true);
  $('#nukeDS-modal-accept').attr('disabled', true);

  $('#nuke-list-studies').on('click', function() {
    $('#nukeLSModal').modal('toggle');
  });  

  $('#nukeLS-modal-accept').on('click', function() {
    remove_all_studies();
    $('#nukeLSModal').modal('toggle');
  });

  $('#id_l_hospital').on('change', list_check_toggle_remove);
  $('#id_l_bamID').on('change', list_check_toggle_remove);
  $('#id_l_bamID').keypress(list_check_toggle_remove);

  $('#id_d_hospital').on('change', deleted_check_toggle_remove);
  $('#id_d_bamID').on('change', deleted_check_toggle_remove);
  $('#id_d_bamID').keypress(deleted_check_toggle_remove);

  $('#nukeDS-modal-accept').on('click', function() {
    remove_all_deleted_studies();
    $('#nukeDSModal').modal('toggle');
  });

  $('#nuke-deleted-studies').on('click', function() {
    $('#nukeDSModal').modal('toggle');
  });
});
