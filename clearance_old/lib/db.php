<?php
class Database {
  function __construct($host='localhost', $user='clearance_rh', $pass='xRatFpM5r7Je1EynA2MQ6tuEePOKc6owx2ISbW058CA', $dbname='clearance_rh') {
    $this->conn = new mysqli($host, $user, $pass, $dbname);
    if (mysqli_connect_errno()) {
      print "Error, unable to connect to database";
      exit();
    }
  }

  function __destruct() {
    $this->conn->close();
  }

  //
  // Getters
  function check_accession_numbers($numbers) {
    $status = array();
    $q = "SELECT 1
          FROM patient
          WHERE accession_number = ? AND status != 'DEL'";
    if ($stmt = $this->conn->prepare($q)) {
      foreach($numbers as $k => $number) {
	if ($stmt->bind_param('s', $number) &&
	    $stmt->execute() &&
	    $stmt->store_result() &&
	    $stmt->num_rows == 1) {
	  $status[$k] = true;
	}
	else {
	  $status[$k] = false;
	}
	$stmt->free_result();
      }
      $stmt->close();
    }
    return $status;
  }


  function get_exams_in_interval($from, $to, $order_by, $status='') {
    switch ($order_by) {
    case "cpr": case "status": case "name": break;
    default: $order_by = "date";
    }
    if (!empty($status)) {
      $q = "SELECT cpr, name, date, status, stamp 
            FROM patient 
            WHERE date >= ? AND date <= ?  AND status = ?
            ORDER BY `$order_by` DESC";
      return $this->generic_get($q, array($from, $to, $status), 'sss');
    }
    else {
      $q = "SELECT cpr, name, date, status, stamp 
            FROM patient 
            WHERE date >= ? AND date <= ? AND status != 'DEL'
            ORDER BY `$order_by` DESC";
      return $this->generic_get($q, array($from, $to), 'ss');
    }
  }

  function get_new_exams() {
    $exams = array();
    $q = "SELECT cpr, name, date, status, stamp
          FROM patient 
          WHERE status = 'NEW'
          ORDER BY date DESC, name ASC";
    if ($rs = $this->conn->query($q)) {
      // Replace with mysqli_fetch_all when we get php >= 5.3
      while($exam = $rs->fetch_assoc()) {
	$exams[] = $exam;
      }
      $rs->close();
    }
    return $exams;
  }

  function get_samples($first_sample_no, $last_sample_no, $stamp) {
    $q = 'SELECT n, counts, time
          FROM samples
          WHERE n >= ? AND n <= ? AND stamp = ?';
    return $this->generic_get($q, array($first_sample_no, $last_sample_no, $stamp), 'iis');
  }

  function get_factor() {
    $factor = array();
    $q = "SELECT f, batch, std_count
          FROM factor";
    if ($rs = $this->conn->query($q)) {
      $factor = $rs->fetch_assoc();
      $rs->close();
    }
    return $factor;
  }

  function get_name($cpr) {
    $q = 'SELECT name
          FROM patient
          WHERE cpr = ?';
    $result_array = $this->generic_get($q, array($cpr), 's');
    return empty($result_array[0]) ? '' : $result_array[0]['name'];
  }

  function get_method($stamp) {
    $q = 'SELECT metode 
          FROM patient
          WHERE stamp = ?';
    $result_array = $this->generic_get($q, array($stamp), 's');
    return $result_array[0]['metode'];
  }

  function get_full_exam_info($stamp) { 
    $q = 'SELECT * 
          FROM patient
          WHERE stamp = ?';
    $result_array = $this->generic_get($q, array($stamp), 's');
    return $result_array[0];
  }

  function get_basic_exam_info($stamp) {
    $q = 'SELECT name, date, cpr
          FROM patient
          WHERE stamp = ?';
    $result_array = $this->generic_get($q, array($stamp), 's');
    return $result_array[0];
  }

  function get_clearance_history($cpr) {
    $q = "SELECT date, clearance, clearance_norm
          FROM patient
          WHERE cpr = ? AND status != 'DEL'";
    $result_array = $this->generic_get($q, array($cpr), 's');
    return $result_array;
  }

  function get_clearance_history2($cpr) {
    $q = "SELECT date, clearance, clearance_norm
          FROM patient
          WHERE cpr = ? AND status = 'LOCK'";
    $result_array = $this->generic_get($q, array($cpr), 's');
    return $result_array;
  }

