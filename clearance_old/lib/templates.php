<?php
require_once "clearance_functions.php";
class Header {
  var $title;
  var $icon;
  var $stylesheets = array();
  var $scripts = array();

  function __construct($title, $icon="images/hsgfr-16.png", $stylesheet='css/base.css') {
    $this->title = $title;
    $this->icon = $icon;
    $this->stylesheets[] = $stylesheet;
  }

  function add_stylesheet($href) {
    if (!in_array($href, $this->stylesheets)) {
      $this->stylesheets[] = $href;
    }
  }

  function add_script($src) {
    $this->scripts[] = $src;
  }

  function to_string() {
    $out = '<!doctype html>
			<head>
			<meta HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8"/>
			<title>'. $this->title .'</title>
			<link rel="icon" href="'.$this->icon.'" />';
    foreach ($this->stylesheets as $href) {
      $out .= '<link rel="stylesheet" href="' . $href . '" />';
    }
    foreach ($this->scripts as $src) {
      $out .= "<script type=\"text/javascript\" src=\"$src\"></script>";
    }
    $out .= '</head>';
    return $out;
  }

  function pprint() {
    print $this->to_string();
  }
};


class Body {
  var $logo;
  var $title;
  var $menu;
  var $content = array();
  var $scripts = array();

  function __construct($title="GFRcalc") {
    $this->title = $title;
    $this->logo = new Logo();
    $this->menu = new Menu();
  }

  function add_content($title, $string) {
    $this->content[] = array('title' => $title, 'string' => $string);
  }

  function add_placeholder($id) {
    $this->add_content('', "<div id=\"$id\"></div>");
  }

  function add_script($script) {
    $this->scripts[] = $script;
  }

  function to_string() {
    $out = '<body><div id="wrapper"><div id="title">'
      .$this->logo->to_string()
      ."<h1><a href=\"index.php\">$this->title</a></h1></div>"
      .$this->menu->to_string()
      .'<div id="content">';
    foreach ($this->content as $content) {
      if (!empty($content['title'])) {
	$out .= '<h2>'.$content['title'].'</h2>';
      }
      $out .= $content['string'];
    }
    $out .='</div></div><script type="text/javascript">';
    foreach ($this->scripts as $script) {
      $out .= $script;
    }
    $out .= '</script></body></html>';
    return $out;
  }

  function pprint() {
    print $this->to_string();
  }
};

class Menu {
  var $items;
  function __construct($items = '') {
    if (empty($items)) {
      $this->items = 
	array("Velkommen" => array("url" => "index.php", 
				   "title" => "Velkommen til 51Cr-EDCA Clearance beregning"),
	      "Daglige Værdier" => array("url" => "setup.php",
					 "title" => "Daglige Værdier"),
	      "Ny Undersøgelse" => array("url" => "new_examination.php", 
					 "title" => "Ny Undersøgelse"),
	      "Hent Undersøgelse" => array("url" => "get_examination.php",
					   "title" => "Hent Undersøgelse"),
	      "Database" => array("url" => "database.php", 
				  "title" => "Database"),
	      "Info" => array("url" => "info.php", 
			      "title" => "Information om dette program"));
    }
    else {
      $this->items = $items;
    }
  }

  function add_item($name, $url, $description) {
    if (!array_key_exists($name)) {
      $items[$name] = array('url' => $url, 'title' => $description);
    }
  }

  function to_string() {
    $out = '<div id="menu"><ul>';
    foreach ($this->items as $txt => $info) {
      $out .= "<li><a href=\"{$info['url']}\" title=\"{$info['title']}\">$txt</a></li>";
    }
    $out .= "</ul></div>";
    return $out;
  }

  function pprint() {
    print to_string();
  }
};

class Logo {
  var $src;
  var $width;
  var $height;
  var $alt;

  function __construct($src="images/Logo_Rigshospitalet_RGB.gif", 
		       $width="196", 
		       $height="57",
		       $alt="Region H. Rigshospitalet") {
    $this->src = $src;
    $this->width = $width;
    $this->height = $height;
    $this->alt = $alt;
  }

  function to_string() {
    $out = "<img id=\"logo\" src=\"$this->src\" width=\"$this->width\" "
      ."height=\"$this->height\" alt=\"$this->alt\" />";
    return $out;
  }

  function pprint() {
    print to_string();
  }
};


class input_error {
  var $n = 0;
  var $field;
  var $value;

  function insert($f, $v) {
    $this->n++;
    $this->field[$this->n] = $f;
    $this->value[$this->n] = $v;
  }

