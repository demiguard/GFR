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
  $('#loader').show();
  $('#ss-wrapper .form-group').css('float', 'left');
}

// Removes the loading spinner
let hide_loading = function() {
  $('#loader').hide();
  $('#ss-wrapper .form-group').css('float', '');
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
  
  let dfa = $('#id_from_date').val().split('-');
  let dta = $('#id_to_date').val().split('-');
  var date_from, date_to;
  if(dfa.length === 3) {
    date_from = dfa[2] + "-" + dfa[1] + "-" + dfa[0];
  } else {
    date_from = "";
  }
  if(dta.length === 3) {
    date_to = dta[2] + "-" + dta[1] + "-" + dta[0];
  } else {
    date_to = "";
  }

  // Display loading element
  disable_search_fields();
  show_loading();

  $.get({
    url: 'api/search',
    data: {
      'name': name,
      'cpr': cpr,
      'accession_number': accession_number,
      'date_from': date_from,
      'date_to': date_to
    },
    success: function(data) {
      console.debug("Successful search");
      
      // Insert search results into table
      search_results = data.search_results;

      for (var i = 0; i < search_results.length; i++) {
        // Create elements for table entry
        var trow = document.createElement('tr');
        trow.setAttribute('id', search_results[i].accession_number);

        var td_name = document.createElement('td');
        td_name.innerHTML = search_results[i].name;
        td_name.classList.add("redirect-present");

        var td_cpr = document.createElement('td');
        td_cpr.innerHTML = search_results[i].cpr;
        td_cpr.classList.add("redirect-present");

        var td_date = document.createElement('td');
        td_date.innerHTML = search_results[i].date;
        td_date.classList.add("redirect-present");

        var td_accession_number = document.createElement('td');
        td_accession_number.innerHTML = search_results[i].accession_number;
        td_accession_number.classList.add("redirect-present");

        var td_create_new = document.createElement('td');
        var create_new_btn = document.createElement("button");
        create_new_btn.type = "button";
        create_new_btn.classList.add("new-hist-btn");
        create_new_btn.classList.add("btn");
        create_new_btn.classList.add("btn-link");
        var create_new_span = document.createElement("spam");
        create_new_span.classList.add("oi");
        create_new_span.classList.add("oi-document"); // Choose which icon to use for the button
        create_new_span.setAttribute("aria-hidden", "true");
        create_new_span.setAttribute("title", "Ny undersøgelse fra historisk");
        
        create_new_btn.appendChild(create_new_span);
        td_create_new.appendChild(create_new_btn);

        // Insert table entry into the table
        trow.appendChild(td_name);
        trow.appendChild(td_cpr);
        trow.appendChild(td_date);
        trow.appendChild(td_accession_number);
        trow.appendChild(td_create_new);
        $('#search-table-body').append(trow);

        // Make rows redirect to present_old_study page on click
        // $('#' + search_results[i].accession_number).on('click', function() {
        //   document.location = '/present_old_study/' + $(this).attr('id');
        // });
        $(".redirect-present").on('click', function() {
          let accession_number = $(this).parent().attr('id');
          document.location = '/present_old_study/' + accession_number;
        });
      }

      // Make create new buttons send POST request to the page
      $(".new-hist-btn").on("click", function() {
        // Get accession number of clicked historical study
        let hist_accession_number = $(this).parent().parent().children()[3].innerHTML;

        $.post({
          url: "/search",
          data: {
            "hist_accession_number": hist_accession_number
          },
          success: function(data) {
            // Redirect to the new study copy
            console.debug("Should redirect to: " + data.redirect_url);
            window.location.href = data.redirect_url;
          }
        });
      });

      hide_loading();
      enable_search_fields();
    },
    error: function(data) {
      console.debug("Failed search");

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
  let day = today.getDate().toString();
  if (day.length == 1) {
    day = "0" + day;
  }
  let month = (today.getMonth() + 1).toString(); // January is 0!
  if (month.length == 1) {
    month = "0" + month;
  }

  let year = today.getFullYear();
  
  let today_str = day + '-' + month + '-' + year;

  // Get date one week ago
  let week_ago = new Date();
  week_ago.setDate(week_ago.getDate() - 7);
  let wday = week_ago.getDate().toString();
  if (wday.length == 1) {
    wday = "0" + wday;
  }

  let wmonth = (week_ago.getMonth() + 1).toString(); // January is 0!
  if (wmonth.length == 1) {
    wmonth = "0" + wmonth;
  }
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
  
  // hide_loading();
  show_loading();

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
