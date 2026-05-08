<?php
if (($_GET['t'] ?? '') !== 'pravolog2026') { http_response_code(403); exit('Forbidden'); }
header('Content-Type: text/plain; charset=utf-8');
$f = __DIR__ . '/submissions.log';
echo file_exists($f) ? file_get_contents($f) : 'Лог пуст.';
