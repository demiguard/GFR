<?php
require_once "lib/templates.php";
require_once "lib/db.php";

$head = new Header("Hent undersøgelse");
$head->add_script('js/base.js');
$head->pprint();

$body = new Body();
$db = new Database();
$exams = $db->get_new_exams();
$content = exams_table($exams);
$body->add_content("Hent undersøgelse", $content);
$script = 'replace_cell_links_with_row_link();';
$body->add_script($script);

$body->pprint();
?>
