/*
Handles everything related to the csv files and adding tests
*/

var csv_handler = (function() {
  var alerter = null;
  var csv_row_ids = [];
  var test_count = 0;

  const MAX_SELECT_COUNT = 6;
  const COUNT_COLUMN_NUMBER = 2;
  const MAX_DIFFERENCE = 0.25;

  /*
  Initializes the handler:
    * Sets the alerter (this should be an already initialized alerter)
    * Sets the test_count based on how many previous tests have been added
    * Adds click events to all previous lock and remove buttons
  */
  var initialize = function(_alerter) {
    // Set alerter
    alerter = _alerter;

    // Set click events and test_count
    let old_locks = $('.row-lock-btn');
    let old_locks_len = old_locks.length;
    for (var i = 0; i < old_locks_len; i++) {
      add_lock_functionality($('#' + old_locks[i].id));
    }

    let old_rmvs = $('.row-remove-btn');
    let old_rmvs_len = old_rmvs.length;
    for (var i = 0; i < old_rmvs_len; i++) {
      add_remove_functionality($('#' + old_rmvs[i].id));
    }

    test_count = old_locks_len;

    check_test_count();
  };

  /*
  Gets the count from a row by id

  Args:
    row_id: id of row to get count from

  Returns:
    float value of the count from the row

  Remark:
    The '#' character in the row id is optional
  */
  var get_row_count = function(row_id) {
    var clean_id = row_id;
    if (row_id[0] === '#') {
      clean_id = row_id.substring(1, row_id.length);
    }
    
    return parseFloat($('#' + clean_id).children().eq(COUNT_COLUMN_NUMBER).text());
  };

  /*
  Computes the average of all selected rows

  Returns:
    The average of selected rows
  */
  var compute_selected_avg = function() {
    var sum = 0;
    let row_count = csv_row_ids.length;
    
    for (var i = 0; i < row_count; i++) {
      sum += get_row_count(csv_row_ids[i]);
    }

    return sum / row_count;
  };

  /*
  Checks whether any two rows in the selected rows array (csv_row_ids)
  has a large numerical difference between them.

  Args:
    threshold: the threshold for the difference

  Returns: 
    True if there are two rows with a large numerical difference, false otherwise.
  */
  var difference_check = function(threshold) {
    if (csv_row_ids.length <= 1) {
      return false;
    }
    
    var ret = true;

    let row_count = csv_row_ids.length;
    for (var i = 0; i < row_count; i++) {
      var row_i_val = get_row_count(csv_row_ids[i]);

      for (var j = i + 1; j < row_count; j++) {
        var row_j_val = get_row_count(csv_row_ids[j]);
        var diff = Math.abs((row_i_val - row_j_val) / (row_i_val + row_j_val));

        ret &= diff > threshold;
        if (!ret) {
          return ret;
        }
      }
    }

    return ret;
  }

  /*
  Adds the on click event to each row in every csv file

  Args:
    row_class: class assigned to each row in the csv accordion
  */
  var init_row_selector = function(row_class) {
    $(row_class).click(function() {
      let row_id = $(this).attr('id');

      if (csv_row_ids.includes(row_id)) { // If already selected - deselect it
        $(this).removeClass('row-selected');
        
        let idx = csv_row_ids.indexOf(row_id);
        csv_row_ids.splice(idx, 1);
      } else if (csv_row_ids.length < MAX_SELECT_COUNT) {
        $(this).addClass('row-selected');

        csv_row_ids.push(row_id);
      }
    });
  };

  /*
  Removes all selected rows
  */
  var clear_selected_rows = function() {
    csv_row_ids_len = csv_row_ids.length;
    for (var i = 0; i < csv_row_ids_len; i++) {
      $('#' + csv_row_ids[i]).removeClass('row-selected');
    }

    csv_row_ids = [];
  };

  /*
  Adds lock button functionality to a given button
  */
  var add_lock_functionality = function(lock_btn) {
    lock_btn.click(function() {
      var form_parent = $(this).parent().parent();
      
      var readonly_fields = form_parent.children('.readonly-field');
      let readonly_fields_len = readonly_fields.length;
      
      for (var i = 0; i < readonly_fields_len; i++) {
        readonly_fields[i].firstElementChild.readOnly = false;
      }

      // Remove the lock once clicked
      $(this).remove();
    });
  };

  /*
  Adds remove button functionality to a given button
  */
  var add_remove_functionality = function(remove_btn) {
    remove_btn.click(function() {
      test_count--;

      $(this).parent().parent().remove();

      // Check if buttons should be enabled
      check_test_count();
    });
  }

  /*
  Checks if the number of selected rows is greater than 0

  Returns:
    True, if the number of selected row is greater than 0, false otherwise.

  Remark:
    This function might set alerts based on the number of selected rows.
  */
  var check_selected_count = function() {
    if (csv_row_ids.length == 0) {
      alerter.add_alert('Der skal vælges min. 1 datapunkt for at kunne tilføje en prøve.', 'danger');
      return false;
    }
    
    if (csv_row_ids.length == 1) {
      alerter.add_alert('Det anbefaldes at der bruges 2 datapunkter for større sikkerhed', 'warning');
    }

    return true;
  }

  /*
  adds a new sample to the list of tests

  Args:
    selected_avg_func: function which computes the average of selected csv rows
  */
  var add_test = function(selected_avg_func) {
    // Check if time and date fields are correctly formatted
    let study_time_field = $('#id_study_time');
    let study_date_field = $('#id_study_date');

    if (!helper.valid_time_format(study_time_field.val())) {
      alerter.add_field_alert(study_time_field, 'danger');
      return;
    }
    
    if (!helper.valid_danish_date_format(study_date_field.val())) {
      alerter.add_field_alert(study_date_field, 'danger');
      return;
    }

    // Check if there is a large numerical difference between any two tests
    if (difference_check(MAX_DIFFERENCE)) {
      alerter.add_alert(
        'Datapunkterne har meget stor numerisk forskel, Tjek om der ikke er sket en tastefejl!', 
        'warning'
      );
    }

    // Check if time difference between injection time and test time is within a set threshold
    let time_of_inj = new Date($('#id_injection_date').val() + 'T' + $('#id_injection_time').val() + ':00');
    let time_of_study = new Date(study_date_field.val() + 'T' + study_time_field.val() + ':00');
    let time_diff = time_of_study - time_of_inj;

    // Check if study date was before injection date - this shouldn't be possible...
    if (time_of_study < time_of_inj) {
      alerter.add_field_alert(study_date_field, 'danger');
      alerter.add_field_alert(study_time_field, 'danger');
      
      alerter.add_alert(
        'Prøve tidspunktet kan ikke være før injektionstidspunktet.',
        'danger'
      );

      return;
    }

    // Set threshold based on study type
    var lower = 0;
    var upper = 0;
    if ($('input[name=study_type]:checked').val() == 1) {   // 'Et punkt barn'
      lower = 110 * 60 * 1000;  // 110 min.
      upper = 130 * 60 * 1000;  // 130 min.
    } 
  
    if ($('input[name=study_type]:checked').val() == 0) {   // 'Et punkt voksen'
      lower = 180 * 60 * 1000;  // 180 min.
      upper = 240 * 60 * 1000;  // 240 min.
    }

    // Perform difference check - not for multiple point tests
    if ($('input[name=study_type]:checked').val() != 2) {
      if (!helper.is_within_threshold(time_diff, lower, upper)) {
        let lower_min = lower / 60 / 1000;
        let upper_min = upper / 60 / 1000;

        alerter.add_alert(
          'Prøven er foretaget udenfor det tidskorrigeret interval af metoden, prøven kan derfor være upræcis.<br>Det anbefalet interval er imellem ' + lower_min + ' minuter og ' + upper_min + ' minuter',
          'warning'
        );
      }
    }

    // Generate DOM elements for study fields
    var row_div = document.createElement('div');
    row_div.classList.add('form-row');

    var date_field_div = document.createElement('div');
    date_field_div.classList.add('form-group');
    date_field_div.classList.add('col-md-3');
    date_field_div.classList.add('readonly-field');

    var date_input = document.createElement('input');
    date_input.type = 'text';
    date_input.classList.add('form-control');
    date_input.name = 'study_date';
    date_input.value = study_date_field.val();
    date_input.readOnly = true;
    date_field_div.appendChild(date_input);

    var time_field_div = document.createElement('div');
    time_field_div.classList.add('form-group');
    time_field_div.classList.add('col-md-3');
    time_field_div.classList.add('readonly-field');

    var time_input = document.createElement('input');
    time_input.type = 'text';
    time_input.classList.add('form-control');
    time_input.name = 'study_time';
    time_input.value = study_time_field.val();
    time_input.readOnly = true;
    time_field_div.appendChild(time_input);
    
    var count_field_div = document.createElement('div');
    count_field_div.classList.add('form-group');
    count_field_div.classList.add('col-md-3');
    count_field_div.classList.add('readonly-field');

    var count_input = document.createElement('input');
    count_input.type = 'text';
    count_input.classList.add('form-control');
    count_input.name = 'test_value';
    count_input.value = helper.round_to(compute_selected_avg(), 3);
    count_input.readOnly = true;
    count_field_div.appendChild(count_input);

    var remove_btn_div = document.createElement('div');
    remove_btn_div.classList.add('form-group');
    remove_btn_div.classList.add('col-md-1');

    var remove_btn = document.createElement('input');
    remove_btn.type = 'button';
    remove_btn.value = 'X';
    remove_btn.id = 'remove' + test_count.toString();
    remove_btn.classList.add('btn');
    remove_btn.classList.add('btn-danger');
    remove_btn.classList.add('row-remove-btn');
    remove_btn_div.appendChild(remove_btn);

    var lock_btn_div = document.createElement('div');
    lock_btn_div.classList.add('form-group');
    lock_btn_div.classList.add('col-md-1');

    var lock_btn = document.createElement('input');
    lock_btn.type = 'button';
    lock_btn.value = '🔒';
    lock_btn.id = 'lock' + test_count.toString();
    lock_btn.classList.add('btn');
    lock_btn.classList.add('btn-light');
    lock_btn.classList.add('row-lock-btn');
    lock_btn_div.appendChild(lock_btn);
    
    // Append everything to the DOM
    $('#test-data-container').append(row_div);
    $('#test-data-container .form-row').last().append(date_field_div);
    $('#test-data-container .form-row').last().append(time_field_div);
    $('#test-data-container .form-row').last().append(count_field_div);
    $('#test-data-container .form-row').last().append(remove_btn_div);
    $('#test-data-container .form-row').last().append(lock_btn_div);

    // Add lock and remove button on click events
    add_lock_functionality($('#lock' + test_count.toString()));
    add_remove_functionality($('#remove' + test_count.toString()));

    // Clear time field and selected rows
    study_time_field.val('');
    clear_selected_rows();

    // Check if buttons should be disabled
    check_test_count();

    test_count++;
  };

  /*
  Initializes the click event for 'Tilføj prøve'
  */
  var init_add_test = function() {
    $('#add-test').on('click', function() {
      // Reset error messages
      alerter.clear_alerts();
      
      // Check if zero datapoints have been selected
      if (!check_selected_count()) {
        return;
      }

      add_test(compute_selected_avg); 
    });
    
    // 'Tilføj tom prøve'
    $('#add-empty-value').on('click', function() {
      add_test(function() {
        return 0;
      });

      // Remove the inserted NaN or avg. value
      $('#test-data-container .form-row:last-child .form-group:nth-of-type(3) input').val(0)
    });
  };

  /*
  Initializes a reset selected rows button to a given button
  */
  var init_reset_selected = function(reset_btn) {
    reset_btn.click(clear_selected_rows);
  };

  /*
  Initializes the add standard button to a given button
  */
  var init_add_standard = function(add_standard_btn) {
    add_standard_btn.click(function() {
      // Remove previous alerts
      alerter.clear_alerts();

      // Check if zero datapoints have been selected
      if (!check_selected_count()) {
        return;
      }

      // Check if there is a large numerical difference between any two selected rows
      if (difference_check(MAX_DIFFERENCE)) {
        alerter.add_alert(
          'Datapunkterne har meget stor numerisk forskel. Tjek om der ikke er sket en tastefejl.', 
          'warning'
        );
      }

      // Add the computed avg. to the standard field
      $('#standard-field').val(helper.round_to(compute_selected_avg(), 3));

      // Remove selection
      clear_selected_rows();
    });
  };

  /*
  Disables the 'tilføj prøve' container
  */
  var disable_add_test = function() {
    $('#add-test-container').addClass('hide-elm');
  };

  /*
  Enables the 'tilføj prøve' container
  */
  var enable_add_test = function() {
    $('#add-test-container').removeClass('hide-elm');
  };

  /*
  Removes tests until there is only max_tests number of the latest tests left

  Args:
    max_tests: number of tests to leave be
  */
  var resolve_tests = function(max_tests) {
    var test_rows = $('#test-data-container .form-row');
    let test_rows_len = test_rows.length;
    
    for (var i = 0; i < test_rows_len - max_tests; i++) {
      test_rows[i].parentNode.removeChild(test_rows[i]);
    }
  }

  /*
  Determines wheter or not to display the button for adding more tests
  */
  var check_test_count = function() {
    let study_method = $('input[name=study_type]:checked').val();
    
    if (study_method <= 1) {          // 'Et punkt voksen' eller 'Et punkt voksen'
      let test_count = $('#test-data-container .form-row').length;
      if (test_count >= 1) {
        disable_add_test();

        resolve_tests(1);
      } else {
        enable_add_test();
      }
    } else if (study_method == 2) {   // 'Flere punkts prøve'
      enable_add_test();
    }
  };

  /*
  Triggers whenever a radio button for the study method is clicked

  Remark:
    Selected tests won't be deselected
  */
  var init_study_method = function() {
    $('input[name="study_type"]').click(function() { 
      check_test_count();
    });
  };

  return {
    initialize_handler: initialize,
    init_row_selector: init_row_selector,
    init_add_test: init_add_test,
    init_reset_selected: init_reset_selected,
    init_add_standard: init_add_standard,
    init_study_method: init_study_method,
    csv_row_ids : csv_row_ids,
    clear_selected_rows : clear_selected_rows
  }

})();
