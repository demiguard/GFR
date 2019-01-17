<?php
require_once "lib/db.php";
$db = new Database();
if (!empty($_GET['f']) && !empty($_GET['batch']) && !empty($_GET['std_count'])) {
  $db->set_global_factor($_GET['f']);
  $db->set_global_batch($_GET['batch']);
  $db->set_global_std_count($_GET['std_count']);
  header('Location: index.php');
  exit;
}

require_once "lib/templates.php";
$header = new Header("Daglige værdier");
$header->pprint();

$body = new Body();

$daily_values = $db->get_factor();
$content = daily_values_form($daily_values, "setup.php");

$body->add_content("Indtast dagens standard værdier", $content);
$body->pprint();
?>