  function to_string() {
    $out = '<dl>';
    for ($i = 1; $i <= $this->n; ++$i) {
      $out .= "<dt>{$this->field[$i]}</dt><dd>{$this->value[$i]}</dd>";
    }
    $out .= "</dl>";
    return $out;
  }
}

class search_date {
  var $day;
  var $month;
  var $year;

  function search_date($d,$m,$y) {
    if (($d > 0 && $d < 32) && ($m > 0 && $m < 13) && ($y > 2002)) {
      $this->day=$d;
      $this->month=$m;
      $this->year=$y;
    }
    else {
      echo "Invalid search date!";
    }
  }

  function sql_string() {
    return sprintf("%04d-%02d-%02d", $this->year, $this->month, $this->day);
  }

  function timestamp() {
    return mktime(0,0,0,$this->day,$this->$month,$this->year);
  }
}


function database_table($exams) {
  $out = '<table class="listing">'
    .'<form action="delete_patients.php" method=GET>'
    .'<tr><td colspan=5 align="right"><input type="submit" value="Delete selected"></td></tr>'
    .row_many_cells(array('Udskrift', 'Historik', 'Navn', 'CPR', 'Study Dato', 'Status', 'Delete'));

  $even_odd = array('even', 'odd');
  $i = 1;
  $row_nr = 0;
  foreach ($exams as $exam) {
    ++$row_nr;
    $i ^= 1;
    $birth = cpr_birth($exam['cpr']);
    $run_nr = cpr_runnr($exam['cpr']);
    if ($exam['status']=='NEW'){
      $url = "input_flerpunkt.php?stamp={$exam['stamp']}";
      $svarurl = "";
    }
    else {
      $url = "list_locked.php?stamp={$exam['stamp']}";
      $svarurl="<a href='svar.php?stamp={$exam['stamp']}'><img src=images/gulpapir_20.png border=0></a>";
    }
    $history_url = "<a href='clearance_history.php?stamp={$exam['stamp']}'>historik</a>";
    $cells = array($svarurl,
		   $history_url,
		   format_link($url, $exam['name']),
		   format_link($url, "$birth-$run_nr"),
		   format_link($url, $exam['date']),
		   $exam['status'],
		   checkbox("d$row_nr", $exam['stamp']));
    $out .= row_many_cells($cells, '', $even_odd[$i]);
  }
  $out .= "<input type=hidden name=pcount value='$row_nr'>
		</form>
		</table>";

  return $out;
}

function clearance_history_table($clearance_history, $cpr) {
  $out = '<table id="clearance_history" border="0">';
  foreach ($clearance_history as $row) {
    $mean_GFR = normal_mean_GFR($cpr, $row['date']);
    // See comment regarding rounding in clearance_calc_table
    $low_range = round($mean_GFR - ($mean_GFR/4));
    $high_range = round($mean_GFR + ($mean_GFR/4));
    $GFR_normal_range = sprintf("(%.0f - %.0f)", $low_range, $high_range);
    $index_GFR = 100.0 * ($mean_GFR - $row['clearance_norm']) / $mean_GFR;
    $s = index_GFR_Text($index_GFR);
    
    $display_clearance = round($row['clearance']);
    $display_clearance_norm = round($row['clearance_norm']);
    // The clearance history needs to be copied to another application,
    // so it is necesary to control formatting
    $out .= '<pre style="font-family: arial, sans-serif; font-size: 11pt">'
      .sprintf("%s     ", $row['date'])
      .sprintf("GFR(ml/min): %.0f     ", $display_clearance)
      .sprintf("GFR(ml/min x 1.73<sup>2</sup>): %.0f $GFR_normal_range     ", $display_clearance_norm)
      ."<b>$s</b>"
      .'</pre>';
  }
  $out .= "</table>";
  return $out;
}


