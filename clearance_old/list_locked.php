<?php
require_once "lib/templates.php";
require_once "lib/db.php";
require_once "clearance_functions.php";


$head = new Header("Svarark");
$head->pprint();

$body = new Body();
if (empty($_GET['stamp'])) {
  $body->add_content("Fejl", "Mangler stamp");
}
else {
  $db = new Database();
  $stamp = $_GET['stamp'];
  $examination = $db->get_full_exam_info($stamp);
  $examination = calculate_clearance($stamp, $examination);
  $examination['cpr_string'] = cpr_birth($examination['cpr']) . '-' . cpr_runnr($examination['cpr']);
  $examination['age'] = cpr_age($examination['cpr']);
  switch ($examination['metode']) 
    {
    case 'EPV': 
      $examination['metode_display'] = 'EP VOKSEN';
      break;
    case 'EPB':
      $examination['metode_display'] = 'EP BARN';
      break;
    case 'FP':
      $examination['metode_display'] = 'FLERE PR';
      break;
    default:
      $examination['metode_display'] = 'UKENDT';
    }

  if (empty($examination['error'])) {
    $body->add_content("Svarark", clearance_calc_table($examination));
  }
  else {
    $body->add_content("Fejl", $examination['error']);
  }
}
$body->pprint();

?>