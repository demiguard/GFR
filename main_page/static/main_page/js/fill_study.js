/*
Initializes the correct sizing of the select test div on window resizing

Remarks: 
  THIS IS JUST A TEMPORARY FIX AND SHOULD FIXED IN CSS
*/
function init_test_div_resizer() {
  let largescreen_offset = 80;
  let smallscreen_offset = 105;
  let screen_diff = 1300;

  $(window).on('resize', function() {
    var test_div = $('#right_side')
    var doc_height = $(document).innerHeight();
    var new_height = 0;
    
    if (doc_height <= screen_diff) {
      new_height = (doc_height - test_div.position().top) - smallscreen_offset;
    } else {
      new_height = (doc_height - test_div.position().top) - largescreen_offset;
    }

    test_div.height(new_height);
  });
};

/*
Adds threshold checking on number fields
*/
function add_threshold_checking() {
  let id_thresholds = [
    {'id': '#id_height',              'min_val': 40,    'max_val': 210},
    {'id': '#id_weight',              'min_val': 30,    'max_val': 150},
    {'id': '#id_vial_weight_before',  'min_val': 3,     'max_val': 5},
    {'id': '#id_vial_weight_after',   'min_val': 0,     'max_val': 5},
    {'id': '#id_std_cnt',             'min_val': 1000,  'max_val': 10000},
    {'id': '#id_thin_fac',            'min_val': 3500,  'max_val': 10000},
    {'id': '#standard-field',         'min_val': 0,     'max_val': 100000}
  ];
  
  let id_thresholds_length = id_thresholds.length;
  for (var i = 0; i < id_thresholds_length; i++) {
    alerter.field_auto_warn(
      $(id_thresholds[i].id),
      'warning',
      function(field, options) {
        let field_val = field.val();
        if (!helper.is_number(field_val)) {
          return true;
        }
        
        let parse_val = parseFloat(field_val);
        return !helper.is_within_threshold(parse_val, options.min_val, options.max_val);
      },
      {
        'min_val': id_thresholds[i].min_val,
        'max_val': id_thresholds[i].max_val
      }
    );
  }
}

/*
Adds checking on time fields
*/
function add_time_checking() {
  let time_ids = [
    ['#id_injection_time', 'danger'],
    ['#id_study_time', 'danger']
  ];
  let time_ids_len = time_ids.length;
  
  for (var i = 0; i < time_ids_len; i++) {
    alerter.field_auto_warn(
      $(time_ids[i][0]),
      time_ids[i][1],
      function(field) {
        return !helper.valid_time_format(field.val());
      }
    );
  }
}

/*
Adds checking on date fields
*/
function add_date_checking() {
  let date_ids = [
    ['#id_injection_date', 'danger'],
    ['#id_study_date', 'danger'],
    ['#id_birthdate', 'danger']
  ];
  let date_ids_len = date_ids.length;
  
  for (var i = 0; i < date_ids_len; i++) {
    alerter.field_auto_warn(
      $(date_ids[i][0]),
      date_ids[i][1],
      function(field) {
        return !helper.valid_danish_date_format(field.val());
      }
    );
  }
}

/*
Initializes date fields
*/
function initialize_date_fields() {
  // Add date pickers to date fields
  $('#id_injection_date').datepicker({format: 'dd-mm-yyyy'});
  $('#id_study_date').datepicker({format: 'dd-mm-yyyy'});
  $('#id_birthdate').datepicker({format:'dd-mm-yyyy'});
  $('#id_dateofmessurement').datepicker({format:'dd-mm-yyyy'});
}

/*
Initializes time fields
*/
function initialize_time_fields() {
  // Adding Colons to time fields after seconds character
  helper.auto_char($("input[name='injection_time']"), ':', 2);
  helper.auto_char($("input[name='study_time']"), ':', 2);
}

/*
Performs initialization of required modules
*/
function initialize_modules() {
  // Set the container to display errors in
  alerter.init_alerter($('#error-message-container'));

  csv_handler.initialize_handler(alerter);
  csv_handler.init_row_selector('.csv_row');
  csv_handler.init_add_test();
  csv_handler.init_reset_selected($('#reset-selected'));
  csv_handler.init_add_standard($('#add-standard'));
  csv_handler.init_study_method();
}