function clearance_calc_table($examination) {
  $out = '<table>'
    .row($examination['cpr_string'], 'CPR-nummer')
    .row($examination['name'], 'Navn')
    .row($examination['date'], 'Undersøgelses dato')
    .row($examination['age'], 'Alder', '%u år')
    .row($examination['height'], 'Højde', '%u cm')
    .row($examination['weight'], 'Vægt', '%u kg')
    .row($examination['syringe'], 'Sprøjte nr.')
    .row($examination['inj_before'], 'Sprøjtevægt før injektion', '%.4f g')
    .row($examination['inj_after'], 'Sprøjtevægt efter injektion', '%.4f g')
    .row($examination['factor'], 'Fortyndings faktor')
    .row($examination['std_count'], 'Standardtælletal', '%u cpm')
    .row($examination['dosis'], 'Dosis', '%u cpm')
    .row($examination['OV'], 'Overfladeareal', '%.2f m<sup>2</sup>')
    .row($examination['metode_display'], 'Metode')
    .row($examination['inj_time'], 'Injektions tidspunkt');

  $sample_time = $examination['sample_time'];
  $sample_counts = $examination['sample_counts'];
  for($i = 1; $i <= $examination['nsamples']; ++$i) {
    $out .= row_many_cells(array("Prøve $i", $sample_time[$i], "$sample_counts[$i] cpm"));
  }

  $mean_GFR_tc = normal_mean_GFR( $examination['cpr'], $examination['date'] );
  $index_GFR_tc = 100.0 * ($mean_GFR_tc - $examination['clearance_st']) / $mean_GFR_tc;
  $s_tc = index_GFR_Text($index_GFR_tc);

  // clerance stored in database is truncated to 2 digits, 
  // sprintf uses bankers rounding. This can lead to the value calculated and 
  // the value from the database being displayed differently.
  // The database truncates input so the calculated value >= stored value.
  // So we want to round up, but we are at the mercy of the php implementation.
  // From php version >= 5.2.7 round conforms to C99, but we have 5.2.5...
  $display_clearance_st = round($examination['clearance_st']);
  $display_clearance_korr = round($examination['clearance_korr']);
  $out .= row($display_clearance_st, "<b>GFR(ml/min x 1.73m<sup>2</sup>):</b>", "<b>%.0f</b>")
    .row($display_clearance_korr, "<b>GFR(ml/min): </b>", "<b>%.0f</b>")
    .row("<b>$s_tc</b>", "<b>Tilstand </b>")
    .row('<br />','')
    .'<table>';

  return $out;
}




function exams_table($exams) {
  $even_odd = array('even', 'odd');
  $i = 1;
  $row_nr = 0;
  $out = 
    '<table class="listing">'
    ."<tr><td>CPR-nummer:</td><td>Navn</td><td>Dato</td><td>Status</td></tr>";
  foreach ($exams as $exam) {
    ++$row_nr;
    $i ^= 1;
    $birth = cpr_birth($exam['cpr']);
    $run_nr = cpr_runnr($exam['cpr']);
    $url = "input_flerpunkt.php?stamp={$exam['stamp']}";
    $out .= 
      "<tr class={$even_odd[$i]}>
			<td><a href='$url'>$birth-$run_nr</a></td>
			<td><a href='$url'>{$exam['name']}</a></td>
			<td><a href='$url'>{$exam['date']}</a></td>
			<td>{$exam['status']}</td>
			</tr>";
  }
  $out .= "</table>";
  return $out;
}


function examination_result_table($exam) {
  $mean_GFR = normal_mean_GFR($exam['cpr'], $exam['date']);
  $index_GFR = 100.0 * ($mean_GFR - $exam['clearance_norm']) / $mean_GFR;
  $s = index_GFR_Text($index_GFR);
  $GFR_normal_range = sprintf("%.0f (%.0f - %.0f)", $mean_GFR, $mean_GFR - ($mean_GFR/4), $mean_GFR + ($mean_GFR/4));

  $out = '<table class="info">'
    .row($exam['cpr'], 'CPR nr.:')
    .row($exam['date'],'Undersøgelsesdato:')
    .row($exam['name'],'Navn:')
    ."<tr><td colspan=2 height=50></td></tr>"
    .row(sprintf("%.0f", $exam['clearance']), 'Clearance')
    .row(sprintf("%.0f", $exam['clearance_norm']), 'Korrigeret clearance ml/(min x 1.73 m<sup>2</sup>):')
    .row(sprintf("%s (%.0f%%)", $s, $index_GFR), '')
    .row($GFR_normal_range, "Normalområde for korrigeret clearance ml/(min x 173 m<sup>2</sup>")
    ."</table>";

  return $out;
}

function row($value, $description, $format='') {
  if (!empty($format)) {
    $value = sprintf($format, $value);
  }
  return "<tr><td>$description</td><td>$value</td></tr>";
}

function row_many_cells($fields, $format='', $class='') {
  $out = '<tr '.(!empty($class) ? 'class="'.$class.'"' : '').'>';
  foreach ($fields as $i => $field) {
    if (!empty($format[$i])) {
      $field = sprintf($format[$i], $field);
    }
    $out .= "<td>$field</td>";
  }
  $out .= '</tr>';
  return $out;
}

