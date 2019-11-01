// Retrieves the accession number for the study and recovers it
let recover_study = function() {
  let recover_accession_number = $('#modal-accession-number').text();
    
  $.ajax({
    url: '/api/study/' + recover_accession_number,
    type: 'PATCH',
    success: function() {
      window.location.href = "/deleted_studies";
    },
    error: function() {
      console.warn("Failed to recover study...");
    }
  });
}

// Toggels the recover modal to display when recovering a study
let toggle_recover_modal = function() {
  // Get accession number to display in modal
  var parent_tr = $('.restore-btn').parent().parent();
  let accession_number = parent_tr.children()[3].innerHTML;

  $('#modal-accession-number').text(accession_number);

  // Show the modal
  $('#recoverModal').modal('toggle');
}

// Retrieve the accession number for the study and purges it (completely removes it from the server)
let purge_study = function() {
  let recover_accession_number = $('#purge-modal-accession-number').text();
    
  $.ajax({
    url: '/api/study/' + recover_accession_number,
    type: 'DELETE',
    data: {
      "purge": true
    },
    success: function() {
      window.location.href = "/deleted_studies";
    },
    error: function() {
      console.warn("Failed to purge study...");
    }
  });
}

// Toggels the purge modal to display when purging a study
let toggle_purge_modal = function() {
  // Get accession number to display in modal
  var parent_tr = $('.purge-btn').parent().parent();
  let accession_number = parent_tr.children()[3].innerHTML;

  $('#purge-modal-accession-number').text(accession_number);

  // Show the modal
  $('#purgeModal').modal('toggle');
}

$(function() {
  // ### ON CLICK EVENTS FOR PURGING
  $('.purge-btn').on('click', function() {
    toggle_purge_modal();
  });

  $('#purge-modal-accept').on('click', function() {
    purge_study();
  });

  // ### ON CLICK EVENTS FOR RECOVERY
  // On click event for accepting the recovery of a study
  $('#recover-modal-accept').on('click', function() {
    recover_study();
  });

  // On click event for recovering of a study
  $('.restore-btn').on('click', function() {
    toggle_recover_modal();
  });
});
