// Set changed parameter when a change event in the form occurs
$("form :input").change(function() {
  $(this).closest('form').data('changed', true);

  // Enable user leaving the page event handling
  $(window).on("beforeunload", function() {
    return "Er du sikker på du vil forlade siden?\nIndtastet patient data vil ikke blive gemt.";
  });
});

// 'Afbryd' button clicked
$('#cancel').click(function() {
  redirect_page = "http://127.0.0.1:8000/list_studies";

  // Only alert if change were made to the form
  if($(this).closest('form').data('changed')) {
    if (confirm("Er du sikker på du vil forlade siden?\nIndtastet patient data vil ikke blive gemt.")) {
      // TODO: This shouldn't be hardcoded
      window.location.replace(redirect_page);
    } else {
      // Otherwise, do nothing

    }
  } else {
    window.location.replace(redirect_page);
  }
});

// 'Tilføj' clicked for manual study entry
$('#add-test').click(function() {
  // Reset borders
  $('#id_test_time').css('border', '1px solid #CED4DA');
  $('#id_test_date').css('border', '1px solid #CED4DA');
  
  // Extract form contents
  var ttime_serialized = $('#id_test_time').serialize();
  var test_time = ttime_serialized.split('=')[1];
  test_time = test_time.replace("%3A", ":");
  var TIME_FORMAT = /^([0-1][0-9]|[2][0-3]):[0-5][0-9]$/;

  var tdate_serialized = $('#id_test_date').serialize();
  var test_date = tdate_serialized.split('=')[1];
  var DATE_FORMAT = /^[0-9]{4}-([0][1-9]|[1][0-2])-([0-2][0-9]|[3][0-1])$/;

  // Validate contents
  if (DATE_FORMAT.test(test_date)) {
    if (TIME_FORMAT.test(test_time)) {
      // Insert test filled out (readonly) test form
      var tvalue_serialized = $('#id_test_value').serialize();
      var test_value = tvalue_serialized.split('=')[1];

      var html_row_base_begin = "<div class=\"form-row\">";
      var html_row_base_end = "</div>";
      var html_field_begin = "<div class=\"form-group col-md-3\">";
      var html_field_input_begin = "<input type=\"text\" class=\"form-control\" name=\"";
      var html_field_input_end = "\" value=\""
      var html_field_end = "\" readonly></div>";
      //var html_remove_btn = "<button type=\"button\" class=\"btn btn-default btn-lg\"><span class=\"glyphicon glyphicon-remove\" aria-hidden=\"true\"></span></button>"
      var html_remove_btn = "<input type=\"button\" value=\"X\" class=\"row-remove-btn btn btn-danger form-group col-md-1\">";

      $('#test-data-container').append(html_row_base_begin);
      $('#test-data-container .form-row').last().append(html_field_begin + html_field_input_begin + "test_date" + html_field_input_end + test_date + html_field_end);
      $('#test-data-container .form-row').last().append(html_field_begin + html_field_input_begin + "test_time" + html_field_input_end + test_time + html_field_end);
      $('#test-data-container .form-row').last().append(html_field_begin + html_field_input_begin + "test_value" + html_field_input_end + test_value + html_field_end);
      $('#test-data-container .form-row').last().append(html_remove_btn);
      $('#test-data-container').append(html_row_base_end);

      // Register on click event-handler for remove row button
      $('.row-remove-btn').on('click', function() {
        $(this).parent().remove();
      });

      // Clear input fields
      $('#id_test_date').val("");
      $('#id_test_time').val("");
      $('#id_test_value').val("");

    } else { // Incorrect time format
      $('#id_test_time').css('border', '2px solid lightcoral');
    }
  } else { // Incorrect date format
    $('#id_test_date').css('border', '2px solid lightcoral');
  }
});
var csv_row_ids_array = [];
// row on click handlers
$('.csv_row').on('click', function() {
  // Extract count value from table
  //$(this).attr("id")

  if (csv_row_ids_array.includes($(this).attr("id"))){
    $(this).css('background-color', '#ffffff');
    var id = $(this).attr("id")
    csv_row_ids_array = csv_row_ids_array.filter(function(item){
      return id != item;
    });
  }
  else if(csv_row_ids_array.length < 2 ){
    csv_row_ids_array.push($(this).attr("id"))
    $(this).css('background-color', '#39ff14');
  } 
  // Insert count value into 'Prøvetælletal' field
});