<?php
require_once "lib/templates.php";

$error = new input_error();
if (empty($_GET['pcount'])) {
  $error->insert('Fejl', 'Mangler antal undersøgelser.');
}
else {
  require_once "lib/db.php";
  $db = new Database();
  for ($i=0; $i<=$_GET['pcount']; $i++) {
    $p = "d$i";
    if (!empty($_GET[$p])) {
      $db->delete_examination($_GET[$p]);
    }
  }
}

if ($error->n > 0) {
  $head = new Header("Fejl");
  $body = new Body();
  $body->add_content("Fejl ved sletning af undersøgelse", $error->to_string());
  $head->pprint();
  $body->pprint();
}
else {
  header("Location: database.php");
}
?>









