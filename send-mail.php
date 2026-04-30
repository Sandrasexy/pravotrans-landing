<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); exit; }

$raw  = file_get_contents('php://input');
$d    = json_decode($raw, true);
$text = isset($d['text']) ? strip_tags($d['text']) : '';
if (!$text) { echo json_encode(['ok' => false, 'err' => 'empty']); exit; }

$to      = 'otmenim@yandex.ru';
$subject = 'Новая заявка — pravo-trans.ru';
$headers = "MIME-Version: 1.0\r\n"
         . "Content-Type: text/plain; charset=UTF-8\r\n"
         . "From: no-reply@pravo-trans.ru\r\n"
         . "Cc: pr@topinweb.ru\r\n";

$ok = mail($to, '=?UTF-8?B?' . base64_encode($subject) . '?=', $text, $headers);
echo json_encode(['ok' => (bool)$ok]);
