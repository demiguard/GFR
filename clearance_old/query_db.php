<?php
require_once 'lib/db.php';
{
  // array of function names and their named arguments
  // a function is called if both function name and all named arguments match
  $functions = array('get_name' => array('cpr'),
		     'check_accession_numbers' => array('numbers'));
  $function = !empty($_GET['query']) ? $_GET['query'] : '';
  if (empty($function) || !array_key_exists($function, $functions)) {
    exit();
  }

  $args = array();
  foreach ($functions[$function] as $arg) {
    if (!array_key_exists($arg, $_GET)) {
      exit();
    }
    $args[] = json_decode($_GET[$arg]);
  }
  $db = new Database();
  $result = call_user_func_array(array($db, $function), $args);
  print json_encode($result);
}
?>
