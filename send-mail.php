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

// SMTP config
$smtp_host = 'mail.beget.com';
$smtp_port = 465;
$smtp_user = 'peregruzmail@tiwmail.ru';
$smtp_pass = 'A1yZCqanS!0J';
$from      = 'peregruzmail@tiwmail.ru';
$from_name = 'pravo-trans.ru — заявка с сайта';
$to1       = 'otmenim@yandex.ru';
$to2       = 'pr@topinweb.ru';
$subject   = 'Новая заявка - перегруз, негабарит';

$err1 = $err2 = '';
$ok1 = smtp_send($smtp_host, $smtp_port, $smtp_user, $smtp_pass, $from, $from_name, $to1, $subject, $text, $err1);
$ok2 = smtp_send($smtp_host, $smtp_port, $smtp_user, $smtp_pass, $from, $from_name, $to2, $subject, $text, $err2);

$log = date('Y-m-d H:i:s') . " ok1=$ok1 err1=$err1 | ok2=$ok2 err2=$err2\n";
file_put_contents(__DIR__ . '/mail.log', $log, FILE_APPEND);

echo json_encode(['ok' => $ok1 && $ok2, 'e1' => $err1, 'e2' => $err2]);

function smtp_send($host, $port, $user, $pass, $from, $from_name, $to, $subject, $body, &$err) {
    $socket = @fsockopen("ssl://$host", $port, $errno, $errstr, 15);
    if (!$socket) { $err = "connect:[$errno]$errstr"; return false; }

    $r = function() use ($socket) { return fgets($socket, 512); };
    $w = function($s) use ($socket) { fputs($socket, $s . "\r\n"); };

    $r(); // greeting

    $w('EHLO ' . (isset($_SERVER['HTTP_HOST']) ? $_SERVER['HTTP_HOST'] : 'localhost'));
    while ($l = $r()) { if (isset($l[3]) && $l[3] === ' ') break; }

    $w('AUTH LOGIN');
    $r();
    $w(base64_encode($user));
    $r();
    $w(base64_encode($pass));
    $auth = $r();
    if (substr($auth, 0, 3) !== '235') { $err = "auth:" . trim($auth); fclose($socket); return false; }

    $w("MAIL FROM: <$from>");
    $r();
    $w("RCPT TO: <$to>");
    $rcpt = $r();
    if (substr($rcpt, 0, 3) !== '250') { $err = "rcpt:" . trim($rcpt); fclose($socket); return false; }

    $w('DATA');
    $r();

    $enc_subj = '=?UTF-8?B?' . base64_encode($subject) . '?=';
    $msg = "From: =?UTF-8?B?" . base64_encode($from_name) . "?= <$from>\r\n"
         . "To: $to\r\n"
         . "Subject: $enc_subj\r\n"
         . "MIME-Version: 1.0\r\n"
         . "Content-Type: text/plain; charset=UTF-8\r\n"
         . "Content-Transfer-Encoding: base64\r\n"
         . "\r\n"
         . chunk_split(base64_encode($body))
         . "\r\n.\r\n";

    fputs($socket, $msg);
    $resp = $r();

    $w('QUIT');
    fclose($socket);

    if (substr($resp, 0, 3) !== '250') { $err = "data:" . trim($resp); return false; }
    return true;
}
