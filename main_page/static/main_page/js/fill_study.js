// Set changed parameter when a change event in the form occurs
$("form :input").change(function() {
  $(this).closest('form').data('changed', true);

  // Enable user leaving the page event handling
  $(window).on("beforeunload", function() {
    return "Er du sikker på du vil forlade siden?\nIndtastet patient data vil ikke blive gemt.";
  });
});

// 'Afbryd' button clicked
$('#cancel').click(function() {
  redirect_page = "http://127.0.0.1:8000/list_studies";

  // Only alert if change were made to the form
  if($(this).closest('form').data('changed')) {
    if (confirm("Er du sikker på du vil forlade siden?\nIndtastet patient data vil ikke blive gemt.")) {
      // TODO: This shouldn't be hardcoded
      window.location.replace(redirect_page);
    } else {
      // Otherwise, do nothing

    }
  } else {
    window.location.replace(redirect_page);
  }
});

// 'Tilføj' clicked for manual study entry