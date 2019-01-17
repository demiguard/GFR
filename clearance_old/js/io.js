function importCSV(file, callback) {
    var reader = new FileReader();
    reader.onload = function(event) {
	var parsed_data = $.csv.toArrays(event.target.result);
	callback(parsed_data);
    };
    reader.onerror = function(event) {
	console.error("Error while reading " + file);
    };
    
    reader.readAsText(file);
}

function get_clearance_history(cpr, callback) {
    var request = new XMLHttpRequest();
    var query = "query=get_clearance_history&cpr=" + JSON.stringify(cpr);
    request.open("GET", "query_db.php?"+query, true);
    request.send();
    callback(JSON.parse(request.responseText));
}