var alerter = (function() {
  // Div element to append alerts to
  var alert_container = null;
  var is_initialied = false;

  var warn_ids = [];
  var danger_ids = [];

  const VALID_TYPES = [
    'warning',
    'danger'
  ]

  const ALERT_CLASS_MAPPINGS = {
    'warning': 'warn-field',
    'danger': 'danger-field'
  }

  /*
  Asigns the alert_container to the given div.
  */
  var init_alerter = function(div) {
    // Only initialize once
    if (is_initialied) {
      throw new Error("Alerter has already been initialized.");
    }

    alert_container = div;
    is_initialied = true;
  };

  /*
  Validates if a string is a correct alert type
  
  Args:
    type_str: string representing the alert type

  Returns:
    True if the alert type is valid, false otherwise.
  
  Remark:
    Throws an error indicating that an invalid type was passed.
  */
 var is_valid_type = function(type_str) {
  if (!VALID_TYPES.includes(type_str)) {
    return false;
  }

  return true;
 };
  

  /*
  Adds an alert to the alert container

  Args:
    msg: alert message to display
    type: type string representing the type of alert to display

  Remark:
    Alerts can only be either 'warning' or 'danger'
    For more details: https://getbootstrap.com/docs/4.2/components/alerts/
  */
  var add_alert = function(msg, type) {
    // Ensure type is valid
    if (!is_valid_type(type)) {
      throw new Error("Invalid type for alert.");
    }

    // Create strong indicator
    var alert_indicator = document.createElement('strong');
    var indicator_msg = '';
    if (type == VALID_TYPES[0]) {         // Warning
      indicator_msg = 'Advarsel: ';
    } else if (type == VALID_TYPES[1]) {  // Danger
      indicator_msg = 'Fejl: ';
    }
    alert_indicator.innerHTML = indicator_msg;

    // Create alert
    var alert_div = document.createElement('div');
    alert_div.classList.add('alert');
    alert_div.classList.add('alert-' + type);
    alert_div.innerHTML = msg;

    // Insert alert at top of container
    alert_div.prepend(alert_indicator);
    alert_container.prepend(alert_div);
  };

  /*
  Removes all alerts, from the alert container
  */
  var clear_alerts = function() {
    alert_container.empty();
  };

  /*
  Adds an alert from a field, and adds it from the list of either warning or danger ids.
  */
  var add_field_alert = function(field, type_str) {
    let field_id = field.attr('id');
    let alert_class = ALERT_CLASS_MAPPINGS[type_str];
    
    if (type_str === VALID_TYPES[0]) {        // Warning
      warn_ids.push(field_id);
    } else if (type_str === VALID_TYPES[1]) { // Danger
      danger_ids.push(field_id);
    }
    
    field.addClass(alert_class);
  }

  /*
  Removes an alert from a field, and removes it from the list of either warning or danger ids.
  */
  var remove_field_alert = function(field, type_str) {    
    let field_id = field.attr('id');
    let alert_class = ALERT_CLASS_MAPPINGS[type_str];
    
    if (type_str === VALID_TYPES[0]) {        // Warning
      let idx = warn_ids.indexOf(field_id);
      if (idx >= 0) {
        warn_ids.splice(idx, 1);
      }
    } else if (type_str === VALID_TYPES[1]) { // Danger
      let idx = danger_ids.indexOf(field_id);
      if (idx >= 0) {
        danger_ids.splice(idx, 1);
      }
    }

    field.removeClass(alert_class);
  }

  /*
  Checks if a given id has an alert of a given type
  */
  var has_alert = function(id, type_str) {
    // Remove '#' from the id if it's contained within the string
    var check_id = id;
    if (id) {
      if (id[0] === '#') {
        check_id = id.substring(1, id.length);
      }
    }

    // Perform check
    if (type_str === VALID_TYPES[0]) {        // Warning
      return warn_ids.includes(check_id);
    } else if (type_str === VALID_TYPES[1]) { // Danger
      return danger_ids.includes(check_id);
    }
  };

  /*
  Adds a change and on click event on a field which validates whether or not to indicate a warning
  on the field by coloring it yellow.

  Args:
    field: field to add the auto check on.
    alert_type: the string repesenting the type of alert to display (either: 'warning' or 'danger')
    warn_check: function which returns true, if the warning is to be displayed, false otherwise.
                this function should perform the checking on the field and it's value.
    options: a dict of arguments to call the warn_check function with
  Remark:
    When this function is called an initial check is also made.
    Asigns classes to the field to fields to indicate the warning/error.
  */
  var field_auto_warn = function(field, alert_type, warn_check, options) {
    // Ensure valid type
    if (!is_valid_type(alert_type)) {
      throw new Error("Invalid type for alert.");
    }
    
    // Map the alert_type to the assigned class
    let alert_class = ALERT_CLASS_MAPPINGS[alert_type];

    // Initialization check
    if (field.val() != '') {
      if (warn_check(field, options)) {
        add_field_alert(field, alert_type);
      }
    }
    
    // Reset alert classes on click
    field.on('click', function() {
      for (var i = 0; i < VALID_TYPES.length; i++) {
        if (field.hasClass(ALERT_CLASS_MAPPINGS[VALID_TYPES[i]])) {
          remove_field_alert(field, VALID_TYPES[i]);
        }
      }
    });

    // Check on change
    field.on('change', function() {
      if (warn_check(field, options)) {
        add_field_alert(field, alert_type);
      } else {
        if (field.hasClass(alert_class)) {
          remove_field_alert(field, alert_type);
        }
      }
    });
  }

  return {
    init_alerter: init_alerter,
    add_alert: add_alert,
    clear_alerts: clear_alerts,
    field_auto_warn: field_auto_warn,
    has_alert: has_alert,
    add_field_alert: add_field_alert,
    remove_field_alert: remove_field_alert
  };
})();