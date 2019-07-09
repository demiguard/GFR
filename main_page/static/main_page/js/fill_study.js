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
    {'id': '#id_thin_fac',            'min_val': 3500,  'max_val': 7500},
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
        return !helper.valid_date_format(field.val());
      }
    );
  }
}

/*
Initializes date fields
*/
function initialize_date_fields() {
  // Add date pickers to date fields
  $('#id_injection_date').datepicker({format: 'yyyy-mm-dd'});
  $('#id_study_date').datepicker({format: 'yyyy-mm-dd'});
  $('#id_birthdate').datepicker({format:'yyyy-mm-dd'});
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

var json_response;

function GetBackupMessurements(){
  var date = $('#id_dateofmessurement').val();
  
  fetch('/ajax/get_backup/' + date).then(
    function(response){
      if (response.status == 200){
        return response.json();
      } else {
        return null
      }
    }
  ).then(
    function(json) {
      if (json == null) {
        //There's no data, we can't really tell why because you know, js
        //Perhaps display an error message? Ooh well sounds like a simon problem
      } else {
        //There's data
        var history_container = $('#history_container');
        json_response = json;
        // Clear Selected csv
        csv_handler.clear_selected_rows();
        // Empty current history Container
        history_container.empty();
        // Generate New table
        for (json_dataset in json_response) {
          //Initialzation
          var timestamp = json_dataset;
          var dataset_id = timestamp.split(':').join('');
          var dataset = json_response[timestamp];
          //Generate Card
          // To anyone asking why js is crap, Look no further than below, for here rests a monster so faul no coder should ever look at it!
          // But to those unsung heroes, that despite this dire warning, deside to attempt to maintain or boldy try expand on it
          // The idea is as following:
          // div card  
          // div header
          // h2
          // button
          // button text
          // end button
          // end h2
          // end header
          // Target
          // Cardbody
          // Table
          // end cardbody
          // end target
          // div end card
          // To those Wondering why the code endend up THIS cancerous, it's mainly due to when you append a div, it closes it for you

          var card_str = '<div class="card">\n';
          card_str += '<div id="heading-' + dataset_id + '" class="card-header">\n';
          card_str += '<h2 class="mb-0">\n';
          card_str += '<button class="btn btn-link" type ="button" data-toggle="collapse" data-target="#collapse-'+ dataset_id + '" aria-expanded="true" aria-controls="collapse-'+dataset_id +'">\n';
          card_str += timestamp + '\n';
          card_str += '</button>\n';
          card_str += '</h2>\n';
          card_str += '<!-- end div card-header -->\n';
          card_str += '</div>\n';
          //Header done, Generate body
          card_str += '<div id="collapse-' + dataset_id + '" class="collapse" aria-labelledby="heading-'+ dataset_id +'" data-parent="#accordionContainer">\n';
          card_str += '<div class ="card-body">\n';
          //Generate Table 
          card_str += '<table class="table table-bordered table-hover">\n';
          card_str += '<thead>\n';
          card_str += '<tr>\n';
          card_str += '<th>Rack</th>\n';
          card_str += '<th>Position</th>\n';
          card_str += '<th>Tc-99 CPM</th>\n';
          card_str += '</tr>\n';
          card_str += '</thead>\n';
          card_str += '<tbody>\n';
          //Generate Data for Table
          for (datapoint in dataset['Tc-99m CPM']) {
            if (datapoint != undefined) {
              card_str += '<tr id="' + dataset_id + '-' + datapoint + '" class="history_csv_row">\n';
              card_str += '<td>' + dataset['Rack'][datapoint] + '</th>\n';
              card_str += '<td>' + dataset['Pos'][datapoint] + '</th>\n';
              card_str += '<td>' + dataset['Tc-99m CPM'][datapoint] + '</th>\n';
              card_str += '</tr>\n';
            }
          }
          card_str += '</tbody>\n';
          card_str += '</table>\n';
          card_str += '<!-- End of card body -->\n';
          card_str += '</div>\n';
          card_str += '<!-- End of collapse target -->\n';
          card_str += '</div>\n';
          //Generate Card Closing 
          card_str += '<!-- end div card -->\n';
          card_str +='</div>\n';
          card_str +='<br>\n';

          history_container.append(card_str);
        }
        csv_handler.init_row_selector('.history_csv_row');

        // Hide current table
        document.getElementById("accordionContainer").style.display = 'none';
        document.getElementById("dynamic_generate_history").style.display = 'block';
        // display


      }
    }
  )
}

function RemoveBackupMessurement(){
  // Reset Selection before we go back
  csv_handler.clear_selected_rows();

  document.getElementById("accordionContainer").style.display='block';
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
  $("#cancel").click(function() {
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
        'Et eller flere felter er ikke udfyldt.',
        'danger'
      );
     
      alerter.add_field_alert($(failed_id), 'danger');

      return false;
    }

    // Check that injection date isn't in the future
    var now = new Date();
    var inj_date_val = $('#id_injection_date').val();
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

    var inj_date_val = $('#id_injection_date').val();
    var inj_time_val = $('#id_injection_time').val();
    var dt_str = inj_date_val + ' ' + inj_time_val + ':00';
    var dt = Date.parse(dt_str);

    for (var i = 0; i < date_fields.length; i++) {
      var t_str = date_fields[i].value + ' ' + time_fields[i].value + ':00';
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

    // Check that if 'sprøjtevægt efter injektion' is entered then 'sprøjtevægt før injektion' must also be entered
    inj_after = $("#id_vial_weight_after").val();
    inj_before = $("#id_vial_weight_before").val();
    
    if (inj_after != "" && inj_before == "") {
      alerter.add_alert('Sprøjtevægt før skal indtastes.', 'danger');
      alerter.add_field_alert($("#id_vial_weight_before"), 'danger');

      $(window).on("beforeunload", unload_func);
      return false;
    }
  });
});