  //
  // setters
  function new_examination($name, $date, $cpr, $stamp, $accession_number) {
    $result = false;
    $q = "INSERT INTO patient (name, date, cpr, status, stamp, accession_number)
          VALUES(?, ?, ?, 'NEW', ?, ?)";
    if ($stmt = $this->conn->prepare($q)) {
      if ($stmt->bind_param('sssss', $name, $date, $cpr, $stamp, $accession_number) &&
	  $stmt->execute() && 
	  $stmt->affected_rows == 1) {
	$result = true;
      }
      $stmt->close();
    }
    return $result;
  }

  function create_new_patient($date, $cpr, $stamp) {
    $this->new_patient(NULL, $date, $cpr, $stamp, NULL);
  }

  function delete_examination($stamp) {
    $q = "UPDATE patient
          SET status = 'DEL'
          WHERE stamp = ?";
    return $this->generic_update($q, array($stamp), 's', 1);
  }

  function set_status($status, $stamp) {
    $q = "UPDATE patient SET status = ? WHERE stamp = ?";
    return $this->generic_update($q, array($status, $stamp), 'ss', 1);
  }

  function set_name($name, $stamp) {
    $q = "UPDATE patient SET name = ? WHERE stamp = ?";
    return $this->generic_update($q, array($name, $stamp), 'ss', 1);
  }

  function set_height($height, $stamp) {
    $q = "UPDATE patient SET height = ? WHERE stamp = ?";
    return $this->generic_update($q, array($height, $stamp), 'is', 1);
  }

  function set_weight($weight, $stamp) {
    $q = "UPDATE patient SET weight = ? WHERE stamp = ?";
    return $this->generic_update($q, array($weight, $stamp), 'is', 1);
  }

  function set_date($date, $stamp) {
    $q = "UPDATE patient SET date = ? WHERE stamp = ?";
    return $this->generic_update($q, array($date, $stamp), 'ss', 1);
  }

  function set_method($method, $stamp) {
    $q = "UPDATE patient SET metode = ? WHERE stamp = ?";
    return $this->generic_update($q, array($method, $stamp), 'ss', 1);
  }

  function set_syringe($syringe, $stamp) {
    $q = "UPDATE patient SET syringe = ? WHERE stamp = ?";
    return $this->generic_update($q, array($syringe, $stamp), 'is', 1);
  }

  function set_creatinin($creatinin, $stamp) {
    $q = "UPDATE patient SET creatinin = ? WHERE stamp = ?";
    return $this->generic_update($q, array($creatinin, $stamp), 'ds', 1);
  }

  function set_inj_before($inj_before, $stamp) {
    $q = "UPDATE patient SET inj_before = ? WHERE stamp = ?";
    return $this->generic_update($q, array($inj_before, $stamp), 'ds', 1);
  }

  function set_inj_after($inj_after, $stamp) {
    $q = "UPDATE patient SET inj_after = ? WHERE stamp = ?";
    return $this->generic_update($q, array($inj_after, $stamp), 'ds', 1);
  }
  
  function set_inj_time($inj_time, $stamp) {
    $q = "UPDATE patient SET inj_time = ? WHERE stamp = ?";
    return $this->generic_update($q, array($inj_time, $stamp), 'ss', 1);
  }

  function set_factor($factor, $stamp) {
    $q = "UPDATE patient SET factor = ? WHERE stamp = ?";
    return $this->generic_update($q, array($factor, $stamp), 'is', 1);
  }

  function set_batch($batch, $stamp) {
    $q = "UPDATE patient SET batch = ? WHERE stamp = ?";
    return $this->generic_update($q, array($batch, $stamp), 'is', 1);
  }

  function set_std_count($std_count, $stamp) {
    $q = "UPDATE patient SET std_count = ? WHERE stamp = ?";
    return $this->generic_update($q, array($std_count, $stamp), 'is', 1);
  }

  function set_nsamples($nsamples, $stamp) {
    $q = "UPDATE patient SET nsamples = ? WHERE stamp = ?";
    return $this->generic_update($q, array($nsamples, $stamp), 'is', 1);
  }

  function set_clearance($clearance_norm, $clearance, $stamp) {
    $q = "UPDATE patient SET clearance_norm = ?, clearance = ?, status = 'LOCK' WHERE stamp = ?";
    return $this->generic_update($q, array($clearance_norm, $clearance, $stamp), 'dds', 1);
  }

