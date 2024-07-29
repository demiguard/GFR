var csv_handler;

/*
Initializes the correct sizing of the select test div on window resizing

Remarks:
  This is just a temporary fix and should idealy be fixed in css
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

function get_backup_measurements() {
  /*
  This function is called when the button 'Hent målling'
  */
  // Extract url parameters
  var date = helper.convert_danish_date_to_date_format($('#id_dateofmessurement').val());

  if (!helper.is_valid_date(date)) {
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
      //csv_handler.clear_selected_rows();
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

            if (i == 2) {
              td.innerText = Math.round(dataset[DATASET_NAMES[i]][datapoint]); // Round to remove decimals
            } else {
              td.innerText = dataset[DATASET_NAMES[i]][datapoint];
            }

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
      //csv_handler.init_row_selector('.history_csv_row');

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

      // Ensure that the now history rows are clickable
      csv_handler.init_row_selector(".history_csv_row");
    },
    error: function() {
      alerter.add_alert('Kunne ikke forbinde til serveren', 'warning');
    }
  });
}


function remove_backup_measurement() {
  /*
    This Function happens when the button 'Tilbage til Dagens Mållinger' is clicked:

    The purpose of this function is to hide the historical data, and redisplay the old data
  */

  // Reset Selection before we go back
  //csv_handler.clear_selected_rows();

  // Display either the old accordion or the server generated error message
  let old_accordion = document.getElementById("accordionContainer");
  if (old_accordion) {
    old_accordion.style.display='block';
  } else {
    $('#server-error-msg').show();
  }

  document.getElementById("dynamic_generate_history").style.display='none';
}


function add_threshold_checking(field_alerter) {
  /*
  Adds threshold checking on number fields

  Args:
    field_alerter: field alerter used to register the input handler
  */
  // Mappings from field id to their danish display name
  let FIELD_NAME_MAPPINGS = {
    "#id_height"             : "Højde",
    "#id_weight"             : "Vægt",
    "#id_vial_weight_before" : "Sprøjtevægt før injektion",
    "#id_vial_weight_after"  : "Sprøjtevægt efter injektion",
    "#id_thin_fac"           : "Fortyndingsfaktor",
    "#id_Standard"           : "Standardtælletal"
  }

  let id_thresholds = [
    {'id': '#id_height',              'min_val': 0,    'max_val': 210},
    {'id': '#id_weight',              'min_val': 3.5,    'max_val': 500},
    {'id': '#id_vial_weight_before',  'min_val': 2,     'max_val': 5},
    {'id': '#id_vial_weight_after',   'min_val': 0,     'max_val': 5},
    {'id': '#id_thin_fac',            'min_val': 3500,  'max_val': 10000},
    {'id': '#id_Standard',          'min_val': 0,     'max_val': 100000}
  ];

  for (var i = 0; i < id_thresholds.length; i++) {
    let curr_row = id_thresholds[i]
    let curr_field = $(curr_row.id);

    field_alerter.add_input_field_alert(
      curr_field,
      FIELD_NAME_MAPPINGS[curr_row.id] + " ligger udenfor det forventede interval.",
      "warning",
      function(val) {
        // Safely handle commas in the fields before checking
        let f_val = helper.str_to_float(val);

        return helper.within_bound(f_val, curr_row.min_val, curr_row.max_val);
      }
    );
  }
}

function add_inj_comparison(field_alerter) {
  /*
  Adds checking for injection weight fields

  Args:
    field_alerter: field alerter used to register the input handler
  */

  // Variables used to handle the triggering states for interfield checking
  // i.e. they're used to avoid infinite loops of triggering eachother
  var trigger_after  = true;
  var trigger_before = true;

  field_alerter.add_input_field_alert(
    $("#id_vial_weight_after"),
    "Sprøjtevægt efter injektion kan ikke være større end eller lig med sprøjtevægt før.",
    "danger",
    function(val) {
      // Safely handle commas in the fields before checking
      let comp_field = $("#id_vial_weight_before");
      let comp_val = helper.str_to_float(comp_field.val());
      let f_val = helper.str_to_float(val);

      if (trigger_before) {
        trigger_after = false;
        comp_field.trigger("input");
        trigger_after = true;
      }

      return ((f_val < comp_val) || !val);
    }
  );

  field_alerter.add_input_field_alert(
    $("#id_vial_weight_before"),
    "Sprøjtevægt før injektion kan ikke være mindre end eller lig med sprøjtevægt før.",
    "danger",
    function(val) {
      // Safely handle commas in the fields before checking
      let comp_field = $("#id_vial_weight_after");
      let comp_val = helper.str_to_float(comp_field.val());
      let f_val = helper.str_to_float(val);

      if (trigger_after) {
        trigger_before = false;
        comp_field.trigger("input");
        trigger_before = true;
      }

      return ((f_val >= comp_val) || !val);
    }
  );
}

