<?php 
require_once "lib/templates.php";

$head = new Header('Clearance historik');
$head->pprint();

$body = new Body();

if (empty($_GET['stamp'])) {
  $body->add_content("Fejl", "Mangler stamp");
  $body->pprint();
}
else {
  require_once "clearance_functions.php";
  require_once "lib/db.php";
  $db = new Database();

  $stamp = $_GET['stamp'];
  $examination = $db->get_basic_exam_info($stamp);
  $content = "<p>Tidligere undersøgelser af GFR for {$examination['name']}, CPR: {$examination['cpr']}<br><br></p>";
  $body->add_content('', $content);
    
  $clearance_history = $db->get_clearance_history2($examination['cpr']);
  if (empty($clearance_history)) {
    $body->add_content('', 'Ingen tidligere undersøgelser');
  }
  else {
    $body->add_content('', clearance_history_table($clearance_history, $examination['cpr']));
  }

  $body->pprint();
}
?>