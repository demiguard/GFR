<?php
require_once "lib/db.php";
require_once "lib/templates.php";

$head = new Header("Svar");
$head->pprint();

$body = new Body();
if (!empty($_GET['stamp'])) {
  $db = new Database();
  $examination = $db->get_full_exam_info($_GET['stamp']);
  $out = examination_result_table($examination);
  $body->add_content("Svar", $out);
}
else {
  $error = new input_error();
  $error->insert('Kan ikke vise udskrift, "stamp" manngler.');
  $body->add_content($error->to_string());
}
$body->pprint();
?>
