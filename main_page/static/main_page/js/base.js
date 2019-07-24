// TODO: This should really be done in pure CSS (possibly responsive bootstrap code?)
// Resize sidebar for square monitors
let try_resize_menu = function() {
  if ($(window).width() < 1300) {
    document.getElementById('content-container').classList.remove('col-10');
    document.getElementById('content-container').classList.add('col-9');

    document.getElementById('sidebar').classList.remove('col-2');
    document.getElementById('sidebar').classList.add('col-3');

    document.getElementById('sidebar-inner').classList.remove('col-2');
    document.getElementById('sidebar-inner').classList.add('col-3');
  } else {
    document.getElementById('content-container').classList.remove('col-9');
    document.getElementById('content-container').classList.add('col-10');
    
    document.getElementById('sidebar').classList.remove('col-3');
    document.getElementById('sidebar').classList.add('col-2');

    document.getElementById('sidebar-inner').classList.remove('col-3');
    document.getElementById('sidebar-inner').classList.add('col-2');
  }
}


$(function() {
  // Initial resizing and resizing on window resizing event
  try_resize_menu();
  $(window).resize(try_resize_menu);
});