<?php
require_once "lib/templates.php";

$header = new Header("Ny undersøgelse");
$header->add_script('js/base.js');
$header->add_script('js/ris.js');
$header->pprint();

$body = new Body();
$body->add_content("Opret ny undersøgelse", new_patient_form());
$body->add_content('', '<hr /><div id="ris"><button type="button" onclick=\'update_ris();\'>Opdater RIS</button><p id="ris_answer">Henter dagens patienter fra RIS...</p></div>');
$script = '
function tr_onclick(caller) {
  var cpr = caller.querySelector(".PatientID").innerHTML;
  document.new_patient.cpr_birth.value = cpr.slice(0, 6);
  document.new_patient.cpr_runnr.value = cpr.slice(6, 10);
  document.new_patient.PatientName.value = caller.querySelector(".PatientName").innerHTML;
  document.new_patient.AccessionNumber.value = caller.querySelector(".AccessionNumber").innerHTML;
};

get_todays_bookings("ris_answer", tr_onclick);

function update_ris() {
  get_todays_bookings("ris_answer", tr_onclick, true)
}

document.new_patient.PatientName.onfocus = function() {
  if (this.value.length == 0 &&
      document.new_patient.cpr_birth.value.length == document.new_patient.cpr_birth.size &&
      document.new_patient.cpr_runnr.value.length == document.new_patient.cpr_runnr.size) {
    var cpr = document.new_patient.cpr_birth.value + document.new_patient.cpr_runnr.value;
    get_name(cpr, this);
  }
};

//document.getElementById("force_update_ris").onClick = function() { get_todays_bookings("ris_answer", tr_onclick, true); };
';
$body->add_script($script);
$body->pprint();
?>

