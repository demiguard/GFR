function get_name(cpr, target) {
    var request = new XMLHttpRequest();
    var query = "query=get_name&cpr=" + JSON.stringify(cpr);
    request.open("GET", "query_db.php?"+query, true);
    request.send();
    request.onreadystatechange = function() {
	if (request.readyState == 4 && request.status == 200) {
	    var name = JSON.parse(request.responseText);
	    target.value = name;
	}
    };
};


// Remove links from cells and make the row link to the first cells link url
function replace_cell_links_with_row_link() {
    var rows = document.querySelectorAll("tr");
    for (var i = 0; i < rows.length; ++i) {
	var anchors = rows[i].querySelectorAll("td>a");
	if (typeof(anchors) !== 'undefined' && anchors.length > 0) {
	    link = anchors[0].getAttribute("href");
	    rows[i].setAttribute("class", rows[i].getAttribute("class") + " link");
	    rows[i].onclick = (
		function() { 
		    var local_link = link;
		    return function() {
			location.href = local_link;
		    };
		})();
	    for (var j = 0; j < anchors.length; ++j) {
		var text = anchors[j].innerHTML;
		var parent = anchors[j].parentNode;
		parent.removeChild(anchors[j]);
		parent.innerHTML = text;
	    }
	}
    }
};

// function check_cpr(cpr) {
//     var new_format = /^([0-9]{7})([A-Z]{2})([0-9]{1})$/;
//     var old_format = /^([0-9]{10})$/;
//     var checksum = function(cpr) { 
// 	return (cpr[0]*4 + cpr[1]*3 + cpr[2]*2 + cpr[3]*7 + cpr[4]*6 + cpr[5]*5 + 
// 		cpr[6]*4 + cpr[7]*3 + cpr[8]*2 + cpr[9]*1) % 11 == 0;
//     };
//     return new_format.test(cpr) || (old_format.test(cpr) && checksum(cpr));
// }