// Function to open the modal
function openModal(modalId) {
    document.getElementById(modalId).style.display = "block";
  }
  
  // Function to close the modal
  function closeModal(modalId) {
    document.getElementById(modalId).style.display = "none";
  }
  
  // Event listener to open nuke list studies modal
  document.getElementById("nukeLS-modal-accept").addEventListener("click", function() {
    openModal("nukeLSModal");
  });
  
  // Event listener to open nuke deleted studies modal
  document.getElementById("nukeDS-modal-accept").addEventListener("click", function() {
    openModal("nukeDSModal");
  });
  
  // Close modal when clicking outside the modal content
  window.onclick = function(event) {
    // Array of modal IDs
    let modals = ["nukeLSModal", "nukeDSModal"];
    modals.forEach(modalId => {
      let modal = document.getElementById(modalId);
      if (event.target == modal) {
        closeModal(modalId);
      }
    });
  };
  