  function set_global_factor($factor) {
    $q = "UPDATE factor SET f=?";
    return $this->generic_update($q, array($factor), 'i', 1);
  }

  function set_global_batch($batch) {
    $q = "UPDATE factor SET batch=?";
    return $this->generic_update($q, array($batch), 'i', 1);
  }

  function set_global_std_count($std_count) {
    $q = "UPDATE factor SET std_count=?";
    return $this->generic_update($q, array($std_count), 'i', 1);
  }

  function set_sample_time($time, $sample_number, $cpr, $stamp) {
    $q = "UPDATE samples SET time = ?, flag = 1 - flag WHERE stamp = ? AND n = ?";
    $result = $this->generic_update($q, array($time, $stamp, $sample_number), 'ssi', 1);
    if (!$result) {
      $q = "INSERT INTO samples (cpr, n, time, flag, stamp) VALUES(?, ?, ?, 1, ?)";
      if ($stmt = $this->conn->prepare($q)) {
	if ($stmt->bind_param('siss', $cpr, $sample_number, $time, $stamp) &&
	    $stmt->execute() &&
	    $stmt->affected_rows == 1) {
	  $result = true;
	}
	$stmt->close();
      }
    }
    return $result;
  }

  function set_sample_counts($counts, $sample_number, $cpr, $stamp) {
    $q = "UPDATE samples SET counts = ?, flag = 1 - flag WHERE stamp = ? AND n = ?";
    $result = $this->generic_update($q, array($counts, $stamp, $sample_number), 'isi', 1);
    if (!$result) {
      $q = "INSERT INTO samples (cpr, n, counts, flag, stamp) VALUES(?, ?, ?, 1, ?)";
      if ($stmt = $this->conn->prepare($q)) {
	if ($stmt->bind_param('siis', $cpr, $sample_number, $counts, $stamp) &&
	    $stmt->execute() &&
	    $stmt->affected_rows == 1) {
	  $result = true;
	}
	$stmt->close();
      }
    }
    return $result;
  }


  //
  // private
  private $conn;

  private function generic_get($query, $bind_params, $param_types) {
	
    $result = array();
    $i = 0;
    if ($stmt = $this->conn->prepare($query)) {

      // bind_param needs to be called with a string indicating type of arguments
      // and a number of reference variables matching the number of ? in the query.
      // call_user_func_array is used to achieve that.
      $params = array($param_types);
      for ($j = 0; $j < count($bind_params); ++$j) {
	$params[$j+1] = &$bind_params[$j];
      }
      if (call_user_func_array(array($stmt, 'bind_param'), $params) &&
	  $stmt->execute()) {

	// bind_result needs to be called with a number of reference arguments,
	// the names of the fields in the resultset is available in
	// result_metadata. These names are used to create an associative array
	// with the field names and an array of references to the fields in the
	// associative array.
	// With php version >= 5.3 get_result can be used instead this rather
	// hacky approach.
	$meta_rs = $stmt->result_metadata();
	$meta_fields = $meta_rs->fetch_fields();
	$result_params = array();
	$cols = array();
	foreach ($meta_fields as $field) {
	  $result_params[] = & $cols[$field->name];
	}
	if (call_user_func_array(array($stmt, 'bind_result'), $result_params)) {
	  while ($stmt->fetch()) {
	    foreach ($cols as $k => $v) {
	      $result[$i][$k] = $v;
	    }
	    ++$i;
	  }
	}
      }
      $stmt->close();
    }
//	var_dump($result);
    return $result;
  }

  private function generic_update($query, $bind_params, $param_types, $expected_no_affected_rows=-1) {
    $result = false;
    if ($stmt = $this->conn->prepare($query)) {
      $params = array($param_types);
      for ($i = 0; $i < count($bind_params); ++$i) {
	$params[$i+1] = &$bind_params[$i];
      }
      if (call_user_func_array(array($stmt, 'bind_param'), $params) &&
	  $stmt->execute() &&
	  ($expected_no_affected_rows === -1 || // -1 == dont care how many rows affected
	   $expected_no_affected_rows ===$stmt->affected_rows)) {
	$result = true;
      }
      $stmt->close();
    }
    return $result;
  }

}
?>
