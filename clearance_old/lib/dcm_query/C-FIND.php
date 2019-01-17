<?php
// Functions for executing a C-FIND query and returning the result.
// DCMTK - DICOM Toolkit is needed and can be found at http://dicom.offis.de/dcmtk.php.en
//
// The result is returned as an array of records. 
// Each record is an associative array with dicom tags as keys.
// Sequences are returned as nested arrays.
//
// A dcm file containing the query parameters is needed.
// Look at edta_query.dump which is converted to edta_query.dcm by dump2dcm
//
// For output control look at the functions filter_records, format_records,
// format_tagged_value and format_tag.
//
//
// Author: Silas Ørting
// Revision: 2012-11-20

define("DCM_DICT_PATH", '/opt/dcmtk/share/dcmtk/dicom.dic');
define("FINDSCU_BIN", '/opt/dcmtk/bin/findscu');

// A row in the trimmed response from findscu is assumed to contain 4 parts
// part 0: The tag
// part 1: The type
// part 2: The value
// part 3: A comment
define("DCM_ROW_PATTERN", '/(\([0-9a-f]{4},[0-9a-f]{4}\)) ([A-Z]{2}|na) (.*) (#.*)/');

define("RECORD_SEPARATION_STRING", "W: ---------------------------");

// Example query 
// Get the patients booked for today
function get_todays_records() {
  // See the man page for findscu for details about creating a query
  $info_model = '-W'; 
  $substitution = '-k "(0040,0100)[0].ScheduledProcedureStepStartDate='.date('Ymd').'"'; // Always ask for current date
  $aet = '-aet RHEDTA';
  $aec_name = 'VIPCM';
  $aec_host = '10.143.128.247';
  $aec_port = '3320';
  $aec = "-aec $aec_name $aec_host $aec_port";
  $query_filepath = 'lib/dcm_query/edta_query.dcm';
  $query = " $info_model $substitution $aet $aec $query_filepath";

  $response = execute_query($query);
  $parsed = parse_records($response);
  return $parsed;
}


// Execute a query 
function execute_query($query) {
  putenv("DCMDICTPATH=" . DCM_DICT_PATH); // Needed by findscu
  $query = FINDSCU_BIN . $query;
  // findscu prints the response so output buffering is needed to capture it,
  // and the response is written to stderr, so it needs to be redirected to 
  // stdout to be caught in the ouput buffer
  ob_start();
  print passthru($query . ' 2>&1');
  $response = ob_get_contents();
  ob_end_clean();

  return $response; 
}

// Parsing
// returns the parsed records as a numeric array
function parse_records($response) {
  $raw_records = explode(RECORD_SEPARATION_STRING, $response);
  $i = 0;
  $parsed_records = array();
  foreach($raw_records as $raw_record) {
    $raw_lines = explode("W: ", $raw_record); // All lines are prepended with 'W: '
    $trimmed_record = array();
    $j = 0;
    foreach($raw_lines as $raw_line) {
      $trimmed_line = ltrim($raw_line);
      if (!empty($trimmed_line) && $trimmed_line[0] == '(') { // Rows are assumed to start with a tag 
	$trimmed_record[$j++] = $trimmed_line;
      }
    }
    if ($j > 0) {
      $parsed_records[$i++] = parse_record($trimmed_record);
    }
  }
  return $parsed_records;
}

// returns the parsed record as an associative array
function parse_record($record_lines) {
  $record = array();
  for ($i = 0; $i < count($record_lines); ++$i) {
    $parts = preg_split(DCM_ROW_PATTERN, $record_lines[$i], 2, PREG_SPLIT_NO_EMPTY | PREG_SPLIT_DELIM_CAPTURE);
    if ($parts[1] == 'SQ') { // $parts[1] contains the type, SQ is a seqoence type
      $result = parse_sequence(array_slice($record_lines, $i+1));
      $record[$parts[0]] = $result[0];
      $i += $result[1];
    }
    else {
      $record[$parts[0]] = trim($parts[2], " \t\n\r\0\x0B[]");
    }
  }
  return $record;
}

// returns an array containing the parsed sequence and the number of lines consumed
function parse_sequence($record_lines) {
  $sequence = array();
  $i = 0;
  $j = 0;
  for (; $i < count($record_lines); ++$i) {
    $parts = preg_split(DCM_ROW_PATTERN, $record_lines[$i], 2, PREG_SPLIT_NO_EMPTY | PREG_SPLIT_DELIM_CAPTURE);
    if ($parts[0] == '(fffe,e0dd)') {  // (fffe,e0dd) marks the end of a sequence
      ++$i;
      break;
    }
    elseif ($parts[0] == '(fffe,e000)') { // (fffe,e000) marks start of new item
      $result = parse_item(array_slice($record_lines, $i+1));
      $sequence[$j++] = $result[0];
      $i += $result[1];
    }
    else {
      $sequence[$parts[0]] = trim($parts[2], " \t\n\r\0\x0B[]"); // Some values are wrapped in []
    }
  }
  return array($sequence, $i);
}

