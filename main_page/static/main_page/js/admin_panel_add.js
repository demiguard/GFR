$(function() {
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

  console.log("Loaded admin panel add site");

  $('#create-btn').on('click', function() {
    // Extraction object information from all available fields
    var obj_data = { };
    
    $('.form-control').each(function() {
      let attr_name = $(this).attr('name');
      let attr_val = $(this).val(); 

      obj_data[attr_name] = attr_val;
    });

    // Contruct api url
    let url_split = window.location.href.split('/');
    let model_name = url_split[url_split.length - 1];

    let api_url = "/api/" + model_name;

    // Send POST request to create object
    $.ajax({
      url: api_url,
      type: 'POST',
      data: obj_data,
      success: function(data) {
        console.log(data);
      },
      error: function(data) {
        console.log(data);
      }
    });
  });
});