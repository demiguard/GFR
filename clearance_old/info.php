<?php
require_once "lib/templates.php";

$header = new Header("Info side");
$header->pprint();

$body = new Body();
$content = 
'<p><b>GFRcalc</b> beregner GFR Clearance ved brug af én eller flere blod prøver. <br />
     3 analysemetoder er implementeret:</p>
<dl>
  <dt>EPV</dt>
  <dd>Et punkt voksen, GFR beregning for voksne ved én blodprøve</dd>
  <dt>EPB</dt>
  <dd>Et punkt barn, GFR beregning for børn ved én blodprøve</dd>
  <dt>FP</dt>
  <dd>Fler punkt, GFR beregning for voksne ved brug af 4-6 blodprøver</dd>
</dl>
<p><a href="http://hopper.petnet.rh.dk/wiki/Clearance_changelog">Changelog</a> på hopper</p>';
$body->add_content("GFRcalc v2.0", $content);
$body->pprint();
?>
