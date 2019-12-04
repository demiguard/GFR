// Types of alerts which are available
const VALID_ALERT_TYPES = [
  'warning',
  'danger',
  'success'
]


class Alerter {
  /*
  Alerter class for managing alerts (This is ment as a base class)
  */
  constructor(msg_container) {
    /*    
    Args:
      msg_container: container where alert messages will be placed (fetched via. jquery)
    */
    if (msg_container.length == 0) {
      console.error("Alerter error: got empty alert message container");
      return;
    }

    if (!(msg_container.is("div"))) {
      console.error("Alerter error: alert message container must be a div element");
      return;
    }

    this.msg_container = msg_container;

    /*
    Dict of current alerts to present

    Structure:
    {
      {
        "msg": <MESSAGE_TO_PRESENT>
        "type": <TYPE_OF_ALERT_TO_PRESENT>    // Should be either one of options in VALID_ALERT_TYPES
      }
      ...
    }
    */
    this.alerts = { };
    this.to_delete = { }; // Dict of alerts which are to be permantly removed - i.e. remove their DOM element
  }

  add_alert(alert_id, msg, alert_type) {
    /*
    Adds an alert to the current dict of alerts
    
    Args:
      alert_id: unique identifyer for the alert to add
      msg: alert message
      alert_type: type of alert (see VALID_ALERT_TYPES for list of available types)
    */
    if (alert_id in this.alerts) {
      console.error("Alert Error: alert_id is not unique, there already exists an alert with id of '" + alert_id + "'");
      return;
    }

    if (!VALID_ALERT_TYPES.includes(alert_type)) {
      console.error("Alert Error: Got invalid alert type, '" + alert_type + "'");
      return;
    }

    if (msg.length == 0) {
      console.warn("Alert Warning: Got message with length of 0");
    }

    this.alerts[alert_id] = {
      "msg": msg,
      "type": alert_type
    };
  }

  remove_alert(alert_id) {
    /*
    Remove a specific alert by id

    Args:
      alert_id: id if
    */
    if (!(alert_id in this.alerts)) {
      console.error("Alert Error: Failed to delete alert. No alert with id '" + alert_id + "' was found");
      return;
    }

    this.to_delete[alert_id] = this.alerts[alert_id];
    delete this.alerts[alert_id];
  }

  remove_all_alerts() {
    /*
    Remove all alerts
    */
    this.to_delete = this.alerts;
    this.alerts = { };
  }

  show_alerts() {
    /*
    Display each current alert in the message container
    */
    this.hide_alerts();

    for (var alert_id in this.alerts) {
      let curr_alert = $("#" + alert_id);
      if (curr_alert.length != 0) {
        // Show alert element if previously created
        curr_alert.show();
      } else {
        // Create the alert element if it hasn't been created before
        let alert_dict = this.alerts[alert_id];
        let msg = alert_dict["msg"];
        let type = alert_dict["type"];
  
        // Create strong indicator
        var alert_indicator = document.createElement('strong');
        var indicator_msg = '';
        if (type == VALID_ALERT_TYPES[0]) {         // Warning
          indicator_msg = 'Advarsel: ';
        } else if (type == VALID_ALERT_TYPES[1]) {  // Danger
          indicator_msg = 'Fejl: ';
        } else if (type == VALID_ALERT_TYPES[2]) {  // Success
          indicator_msg = 'Success: ';
        }
        alert_indicator.innerHTML = indicator_msg;
    
        // Create alert
        var alert_div = document.createElement('div');
        alert_div.classList.add('alert');
        alert_div.classList.add('alert-' + type);
        alert_div.id = alert_id;
        alert_div.innerHTML = msg;
    
        // Insert alert at top of container
        alert_div.prepend(alert_indicator);
        this.msg_container.prepend(alert_div);
      }
    }
  }

  hide_alerts() {
    /*
    Clear the message container
    */
    // Permantly remove the DOM element if it's in this.to_delete
    for (var alert_id in this.to_delete) {
      $("#" + alert_id).remove();
    }
    this.to_delete = { };

    // Hide the alert if it's present in this.alerts
    for (var alert_id in this.alerts) {
      $("#" + alert_id).hide();
    }
  }
}


// Alert to class name mappings, i.e. classes assigned to fields whenever an alert is triggered
const ALERT_CLASS_MAPPINGS = {
  'warning': 'warn-field',
  'danger': 'danger-field',
  'success': 'success-field',
}

class FieldAlerter extends Alerter {
  add_field_alert(field, alert_type) {
    /*
    Adds a field alert (color the field to indicate) to a specific field

    Args:
      field: jquery object of the field to add alert to
      alert_type: type of alert to indicate on the field

    Remark:
      The field alerts are done by adding a class to the field
      which then has CSS defined in alerter.css specifying the 
      coloring of the field
    */    
    if (!(alert_type in ALERT_CLASS_MAPPINGS)) {
      console.error("Alert error: got invalid alert type with no alert class mapping, '" + alert_type + "'");
      return;
    }
    
    field.addClass(ALERT_CLASS_MAPPINGS[alert_type]);
  }

  remove_field_alert(field) {
    /*
    Remove field alert classes from a field

    Args:
      field: jquery object of the field
    */
    for (var alert_type in ALERT_CLASS_MAPPINGS) {
      field.removeClass(alert_type);
    }
  }
  
  add_input_handler(field, alert_msg, alert_type, func, func_args) {
    /*
    Adds an input handler on the field which checks if an
    alert should be displayed

    Args:
      field     : jquery fetched field
      alert_msg : alert message to display when triggered
      alert_type: type of alert to trigger
      func      : checking function, which takes the value of the field as input, 
                  returning false triggers the alert
      func_args : arguments to pass to the checking function
    
    Remark:
      Uses the id of the field as the unique id for
      for corresponding alerts related to the field.
      If the field doesn't have an id then 
    */
    // Ensure that field has an id
    var alert_id;
    try {
      alert_id = field.attr("id");
    } catch (TypeError) {
      console.error("Alert error: Unable to add input handler, field doesn't have an id.");
      return;
    }

    // Add the bind handler
    field.bind(
      'input', 
      {
        "FA_class": this,         // "this" when passed as an argument refers to the FieldAlerter instance
                                  // it's passed on to the bind handler, since "this" in the handler will be different
        "alert_id": alert_id,
        "alert_msg": alert_msg,
        "alert_type": alert_type,
        "func": func, 
        "func_args": func_args
      },
      this.input_handler);
  }

  input_handler(event) {
    /*
    Event handler for processing field inputs

    Args:
      event: jquery event object

    Remark:
      "this" is the field and not the class in this scope,
      seeing as this an event handler for fields
    */
    // Extract functions and corresponding args.
    let FA_class     = event.data.FA_class;
    let alert_id     = event.data.alert_id;
    let alert_msg    = event.data.alert_msg;
    let alert_type   = event.data.alert_type;
    let func         = event.data.func;
    let func_args    = event.data.func_args;

    if (!func($(this).val(), func_args)) {
      // Alert has been triggered
      if (!(alert_id in FA_class.alerts)) {
        FA_class.add_alert(alert_id, alert_msg, alert_type);
      }
    } else {
      // Success - don't display an alert
      FA_class.remove_alert(alert_id);
    }

    FA_class.show_alerts();
  }
}


function within_bound(val, args) {
  /*
  Checks if given value is with a specified bound

  Args:
    val: integer or float value to check against
    args: dict containing arguments "low" and "high"

  Returns:
    True, if val is within low and high. False otherwise
  */
  let low  = args["low"];
  let high = args["high"];

  return (val >= low && val <= high);
}
