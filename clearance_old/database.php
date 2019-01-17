<?php
require_once "lib/db.php";
require_once "lib/templates.php";

$header = new Header("Database");
$header->pprint();

$body = new Body();
if (!empty($_GET['show_interval'])) {
  $from = new search_date($_GET['from_day'], $_GET['from_month'], $_GET['from_year']);
  $to = new search_date($_GET['to_day'], $_GET['to_month'], $_GET['to_year']);
  $sort_order = $_GET['sort_order'];
  $status = $_GET['status'];
}
else  {
  $parts = explode(' ', date("d m Y", strtotime("-1 day")));
  $from = new search_date($parts[0], $parts[1], $parts[2]);
  $parts = explode(' ', date("d m Y", strtotime("+1 day")));
  $to = new search_date($parts[0], $parts[1], $parts[2]);
  $sort_order = "date";
  $status = 'Alle';
}
$body->add_content("Database", db_interface($from, $to, $sort_order, $status));
$db = new Database();
$status = $status == 'Alle' ? '' : $status;
$exams = $db->get_exams_in_interval($from->sql_string(), $to->sql_string(), $sort_order, $status);
$body->add_content("", database_table($exams));
$body->pprint();
?>
