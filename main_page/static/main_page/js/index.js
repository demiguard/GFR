$(function() {
  // Send csrf token with on ajax requests 
  $.ajaxSetup({ 
    beforeSend: function(xhr, settings) {
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    } 
  });

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
          window.location.href = "{% url main_page:list_studies %}";
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