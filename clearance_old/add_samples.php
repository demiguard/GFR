<?php
require_once "lib/db.php";
require_once 'lib/templates.php';

if (empty($_GET['stamp'])) {
  print "Missing stamp!\n!";
}
else {
  $header = new Header("Indtast prøveværdier");
  $header->pprint();

  $body = new Body();
  $stamp = $_GET['stamp'];
  $db = new Database();
  $exam = $db->get_full_exam_info($stamp);
  $samples = $db->get_samples(1, 6, $stamp);
  $daily_values = $db->get_factor();
  $body->add_content("Indtast prøveværdier", add_sample_form($exam, $samples, $daily_values));
  $body->pprint();
}
?>