// returns an array containing the parsed item, and the number of lines consumed
function parse_item($record_lines) {
  $item = array();
  $i = 0;
  for (; $i < count($record_lines); ++$i) {
    $parts = preg_split(DCM_ROW_PATTERN, $record_lines[$i], 2, PREG_SPLIT_NO_EMPTY | PREG_SPLIT_DELIM_CAPTURE);
    if ($parts[0] == '(fffe,e00d)') {  // (fffe,e00d) marks the end of an item
      ++$i;
      break;
    }
    $item[$parts[0]] = trim($parts[2], " \t\n\r\0\x0B[]");
  }
  return array($item, $i);
}


// Should do some conversion from possible aliases
function get_format($record) {
  if (array_key_exists('(0008,0005)', $record)) {
    return $record['(0008,0005)'];
  }
  return '';
}

// A filter should be an array containing tags and values that should be included
// Only records containing all the specified tags and values will be returned.
// Values should be specified as an array of allowed values or as an empty string
// to allow any value.
// In the following example all records containing the tags
// (0008,0050), (0010,0010), (0010,0020) with any values and the tag
// (0032,1060) with either "Clearance(S)" or "Børneclearance(S)" as value
// will be returned.
// Ensure that the filter and the records use the same encoding and character set.
// $filter = array("(0008,0050)" => "", // AccessionNumber
//                 "(0010,0010)" => "", // PatientName
//		   "(0010,0020)" => "", // PatientID (CPR)
//		   "(0032,1060)" => array("Clearance(S)", "Børneclearance(S)")  // RequestedProcedureDescription
//		  );
function filter_records($records, $filter) {
  $filtered = array();
  foreach ($records as $record) {
    $filtered_record = array();
    $skip = false;
    foreach ($filter as $tag => $values) {
      if (!array_key_exists($tag, $record) || (!empty($values) &&  !in_array($record[$tag], $values))) {
	$skip = true;
	break;
      }
      $filtered_record[$tag] = $record[$tag];
    }
    if (!$skip) {
      $filtered[] = $filtered_record;
    }
  }
  return $filtered;
}


// Formatting
function format_records($records) {
  $formatted = array();
  foreach ($records as $record) {
    $formatted_record = array();
    foreach ($record as $tag => $value) {
      if (is_array($value)) {
	$formatted_record[format_tag($tag)] = format_records($value);
      } else {
	$formatted_record[format_tag($tag)] = format_tagged_value($tag, $value);
      }
    }
    $formatted[] = $formatted_record;
  }
  return $formatted;
}


function format_tagged_value($tag, $value) {
  switch ($tag) {
  case "(0010,0010)":
    $names = explode('^', $value);
    $names = array_reverse($names);
    $name = implode(' ', $names);
    return ltrim(iconv("ISO-8859-1", "UTF-8", $name));
  case "(0032,1060)":
    return iconv("ISO-8859-1", "UTF-8", $value);
  default:
    return $value;
  }
}

function format_tag($tag) {
  $first = intval(substr($tag, 1, 4), 16);
  $second = intval(substr($tag, 6, 4), 16);
  switch ($first) {
  case 0x0008: 
    switch ($second) {
    case 0x0005: return "SpecificCharacterSet";
    case 0x0022: return "AcquisitionDate";
    case 0x0022: return "AcquisitionTime";
    case 0x0050: return "AccessionNumber";
    case 0x0060: return "Modality";
    }
    break;
  case 0x0010:
    switch ($second) {
    case 0x0010: return "PatientName";
    case 0x0020: return "PatientID";
    case 0x0030: return "PatientBirthDate";
    case 0x0040: return "PatientSex";
    case 0x1010: return "Age";
    case 0x1030: return "Weight";
    case 0x1040: return "Address";
    case 0x2000: return "MedicalAlerts";
    case 0x2110: return "ContrastAllergies";
    case 0x21c0: return "Pregnancy";
    }
    break;
  case 0x0020:
    switch($second) {
    case 0x000d: return "StudyInstanceUID";
    }
    break;
  case 0x0032:
    switch($second) {
    case 0x1032: return "RequestingPhysician";
    case 0x1060: return "RequestedProcedureDescription";
    case 0x1070: return "RequestedContrastAgent";
    }
    break;
  case 0x0040:
    switch($second) {
    case 0x0001: return "ScheduledStationAETitle";
    case 0x0002: return "ScheduledProcedureStepStartDate";
    case 0x0003: return "ScheduledProcedureStepStartTime";
    case 0x0006: return "ScheduledPerformingPhysiciansName";
    case 0x0007: return "ScheduledProcedureStepDescription";
    case 0x0009: return "ScheduledProcedureStepID";
    case 0x0010: return "ScheduledStationName";
    case 0x0011: return "ScheduledProcedureStepLocation";
    case 0x0012: return "PreMedication";
    case 0x0020: return "ScheduledProcedureStepStatus";
    case 0x0400: return "CommentsOnTheScheduledProcedureStep";
    case 0x0100: return "ScheduledProcedureStepSequence";
    case 0x1001: return "RequestedProcedureID";
    case 0x1003: return "RequestedProcedurePriority";
    }
    break;
  default: return $tag;
  }
  return $tag;
}

?>
