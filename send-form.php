<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); exit; }

const SMTP_HOST = 'smtp.beget.com';
const SMTP_PORT = 465;
const SMTP_USER = 'peregruzmail@tiwmail.ru';
const SMTP_PASS = 'A1yZCqanS!0J';
const MAIL_FROM = 'peregruzmail@tiwmail.ru';
const MAIL_NAME = 'pravo-trans.ru — заявка с сайта';
const MAIL_TO   = ['otmenim@yandex.ru', 'pr@topinweb.ru'];
const MAIL_SUBJ = 'Новая заявка - перегруз, негабарит';
const LOG_FILE  = __DIR__ . '/submissions.log';

$d = json_decode(file_get_contents('php://input'), true);
if (!$d) { echo json_encode(['ok' => false]); exit; }

// Отвечаем браузеру немедленно, не дожидаясь отправки
$response = json_encode(['ok' => true]);
header('Content-Length: ' . strlen($response));
header('Connection: close');
echo $response;
if (function_exists('fastcgi_finish_request')) {
    fastcgi_finish_request();
} else {
    ob_end_flush();
    flush();
}
ignore_user_abort(true);
set_time_limit(60);

// Фоновая обработка: email
$tx       = '10000001:' . time();
$text     = build_text($d, $tx, 'https://pravo-trans.ru/');
$mail_err = '';
$mail_ok  = smtp_send(SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
                      MAIL_FROM, MAIL_NAME, MAIL_TO, MAIL_SUBJ, $text, $mail_err);

$name  = $d['name']  ?? ($d['orgName'] ?? '?');
$phone = $d['phone'] ?? '?';
$log   = date('Y-m-d H:i:s')
       . " | {$name} | {$phone}"
       . " | Email:" . ($mail_ok ? 'OK' : "FAIL({$mail_err})")
       . " | TX:{$tx}\n";
file_put_contents(LOG_FILE, $log, FILE_APPEND | LOCK_EX);

function build_text($d, $tx, $site) {
    $lines = ['Request details:'];
    $name = $d['name'] ?? ($d['orgName'] ?? null);
    if ($name)                    $lines[] = "Name: {$name}";
    if (!empty($d['phone']))      $lines[] = "Phone: {$d['phone']}";
    if (!empty($d['orgName']))    $lines[] = "Organization: {$d['orgName']}";
    if (!empty($d['orgAddress'])) $lines[] = "Address: {$d['orgAddress']}";
    if (!empty($d['phone2']))     $lines[] = "Phone 2: +7{$d['phone2']}";
    if (!empty($d['email']))      $lines[] = "Email: {$d['email']}";
    if (!empty($d['inn']))        $lines[] = "INN: {$d['inn']}";
    if (!empty($d['kpp']))        $lines[] = "KPP: {$d['kpp']}";
    if (!empty($d['ogrn']))       $lines[] = "OGRN: {$d['ogrn']}";
    if (!empty($d['okpo']))       $lines[] = "OKPO: {$d['okpo']}";
    if (!empty($d['message']))    $lines[] = "Message: {$d['message']}";
    $lines[] = '';
    $lines[] = 'Additional information:';
    $lines[] = "Transaction ID: {$tx}";
    $lines[] = $site;
    $lines[] = "UTM source: "   . ($d['utm_source']   ?? '');
    $lines[] = "UTM medium: "   . ($d['utm_medium']   ?? '');
    $lines[] = "UTM campaign: " . ($d['utm_campaign'] ?? '');
    $lines[] = "UTM content: "  . ($d['utm_content']  ?? '');
    $lines[] = "UTM term: "     . ($d['utm_term']     ?? '');
    $lines[] = '-----';
    return implode("\n", $lines);
}

function smtp_send($host, $port, $user, $pass, $from, $from_name, $to, $subject, $body, &$err) {
    $socket = @fsockopen("ssl://{$host}", $port, $errno, $errstr, 15);
    if (!$socket) { $err = "connect:[{$errno}]{$errstr}"; return false; }

    $r = function() use ($socket) { return fgets($socket, 512); };
    $w = function($s) use ($socket) { fputs($socket, $s . "\r\n"); };

    $r();
    $w('EHLO ' . ($_SERVER['HTTP_HOST'] ?? 'localhost'));
    while ($l = $r()) { if (isset($l[3]) && $l[3] === ' ') break; }

    $w('AUTH LOGIN'); $r();
    $w(base64_encode($user)); $r();
    $w(base64_encode($pass));
    $auth = $r();
    if (substr($auth, 0, 3) !== '235') { $err = 'auth:' . trim($auth); fclose($socket); return false; }

    $w("MAIL FROM: <{$from}>"); $r();
    foreach ((array)$to as $addr) {
        $w("RCPT TO: <{$addr}>");
        $rcpt = $r();
        if (substr($rcpt, 0, 3) !== '250') { $err = "rcpt<{$addr}>:" . trim($rcpt); fclose($socket); return false; }
    }

    $w('DATA'); $r();
    $enc_subj = '=?UTF-8?B?' . base64_encode($subject) . '?=';
    $msg = "From: =?UTF-8?B?" . base64_encode($from_name) . "?= <{$from}>\r\n"
         . "To: " . implode(', ', (array)$to) . "\r\n"
         . "Subject: {$enc_subj}\r\n"
         . "MIME-Version: 1.0\r\n"
         . "Content-Type: text/plain; charset=UTF-8\r\n"
         . "Content-Transfer-Encoding: base64\r\n\r\n"
         . chunk_split(base64_encode($body))
         . "\r\n.\r\n";
    fputs($socket, $msg);
    $resp = $r();
    $w('QUIT');
    fclose($socket);

    if (substr($resp, 0, 3) !== '250') { $err = 'data:' . trim($resp); return false; }
    return true;
}
