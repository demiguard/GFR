<?php
require_once 'lib/db.php';

function calculate_clearance($stamp, $fields) {
  // This is common to both single and multiple calculations
  $fields['OV'] = overflade($fields['height'],$fields['weight']);
  $fields['inj_weight'] = $fields['inj_before'] - $fields['inj_after'];
  $fields['dosis'] = dosis($fields['inj_weight'], $fields['factor'], $fields['std_count']);

  if ($fields['metode'] == 'FP') {
    return clearance_multiple($stamp, $fields);
  } 
  else {
    return clearance_single($stamp,$fields);
  }
}

function clearance_single($stamp, $fields) {
  $db = new Database();
  $sample = $db->get_samples($fields['nsamples'], $fields['nsamples'], $stamp);
  $fields['sample_time'] = array(0, $sample[0]['time']);
  $fields['sample_counts'] = array(0, $sample[0]['counts']);

  $deltaT = (strtotime($sample[0]['time']) - strtotime($fields['inj_time']))/ 60;

  if ($fields['metode'] == 'EPV') {
    $fields['clearance_st'] = (0.213 * $deltaT - 104) * log($sample[0]['counts'] * $fields['OV']/$fields['dosis']) + 1.88 * $deltaT - 928;
    $fields['clearance_korr'] = $fields['clearance_st'] * $fields['OV'] / 1.73;
  }
  elseif ($fields['metode'] == 'EPB') {
    $ECV = 5867 * pow($fields['OV'],1.1792);
    $g = 1.01 * exp(-0.00011 * $deltaT) + 0.538 * exp(-0.0178 * $deltaT);
    $fields['clearance_korr'] = (-log($sample[0]['counts'] * $ECV / $fields['dosis']) * $ECV)/($deltaT * $g);
    $fields['clearance_st'] = $fields['clearance_korr'] * 1.73 / $fields['OV'];
  }
  else {
    $fields['error'] = 'Clearance calculation method not defined';
  }
  return $fields;
}


function clearance_multiple($stamp, $fields) {
  $nsamples = $fields['nsamples'];
  $sample_counts[0] = 0;
  $sample_time[0] = $fields['inj_time'];
  
  $db = new Database();
  $samples = $db->get_samples(1, $nsamples, $stamp);
  for ($i = 1, $j = 0; $i <= $nsamples; ++$i, ++$j) {
    $sample_counts[$i] = $samples[$j]['counts'];
    $sample_time[$i] = $samples[$j]['time'];
  }
  $fields['sample_time'] = $sample_time;
  $fields['sample_counts'] = $sample_counts;

  for($i = 0; $i <= $nsamples; ++$i) {
    $stid[$i] = strtotime($sample_time[$i]);
    $tid[$i]=($stid[$i]-$stid[0])/60;
  }

  for($i = 1, $j = 0; $i <= $nsamples; ++$i, ++$j) {
    $sample_logcounts[$j] = log($sample_counts[$i]);
    $time_regress[$j] = $tid[$i];
  }

  require_once "lib/regress.php";

  $slr = new SimpleLinearRegression($time_regress, $sample_logcounts);  
  $C0 = exp($slr->YInt);
  $k = - $slr->Slope;
  $clearance = $fields['dosis'] * $k / $C0;

  $fields['clearance_korr'] = (0.990778 * $clearance) - (0.001218 * $clearance * $clearance);
  $fields['clearance_st'] = $fields['clearance_korr'] * 1.73 / $fields['OV'];

  return $fields;
}

// Calculates surface area using Du Bois formula
// height should be in cm, weight should be in kg and result is in m^2
function overflade($h,$w) {
  return (pow($h,0.725) * pow($w,0.425) * 71.84)/ 10000;   
}

function dosis($inj,$f,$stc) {
  return $inj * $f * $stc;
}

function cpr_birth($cpr) {
  return substr($cpr, 0 , 6);
}

function cpr_runnr($cpr) {
  return substr($cpr, 6 , 4);
}

function cpr_age($cpr) {
  $b = substr($cpr, 0 , 6);
  $r = substr($cpr, 6 , 4);
  if (is_string($r)) {
    $year = substr($b,4,2) + 2000;
    if ($year > date("Y")) {
      $year -= 100;
    }

  } else {
    if (($r >= 4000 AND $r <= 9999) OR ($r >= 0 AND $r <= 36)){
      $year = substr($b,4,2) + 2000; 
    } else {
      $year = substr($b,4,2) + 1900; 
    }
  }
  $monthday = date('nd');
  $day = substr($b,0,2);
  $month = substr($b,2,2);
  $link = $month.$day;
  $datepoint = $link;
  $r = date("Y") - $year;
   
  if ($monthday < $datepoint) {
    $r -=1;
  }   	    
  return $r; 
}

