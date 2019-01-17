<?php 
require_once "lib/templates.php";

$head = new Header('Hent GFR historik');
$head->add_script('js/jquery-2.1.1.js');
$head->add_script('js/jquery.csv-0.71.js');
$head->add_script('js/io.js');
$head->pprint();

$body = new Body();
$body->add_content('Indlæs patient liste fra csv fil', 	'<form method="POST" enctype="multipart/form-data" id="import_form"><input type="file" id="import_file_selector" name="import_file" /><input type="submit" value="Indlæs" /></form>');
$script = "
$('#import_form').submit(function(e) {
	e.preventDefault();
	var file = $('#import_file_selector')[0].files[0];
	console.log('file', file);
	var target = '#csv_header_check';
	importCSV(file, function(data) {
            console.log(data);
            var result = {}
            for (var i in data) {
              get_clearance_history(data[i][0], function(cpr) {
                  return function(hist) { result[cpr] = hist; }
              }(data[i][0]));
            }
            console.log(result);
	});
    });
";
$body->add_script($script);
$body->pprint();
?>
