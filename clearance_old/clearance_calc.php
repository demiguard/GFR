<?php 
require_once "lib/templates.php";

$head = new Header('Svarark');
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
    if (empty($_GET['avoid_database'])) {
      $db->set_clearance($examination['clearance_st'], $examination['clearance_korr'], $stamp);
      //$db->set_status('NEW', $stamp); // hack
      $start = 'Denne og tidligere ';
    }
    else {
      $start = 'Tidligere ';
    }

    $clearance_calc = clearance_calc_table($examination);
    $body->add_content("Svarark", $clearance_calc);
    
    $content = "<p>$start undersøgelser af GFR for {$examination['name']}, CPR: {$examination['cpr_string']}<br><br></p>";
    $body->add_content('', $content);
    
    $clearance_history = $db->get_clearance_history($examination['cpr']);
//	print '<pre>'; var_dump($examination); print '</pre>';
    $body->add_content('', clearance_history_table($clearance_history, $examination['cpr']));
  }
  else {
    $body->add_content("Fejl", $examination['error']);
  }

  $body->pprint();
}
?>
