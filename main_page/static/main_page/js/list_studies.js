

$(function() {
  // Add tooltips to status icons
  $('.oi-clipboard').each(function() {
    if ($(this).hasClass('exam-status-0')) {
      $(this).attr('title', 'Ingen ændringer');
    } else if ($(this).hasClass('exam-status-1')) {
      $(this).attr('title', 'Ændringer gemt');
    } else if ($(this).hasClass('exam-status-2')) {
      $(this).attr('title', 'Klar til PACS');
    }
  });

  // On click event for accepting the deletion of a study
  $('#delete-modal-accept').on('click', function() {
    let del_accession_number = $('#modal-accession-number').text();
    
    $.post({
      url: '/ajax/delete_study',
      data: {
        'delete_accession_number': del_accession_number,
      },
      success: function() {
        window.location.href = "/list_studies";
      },
      error: function() {
        console.warn("Failed to delete study...");
      }
    });
  });

  // On click event for deletion of a study
  $('.trash-btn').on('click', function() {
    // Get accession number to display in modal
    var parent_tr = $(this).parent().parent();
    let accession_number = parent_tr.children()[5].innerHTML;

    $('#modal-accession-number').text(accession_number);

    // Show the modal
    $('#deleteModal').modal('toggle');
  });

  $('#thining_factor_button').on('click', function(){
    
    var a_thining_factor = $('#id_thin_fac').val()
    
    $.post({
      url:'/ajax/update_thining_factor',
      data:{
        'thining_factor': a_thining_factor
      },
      success: function(){
        window.location.href = '/list_studies'
      },
      error: function(){

      }
    });
  });
});