function add_datetime_checking(field_alerter) {
  /*
  Adds checking on time fields to ensure that dates and timestamps are correctly formatted

  Args:
    field_alerter: field alerter used to register the input handler
  */
  // Mappings from field ids to their danish display text for alert messages
  let ID_NAME_MAPPINGS = {
    "#id_InjectionTime": "Injektionstidspunkt",
    "#id_SampleTime": "Prøvetidspunkt",
    "#id_InjectionDate": "Injektionsdato",
    "#id_SampleDate": "Prøvedato",
    "#id_dateofmessurement": "Hent fra backup dato",
    "#PatientBirthDate": "Fødselsdato",
  };

  let time_ids = [
    { "id": "#id_InjectionTime", "alert_type": "danger"},
    { "id": "#id_SampleTime", "alert_type": "danger" },
  ];

  let date_ids = [
    { "id": "#id_InjectionDate", "alert_type": "danger" },
    { "id": "#id_SampleDate", "alert_type": "danger" },
    { "id": "#id_dateofmessurement", "alert_type": "warning" },
    { "id": "#id_PatientBirthDate", "alert_type": "danger" },
  ];

  // Add to time fields
  for (var i = 0; i < time_ids.length; i++) {
    let curr_row = time_ids[i];
    let name_mapping = ID_NAME_MAPPINGS[curr_row.id];

    field_alerter.add_input_field_alert(
      $(curr_row.id),
      name_mapping + " er ikke korrekt formatteret.",
      curr_row.alert_type,
      helper.is_valid_time
    );
  }

  // Add to date fields
  for (var i = 0; i < date_ids.length; i++) {
    let curr_row = date_ids[i];
    let name_mapping = ID_NAME_MAPPINGS[curr_row.id];

    field_alerter.add_input_field_alert(
      $(curr_row.id),
      name_mapping + " er ikke korrekt formatteret.",
      curr_row.alert_type,
      helper.is_danish_date
    );
  }
}

function add_timefield_auto_colons() {
  /*
  Initializes time fields:
  automatically add colons after the second character has been typed
  */
  helper.auto_char($("input[name='InjectionTime']"), ':', 2);
  helper.auto_char($("input[name='SampleTime']"), ':', 2);
  helper.auto_char($(".sample_time_field"), ':', 2)
}

function initialize_date_fields() {
  /*
  Initializes date fields:
  add datepicker widgets to each field
  */
  // Add date pickers to date fields
  $('#id_SampleDate').datepicker({format: 'dd-mm-yyyy'});
  $('#id_InjectionDate').datepicker({format: 'dd-mm-yyyy'});
  $('#id_PatientBirthDate').datepicker({format:'dd-mm-yyyy'});
  $('#id_dateofmessurement').datepicker({format:'dd-mm-yyyy'});}

function initialize_number_fields() {
  /*
  Initialize number fields:

  */

  var ids_with_comma = ['#id_height', '#id_weight', '#id_vial_weight_before', '#id_vial_weight_after'];
  var ids_no_comma   = ['#id_thin_fac', '#id_standcount'];

  var ids_with_comma_length = ids_with_comma.length;
  var ids_no_comma_length = ids_no_comma.length;

  for (var i = 0; i < ids_with_comma_length; i++) {
    $(ids_with_comma[i]).val(bad_input_handler.replace_dots_with_commas($(ids_with_comma[i]).val()));
    bad_input_handler.number($(ids_with_comma[i]));
  }

  for(var i = 0; i < ids_no_comma_length; i++){
    $(ids_no_comma[i]).val(bad_input_handler.remove_decimal_values($(ids_no_comma[i]).val()));
    bad_input_handler.number($(ids_no_comma[i]));
  }

  $(".value-field").each(function(){
    this.value = bad_input_handler.remove_decimal_values(this.value);
    bad_input_handler.number($(this));
  });
}

