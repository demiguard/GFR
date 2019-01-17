<?php
require_once("../dcm_query/C-FIND.php");

while(true) {
  print "Updating\n";
  update();
  print "Sleeping\n";
  sleep(60*30);
}

function update() {
  $file = "get_todays_records.cache";
  $data = get_todays_records();
  file_put_contents($file, serialize($data), LOCK_EX);
}


/* class Cache { */
/*   function __construct($function_to_cache, $expiration_time_in_seconds) { */
/*     $this->f = $function_to_cache; */
/*     $this->expiry_time = $expiration_time_in_seconds; */
/*     $this->cache_file = $function_to_cache . "cache"; */
/*   } */


/*   function is_fresh() { */
/*     $last_update = filemtime($this->cache_file) */
/*     return $last_update + $this->expiry_time > time(); */
/*   } */
/* } */


/* class Cache { */
/*   function __construct($expiration_time_in_seconds) { */
/*     $this->data = array() */
/*     $this->expiry_time = $expiration_time_in_seconds; */
/*   } */

/*   function add($key, $data) { */
/*     $this->data[$key] = array("expires" => time() + $this->expiry_time, */
/* 			      "data" => $data); */
/*   } */

/*   function get($key) { */
/*     if (!empty($data[$key])) { */
/*       return $this->data[$key]["data"]; */
/*     } */
/*     else { */
/*       return ''; */
/*     } */
/*   } */

/*   function is_fresh($key) { */
/*     $is_fresh = false; */
/*     if (!empty($data[$key])) { */
/*       $is_fresh = $this->data[$key]["expires"] > time(); */
/*     } */
/*     return $is_fresh; */
/*   } */
/* } */
?>