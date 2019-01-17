<?php
require_once "lib/templates.php";

$header = new Header("Velkommen");
$header->pprint();

$body = new Body();
$content = "<p>Et online-program til beregning af <sup>51</sup>Cr-EDTA clearance for børn og voksne ved brug af én eller flere blodprøver.</p>";
$body->add_content("Velkommen til GFRcalc v2.0", $content);
$body->pprint();
?>