function initialize_before_unload_handler() {
  /*
  The before unload handler ensures that users are prompted
  with an alert if they have entered any data in any fields
  that entered data is lost once they leave the site without
  saving.
  */
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
  /*$("#cancel").on('click', function() {
    confirm_cancel_study(
      function() {
        // Redirect on success
        window.location.replace("/list_studies");
      },
      function() { }
    );
  });
  */
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
}

function initialize_thin_fac() {
  // Save fortyndingsfaktor - so it can be reused with 'Hent fortyndingsfaktor'
  let tmp_thin_fac = $('#id_thin_fac').val();

  $('#reset_thin_fac').on('click', function() {
    $('#id_thin_fac').val(tmp_thin_fac);
  });
}

function initialize_save_button(alerter) {
  // 'Gem' on click event
  $('#save').click(function() {
    alerter.remove_alert('no_tests');
    alerter.remove_alert('model_tests_selected');
    alerter.remove_alert('missing_fields');
    alerter.show_alerts();

    // Disable the 'beforeunload' event as to not trigger it
    $(window).off("beforeunload");

    if (alerter.alert_type_exists("danger", true)) {
      return false;
    }
  });
}

/*
Performs initialization of required modules
*/
function initialize_csv_handler(alerter) {
  // Set the container to display errors in
  csv_handler = new CSVHandler(alerter);

  csv_handler.init_row_selector(".csv_row");
  csv_handler.init_add_button_handler($('#add-test'));
  csv_handler.init_reset_selected($('#reset-selected'));
  csv_handler.init_add_standard($('#add-standard'));
  csv_handler.init_study_method();

  $("#get-backup-btn").on("click", get_backup_measurements);
  $("#remove-backup-btn").on("click", remove_backup_measurement);
}

