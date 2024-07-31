// /*
// Handles everything related to the csv files and adding tests
// */

const MAX_DIFFERENCE = 0.25; // Maximum percentage difference allow when checking if two count samples have a large numerical difference between them
const MAX_SELECT_COUNT = 6; // Maximum number of rows allowed to be selected
const COUNT_COLUMN_NUMBER = 2; // Index of count values in each accordion table

class CSVHandler {
  constructor(field_alerter) {
    this.alerter = field_alerter; // Alerter instance

    this.selected_row_ids = [ ]; // List of which rows have been currently selected

    this.test_count = 0; // Counter of how many tests have been added

    // Set click events and test_count
    let old_locks = $('.row-lock-btn');
    let old_locks_len = old_locks.length;
    for (var i = 0; i < old_locks_len; i++) {
      this.add_lock_functionality($('#' + old_locks[i].id));
    }

    let old_rmvs = $('.row-remove-btn');
    let old_rmvs_len = old_rmvs.length;
    for (var i = 0; i < old_rmvs_len; i++) {
      this.add_remove_functionality($('#' + old_rmvs[i].id));
    }

    this.test_count = old_locks_len;

    this.check_test_count();
  }

  init_row_selector(row_class) {
    /*
    Adds the on click event to each row in every csv file

    Args:
      row_class: class assigned to each row in the csv accordion
    */
    let csv_handler = this;

    $(row_class).click(function() {
      let row_id = $(this).attr('id');

      if (csv_handler.selected_row_ids.includes(row_id)) { // If already selected - deselect it
        $(this).removeClass('row-selected');

        let idx = csv_handler.selected_row_ids.indexOf(row_id);
        csv_handler.selected_row_ids.splice(idx, 1);
      } else if (csv_handler.selected_row_ids.length < MAX_SELECT_COUNT) {
        // Add to list of selected rows if below the max. number of rows allowed to be selected
        $(this).addClass('row-selected');

        csv_handler.selected_row_ids.push(row_id);
      }
    });
  }

  init_add_button_handler(add_test_btn) {
    // /*
    // Initializes the click event for 'Tilføj prøve'
    // */
    let csv_handler = this;

    add_test_btn.on('click', function() {
      if (csv_handler.check_selected_count()) {
        // Add average over selected samples
        csv_handler.add_test(csv_handler.compute_selected_avg);
      } else {
        // Add empty test, if no samples were selected
        csv_handler.add_test(function() { return 0; });
      }
    });
  }

