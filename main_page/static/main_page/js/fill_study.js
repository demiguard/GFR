// Wait until document ready
$(function() {
  /*
  Initializes the correct sizing the select test div on window resizing
  
  TODO: THIS IS JUST A TEMPORARY FIX AND SHOULD FIXED IN CSS
  */
  (function init_test_div_resizer() {
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
  })();

  /* 
  Adds an alert to the error message container

  Args:
    msg: alert message to display
    type: type string representing the type of alert to display

  Remark:
    Alerts can only be either 'warning' or 'danger'
    For more details: https://getbootstrap.com/docs/4.2/components/alerts/
  */
  function add_alert(msg, type) {
    // Ensure type is valid
    let valid_types = [
      'warning',
      'danger'
    ]

    if (!valid_types.includes(type)) {
      throw new Error("Invalid type for alert.");
    }
    
    // Create strong indicator
    var alert_indicator = document.createElement('strong');
    var indicator_msg = '';
    if (type == valid_types[0]) {         // Warning
      indicator_msg = 'Advarsel: ';
    } else if (type == valid_types[1]) {  // Danger
      indicator_msg = 'Fejl: ';
    }
    alert_indicator.innerHTML = indicator_msg;

    // Create alert
    var alert_div = document.createElement('div');
    alert_div.classList.add('alert');
    alert_div.classList.add('alert-' + type);
    alert_div.innerHTML = msg;

    // Insert alert at top of container
    alert_div.prepend(alert_indicator);
    $('#error-message-container').prepend(alert_div);
  }

  /*
  Removes all alerts
  */
  function remove_alerts() {
    $('#error-message-container').empty();
  }

  /*
  Helper function to round of floating point numbers

  Args:
    num: number to round off
    n: how many decimals to round off to
  */
  function round_to(num, n) {
    p = Math.pow(10, n);
    return Math.round(num * p) / p;
  }

  /*
  Automatically appends a character after the n'th character is typed.

  Args:
    field: the field to apply the bind on.
    c: character to append
    n: after how many characters should it append

  Remark:
    The function ignores backspaces (the character code 8)
  */
  function auto_char(field, c, n) {
    function add_char(key){
      if (key.which !== 8){
        var number_of_chars = $(this).val().length;
        if (number_of_chars === n){
          var copyvalue = $(this).val();
          copyvalue += c;
          $(this).val(copyvalue);
        }
      }
    }
    
    field.bind('keypress', add_char);
  }

  // Adding Colons to time fields
  auto_char($("input[name='injection_time']"), ':', 2);
  auto_char($("input[name='study_time']"), ':', 2);
  
  //END:Adding Colons to time fields

  // Add date pickers to date fields
  $('#id_injection_date').datepicker({format: 'yyyy-mm-dd'});
  $('#id_study_date').datepicker({format: 'yyyy-mm-dd'});
  $('#id_birthdate').datepicker({format:'yyyy-mm-dd'});

  // Set changed parameter when a change event in the form occurs
  $("#fill-study-form :input").change(function() {
    $("#fill-study-form").data('changed', true);
  });

  var unload_func = function() {
    if ($('#fill-study-form').data('changed')) {
      return "Skal undersøgelsen afbrydes?\nIndtastet information vil gå tabt!";
    }
  }

  $(window).on("beforeunload", unload_func);

  // 'Afbryd' click event
  $("#cancel").click(function() {
    if ($("#fill-study-form").data('changed')) {
      var resp = confirm("Skal undersøgelsen afbrydes?\nIndtastet information vil gå tabt!");
      if (!resp) {
        return false;
      }
    }

    window.location.replace("/list_studies");
  });

  // Sidemenu item clicked
  $(".menu-item").click(function() {
    $(window).off("beforeunload");

    if ($("#fill-study-form").data('changed')) {
      var resp = confirm("Skal undersøgelsen afbrydes?\nIndtastet information vil gå tabt!");
      if (!resp) {
        $(window).on("beforeunload", unload_func);
        return false;
      }
    }

    return true;
  });

  // Validates a given time string (format: tt:mm)
  function valid_time_format(time_str) {
    let TIME_FORMAT = /^([0-1][0-9]|[2][0-3]):[0-5][0-9]$/;
    return TIME_FORMAT.test(time_str);
  }

  // Validates a given date string (format: YYYY-MM-DD)
  function valid_date_format(date_str) {
    let DATE_FORMAT = /^[0-9]{4}-([0][1-9]|[1][0-2])-([0-2][0-9]|[3][0-1])$/;
    return DATE_FORMAT.test(date_str);
  }

  // 'Tilføj' clicked for manual study entry
  var test_count = $('.row-lock-btn').length; // Get the count of previous samples

  // Add the on click event handlers to the previous sample locks
  $('.row-lock-btn').each(function() {
    $('#' + this.id).on('click', function() {
      var resp = confirm("Advarsel: manuel rettelse bør kun anvendes i nødstilfælde!");
          
      if (resp) {
        var form_parent = $(this).parent().parent();
        form_parent.children('.readonly-field').each(function() {
         $(this).children('input').attr('readonly', false);
        });
      }
    });
  });

  // Add the on click event handlers to the previous sample remove buttons
  $('.row-remove-btn').each(function() {
    $('.row-remove-btn').on('click', function() {
      test_count--;
      $(this).parent().parent().remove();
      add_add_test_functionality();

    });
  });


  var csv_row_ids_array = [];
  var sanity_checker = 0.25
  $('#add-test').click(function() {
    // Reset error messages container
    remove_alerts();

    // Reset borders
    $('#id_study_time').css('border', '1px solid #CED4DA');
    $('#id_study_date').css('border', '1px solid #CED4DA');
    
    // Extract form contents
    var study_time = $('#id_study_time').val();
    var study_date = $('#id_study_date').val();

    // Validate contents
    if (valid_date_format(study_date)) {
      if (valid_time_format(study_time)) { 
        if (csv_row_ids_array.length > 0){
        // Avg. of two selected rows
        var sum = 0
        if (csv_row_ids_array.length >= 2) {
          var data_values = []

          csv_row_ids_array.forEach(element => {
            data_values.push(parseFloat($('#' + element).children().eq(2).text()))
            sum += parseFloat($('#' + element).children().eq(2).text()) / csv_row_ids_array.length
          });
          
          var sanity = true;
          for (i = 0; i < csv_row_ids_array.length; i++) {
            for (j = i+1; j < csv_row_ids_array.length; j++){
              var distance = Math.abs((data_values[i] - data_values[j]) / (data_values[i] + data_values[j])); 
              sanity &= distance > sanity_checker;
            }
          }

          if (sanity) {
            add_alert('Datapunkterne har meget stor numerisk forskel, Tjek om der ikke er sket en tastefejl!', 'warning');
          }

        } else { //Only 1 element selected
          csv_row_ids_array.forEach(element => {
            sum += parseFloat($('#' + element).children().eq(2).text())
          });

          add_alert('Det anbefaldes at der bruges 2 datapunkter for større sikkerhed', 'warning');
        }

        // ------------ Range Checker --------------- 
        // Range checker for kids
        if ($('input[name=study_type]:checked').val() == 1) {
          //Time ranges in milisecounds!
          var range_low = 110*60*1000
          var range_high = 130*60*1000
          
          var time_of_inj = new Date($('#id_injection_date').val() + 'T' + $('#id_injection_time').val() + ':00')
          var time_of_sample = new Date($('#id_study_date').val() + 'T' + $('#id_study_time').val() + ':00')

          if (!(time_of_sample - time_of_inj >= range_low && time_of_sample - time_of_inj <= range_high)) {
            add_alert(
              'Prøven er foretaget udenfor det tidskorrigeret interval, prøven kan derfor være upræcis<br>Det anbefalet interval er imellem 110 minuter og 130 minuter.', 
              'warning'
            );
          }
        }

        // Range Checker for grown ups
        if ($('input[name=study_type]:checked').val() == 0) {
          // Time ranges in milisecounds!
          var range_low = 180*60*1000
          var range_high = 240*60*1000
          
          var time_of_inj = new Date($('#id_injection_date').val() + 'T' + $('#id_injection_time').val() + ':00')
          var time_of_sample = new Date($('#id_study_date').val() + 'T' + $('#id_study_time').val() + ':00')

          if (!(time_of_sample - time_of_inj >= range_low && time_of_sample - time_of_inj <= range_high)) {
            add_alert(
              'Prøven er foretaget udenfor det tidskorrigeret interval af metoden, prøven kan derfor være upræcis.<br>Det anbefalet interval er imellem 180 minuter og 240 minuter',
              'warning'
            );
          }
        }

        var html_row_base_begin = "<div class=\"form-row\">";
        var html_row_base_end = "</div>";
        var html_field_begin = "<div class=\"form-group col-md-3 readonly-field\">";
        var html_field_input_begin = "<input type=\"text\" class=\"form-control\" name=\"";
        var html_field_input_end = "\" value=\""
        var html_field_end = "\" readonly></div>";
        
        var html_button_div = "<div class=\"form-group col-md-3\">"
        var html_button_div_end = "</div>";
        var html_remove_btn = "<input type=\"button\" value=\"X\" class=\"row-remove-btn btn btn-danger\">";
        var html_lock_btn = "<input type=\"button\" value=\"&#x1f512;\" class=\"row-lock-btn btn btn-light\" id=\"lock" + test_count.toString() + "\">";

        $('#test-data-container').append(html_row_base_begin);
        $('#test-data-container .form-row').last().append(html_field_begin + html_field_input_begin + "study_date" + html_field_input_end + study_date + html_field_end);
        $('#test-data-container .form-row').last().append(html_field_begin + html_field_input_begin + "study_time" + html_field_input_end + study_time + html_field_end);
        $('#test-data-container .form-row').last().append(html_field_begin + html_field_input_begin + "test_value" + html_field_input_end + round_to(sum, 3) + html_field_end);
        $('#test-data-container .form-row').last().append(html_button_div + html_remove_btn + html_lock_btn + html_button_div_end);
        $('#test-data-container').append(html_row_base_end);

        // Register on click event-handler for remove row button
        $('.row-remove-btn').on('click', function() {
          test_count--;
          $(this).parent().parent().remove();
          if(test_count == 0) {
            add_add_test_functionality();
          }

          remove_alerts();
        });

        // 'Lock' button on click
        var lock_str = '#lock' + test_count.toString();
        $(lock_str).on('click', function() {
          var resp = confirm("Advarsel: Manuel rettelse bør kun anvendes i nødstilfælde!");
          
          if (resp) {
            var form_parent = $(this).parent().parent();
            form_parent.children('.readonly-field').each(function() {
             $(this).children('input').attr('readonly', false);
            });
          }
        });

        test_count++;

        // Clear input fields
        $('#id_study_time').val("");
        $('#id_study_value').val("");

        // Deselect the two tests
        csv_row_ids_array.forEach(function(item) {
          $("#" + item).css('background-color', 'white');
        });

        csv_row_ids_array = [];

        // If method one point Remove option to add more tests
        if ($('input[name="study_type"]:checked').val() != 2) {
          remove_add_test_functionality()
        }

        } else { //Not enought Data selected
          add_alert('Der skal bruges midst 1 datapunkt, 2 anbefales.', 'danger');
        }
      } else { // Incorrect time formatinjection_time
        $('#id_study_time').css('border', '2px solid lightcoral');
      }
    } else { // Incorrect date format
      $('#id_study_date').css('border', '2px solid lightcoral');
    }
  });

  // Handler for tilføj-standart button
  $('#add-standart').on('click', function() {
    remove_alerts();

    if(csv_row_ids_array.length > 0) {
      var sum = 0;
      if (csv_row_ids_array.length >= 2) {
        // TO DO ADD Sanity checks
        var data_values = [];
        csv_row_ids_array.forEach(element => {
          data_values.push(parseFloat($('#' + element).children().eq(2).text()))  
          sum += parseFloat($('#' + element).children().eq(2).text()) / csv_row_ids_array.length
        });
        var sanity = true;
        for (i = 0; i < csv_row_ids_array.length; i++) {
          for (j = i+1; j < csv_row_ids_array.length; j++){
            var distance = Math.abs((data_values[i] - data_values[j]) / (data_values[i] + data_values[j])); 
            sanity &= distance > sanity_checker;
          }

        }
        if (sanity) { // Value to be updated
          add_alert('Datapunkterne har meget stor numerisk forskel. Tjek om der ikke er sket en tastefejl.', 'warning');
        }
      } else {
        csv_row_ids_array.forEach(element => {
          sum += parseFloat($('#' + element).children().eq(2).text())
        });
      }
    
      if (csv_row_ids_array.length > 1) {
        //If lenght = 2,3
        $('#standart-text').val(round_to(sum, 3));
      } else {
        // If lenght = 1
        $('#standart-text').val(round_to(sum, 3));

        add_alert('Det anbefales at der bruges 2 prøver, for øget sikkerhed.', 'warning');      
      }
      // Deselect the two tests
      csv_row_ids_array.forEach(function(item) {
        $("#" + item).css('background-color', 'white');
      });

      csv_row_ids_array = [];
    } else {
      // If lenght = 0
      add_alert('Der skal bruges midst 1 datapunkt, 2 anbefales.', 'danger');
    }
  });

  // Table row on click handlers
  $('.csv_row').on('click', function() {
    // Extract count value from table
    if (csv_row_ids_array.includes($(this).attr("id"))) {
      $(this).css('background-color', ''); // This shouldn't be directly set to a color since it's hover is done by bootstrap
      var id = $(this).attr("id");
      csv_row_ids_array = csv_row_ids_array.filter(function(item){
        return id != item;
      });
    }
    else if(csv_row_ids_array.length < 3 ){
      csv_row_ids_array.push($(this).attr("id"));
      $(this).css('background-color', '#bada55');
    } 
  });
   

  // Click function to reset color
  var ids_to_check = [
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
    "#id_thin_fac"
  ];

  ids_to_check.forEach(function(elm) {
    $(elm).on('click', function() {
      $(this).css("border", "1px solid #CED4DA");
    });
  });

  // Evaluate if entered value is within threshold
  var id_thresholds = {
    "#id_age":                 {'min_value': 0,     'max_value': 99},
    "#id_height":              {'min_value': 40,    'max_value': 210},
    "#id_weight":              {'min_value': 30,    'max_value': 150},
    "#id_vial_weight_before":  {'min_value': 3,     'max_value': 5},
    "#id_vial_weight_after":   {'min_value': 0,     'max_value': 5},
    "#id_std_cnt":             {'min_value': 1000,  'max_value': 10000},
    "#id_thin_fac":            {'min_value': 3500,   'max_value': 7500},
  };

  for (var key in id_thresholds) {
    $(key).focusout(function() {
      var v = parseFloat($(this).val());
      var th = id_thresholds["#" + $(this).attr('id')];
      
      if (v < th['min_value'] || v > th['max_value']) {
        $(this).css('border', '2px solid #ffeeba'); // Set warning color
      } else {
        $(this).css('border', '1px solid #CED4DA'); // Set back to normal
      }
    });
  };


  // Check formatting on injection time and date
  $("#id_injection_time").focusout(function() {
    if (!valid_time_format($(this).val())) {
      $(this).css('border', '2px solid lightcoral');
    }
  });

  $("#id_injection_time").click(function() {
    $(this).css('border', '1px solid #CED4DA');
  });

  $("#id_injection_date").focusout(function() {
    if (!valid_date_format($(this).val())) {
      $(this).css('border', '2px solid lightcoral');
    }
  });

  $("#id_injection_date").click(function() {
    $(this).css('border', '1px solid #CED4DA');
  });

  // 'Beregn' on click event
  $('#calculate').click(function() {
    $(window).off("beforeunload");

    // Remove previous error message, if any
    $("#submit-err-container").empty();

    // Check if any tests have been added
    var test_count = $('#test-data-container').children().length;
    if (test_count == 0) {
      $("#submit-err-container").append("<p style=\"color: lightcoral;\">Kan ikke beregne uden prøver.</p>");
      return false;
    }

    // Check that all fields are filled out
    is_valid = true;
    failed_id = "";
    for (var i = 0; i < ids_to_check.length; i++) {
      if ($(ids_to_check[i]).val() == "") {
        is_valid = false;
        failed_id = ids_to_check[i];
        break;
      }
    };

    if (!is_valid) {
      $("#submit-err-container").append("<p style=\"color: lightcoral;\">Et eller flere felter er ikke udfyldt.</p>");
      $(failed_id).css('border', '2px solid lightcoral');
      return false;
    }

    // Check that injection date isn't in the future
    var now = new Date();
    var inj_date_val = $('#id_injection_date').val();
    var inj_time_val = $('#id_injection_time').val();
    var dt_str = inj_date_val + ' ' + inj_time_val + ':00';
    var dt = Date.parse(dt_str);

    if (dt > now) {
      $("#submit-err-container").append("<p style=\"color: lightcoral;\">Injektionstidspunkt kan ikke være i fremtiden.</p>");
      return false;
    }

    // Check that the difference between the injection before and after isn't negative
    var weight_before = $('#id_vial_weight_before').val();
    var weight_after = $('#id_vial_weight_after').val();
    if (weight_before - weight_after <= 0) {
      $("#submit-err-container").append("<p style=\"color: lightcoral;\">Injektionsvægt efter kan ikke være større end den før.</p>");
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
        $("#submit-err-container").append("<p style=\"color: lightcoral;\">Prøvetidspunkter kan ikke være før injektionstidspunkter.</p>");
        return false;
      }
    }

    return true;
  });


  // 'Gem' on click event
  $('#save').click(function() {
    $(window).off("beforeunload");

    // Clear previous error message
    $("#submit-err-container").empty();

    // Check that both date and time fields are filled out
    inj_time = $("#id_injection_time").val();
    inj_date = $("#id_injection_date").val();
    if ((inj_time == "" ? 0 : 1) ^ (inj_date == "" ? 0 : 1)) {
      $("#submit-err-container").append("<p style=\"color: lightcoral;\">Både tid og dato skal være udfyldt før der kan gemmes.</p>");
      
      if (inj_time = "") {
        $("#id_injection_time").css('border', '2px solid lightcoral');
      } else {
        $("#id_injection_date").css('border', '2px solid lightcoral');
      }

      $(window).on("beforeunload", unload_func);
      return false;
    }

    // Check that if 'sprøjtevægt efter injektion' is entered then 'sprøjtevægt før injektion' must also be entered
    inj_after = $("#id_vial_weight_after").val();
    inj_before = $("#id_vial_weight_before").val();
    if (inj_after != "" && inj_before == "") {
      $("#submit-err-container").append("<p style=\"color: lightcoral;\">Sprøjtevægt før skal indtastes.</p>");
      $("#id_vial_weight_before").css('border', '2px solid lightcoral');

      $(window).on("beforeunload", unload_func);
      return false;
    }
  });

  //'Nulstil prøver' knappen functionality
  $('#reset-selected').click(function(){
    csv_row_ids_array.forEach(function(item) {
      $("#" + item).css('background-color', 'white');
    });
    csv_row_ids_array = [];
  })
  //END:'Nulstil prøver' knappen functionality

  //Radio, method selection
  //Note we do not remove selected tests
  $('input[name="study_type"]').click(function(){
    // one sample Grown up or Childern method selection
    if (this.value < 2 && test_count != 0) {
      remove_add_test_functionality();
    }
    // Multiple samples method selected
    if (this.value == 2){
      add_add_test_functionality(); 
    }
  })

  //Comic relief line: By the saying 'The user is always right' it have been commanded from the high heavens to remove the add test functional, after a test have been added
  // Used by the function remove_add_test_functionality, add_add_test_functionality
  var test_container_full = true;
  var add_test_container = $('#add-test-container').clone(true,true);

  // These Functions are Removes and add the option to add more tests
  function remove_add_test_functionality() {
    //User understanding: Removes option to add additional test
    //Programmer understadning: Removes the contains of the add-test-container
    test_container_full = false;
    $('#add-test-container').empty();
  }

  function add_add_test_functionality() {
    //Add the functionality
    if (!test_container_full) {
      $('#add-test-container').append((add_test_container.clone(true,true)).contents());
      test_container_full = true;
    }
  }

  if (test_count > 0 && document.getElementById("id_study_type_2").checked) {
    remove_add_test_functionality()
    console.log(testcount > 0)
    conlone.log(document.getElementById("id_study_type_2").checked)
  }
});