function get_backup_measurements(){
  /* 
  This function is called when the button 'Hent målling'
  */
  // Extract url parameters
  var date = helper.convert_danish_date_to_date_format($('#id_dateofmessurement').val());
  
  if (helper.valid_danish_date_format(date)) {
    console.log('Not a valid date format');
    return;
  }

  // Send api request
  let api_url = "/api/get_backup/" + date;

  $.ajax({
    url: api_url,
    type: 'GET',
    data: { },
    success: function(data) {
      // Container to insert historical accordion into
      let history_container = $('#history_container');

      // Clear previous data
      csv_handler.clear_selected_rows();
      history_container.empty();

      // Generate New table
      for (timestamp in data) {
        
        // Initialzation
        let dataset_id = timestamp.split(':').join('');
        let dataset = data[timestamp];
      
        // Generate div containers for accordion
        var card_div = document.createElement('div');
        card_div.classList.add('card');
        
        var card_header_div = document.createElement('div');
        card_header_div.classList.add('card-header');
        card_header_div.id = 'heading-' + dataset_id;
        card_div.appendChild(card_header_div);

        var card_header = document.createElement('h2');
        card_header.classList.add('mb-0');
        card_header_div.appendChild(card_header);

        var card_button = document.createElement('button');
        card_button.classList.add('btn');
        card_button.classList.add('btn-link');
        card_button.type = 'button';
        card_button.innerText = timestamp;
        card_button.setAttribute('data-toggle', 'collapse');
        card_button.setAttribute('data-target', '#collapse-' + dataset_id);
        card_button.setAttribute('aria-expanded', 'true');
        card_button.setAttribute('aria-controls', 'collapse-' + dataset_id);
        card_header.appendChild(card_button);

        var card_body_container = document.createElement('div');
        card_body_container.classList.add('collapse');
        card_body_container.id = 'collapse-' + dataset_id;
        card_body_container.setAttribute('aria-labelledby', 'heading-' + dataset_id);
        card_body_container.setAttribute('data-parent', '#history_container');
        card_div.appendChild(card_body_container);

        var card_body = document.createElement('div');
        card_body.classList.add('card-body');
        card_body_container.appendChild(card_body);

        // Generate: table head
        var card_table = document.createElement('table');
        card_table.classList.add('table');
        card_table.classList.add('table-bordered');
        card_table.classList.add('table-hover');
        card_body.appendChild(card_table);

        var table_head = document.createElement('thead');
        card_table.appendChild(table_head);
        
        var table_head_row = document.createElement('tr');
        let TABLE_HEADERS = ['Rack', 'Position', 'Tc-99m CPM'];
        let DATASET_NAMES = ['Rack', 'Pos', 'Tc-99m CPM'];
        for (var i = 0; i < TABLE_HEADERS.length; i++) {
          var th = document.createElement('th');
          th.innerText = TABLE_HEADERS[i];

          table_head_row.appendChild(th);
        }
        table_head.appendChild(table_head_row);
        
        // Generate: table body
        var table_body = document.createElement('tbody');
        card_table.appendChild(table_body);

        for (datapoint in dataset['Tc-99m CPM']) {
          var tr = document.createElement('tr');
          tr.classList.add('history_csv_row');
          tr.id = dataset_id + '-' + datapoint

          // Generate entries for each corresponding table head
          for (i in DATASET_NAMES) {
            var td = document.createElement('td');
            td.innerText = dataset[DATASET_NAMES[i]][datapoint];
            
            tr.appendChild(td);
          }

          table_body.appendChild(tr);
        }

        // Append to history container
        history_container.append(card_div);

        // Append break between each card
        var br = document.createElement('br');
        history_container.append(br);
      }

      // Apply js to newly genereated Table
      csv_handler.init_row_selector('.history_csv_row');

      // Hide current table - if it was created
      let oldAccordion = document.getElementById("accordionContainer");
      if (oldAccordion) {
        oldAccordion.style.display = 'none';
      } else {
        // Else hide the error message generated by the server
        $('#server-error-msg').hide();
      }

      // display newly generated table
      document.getElementById("dynamic_generate_history").style.display = 'block';
    },
    error: function() {
      alerter.add_alert('Kunne ikke forbinde til serveren', 'warning');
    }
  });
}


function remove_backup_measurement(){
  /* 
    This Function happens when the button 'Tilbage til Dagens Mållinger' is clicked:

    The purpose of this function is to hide the historical data, and redisplay the old data
  */

  // Reset Selection before we go back
  csv_handler.clear_selected_rows();

  // Display either the old accordion or the server generated error message
  let old_accordion = document.getElementById("accordionContainer");
  if (old_accordion) {
    old_accordion.style.display='block';
  } else {
    $('#server-error-msg').show();
  }
  
  document.getElementById("dynamic_generate_history").style.display='none';
}


