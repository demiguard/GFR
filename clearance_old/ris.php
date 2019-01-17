<?php
require_once("lib/dcm_query/C-FIND.php");
$cache = new Cache("cache/ris.cache", 60*60);
if (empty($_GET['force_update']) && $cache->is_fresh()) {
  print $cache->get();
}
else {
  $records = get_todays_records();
  $filter = array("(0008,0050)" => "", // AccessionNumber
		  "(0010,0010)" => "", // PatientName
		  "(0010,0020)" => "", // PatientID (CPR)
//		  "(0032,1060)" => array("Clearance(S)", iconv("UTF-8", "ISO-8859-1", "Børneclearance(S)"))  // RequestedProcedureDescription
		  );
  $filtered = filter_records($records, $filter);
  $records = format_records($filtered);
  uasort($records, 'cmp_record_name');
  $encoded = json_encode($records);
  $cache->set($encoded);

  print $encoded;
}

function cmp_record_name($a, $b) {
  return strcmp($a['PatientName'], $b['PatientName']);
}

class Cache {
  function __construct($file, $expiration_time_in_seconds) {
    $this->file = $file;
    $this->expiry_time = $expiration_time_in_seconds;
  }

  function is_fresh() {
    $path = dirname($_SERVER['SCRIPT_FILENAME']) . "/" . $this->file;
    if (file_exists($path)) {
      $last_update = filemtime($path);
      return $last_update + $this->expiry_time > time();
    }
    return false;
  }

  function get() {
    return file_get_contents($this->file, true);
  }

  function set($data) {
    file_put_contents($this->file, $data, LOCK_EX | FILE_USE_INCLUDE_PATH );
  }
}


?>
