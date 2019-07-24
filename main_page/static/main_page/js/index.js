// Ajax login on 'log ind' click and enter key on the password field
let try_login = function() {
  // Clear previous error messages
  $('#err-msg-container').empty();

  // Send the username and password for validation
  let user = $('#id_username').val();
  let pass = $('#id_password').val();
  
  $.post({
    url: '/ajax/login',
    data: {
      'username': user,
      'password': pass,
    },
    success: function(data) {
      if (data.signed_in) {
        //window.location.href = "http://localhost:8000/list_studies";
        window.location.href = "/list_studies"; //{% url main_page:list_studies %};
      }
    },
    error: function() {
      $('#err-msg-container').append("<p style='color: lightcoral;'>Forkert login.</p>");
    }
  });
}


// Field attempt login on enter press
let ENTER_KEY = '13';
let enter_login = function(event) {
  if (event.which == ENTER_KEY) {
    try_login();
  }
}


// Figures out the type and version number of the current userAgents browser
get_browser = function() {
  var ua= navigator.userAgent, tem, M = ua.match(/(opera|chrome|safari|firefox|msie|trident(?=\/))\/?\s*(\d+)/i) || [ ];
  
  if (/trident/i.test(M[1])){
    tem = /\brv[ :]+(\d+)/g.exec(ua) || [ ];
    return 'IE ' + (tem[1] || '');
  }
  
  if (M[1] === 'Chrome'){
    tem = ua.match(/\b(OPR|Edge)\/(\d+)/);

    if (tem!= null) {
      return tem.slice(1).join(' ').replace('OPR', 'Opera');
    }
  }
  
  M = M[2] ? [M[1], M[2]]: [navigator.appName, navigator.appVersion, '-?'];
  
  if ((tem = ua.match(/version\/(\d+)/i)) != null) {
    M.splice(1, 1, tem[1]);
  }
  
  return M.join(' ');
}


$(function() {
  alerter.init_alerter($('#err-msg-container'));

  // Login events
  $('#login-btn').click(try_login);
  $('#id_password').keypress(enter_login);
  $('#id_username').keypress(enter_login);


  // Detect browser type/version - warn user that they are using an unsupported browser
  let browser = get_browser().toLowerCase();
  var supported_browser = false;
  let SUPPORTED_BROWSERS = [
    'chrome',
    'firefox'
  ];

  for (var i = 0; i < SUPPORTED_BROWSERS.length; i++) {
    if (browser.includes(SUPPORTED_BROWSERS[i])) {
      supported_browser = true;
      break;
    }    
  }

  if (!supported_browser) {
    alerter.add_alert("Den anvendte browser er ikke understyttet af denne hjemmeside. Visse funktioner fungere muligvis ikke som ønsket. Det anbefales at man anvender en understøttet browser: Google Chrome eller Mozilla Firefox, som kan hentes i Software shoppen.", 'warning');
  }
});