function format_link($href, $content) {
  return '<a href="'.$href.'">'.$content.'</a>';
}

function checkbox($name, $value) {
  return '<input type="checkbox" name="'.$name.'" value="'.$value.'">';
}

//
// Forms
//
function new_patient_form() {
  return '<form name="new_patient" action="create_examination.php" method=post>
		<input type="hidden" name="AccessionNumber" />
		<table>'
    .row(date("Y-m-d"), "Idag")
    .'<tr>
		<td>CPR nr.:</td>
		<td>
		<input type="text" name="cpr_birth" size="6" maxlength="6" autofocus />
		<input type="text" name="cpr_runnr" size="4" maxlength="4" />
		</td>
		</tr>'
    .input_row('', 'Navn:', 'PatientName', 30)
    .input_row(date("Y-m-d"), 'Dato (YYYY-MM-DD):', 'date', 10)
    .'<tr>
									 <td><input type="submit" name="save" value="Gem" /></td>
									 </tr>
									 </table>              
									 </form>';
}

function add_sample_form($examination, $samples, $daily_values) {
  $form = "add_sample";
  $out = 
    '<form name="'.$form.'" action="process_samples.php" method="POST">'
    .'<div class="wrapper">'
    .daily_values_fieldset($daily_values, $form)
    .examination_data_fieldset($examination, $form)
    .'</div>'
    .sample_data_fieldset($examination['metode'], $samples, $form);
  if ($examination['status'] == 'NEW') {
    $out .= '<p>
			<input type=hidden name=stamp value="'.$examination['stamp'].'" />
			<input type=hidden name=cpr value="'.$examination['cpr'].'" />
			<input name=button type=submit value="Beregn" />
			<input type=submit name=button value="Gem" />
			<input type=submit name=button value="Beregn udenom databasen" />
			<input type=submit name=button value="Afbryd" />
			</p>';
  }
  $out .= "</form>";
  return $out;
}


function daily_values_form($daily_values, $action, $method='GET') {
  $form = 'daily_values';
  return '<form name="'.$form.'" action="'.$action.'" method="'.$method.'">'
    .daily_values_fieldset($daily_values, $form)
    .'<tr><td><input type="submit" value="Gem"></td></tr>'
    .'</form>';
}


function daily_values_fieldset($daily_values, $form) {
  return 
    '<fieldset id="daily_values"><legend>Daglige værdier</legend>'
    .'<table>'
    .input_row($daily_values['f'], 'Faktor:', 'f', 5, $form, "batch")
    .input_row($daily_values['batch'], 'Batch:', 'batch', 5, $form, "std_count")
    .input_row($daily_values['std_count'], 'Standard tælletal:', 'std_count', 5, $form, "name")
    .'</table>'
    .'</fieldset>';
}

function examination_data_fieldset($examination, $form) {
  return '<fieldset id="examination_data"><legend>Undersøgelses data</legend><table>'
    .row($examination['date'], 'Dato:')
    .row($examination['cpr'], "CPR nr.:")
    .input_row($examination['name'], 'Navn:', 'name', 40, $form, 'height')
    .input_row($examination['height'], 'Højde: (cm):','height', 3, $form, 'weight')     
    .input_row($examination['weight'], 'Vægt (kg):','weight', 3, $form, 'syringe')
    .input_row($examination['syringe'], 'Sprøjte:','syringe', 2, $form, 'inj_before')
    .input_row($examination['inj_before'], 'Sprøjtevægt før Injektion (g:)'
	       ,'inj_before', 5, $form, 'inj_after')
    .input_row($examination['inj_after'], 'Sprøjtevægt efter injektion (g):' 
	       ,'inj_after', 5, $form, 'inj_time_hh')
    .input_row_time($examination['inj_time'], 'Injektionstidspunkt (tt:mm):', 'inj_time', $form)
    ."</table></fieldset>";
}

function sample_data_fieldset($method, $samples, $form) {
  $choices = array(array("Et punkt voksen", "EPV"),
		   array("Et punkt barn", "EPB"),
		   array("Flere punkter voksen", "FP"));
  return '<fieldset id="sample_data"><legend>Prøve data</legend><table>'
    .radio_buttons('Metode:', 'metode', $choices, $method)
    .'</table><table>'
    .input_samples($samples, 6, $form)
    ."</table></fieldset>";
}


