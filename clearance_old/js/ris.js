function get_todays_bookings(target, tr_onclick, force_update) {
    var query = '';
    if (force_update) {
	console.log(force_update);
	query = '?force_update=1';
    }
    var request = new XMLHttpRequest();
    request.open("GET", "ris.php"+query, true);
    request.onreadystatechange = function() {
	if (request.readyState == 4 && request.status == 200) {
	    var records = JSON.parse(request.responseText);
	    var table = document.createElement("table");
	    table.setAttribute("class", "listing");
	    var even_odd = {0 : 'even', 1 : 'odd'};
	    // The table header
	    var tr = document.createElement("tr");
	    for(var key in records[0]) {
		var th = document.createElement("th");
		var text = document.createTextNode(key);
		th.appendChild(text);
		tr.appendChild(th);
	    }
	    table.appendChild(tr);
	    
	    // check if the records has been used already
	    var accession_numbers = new Array(records.length);
	    for (var i in records) {
		accession_numbers[i] = records[i]['AccessionNumber'];
	    }
	    var checked = check_accession_numbers(accession_numbers);

	    // The rows
	    var j = 0;
            for (var i in records) {
		// Skip if already used.
		if (!checked[i]) {
		    tr = document.createElement("tr");
		    tr.setAttribute('class', even_odd[j] + " link");
		    j ^= 1;
		    if (typeof(tr_onclick) !== "undefined") {
			tr.onclick = function() { tr_onclick(this); };
		    }
                    var record = records[i];
		    for(var key in record) {
			var text = document.createTextNode(record[key]);
			var td = document.createElement("td");
			td.setAttribute("class", key);
			td.appendChild(text);
			tr.appendChild(td);
		    }
		    table.appendChild(tr);
		}
	    }
	    var target_node = document.getElementById(target);
	    var parent = target_node.parentNode;
	    parent.replaceChild(table, target_node);
	    table.setAttribute("id", target);
	}
    };
    request.send();
};

function check_accession_numbers(numbers) {
    var request = new XMLHttpRequest();
    var query = "query=check_accession_numbers&numbers=" + JSON.stringify(numbers);
    request.open("GET", "query_db.php?"+query, false);
    request.send();
    return JSON.parse(request.responseText);
};
