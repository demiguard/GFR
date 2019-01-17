<!doctype html>
<head>
<meta HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8"/>
<title>Test</title>
</head>
<body>
<?php
require_once 'C-FIND.php';

function test($query_file, $date) {
  // See the man page for findscu for details about creating a query
  $info_model = '-W'; 
  $substitution = '-k "(0040,0100)[0].ScheduledProcedureStepStartDate='.$date.'"';
  $aet = '-aet RH_EDTA';
  $aec_name = 'VIPCM';
  $aec_host = '10.143.128.247';
  $aec_port = '3320';
  $aec = "-aec $aec_name $aec_host $aec_port";
  $query = " $info_model $substitution $aet $aec $query_file";

  $response = execute_query($query);
  $records = format_records(parse_records($response));
  foreach ($records as $record) {
    print_record($record);
  }
}

function print_record($record) {
  print "<ul>";
  foreach ($record as $k => $v) {
    print "<li>$k: ";
    if (is_array($v)) {
      foreach ($v as $subrecord) {
	print_record($subrecord);
      }
    }
    else {
      print "$v";
    }
    print "</li>";
  }
  print "</ul>";
}
/* function nub_by($records, $key) { */
/*   $filtered = array(); */
/*   foreach ($records as $record) { */
/*     $filtered_record = array(); */
/*     $skip = false; */
/*     foreach ($filter as $tag => $values) { */
/*       if (!array_key_exists($tag, $record) || (!empty($values) &&  !in_array($record[$tag], $values))) { */
/* 	$skip = true; */
/* 	break; */
/*       } */
/*       $filtered_record[$tag] = $record[$tag]; */
/*     } */
/*     if (!$skip) { */
/*       $filtered[] = $filtered_record; */
/*     } */
/*   } */
/*   return $filtered; */
/* } */

$date = empty($_GET['date']) ? date('Ymd') : $_GET['date'];
print "<h1>Fetching records from $date</h1>";
test('test.dcm', $date);
?>
</body>
</html>