// Wait until document ready
$(function() {
  initialize_modules();

  initialize_date_fields();
  initialize_time_fields();

  add_threshold_checking();
  add_time_checking();
  add_date_checking();

  // Save fortyndingsfaktor - so it can be reused with 'Hent fortyndingsfaktor'
  let tmp_thin_fac = $('#id_thin_fac').val();
  
  $('#reset_thin_fac').on('click', function() {
    $('#id_thin_fac').val(tmp_thin_fac);
  });

  // ### 'beforeunload' handler START ###
  // Set changed parameter when a change event in the form occurs
  $("#fill-study-form :input").change(function() {
    $("#fill-study-form").data('changed', true);
  });

  /*
  Prompts the user to confirm that some information might be lost if they cancel the study

  Args:
    success_callback: function to call if the confirm returned true
    failure_callback: function to call if the confirm returned false
  */
  var confirm_cancel_study = function(success_callback, failure_callback) {
    if ($("#fill-study-form").data('changed')) {
      var resp = confirm("Skal undersøgelsen afbrydes?\nIndtastet information vil gå tabt!");
      if (resp) {
        success_callback();
      } else {
        failure_callback();
      }
    } else {
      success_callback();
    }
  };

  /*
  Helper function for the 'beforeunload' event
  */
  var unload_func = function() {
    if ($('#fill-study-form').data('changed')) {
      return "Skal undersøgelsen afbrydes?\nIndtastet information vil gå tabt!";
    }
  };

  $(window).on("beforeunload", unload_func);

  // 'Afbryd' click event
  $("#cancel").on('click', function() {
    confirm_cancel_study(
      function() {
        // Redirect on success
        window.location.replace("/list_studies");
      },
      function() { }
    );
  });

  // Sidemenu item clicked
  $(".menu-item").click(function() {
    $(window).off("beforeunload");

    confirm_cancel_study(
      function() { },
      function() {
        // Reenable the beforeunload function if failed
        $(window).on("beforeunload", unload_func);
      }
    );
  });
  // ### 'beforeunload' handler END ###



  // 'Beregn' on click event
  $('#calculate').click(function() {
    // Disable the 'beforeunload' event as to not trigger it
    $(window).off("beforeunload");
  
    alerter.clear_alerts();

    // Check if any tests have been added
    let test_count = $('#test-data-container .form-row').length;
    if (test_count == 0) {
      alerter.add_alert(
        'Kan ikke beregne uden prøver.',
        'danger'
      );
      return false;
    } else if (test_count == 1 && $('id_study_type_2').is(":checked")) {
      alerter.add_alert(
        'Flere Prøve modellen er valgt, men der er kun tilføjet en prøve',
        'danger'
      );
      return false;
    }

    // Check that all fields are filled out or has a danger alert
    let ids_to_check = [
      "#id_cpr",
      "#id_name",
      "#id_sex",
      "#id_age",
      "#id_height",
      "#id_weight",
      "#id_vial_weight_before",
      "#id_vial_weight_after",
      "#id_injection_time",
      "#id_injection_date",
      "#id_std_cnt",
      "#id_thin_fac",
      '#standard-field'
    ];
    
    is_valid = true;
    failed_id = "";
    for (var i = 0; i < ids_to_check.length; i++) {
      if ($(ids_to_check[i]).val() == "" || alerter.has_alert(ids_to_check[i], 'danger')) {
        is_valid = false;
        failed_id = ids_to_check[i];
        break;
      }
    };

    if (!is_valid) {
      alerter.add_alert(
        'Et eller flere felter er ikke udfyldt korrekt.',
        'danger'
      );
     
      alerter.add_field_alert($(failed_id), 'danger');

      return false;
    }

    // Check that injection date isn't in the future
    var now = new Date();
    var inj_date_val = helper.convert_danish_date_to_date_format($('#id_injection_date').val());
    var inj_time_val = $('#id_injection_time').val();
    var dt_str = inj_date_val + ' ' + inj_time_val + ':00';
    var dt = Date.parse(dt_str);

    if (dt > now) {
      alerter.add_alert(
        'Injektionstidspunkt kan ikke være i fremtiden.',
        'danger'
      );
      return false;
    }

    // Check that the difference between the injection before and after isn't negative
    var weight_before = $('#id_vial_weight_before').val();
    var weight_after = $('#id_vial_weight_after').val();
    if (weight_before - weight_after <= 0) {
      alerter.add_alert(
        'Injektionsvægt efter kan ikke være større end den før.',
        'danger'
      )
      return false;
    }

    // Check that all test dates are after the injection date
    var date_fields = $("#test-data-container [name='study_date']");
    var time_fields = $("#test-data-container [name='study_time']");

    var inj_date_val = helper.convert_danish_date_to_date_format($('#id_injection_date').val());
    var inj_time_val = $('#id_injection_time').val();
    var dt_str = inj_date_val + ' ' + inj_time_val + ':00';
    var dt = Date.parse(dt_str);

    for (var i = 0; i < date_fields.length; i++) {
      var t_date = helper.convert_danish_date_to_date_format(date_fields[i].value);
      var t_str = t_date + ' ' + time_fields[i].value + ':00';

      var t = Date.parse(t_str);

      if (dt >= t) { // injection timestamp >= test timestamp
        alerter.add_alert(
          'Prøvetidspunkter kan ikke være før injektionstidspunkter.',
          'danger'
        );
        return false;
      }
    }

    return true;
  });

  // 'Gem' on click event
  $('#save').click(function() {
    // Disable the 'beforeunload' event as to not trigger it
    $(window).off("beforeunload");
  
    alerter.clear_alerts();
  });

  // Disable all enter keys on fields
  $('input').on('keyup keypress', function(e) {
    var keyCode = e.keyCode || e.which;
    
    if (keyCode === 13) { 
      e.preventDefault();
      return false;
    }
  });

  // Initial check to see if any study dates differ from the injection date
  var inj_date = $("#id_injection_date").val();
  $("#test-data-container .form-row .form-group:first-child input").each(function() {
    if (inj_date != $(this).val()) { // One of the study dates differ from the injection date
      alerter.add_alert("En eller flere blodprøve(r) har anden dato end injektionsdatoen.", "warning");
      return false; // I.e. break
    }
  });
});
