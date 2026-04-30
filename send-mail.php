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

$ok1 = smtp_send($smtp_host, $smtp_port, $smtp_user, $smtp_pass,
                 $from, $from_name, $to1, $subject, $text);
$ok2 = smtp_send($smtp_host, $smtp_port, $smtp_user, $smtp_pass,
                 $from, $from_name, $to2, $subject, $text);
echo json_encode(['ok' => $ok1 && $ok2]);

function smtp_send($host, $port, $user, $pass, $from, $from_name, $to, $subject, $body) {
    $socket = @fsockopen("ssl://$host", $port, $errno, $errstr, 15);
    if (!$socket) return false;

    $r = function() use ($socket) { return fgets($socket, 512); };
    $w = function($s) use ($socket) { fputs($socket, $s . "\r\n"); };

    $r(); // greeting

    $w('EHLO ' . (isset($_SERVER['HTTP_HOST']) ? $_SERVER['HTTP_HOST'] : 'localhost'));
    while ($l = $r()) { if ($l[3] === ' ') break; }

    $w('AUTH LOGIN');
    $r();
    $w(base64_encode($user));
    $r();
    $w(base64_encode($pass));
    $auth = $r();
    if (substr($auth, 0, 3) !== '235') { fclose($socket); return false; }

    $w("MAIL FROM: <$from>");
    $r();
    $w("RCPT TO: <$to>");
    $r();

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

    return substr($resp, 0, 3) === '250';
}