function index_GFR_Text($i_GFR) {	
  if ($i_GFR < 25)
    $s = "Normal";		
  elseif ($i_GFR < 50)
    $s = "Moderat nedsat";
  elseif ($i_GFR < 75)
    $s = "Middelsvært nedsat";
  else
    $s = "Svært nedsat";		
  return $s;
}

function cpr_birth_date($cpr) {
  $b = substr($cpr, 0 , 6);
  $r = substr($cpr, 6 , 4);
  if (is_string($r)) {
    $year = substr($b,4,2) + 2000;
    if ($year > date("Y")) { 
      $year -= 100;
    }
  } 
  else {
    if (($r >= 4000 AND $r <= 9999) OR ($r >= 0 AND $r <= 36)) {
      $year = substr($b,4,2) + 2000; 
    } 
    else {
      $year = substr($b,4,2) + 1900; 
    }
  }

  $day = substr($b,0,2);
  $month = substr($b,2,2);

  return mktime(0,0,0,$month, $day, $year);
}

function normal_mean_GFR($cpr, $exam_time="now") {
  $female_reference_pct = 0.929;
  $age = cpr_age($cpr);
  $time_birth = cpr_birth_date($cpr);

  if ($exam_time == "now") {
    $time_exam = mktime(0,0,0,date('m'), date('d'), date('Y'));
    $age_in_sec = $time_exam - $time_birth;
  }
  else {
    $time_exam = mktime(0,0,0, substr($exam_time, 5,2), substr($exam_time, 8,2), substr($exam_time, 0,4));
    $age_in_sec = $time_exam - $time_birth;
    $age = floor($age_in_sec / (60 * 60 * 24 * 365.2425) );
  }

  $sex = $age < 15 ? 'B' 
    : (!(substr($cpr,9,1)%2) ? 'F' : 'M');

  switch ($sex) 
    {
    case 'M':
      $r = $age > 40 
	? (-1.16 * $age + 157.8) 
	: 111.0;
      break;
    case 'F':
      $r = $age > 40
	? (-1.16 * $age + 157.8) * $female_reference_pct
	: 103.0;
      break;
    case 'B':
      // We need to calculate in days for small children (< 2 years)
      $r = $age < 2
	? pow(10, (0.209 * log10(floor($age_in_sec / (60 * 60 * 24))) +1.44))
	: 109.0;
      break;
    }
  return $r;
}

function nice_name($n) {
  $words = split(' ',utf8_decode($n));
  $newwords = array(); 
  foreach ($words as $w) {
    array_push($newwords, upper_fc($w));
  }
  return utf8_encode(join(' ', $newwords));
}

function upper_fc($str) {
  // support only $str as iso (ie. NOT utf8)
  $i = 0;
  $not_locale_bank_up  =utf8_decode("AÁÀÂBCDEÉÈÊFGHIÏÎJKLMNOPQRSTUÜVXYZÆÅÄÖØ");
  $not_locale_bank_down=utf8_decode("aáàâbcdeéèêfghiïîjklmnopqrstuüvxyzæåäöø");
  $str = strtolower(strtr($str,$not_locale_bank_up,$not_locale_bank_down));

  while(strlen($not_locale_bank_up) >= $i){
    if(substr($str, 0, 1) == substr($not_locale_bank_down, $i, 1)) {
      $rep=substr($not_locale_bank_up,$i, 1);
      $string=substr_replace($str,$rep, 0, 1);
      break;
    }
    $i++;
  }
  return $string;
}

function check_cpr($cpr) {
  return (!empty($cpr) &&
	  (ereg('^([0-9]{7})([A-Z]{2})([0-9]{1})$',$cpr) ||
	   (ereg('^([0-9]{10})$',$cpr) &&
	    (($cpr[0]*4+$cpr[1]*3+$cpr[2]*2+$cpr[3]*7+$cpr[4]*6+$cpr[5]*5+$cpr[6]*4+$cpr[7]*3+$cpr[8]*2+$cpr[9]*1) % 11 == 0)) 
	   //|| preg_match('/^[0-9]{6}0\p{L}{2}[0-9]$/u', $cpr) // temporary cpr uses initials from firstname and lastname.
	   )
	  );
}

function check_time($HH, $mm) {
  return (!empty($HH) && !empty($mm) &&
	  ereg('^([0-9]{1,2})$',$HH) && 
	  ereg('^([0-9]{1,2})$',$mm) &&
	  ($HH < 24)                 &&
	  ($mm < 60));
}
?>