// Types of alerts which are available
const VALID_ALERT_TYPES = [
  'warning',
  'danger',
  'success'
]

// Alert to class name mappings, i.e. classes assigned to fields whenever an alert is triggered
const FIELD_ALERT_CLASS_MAPPINGS = {
  'warning': 'warn-field',
  'danger': 'danger-field',
  'success': 'success-field',
}

const ALERT_CLASS_MAPPINGS = {
  'warning': 'alert-warn',
  'danger': 'alert-danger',
  'success': 'alert-success',
}


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
      console.warn("Alert Error: Failed to delete alert. No alert with id '" + alert_id + "' was found");
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

  alert_type_exists(alert_type, check_container) {
    /*
    Checks if there is at least one alert of a given type

    Args:
      alert_type: type of alert to check if exists
      check_container: if true, then the given msg_container is check as well

    Returns:
      True, if an alert of the given type exists. False, otherwise
    */

    // Check internal alert dict.
    for (var key in this.alerts) {
      let curr_alert = this.alerts[key];
      if (curr_alert.type == alert_type) {
        return true;
      }
    }

    // Check container if specified
    if (check_container) {
      let ts = "#" + this.msg_container.attr("id") + " ." + ALERT_CLASS_MAPPINGS[alert_type];
      console.debug(ts);
      if ($(ts).length != 0) {
        return true;
      }
    }

    return false;
  }
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
    if (!(alert_type in FIELD_ALERT_CLASS_MAPPINGS)) {
      console.error("Alert error: got invalid alert type with no alert class mapping, '" + alert_type + "'");
      return;
    }

    field.addClass(FIELD_ALERT_CLASS_MAPPINGS[alert_type]);
  }

  remove_field_alert(field, alert_type) {
    /*
    Remove field alert classes from a field

    Args:
      field: jquery object of the field
      alert_type: alert type to remove
    */
    // for (var alert_type in FIELD_ALERT_CLASS_MAPPINGS) {
    //   field.removeClass(FIELD_ALERT_CLASS_MAPPINGS[alert_type]);
    // }
    field.removeClass(FIELD_ALERT_CLASS_MAPPINGS[alert_type]);
  }
  
  field_alert_exists(alert_type) {
    /*
    Checks if there exists a field with a given alert type

    Args:
      alert_type: type of alert to check if exists

    Returns:
      True, if there exists a field which has an alert. False, otherwise
    */
    if (!(alert_type in FIELD_ALERT_CLASS_MAPPINGS)) {
      console.error("Alert error: got invalid alert type with no alert class mapping, '" + alert_type + "'");
      return;
    }

    let alert_class = FIELD_ALERT_CLASS_MAPPINGS[alert_type];

    let alert_objs = $("." + alert_class);
    return (alert_objs.length != 0);
  }

  add_input_field_alert(field, alert_msg, alert_type, func) {
    /*
    Adds an input handler on the field which checks if an
    alert should be displayed

    Args:
      field     : jquery fetched field
      alert_msg : alert message to display when triggered
      alert_type: type of alert to trigger
      func      : checking function, which takes the value of the field as input, 
                  returning false triggers the alert
    
    Remark:
      Uses the id of the field as the unique id for
      for corresponding alerts related to the field.
      If the field doesn't have an id then 
    */
    // Ensure that field has an id
    var alert_id;
    try {
      alert_id = "alert_" + field.attr("id"); // Prepend "alert_" as not to give the alert the same id as the field
    } catch (TypeError) {
      console.error("Alert error: Unable to add input handler, field doesn't have an id.");
      return;
    }

    // Add the bind handler
    field.bind(
      "input",
      {
        "FA_class": this,         // "this" when passed as an argument refers to the FieldAlerter instance
                                  // it's passed on to the bind handler, since "this" in the handler will be different
        "alert_id": alert_id,
        "alert_msg": alert_msg,
        "alert_type": alert_type,
        "func": func
      },
      this.input_handler
    );

    // Initial trigger of the newly registered event
    field.trigger("input");
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

    if (!func($(this).val())) {
      // Alert has been triggered
      if (alert_id in FA_class.alerts) {
        if (alert_type == "danger" && $(this).hasClass(FIELD_ALERT_CLASS_MAPPINGS["warning"])) {
          FA_class.remove_alert(alert_id);
          FA_class.remove_field_alert($(this));
        }
      }
      FA_class.add_alert(alert_id, alert_msg, alert_type);
      FA_class.add_field_alert($(this), alert_type);
    } else {
      // Success - don't display an alert the current alert
      FA_class.remove_alert(alert_id);
      FA_class.remove_field_alert($(this), alert_type);
    }

    FA_class.show_alerts();
  }
}
