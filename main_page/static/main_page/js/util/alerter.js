var alerter = (function() {
  // Div element to append alerts to
  var alert_container = null;
  var is_initialied = false;

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
    let valid_types = [
      'warning',
      'danger'
    ]

    if (!valid_types.includes(type)) {
      throw new Error("Invalid type for alert.");
    }

    // Create strong indicator
    var alert_indicator = document.createElement('strong');
    var indicator_msg = '';
    if (type == valid_types[0]) {         // Warning
      indicator_msg = 'Advarsel: ';
    } else if (type == valid_types[1]) {  // Danger
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
  Adds a focusout and on click event on a field which validates whether or not to indicate a warning
  on the field by coloring it yellow.

  Args:
    field: field to add the auto check on.
    alert_type: the string repesenting the type of alert to display (either: 'warning' or 'danger')
    warn_check: function which returns true, if the warning is to be displayed, false otherwise.
                this function should perform the checking on the field and it's value.
    options: a dict of arguments to call the warn_check function with
  Remark:
    Asigns classes to the field to fields to indicate the warning/error
  */
  var field_auto_warn = function(field, alert_type, warn_check, options) {
    
    // TODO: Add the same kind of check as the add_alert function above
    // TODO: The fields should also be checked when the page loads, i.e. the same check with focusout should be done right before it
    
    var alert_class = '';
    if (alert_type === 'warning') {
      alert_class = 'warn-field';
    } else if (alert_type === 'danger') {
      alert_class = 'danger-field';
    }
    
    // Reset border on click
    field.on('click', function() {
      if (field.hasClass(alert_class)) {
        field.removeClass(alert_class);
      }
    });

    // Check on focusout
    field.on('focusout', function() {
      if (warn_check(field, options)) {
        field.addClass(alert_class);
      } else {
        if (field.hasClass(alert_class)) {
          field.removeClass(alert_class)
        }
      }
    });
  }

  return {
    init_alerter: init_alerter,
    add_alert: add_alert,
    clear_alerts: clear_alerts,
    field_auto_warn: field_auto_warn
  };
})();