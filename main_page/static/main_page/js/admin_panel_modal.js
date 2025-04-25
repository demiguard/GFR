
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = "block";
        document.body.style.overflow = "hidden"; // prevent background scroll
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = "none";
        document.body.style.overflow = ""; // restore scroll
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const nukeListBtn = document.getElementById("nuke-list-studies");
    const nukeDeletedBtn = document.getElementById("nuke-deleted-studies");

    if (nukeListBtn) {
        nukeListBtn.addEventListener("click", () => openModal("nukeLSModal"));
    }

    if (nukeDeletedBtn) {
        nukeDeletedBtn.addEventListener("click", () => openModal("nukeDSModal"));
    }
});