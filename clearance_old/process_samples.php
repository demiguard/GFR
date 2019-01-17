<?php
require_once "lib/templates.php";

$error = new input_error();
$actions = array('Afbryd', 'Gem', 'Beregn', 'Beregn udenom databasen');
$button = empty($_POST['button']) ? '' : $_POST['button'];
if (!empty($_POST['stamp']) && in_array($button, $actions)) {
  if ($button == 'Afbryd') {
    header('Location: index.php');
  }
  else {
    $error = store_patient($_POST);
    if ($error->n == 0) {
      if ($button == 'Gem') {
	header('Location: index.php');
      }
      elseif ($button == 'Beregn') {
	header("Location: clearance_calc.php?stamp={$_POST['stamp']}");
      }
      else {
	header("Location: clearance_calc.php?stamp={$_POST['stamp']}&avoid_database=1");
      }
    }
    else {
      show_errors($error);
    }
  }
}
else {
  $error->insert('Mangler stamp eller ukendt handling', '');
  show_errors($error);
}

function show_errors($error) {
  $head = new Header("Fejl");
  $body = new Body();
  $body->add_content("Fejl ved indtastning af prøve værdier", $error->to_string());
  $head->pprint();
  $body->pprint();
}

function store_patient($values) {
  require_once "lib/db.php";
  $db = new Database();
  $stamp = $values['stamp'];
  $result = $db->get_basic_exam_info($stamp);
  $cpr   = $result['cpr'];
  $dato  = $result['date'];
  $ierror = new input_error();

  if (!empty($values['f']) && ereg('^([0-9]{3,5})$',$values['f'])) {
    $db->set_factor($values['f'], $stamp);
  }
  else {
    $ierror->insert('Factor','100 - 99999');
  }

  if (!empty($values['batch']) && ereg('^([0-9]{1,5})$',$values['batch'])) {
    $db->set_batch($values['batch'], $stamp);
  }
  else {
    $ierror->insert('Batch','0 - 99999');
  }
  
  if (!empty($values['std_count']) && ereg('^([0-9]{3,5})$',$values['std_count'])) {
    $db->set_std_count($values['std_count'], $stamp);
  }
  else {
    $ierror->insert('Standard Count','100 - 99999');
    
  }

  if (!empty($values['name']) && strlen($values['name']) <= 255) {
    $db->set_name($values['name'], $stamp);
  }
  else {
    $ierror->insert('Navn','Max 255 tegn');
  }
  
  if (!empty($values['height']) && ereg('^([0-9]{2,3})$',$values['height'])) {
    $db->set_height($values['height'], $stamp);
    }
  else {
    $ierror->insert('Højde','10 - 999, ingen komma');
  }

  if (!empty($values['weight']) && ereg('^([0-9]{1,3})$',$values['weight'])) {
    $db->set_weight($values['weight'], $stamp);
  }
  else {
    $ierror->insert('Vægt','0 - 999, ingen komma');
  }

  if (!empty($values['metode'])) {
    $db->set_method($values['metode'], $stamp);
  }
  else {
    $ierror->insert('Metode','Vælg EPV, EPB eller FP!');
  }
  
  if (!empty($values['syringe']) && ereg('^([0-9]{1,2})$',$values['syringe'])) {
    $db->set_syringe($values['syringe'], $stamp);
  }
  else {
    $ierror->insert('Sprøjte','0 - 99');
  }
  
  if (!empty($values['inj_before'])) {  	
    $values['inj_before'] = ereg_replace(',','.',$values['inj_before']);   	
    if (ereg('^([0-9]{1,2})\.([0-9]{1,4})$',$values['inj_before'])) {
      $db->set_inj_before($values['inj_before'], $stamp);
    }
    else {
      $ierror->insert('Vægt før','0.00000 - 99.9999');
    }
  }
  else {
    $ierror->insert('Vægt før','0.00000 - 99.9999');
  }

  if (!empty($values['inj_after'])) {
    $values['inj_after'] = ereg_replace(',','.',$values['inj_after']);
    if (ereg('^([0-9]{1,2})\.([0-9]{1,4})$',$values['inj_after'])) {
      $db->set_inj_after($values['inj_after'], $stamp);
    }
    else {
      $ierror->insert('Vægt efter','0.00000 - 99.9999');
    }
  } else {
    $ierror->insert('Vægt efter','0.00000 - 99.9999');
  }

  if (!empty($values['inj_time_hh']) && !empty($values['inj_time_mm']) && 
      check_time($values['inj_time_hh'], $values['inj_time_mm'])) {
    $inj_time = $dato . ' ' . $values['inj_time_hh'] . ":" . $values['inj_time_mm'];
    $db->set_inj_time($inj_time, $stamp);
  }
  else {
    $ierror->insert('Injektions tidspunkt','0:00 - 23:59');
  }

  $nsamples=0;
  $i=1;
  while ($i <= 6) {
    $updated = 0;
    if (!empty($values["sample_time$i" . "_hh"]) && !empty($values["sample_time$i" . "_mm"])) {
      $HH = $values["sample_time$i" . "_hh"];
      $mm = $values["sample_time$i" . "_mm"];
      if (!check_time($HH,$mm)) {
	$ierror->insert('Prøve $i','0:00 - 23.59, counts: 0 - 9999');
      }
      else {   		  			  		
	$sample_time[$i] = $dato . ' ' .$values["sample_time$i" . "_hh"] . ":" . $values["sample_time$i" . "_mm"];
	$db->set_sample_time($sample_time[$i], $i, $cpr, $stamp);
	$updated = 1;
      }
    }
      
    if (!empty($values["sample_counts$i"])) {
      if (!ereg('^([0-9]{1,6})$',$values["sample_counts$i"])) {
	$ierror->insert('Prøve $i','counts: 0 - 999999');
      }
      else {
	$sample_counts[$i] = $values["sample_counts$i"];
	$db->set_sample_counts($sample_counts[$i], $i, $cpr, $stamp);
	$updated = 1;
      }
    }
    $nsamples += $updated;
    $i++;
  }
  $db->set_nsamples($nsamples, $stamp);
  if ($nsamples == 0) {
    $ierror->insert('Prøve','Prøve tid og tælletal mangler!');
  }

  return $ierror;
}

?>
