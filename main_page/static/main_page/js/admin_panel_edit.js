// TODO: Only send keys and values for the fields which have actually been changed

function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

$(function() {
  console.log("admin panel edit loaded");

  alerter.init_alerter($('#error-msg-container'));

  MODEL_TRANSLATION_MAPPINGS = {
    'user': 'bruger',
    'department': 'afdeling',
    'config': 'konfiguration',
    'hospital': 'hospital',
    'handled_examination': 'behandlede undersøgelse',
    'proceduretype' : 'procedure',
    'procedure_mapping': 'procedure filter',
  };

  // Save button on click - update model using backend REST api
  $('#save-btn').on('click', function() {
    // Extraction object information from all available fields
    var save_data = { };
    
    $('.form-control').each(function() {
      let attr_name = $(this).attr('name');
      let attr_val = $(this).val(); 

      save_data[attr_name] = attr_val;
    });

    // Contruct api url
    let url_split = window.location.href.split('/');
    let model_name = url_split[url_split.length - 2];
    let model_id = url_split[url_split.length - 1];

    let api_url = "/api/" + model_name + "/" + model_id;

    // Send PATCH request to update model
    $.ajax({
      url: api_url,
      type: 'PATCH',
      data: save_data,
      success: function(data) {
        console.log(data);
        let display_name = capitalizeFirstLetter(MODEL_TRANSLATION_MAPPINGS[model_name]);
        alerter.add_alert(display_name + ' blev redigeret', 'success');
      },
      error: function(data) {
        console.log(data);
        alerter.add_alert('Kunne ikke redigere ' + MODEL_TRANSLATION_MAPPINGS[model_name], 'danger');
      }
    });
  });
});
