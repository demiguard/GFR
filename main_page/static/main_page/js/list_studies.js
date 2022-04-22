// Add tooltips to status icons
var init_tooltips = function() {
  $('.oi-clipboard').each(function() {
    if ($(this).hasClass('exam-status-0')) {
      $(this).attr('title', 'Ingen ændringer');
    } else if ($(this).hasClass('exam-status-1')) {
      $(this).attr('title', 'Ændringer gemt');
    } else if ($(this).hasClass('exam-status-2')) {
      $(this).attr('title', 'Klar til PACS');
    }
  });
};


// Sends a delete request to the server to move the dicom object with accession number (ris number)
// to the trash can for later deletion.
var delete_study = function(accession_number) {
  $.ajax({
    url: '/api/study/' + accession_number,
    type: 'DELETE',
    success: function() {
      console.debug("Successfully move study to trash.");
      window.location.href = "/list_studies";
    },
    error: function() {
      console.warn("Error: Unable to move study to trash with accession number: '" + accession_number + "'");
    }
  });
};


$(function() {
  init_tooltips();

  // On click event for accepting the deletion of a study
  $('#delete-modal-accept').on('click', function() {
    let del_accession_number = $('#modal-accession-number').text();
    
    delete_study(del_accession_number);
  });

  // On click event for deletion of a study
  $('.trash-btn').on('click', function() {
    // Get accession number to display in modal
    var parent_tr = $(this).parent().parent();
    let accession_number = parent_tr.children()[4].innerHTML;

    $('#modal-accession-number').text(accession_number);

    // Show the modal
    $('#deleteModal').modal('toggle');
  });

  /* Event handlers for modal and button for deleting ALL studies more than a day old */
  $("#del-day-olds-btn").on("click", function() {
    $("#dayOldModal").modal("toggle");
  });

  $("#ChangeUserGroup").on("change", function(event){
    console.log(event); 
    $.ajax({
      url: 'api/changeDepartment/' + event.target.value,
      type: 'PUT'
    }).then(() => {window.location.reload()});
  });
});