  add_test(selected_avg_func) {
    /*
    adds a new sample to the list of tests

    Args:
      selected_avg_func: function which computes the average of selected csv rows
    */
    console.log('Add test is called with: ' + String(selected_avg_func));
    let alerter = this.alerter;

    // Check if time and date fields are correctly formatted
    let sample_time_field = $('#id_NewSampleTime');
    let study_date_field = $('#id_NewSampleDate');

    alerter.remove_alert('deviation')
    var deviation = 0;
    var numbers = this.get_selected_numbers();
    if (numbers.length >= 2){
      deviation = this.deviation(numbers);
    }

    // Check if there is a large numerical difference between any two tests
    alerter.remove_alert('diff_check');

    if (this.difference_check(MAX_DIFFERENCE)) {
      alerter.add_alert(
        'diff_check',
        'Datapunkterne har meget stor numerisk forskel, Tjek om der ikke er sket en tastefejl!',
        'warning'
      );
    }

    // Check if time difference between injection time and test time is within a set threshold

    const sampleDateValue = $('#id_InjectionDate').val();
    console.log(sampleDateValue)
    let inj_date_val = helper.convert_danish_date_to_date_format(sampleDateValue);
    let inj_time_val = $('#id_InjectionTime').val();
    let inj_datetime_str = inj_date_val + 'T' + inj_time_val + ':00';

    let time_of_inj = new Date(inj_datetime_str);

    let study_date_val = helper.convert_danish_date_to_date_format(study_date_field.val());
    let study_time_val = sample_time_field.val();
    let study_datetime_str = study_date_val + 'T' + study_time_val + ':00';

    let time_of_study = new Date(study_datetime_str);

    let time_diff = time_of_study - time_of_inj;
    console.log("time_diff: " + time_diff, time_of_study, time_of_inj);

    // Check if study date was before injection date - this shouldn't be possible...
    alerter.remove_alert("inj_diff");
    if (time_of_study < time_of_inj) {
      // alerter.add_field_alert(study_date_field, 'danger');
      // alerter.add_field_alert(study_time_field, 'danger');

      alerter.add_alert(
        'inj_diff',
        'Prøve tidspunktet kan ikke være før injektionstidspunktet.',
        'warning'
      );

      return;
    }

    // Set threshold based on study type
    alerter.remove_alert('time_korrig');

    var lower = 0;
    var upper = 0;
    if ($('input[name=Method]:checked').val() === "En blodprøve, Barn") {   // 'Et punkt barn'
      lower = 100 * 60 * 1000;  // 100 min.
      upper = 140 * 60 * 1000;  // 140 min.
    }

    if ($('input[name=Method]:checked').val() == "En blodprøve, Voksen") {   // 'Et punkt voksen'
      lower = 180 * 60 * 1000;  // 180 min.
      upper = 240 * 60 * 1000;  // 240 min.
    }

    // Perform difference check - not for multiple point tests
    if ($('input[name=Method]:checked').val() != "Flere blodprøver") {
      if (!helper.within_bound(time_diff, lower, upper)) {
        let lower_min = lower / 60 / 1000;
        let upper_min = upper / 60 / 1000;

        alerter.add_alert(
          'time_korrig',
          'Prøven er foretaget udenfor det tidskorrigeret interval af metoden, prøven kan derfor være upræcis.<br>Det anbefalet interval er imellem ' + lower_min + ' minuter og ' + upper_min + ' minuter',
          'warning'
        );
      }
    }

    const total_value = Number($('#id_form-TOTAL_FORMS').val())
    const max_value = Number($('#id_form-MAX_NUM_FORMS').val())
    const form_number = total_value + 1;

    // Generate DOM elements for study fields
    const row_div = document.createElement('div');
    row_div.classList.add('form-row');

    const date_field_div = document.createElement('div');

    date_field_div.classList.add('form-group');
    date_field_div.classList.add('col-md-2');
    date_field_div.classList.add('readonly-field');

    const date_input = document.createElement('input');
    date_input.id = `id_form-${this.test_count}-SampleDate`;
    date_input.type = 'text';
    date_input.classList.add('form-control');
    date_input.name = `form-${this.test_count}-SampleDate`;
    date_input.value = study_date_field.val();
    date_input.readOnly = true;
    date_field_div.appendChild(date_input);

    const time_field_div = document.createElement('div');
    time_field_div.classList.add('form-group');
    time_field_div.classList.add('col-md-2');
    time_field_div.classList.add('readonly-field');

    const time_input = document.createElement('input');
    time_input.type = 'text';
    time_input.id = `id_form-${this.test_count}-SampleTime`
    time_input.classList.add('form-control');
    time_input.classList.add('sample_time_field')
    time_input.name = `form-${this.test_count}-SampleTime`;
    time_input.value = sample_time_field.val();
    time_input.readOnly = true;
    time_field_div.appendChild(time_input);
    helper.auto_char($(time_input),':',2)

    const count_field_div = document.createElement('div');
    count_field_div.classList.add('form-group');
    count_field_div.classList.add('col-md-2');
    count_field_div.classList.add('readonly-field');

    const count_input = document.createElement('input');
    count_input.id = `id_form-${this.test_count}-CountPerMinutes`
    count_input.type = 'text';
    count_input.classList.add('form-control');
    count_input.classList.add('value-field');
    count_input.classList.add('sample_count_field')
    count_input.name = `form-${this.test_count}-CountPerMinutes`;
    count_input.value = selected_avg_func();
    count_input.readOnly = true;
    count_field_div.appendChild(count_input);

    const deviation_field_div = document.createElement('div');
    deviation_field_div.classList.add('form-group');
    deviation_field_div.classList.add('col-md-2');
    deviation_field_div.classList.add('readonly-field');

    const deviation_input = document.createElement('input');
    deviation_input.id = `id_form-${this.test_count}-DeviationPercentage`
    deviation_input.type = 'text';
    deviation_input.classList.add('form-control');
    deviation_input.name = `form-${this.test_count}-DeviationPercentage`;
    deviation_input.value = deviation.toFixed(3);
    deviation_input.readOnly = true;
    deviation_field_div.appendChild(deviation_input);

    const remove_btn_div = document.createElement('div');
    remove_btn_div.classList.add('form-group');
    remove_btn_div.classList.add('col-md-1');

    const remove_btn = document.createElement('input');
    remove_btn.type = 'button';
    remove_btn.value = 'X';
    remove_btn.id = 'remove' + this.test_count.toString();
    remove_btn.classList.add('btn');
    remove_btn.classList.add('btn-danger');
    remove_btn.classList.add('row-remove-btn');
    remove_btn_div.appendChild(remove_btn);

    const lock_btn_div = document.createElement('div');
    lock_btn_div.classList.add('form-group');
    lock_btn_div.classList.add('col-md-1');

    const lock_btn = document.createElement('input');
    lock_btn.type = 'button';
    lock_btn.value = '🔒';
    lock_btn.id = 'lock' + this.test_count.toString();
    lock_btn.classList.add('btn');
    lock_btn.classList.add('btn-light');
    lock_btn.classList.add('row-lock-btn');
    lock_btn_div.appendChild(lock_btn);

    // Append everything to the DOM
    $('#test-data-container').append(row_div);
    $('#test-data-container .form-row').last().append(date_field_div);
    $('#test-data-container .form-row').last().append(time_field_div);
    $('#test-data-container .form-row').last().append(count_field_div);
    $('#test-data-container .form-row').last().append(deviation_field_div);
    $('#test-data-container .form-row').last().append(remove_btn_div);
    $('#test-data-container .form-row').last().append(lock_btn_div);

    $('#id_form-TOTAL_FORMS').val(form_number);
    $('#id_form-INITIAL_FORMS').val(form_number);
    $('#id_form-MAX_NUM_FORMS').val(form_number);

    // Add lock and remove button on click events
    this.add_lock_functionality($('#lock' + this.test_count.toString()));
    this.add_remove_functionality($('#remove' + this.test_count.toString()));

    // Clear time field and selected rows
    sample_time_field.val('');
    this.clear_selected_rows();

    // Check if buttons should be disabled
    this.check_test_count();

    this.test_count++;

    alerter.show_alerts();
  }

