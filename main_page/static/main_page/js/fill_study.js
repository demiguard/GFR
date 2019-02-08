// Wait until document ready
$(function() {

  // "Beregn" and "Gem" button on click events
  $("#calculate, #save").click(function() {
    
  });

  // HANDLING OF LEAVING THE PAGE
  var unload_func = function() {
    return "Skal undersøgelsen afbrydes?\nIndtastet information vil gå tabt!";
  }

  // Set changed parameter when a change event in the form occurs
  $("#fill-study-form :input").change(function() {
    $("#fill-study-form").data('changed', true);
  });

  // In browser back button clicked
  $(window).on("beforeunload", unload_func);

  // 'Afbryd' click event
  $("#cancel").click(function() {
    $(window).off("beforeunload"); // Don't prompt twice

    if ($("#fill-study-form").data('changed')) {
      var resp = confirm("Skal undersøgelsen afbrydes?\nIndtastet information vil gå tabt!");
      if (!resp) {
        $(window).on("beforeunload", unload_func);
        return false;
      }
    }

    window.location.replace('http://localhost:8000/list_studies');
  });

  // Sidemenu item clicked
  $(".menu-item").click(function() {
    $(window).off("beforeunload"); // Don't prompt twice

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
  var valid_time_format = function(time_str) {
    var TIME_FORMAT = /^([0-1][0-9]|[2][0-3]):[0-5][0-9]$/;
    return TIME_FORMAT.test(time_str);
  }

  // Validates a given date string (format: YYYY-MM-DD)
  var valid_date_format = function(date_str) {
    var DATE_FORMAT = /^[0-9]{4}-([0][1-9]|[1][0-2])-([0-2][0-9]|[3][0-1])$/;
    return DATE_FORMAT.test(date_str);
  }

  // 'Tilføj' clicked for manual study entry
  var csv_row_ids_array = [];
  $('#add-test').click(function() {
    $('#error-message-container').empty()
    // Reset borders
    $('#id_study_time').css('border', '1px solid #CED4DA');
    $('#id_study_date').css('border', '1px solid #CED4DA');
    
    // Extract form contents
    var study_time = $('#id_study_time').val();
    var study_date = $('#id_study_date').val();

    // Validate contents
    if (valid_date_format(study_date)) {
      if (valid_time_format(study_time)) { 
        if (csv_row_ids_array.length == 2){
        // Avg. of two selected rows
        var sum = 0
        csv_row_ids_array.forEach(element => {
          sum += parseFloat($('#' + element).children().eq(3).text()) / 2
        });

        var html_row_base_begin = "<div class=\"form-row\">";
        var html_row_base_end = "</div>";
        var html_field_begin = "<div class=\"form-group col-md-3\">";
        var html_field_input_begin = "<input type=\"text\" class=\"form-control\" name=\"";
        var html_field_input_end = "\" value=\""
        var html_field_end = "\" readonly></div>";
        //var html_remove_btn = "<button type=\"button\" class=\"btn btn-default btn-lg\"><span class=\"glyphicon glyphicon-remove\" aria-hidden=\"true\"></span></button>"
        var html_remove_btn = "<input type=\"button\" value=\"X\" class=\"row-remove-btn btn btn-danger form-group col-md-1\">";

        $('#test-data-container').append(html_row_base_begin);
        $('#test-data-container .form-row').last().append(html_field_begin + html_field_input_begin + "study_date" + html_field_input_end + study_date + html_field_end);
        $('#test-data-container .form-row').last().append(html_field_begin + html_field_input_begin + "study_time" + html_field_input_end + study_time + html_field_end);
        $('#test-data-container .form-row').last().append(html_field_begin + html_field_input_begin + "test_value" + html_field_input_end + sum + html_field_end);
        $('#test-data-container .form-row').last().append(html_remove_btn);
        $('#test-data-container').append(html_row_base_end);

        // Register on click event-handler for remove row button
        $('.row-remove-btn').on('click', function() {
          $(this).parent().remove();
        });

        // Clear input fields
        $('#id_study_time').val("");
        $('#id_study_value').val("");
        } else { //Not enought Data selected
          $('#error-message-container').append("<p id=\"error-message\">Der skal bruges 2 datapunkter</p>");
          $('#error-message').css('color', '#FF0000')
          $('#error-message').css('font-size', 22)
        }
      } else { // Incorrect time format
        $('#id_study_time').css('border', '2px solid lightcoral');
      }
    } else { // Incorrect date format
      $('#id_study_date').css('border', '2px solid lightcoral');
    }
  });


  // Table row on click handlers
  $('.csv_row').on('click', function() {
    // Extract count value from table
    if (csv_row_ids_array.includes($(this).attr("id"))){
      $(this).css('background-color', '#ffffff');
      var id = $(this).attr("id");
      csv_row_ids_array = csv_row_ids_array.filter(function(item){
        return id != item;
      });
    }
    else if(csv_row_ids_array.length < 2 ){
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
    "#id_thin_fac":            {'min_value': 500,   'max_value': 1500},
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

  $("#id_injection_date").focusout(function() {
    if (!valid_date_format($(this).val())) {
      $(this).css('border', '2px solid lightcoral');
    }
  });


  // 'Beregn' on click event
  $('#calculate').click(function() {
    // Remove previous error message, if any
    $("#submit-err-container").empty();

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

    // Prompt to confim study
    $(window).off("beforeunload");
    var resp = confirm("Er undersøgelsen fuldendt?");
    if (!resp) {
      $(window).on("beforeunload", unload_func);
      return false;
    }
  });


  // 'Gem' on click event
  $('#save').click(function() {
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

      return false;
    }

    // Check that if 'sprøjtevægt efter injektion' is entered then 'sprøjtevægt før injektion' must also be entered
    inj_after = $("#id_vial_weight_after").val();
    inj_before = $("#id_vial_weight_before").val();
    if (inj_after != "" && inj_before == "") {
      $("#submit-err-container").append("<p style=\"color: lightcoral;\">Sprøjtevægt før skal indtastes.</p>");
      $("#id_vial_weight_before").css('border', '2px solid lightcoral');

      return false;
    }
  });

});