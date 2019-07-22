$(function() {
  console.log("Loaded admin panel add site");

  MODEL_TRANSLATION_MAPPINGS = {
    'user': 'bruger',
    'department': 'afdeling',
    'config': 'konfiguration',
    'hospital': 'hospital',
    'handled_examination': 'behandlede undersøgelse',
  };

  alerter.init_alerter($('#error-msg-container'));

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
        alerter.add_alert('Tilføjede ' + MODEL_TRANSLATION_MAPPINGS[model_name], 'success');

      },
      error: function(data) {
        alerter.add_alert('Kunne ikke oprette ' + MODEL_TRANSLATION_MAPPINGS[model_name], 'danger');
      }
    });
  });
});