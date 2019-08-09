

$(function() {  
  // On click event for accepting the recovery of a study
  $('#recover-modal-accept').on('click', function() {
    let recover_accession_number = $('#modal-accession-number').text();
    
    $.post({
      url: '/ajax/restore_study',
      data: {
        'recover_accession_number': recover_accession_number,
      },
      success: function() {
        window.location.href = "/deleted_studies";
      },
      error: function() {
        console.warn("Failed to recover study...");
      }
    });
  });

  // On click event for recovering of a study
  $('.restore-btn').on('click', function() {
    // Get accession number to display in modal
    var parent_tr = $(this).parent().parent();
    let accession_number = parent_tr.children()[4].innerHTML;

    $('#modal-accession-number').text(accession_number);

    // Show the modal
    $('#recoverModal').modal('toggle');
  });
});
