$(function() {
  // Ajax login on 'log ind' click and enter key on the password field
  let try_login = function() {
    // Clear previous error messages
    $('#err-msg-container').empty();

    // Send the username and password for validation
    let user = $('#id_username').val();
    let pass = $('#id_password').val();
    
    $.post({
      url: '/ajax/login',
      data: {
        'username': user,
        'password': pass,
      },
      success: function(data) {
        if (data.signed_in) {
          //window.location.href = "http://localhost:8000/list_studies";
          window.location.href = "/list_studies"; //{% url main_page:list_studies %};
        }
      },
      error: function() {
        $('#err-msg-container').append("<p style='color: lightcoral;'>Forkert login.</p>");
      }
    });
  }

  $('#login-btn').click(try_login);
  $('#id_password').keypress(function(event) {
    if (event.which == '13') { // Enter key
      try_login();
    }
  });
});