  /**
   * Calculates the deviation of the Samples
   *
   * @param {List of numbers for the devation to be caculated from} numbers
   *
   * See Flemmings mail from 2020-05-06
   */
  deviation(numbers ){
    var min_number = 1000000;
    var max_number = 0;
    for( var i = 0; i < numbers.length; i++){
      if (min_number > numbers[i]) {
        min_number = numbers[i];
      }
      if (max_number < numbers[i]){
        max_number = numbers[i];
      }
    }
    return (max_number-min_number) / (max_number+min_number) * 100;

  }

  /*
  * Return the selected Numbers
  */
  get_selected_numbers() {
    var numbers = [];

    for(var i = 0; i < this.selected_row_ids.length; i++){
      numbers.push(this.get_row_count(this.selected_row_ids[i]));
    }

    return numbers;
  }


  difference_check(threshold) {
    /*
    Checks whether any two rows in the selected rows array (this.selected_row_ids)
    has a large numerical difference between them.

    Args:
      threshold: the threshold for the difference

    Returns:
      True if there are two rows with a large numerical difference, false otherwise.
    */
    // Ignore multiple test studies, always return false
    if (this.selected_row_ids.length <= 1) {
      return false;
    }

    // Check all rows if just one test
    var ret = true;

    let row_count = this.selected_row_ids.length;
    for (var i = 0; i < row_count; i++) {
      var row_i_val = this.get_row_count(this.selected_row_ids[i]);

      for (var j = i + 1; j < row_count; j++) {
        var row_j_val = this.get_row_count(this.selected_row_ids[j]);
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
  Gets the count from a row by id

  Args:
    row_id: id of row to get count from

  Returns:
    float value of the count from the row

  Remark:
    The '#' character in the row id is optional
  */
  get_row_count(row_id) {
    var clean_id = row_id;
    if (row_id[0] === '#') {
      clean_id = row_id.substring(1, row_id.length);
    }

    let text = $('#' + clean_id).children().eq(COUNT_COLUMN_NUMBER).text().replace(',','.');
    return parseFloat(text);
  }

  add_lock_functionality(lock_btn) {
    /*
    Adds lock button functionality to a given button
    */
    lock_btn.on("click", function() {
      var form_parent = $(this).parent().parent();

      var readonly_fields = form_parent.children('.readonly-field');
      let readonly_fields_len = readonly_fields.length;

      for (var i = 0; i < readonly_fields_len; i++) {
        readonly_fields[i].firstElementChild.readOnly = false;
      }

      // Remove the lock once clicked
      $(this).remove();
    });
  }

  add_remove_functionality(remove_btn) {
    /*
    Adds remove button functionality to a given button
    */
    let csv_handler = this;

    remove_btn.on("click", function() {
      csv_handler.test_count--;

      $(this).parent().parent().remove();

      // Check if buttons should be enabled
      csv_handler.check_test_count();
    });
  }

  /*
  Determines wheter or not to display the button for adding more tests
  */
  check_test_count() {
    let study_method = $('input[name=Method]:checked').val();

    if (study_method === "En blodprøve, Voksen"
        || study_method === "En blodprøve, Barn") {
      let test_count = $('#test-data-container .form-row').length;
      if (test_count >= 1) {
        this.disable_add_test();

        this.resolve_tests(1);
      } else {
        this.enable_add_test();
      }
    } else if (study_method === "Flere Flodprøver") {   // 'Flere punkts prøve'
      this.enable_add_test();
    }
  }

  disable_add_test() {
    /*
    Disables the 'tilføj prøve' container
    */
    $('#add-test-container').addClass('hide-elm');
  }

  enable_add_test() {
    /*
    Enables the 'tilføj prøve' container
    */
    $('#add-test-container').removeClass('hide-elm');
  }

  resolve_tests(max_tests) {
    /*
    Removes tests until there is only max_tests number of the latest tests left

    Args:
      max_tests: number of tests to leave be
    */
    var test_rows = $('#test-data-container .form-row');
    let test_rows_len = test_rows.length;

    for (var i = 0; i < test_rows_len - max_tests; i++) {
      test_rows[i].parentNode.removeChild(test_rows[i]);
    }
  }

  compute_selected_avg() {
    /*
    Computes the average of all selected rows

    Returns:
      The average of selected rows
    */
    var sum = 0;
    let rows = $(".row-selected");
    let row_count = rows.length;

    for (var i = 0; i < row_count; i++) {
      sum += parseFloat(bad_input_handler.convert_comma_to_float(rows[i].children[COUNT_COLUMN_NUMBER].innerText));
    }

    let avg_tmp = parseInt(sum / row_count);
    //console.debug("--- Computing avg. of selected rows ---");
    //console.debug("Sum: " + sum);
    //console.debug("Count: " + row_count);
    //console.debug("avg.: " + avg_tmp);

    return avg_tmp;
  }

  check_selected_count() {
    /*
    Checks if the number of selected rows is greater than 0

    Returns:
      True, if the number of selected row is greater than 0, false otherwise.

    Remark:
      This function might set alerts based on the number of selected rows.
    */
    if (this.selected_row_ids.length == 0) {
      return false;
    }

    return true;
  }

  clear_selected_rows() {
    /*
    Removes all selected rows
    */
    let rows = $(".row-selected");
    let csv_row_ids_len = rows.length;
    for (var i = 0; i < csv_row_ids_len; i++) {
      $('#' + rows[i].id).removeClass('row-selected');
    }

    this.selected_row_ids = [];
  }

  init_reset_selected(reset_btn) {
    /*
    Initializes a reset selected rows button to a given button
    */
    let csv_handler = this;

    reset_btn.on("click", csv_handler.clear_selected_rows);
  }

  init_add_standard(add_standard_btn) {
    /*
    Initializes the add standard button to a given button
    */
    let csv_handler = this;


    add_standard_btn.on("click", function() {
      // Remove previous alerts
      // alerter.clear_alerts();

      // Check if zero datapoints have been selected
      if (!csv_handler.check_selected_count()) {
        return;
      }

      csv_handler.alerter.remove_alert('deviation')

      var numbers = csv_handler.get_selected_numbers();
      if (numbers.length >= 2){
        var deviation = csv_handler.deviation(numbers);
        csv_handler.alerter.add_alert(
          'deviation',
          'Prøven har en afvigelse på ' + deviation.toFixed(3) + "%",
          'success'
        )
      }

      // Check if there is a large numerical difference between any two selected rows
      if (csv_handler.difference_check(MAX_DIFFERENCE)) {
        csv_handler.alerter.add_alert(
          'standard_diff',
          'Datapunkterne har meget stor numerisk forskel. Tjek om der ikke er sket en tastefejl.',
          'warning'
        );
      }

      // Add the computed avg. to the standard field
      let average = csv_handler.compute_selected_avg();
      $('#id_Standard').val(average);

      // Remove selection
      csv_handler.clear_selected_rows();
      csv_handler.alerter.show_alerts();
    });
  }

  init_study_method() {
    /*
    Triggers whenever a radio button for the study method is clicked

    Remark:
      Selected tests won't be deselected
    */
    let csv_handler = this;

    $('input[name="study_type"]').on("click", function() {
      csv_handler.check_test_count();
    });
  }

}
