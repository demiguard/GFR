// Make search fields readonly 
let disable_search_fields = function() {
  $('#id_name').attr('readonly', true);
  $('#id_cpr').attr('readonly', true);
  $('#id_accession_number').attr('readonly', true);
  $('#id_from_date').attr('readonly', true);
  $('#id_to_date').attr('readonly', true);
  
  $('#search-btn').prop('disabled', true);
}

// Set readonly to false on search fields
let enable_search_fields = function() {
  $('#id_name').attr('readonly', false);
  $('#id_cpr').attr('readonly', false);
  $('#id_accession_number').attr('readonly', false);
  $('#id_from_date').attr('readonly', false);
  $('#id_to_date').attr('readonly', false);

  $('#search-btn').prop('disabled', false);
}

// Displays the loading spinner
let show_loading = function() {

}

// Removes the loading spinner
let hide_loading = function() {

}

// Sends an ajax GET request with the entered search parameters
let ajax_search = function() {
  // Remove all previous search results
  $('#search-table-body').empty();
  $('#error-message-container').empty();

  // Get search parameters
  let name = $('#id_name').val();
  var cpr = $('#id_cpr').val();

  let re_alpha = /[a-zA-Z]/;    
  if (cpr.includes('-') && !re_alpha.test(cpr)) {
    cpr = cpr.replace('-', '');
  }
  let accession_number = $('#id_accession_number').val();
  let date_from = helper.convert_danish_date_to_date_format($('#id_from_date').val());
  let date_to = helper.convert_danish_date_to_date_format($('#id_to_date').val());

  // Display loading element
  disable_search_fields();
  show_loading();

  $.get({
    url: 'ajax/search',
    data: {
      'name': name,
      'cpr': cpr,
      'accession_number': accession_number,
      'date_from': date_from,
      'date_to': date_to
    },
    success: function(data) {
      // Insert search results into table
      search_results = data.search_results;

      for (var i = 0; i < search_results.length; i++) {
        // Create elements for table entry
        var trow = document.createElement('tr');
        trow.setAttribute('id', search_results[i].accession_number);

        var td_name = document.createElement('td');
        td_name.innerHTML = search_results[i].name;

        var td_cpr = document.createElement('td');
        td_cpr.innerHTML = search_results[i].cpr;

        var td_date = document.createElement('td');
        td_date.innerHTML = search_results[i].date;

        var td_accession_number = document.createElement('td');
        td_accession_number.innerHTML = search_results[i].accession_number;

        // Insert table entry into the table
        trow.appendChild(td_name);
        trow.appendChild(td_cpr);
        trow.appendChild(td_date);
        trow.appendChild(td_accession_number);
        $('#search-table-body').append(trow);

        // Make rows redirect to present_old_study page on click
        $('#' + search_results[i].accession_number).on('click', function() {
          document.location = '/present_old_study/' + $(this).attr('id');
        });
      }

      hide_loading();
      enable_search_fields();
    },
    error: function(data) {
      var err_text = "";
      if (data.statusText == 'timeout') {
        err_text = "Fejl: Kunne ikke forbinde til PACS (timeout).";
      } else {
        err_text = "Fejl: Kunne ikke forbinde til PACS";
      }
      
      // Display appropriate error message
      var error_msg = document.createElement('p');
      error_msg.innerHTML = err_text;
      error_msg.style.color = 'lightcoral';
      $('#error-message-container').append(error_msg);

      hide_loading();
      enable_search_fields();
    },
    timeout: 60000
  });
}

// Fills out initial values for the search form fields
let init_search_fields = function() {
  // Get current date
  let today = new Date();
  let day = today.getDate();
  let month = today.getMonth() + 1; // January is 0!
  let year = today.getFullYear();
  
  let today_str = day + '-' + month + '-' + year;

  // Get date one week ago
  let week_ago = new Date();
  week_ago.setDate(week_ago.getDate() - 7);
  let wday = week_ago.getDate();
  let wmonth = week_ago.getMonth() + 1; // January is 0!
  let wyear = week_ago.getFullYear();
  
  let week_ago_str = wday + '-' + wmonth + '-' + wyear;

  $('#id_from_date').val(week_ago_str);
  $('#id_to_date').val(today_str);
}

// Event handers for click and enter on search fields
let search_field_enter = function(event) {
  if (event.which == '13') { // Enter key
    ajax_search();
  }
}

// Initializes datepickers on date fields
let init_datepickers = function() {
  // Add datepickers to date fields
  $('#id_from_date').datepicker({format: 'dd-mm-yyyy'});
  $('#id_to_date').datepicker({format: 'dd-mm-yyyy'});
}

$(function() {
  init_datepickers();
  
  // Perform initial search
  init_search_fields();
  ajax_search();

  // Register each form field and search button to perform search
  $('#id_name').on('keypress', search_field_enter);
  $('#id_cpr').on('keypress', search_field_enter);
  $('#id_accession_number').on('keypress', search_field_enter);
  $('#id_from_date').on('keypress', search_field_enter);
  $('#id_to_date').on('keypress', search_field_enter);
  $('#search-btn').on('click', ajax_search);
});