function input_samples($samples, $sample_rows, $form) {
  $out = "<tr>
		<th>Prøve</th>
		<th>Prøvetidspunkt (TT:mm):</th>
					     <th>Prøvetælletal (cpm)</th>
						     </tr>";
  for ($i = 1, $j = 0; $j < $sample_rows; ++$i, ++$j) {
    $time = empty($samples[$j]) ? '' : $samples[$j]['time'];
    $count = empty($samples[$j]) ? '' : $samples[$j]['counts'];
    $out .= '<tr>'
      .input_time($time, $i, 'sample_time'.$i, $form, 'sample_counts'.$i)
      .input($count, '', 'sample_counts'.$i, 5)
      .'</tr>';
  }
  return $out;
}


function input_row_time($time, $description, $row_name, $form, $focus_field='') {
  return '<tr>'.input_time($time, $description, $row_name, $form, $focus_field).'</tr>';
}

function input_time($time, $description, $row_name, $form, $focus_field='') {
  $hh = '';
  $mm = '';
  if (!empty($time) && strlen($time) >= 17) {
    $hh = substr($time, 11, 2); // Magic :)
    $mm = substr($time, 14, 2); 
  }
  $out = 
    "<td>$description</td><td>"
    .'<input type="text" value="'.$hh.'" name="'.$row_name.'_hh" maxlength=2 size=2 onKeyUp='."'if (this.value.length == 2) {document.$form.{$row_name}_mm.focus(); }'> : "
    .'<input type="text" value="'.$mm.'" name="'.$row_name.'_mm" maxlength=2 size=2 onKeyUp='."'if (this.value.length == 2) {document.$form.$focus_field.focus(); }'>"
    .'</td>';
  return $out;
}

function radio_buttons($title, $name, $choices, $checked) {
  $out = "<tr><td colspan=2>$title</td></tr>";
  foreach ($choices as $choice) {
    $out .= 
      '<tr><td>'.$choice[0].'</td>'
      .'<td><input type="radio" name="'.$name.'" value="'.$choice[1].'"'
      .($choice[1] == $checked ? 'checked' : '')
      .' /></td></tr>';
  }
  return $out;
}

function db_interface($from, $to, $sort_order, $status) {
  $out = 
    '<form action="database.php" method=GET>'
    .'<ul><li>Fra: '.date_picker('from', $from).'</li><li>Til: '.date_picker('to', $to).'</li>'
    .'<li>Status:<select name="status" size=1>';
  foreach (array('Alle', 'NEW', 'LOCK') as $option) {
    $out .= '<option value="'.$option.'"'. ($option === $status ? " selected" : "") .">$option</option>";
  }
  $out .= '</select></li>'
    .'<li>Sort:<select name="sort_order" size=1>';
  foreach (array('date' => 'Dato', 'status' => 'Status', 'name' => 'Navn', 'cpr' => 'CPR nr.') as $value => $option) {
    $out .= '<option value="'.$value.'"'. ($value === $sort_order ? " selected" : "") .">$option</option>";
  }
  $out .= 
    '</select></li>'
    .'<li><input type=submit name="show_interval" value="Vis patienter"></li>'
    .'</ul></form>';
  return $out;
}

function date_picker($prefix, $selected_date) {
  $out = "<select name={$prefix}_day size=1>";
  for ($i = 1; $i < 32; ++$i) {
    $selected = ($i == $selected_date->day)? 'selected' : '';   
    $out .= "<option $selected>$i</option>";
  }
  $out .= "</select><select name={$prefix}_month size=1>";
  for ($i = 1; $i < 13; ++$i) {
    $selected = ($i == $selected_date->month)? 'selected' : '';  
    $out .= "<option $selected>$i</option>";
  }
  $out .= "</select><select name={$prefix}_year size=1>";
  for ($i = 2000; $i < 2020; ++$i) {
    $selected = ($i == $selected_date->year)? 'selected' : '';  
    $out .= "<option $selected>$i</option>";
  }
  $out .= "</select>";
  return $out;
}

function input_row($value, $description, $name, $size, $focus_form='', $focus_field='') {
  return '<tr>'.input($value, $description, $name, $size, $focus_form, $focus_field).'</tr>';
}

function input($value, $description, $name, $size, $focus_form='', $focus_field='') {
  $out = '';
  if (!empty($description)) {
    $out .= "<td>$description</td>";
  }
  $out .= '<td><input type="text" value="'.$value.'" name="'.$name.'" size="'.$size.'"';
  if (!empty($focus_form) && !empty($focus_field)) {
    $out .= " onKeyUp='if (this.value.length == $size) {document.$focus_form.$focus_field.focus();}'";
  }
  $out .= ' /></td></tr>';
  return $out;
}



?>