function initialize_calculate_button(alerter) {
  // 'Beregn' on click event
  $('#calculate').click(function() {
    // Disable the 'beforeunload' event as to not trigger it
    $(window).off("beforeunload");

    // alerter.clear_alerts();
    alerter.hide_alerts();

    // Check if any tests have been added
    alerter.remove_alert('no_tests');
    alerter.remove_alert('model_tests_selected');
    alerter.remove_alert('missing_fields');
    alerter.remove_alert('inj_future');
    alerter.remove_alert('inj_weight_too_large');
    alerter.remove_alert('test_before');

    let test_count = $('#test-data-container .form-row').length;

    if(test_count == 0){
      alerter.add_alert(
        'model_tests_selected',
        "Der skal vælges mindst 1 prøve før udregning kan laves!",
        "danger"
      );
      return false;
    }

    if (test_count == 1 && $('id_study_type_2').is(":checked")) {
      alerter.add_alert(
        'model_tests_selected',
        'Flere Prøve modellen er valgt, men der er kun tilføjet en prøve',
        'danger'
      );

      alerter.show_alerts();
      return false;
    }

    if (alerter.alert_type_exists("danger", null)) {
      alerter.show_alerts();
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
      "#id_InjectionDate",
      "#id_std_cnt",
      "#id_thin_fac",
      "#id_Standard",
      "#id_birthdate",
    ];






    is_valid = true;
    failed_id = "";
    for (var i = 0; i < ids_to_check.length; i++) {
      if ($(ids_to_check[i]).val() == "") {
        is_valid = false;
        failed_id = ids_to_check[i];
        break;
      }
    };

    let classes_to_Check = [
      ".sample_time_field",
      ".sample_count_field"
    ]

    if (is_valid) for (const field of $(".sample_time_field")) {
      const timeVal = $(field).val()
      const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/
      if (!timeRegex.test(timeVal)) {
        failed_id = ".sample_time_field";
        is_valid = false;
        break;
      }
    }

    if (is_valid) for (const field of $(".sample_count_field")){
      const count_val = Number($(field).val());
      if (count_val <= 0) {
        failed_id = ".sample_count_field";
        is_valid = false;
        break;
      }
    }

    if (!is_valid) {
      const ErrorMap = new Map();
      ErrorMap.set("#id_cpr", "CPR feltet")
      ErrorMap.set("#id_name", "navne feltet")
      ErrorMap.set("#id_sex", "Køn feltet")
      ErrorMap.set("#id_age", "Alders feltet")
      ErrorMap.set("#id_height", "Højde feltet")
      ErrorMap.set("#id_weight", "Vægt feltet")
      ErrorMap.set("#id_vial_weight_before", "SprøjteVægt før feltet")
      ErrorMap.set("#id_vial_weight_after", "Sprøjtevægt efter feltet")
      ErrorMap.set("#id_InjectionTime", "injektions tidpunktet feltet")
      ErrorMap.set("#id_InjectionDate", "injektions datoen feltet")
      ErrorMap.set("#id_std_cnt", "Standard tælletals feltet")
      ErrorMap.set("#id_thin_fac", "Fortydningstals felt")
      ErrorMap.set("#id_Standard", "Standard tælletals feltet")
      ErrorMap.set("#id_birthdate",    "Fødselsdags feltet")
      ErrorMap.set(".sample_time_field", "En prøves tids felt")
      ErrorMap.set(".sample_count_field", "En prøves count felt")

      const ErrorFieldText = ErrorMap.get(failed_id)

      alerter.add_alert(
        'missing_fields',
        ErrorFieldText +' er ikke udfyldt korrekt.',
        'danger'
      );

      // alerter.add_field_alert($(failed_id), 'danger');
      alerter.show_alerts();
      return false;
    }

    // Check that injection date isn't in the future
    var now = new Date();
    var inj_date_val = helper.convert_danish_date_to_date_format($('#id_InjectionDate').val());
    var inj_time_val = $('#id_InjectionTime').val();
    var dt_str = inj_date_val + ' ' + inj_time_val + ':00';
    var dt = Date.parse(dt_str);

    if (dt > now) {
      alerter.add_alert(
        'inj_future',
        'Injektionstidspunkt kan ikke være i fremtiden.',
        'danger'
      );
      alerter.show_alerts();
      return false;
    }

    // Check that the difference between the injection before and after isn't negative
    var weight_before = $('#id_vial_weight_before').val();
    var weight_after = $('#id_vial_weight_after').val();
    if (weight_before - weight_after <= 0) {
      alerter.add_alert(
        'inj_weight_too_large',
        'Injektionsvægt efter kan ikke være større end den før.',
        'danger'
      );
      alerter.show_alerts();
      return false;
    }

    // Check that all test dates are after the injection date
    var date_fields = $("#test-data-container [name='sample_date']");
    var time_fields = $("#test-data-container [name='sample_time']");

    var inj_date_val = helper.convert_danish_date_to_date_format($('#id_InjectionDate').val());
    var inj_time_val = $('#id_InjectionTime').val();
    var dt_str = inj_date_val + ' ' + inj_time_val + ':00';
    var dt = Date.parse(dt_str);

    for (var i = 0; i < date_fields.length; i++) {
      var t_date = helper.convert_danish_date_to_date_format(date_fields[i].value);
      var t_str = t_date + ' ' + time_fields[i].value + ':00';

      var t = Date.parse(t_str);

      if (dt >= t) { // injection timestamp >= test timestamp
        alerter.add_alert(
          'test_before',
          'Prøvetidspunkter kan ikke være før injektionstidspunkter.',
          'danger'
        );
        alerter.show_alerts();
        return false;
      }
    }

    alerter.show_alerts();
    return true;
  });
}

$(function() {
  let field_alerter = new FieldAlerter($("#error-message-container"));

  init_test_div_resizer();
  helper.disable_enter_form_submit($('#fill-study-form'));

  add_timefield_auto_colons();

  initialize_date_fields();


  initialize_before_unload_handler();

  initialize_save_button(field_alerter);

  initialize_calculate_button(field_alerter);

  initialize_csv_handler(field_alerter);

  // Initialize alerters

  add_threshold_checking(field_alerter);

  add_inj_comparison(field_alerter);

  add_datetime_checking(field_alerter);
});
