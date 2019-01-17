<?php
require_once 'lib/templates.php';
require_once 'clearance_functions.php';
require_once 'lib/db.php';

$ierror = new input_error();
if (empty($_POST['PatientName'])) {
  $ierror->insert('Mangler navn', ' ');
}

if (empty($_POST['date'])) {
  $ierror->insert('Mangler dato', ' ');
}

if (empty($_POST['cpr_birth'])) {
  $ierror->insert('CPR fejl. Mangler fødselsdato','000000-311299');
}

if (empty($_POST['cpr_runnr'])) {
  $ierror->insert('CPR fejl. Mangler løbenummer','0000-9999 0AB0 (Kvinder) 0AB1 (Mænd)');
}

if ($ierror->n == 0) {
  $cpr = $_POST['cpr_birth'] . strtoupper($_POST['cpr_runnr']);
  if (check_cpr($cpr)) {
    $db = new Database();
    $stamp = date("Y-m-d H:i:s");
    $accession_number = empty($_POST['AccessionNumber']) ? NULL : $_POST['AccessionNumber'];
    $name = $_POST['PatientName'];
    $date = $_POST['date'];
    if ($db->new_examination($name, $date, $cpr, $stamp, $accession_number)) {
      header("Location: add_samples.php?stamp=$stamp");
      exit;
    }
    else {
      $ierror->insert("Database fejl. Kunne ikke oprette ny undersøgelse", "");
    }
  }
  else {
    $ierror->insert('CPR error ','000000-0000 000000-0AB0 000000-0AB1');
  }
}

$header = new Header("Fejl");
$header->pprint();

$body = new Body();
$body->add_content("Fejl ved oprettelse af ny undersøgelse", $ierror->to_string());
$body->pprint();
?>