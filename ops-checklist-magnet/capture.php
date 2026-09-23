<?php
/**
 * POST /ops-checklist/capture.php
 *
 * Save-first inbox (best effort), then email via Resend.
 * No Cursor webhook, no Grok Bot, no MailerLite on this path.
 *
 * Config (server-only config.php or env):
 *   RESEND_API_KEY (required for send)
 *   RESEND_FROM (optional) default Ana at Tin Dog Digital <ana@tindogdigital.tech>
 *   LEAD_NOTIFY_EMAIL (optional) default ERIC.ROUGH@TINDOGBREWING.COM
 */

function ops_redirect($target) {
  header('Location: ' . $target, true, 303);
  exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
  ops_redirect('index.html');
}

$honeypot = trim((string) (isset($_POST['website']) ? $_POST['website'] : ''));
if ($honeypot !== '') {
  ops_redirect('thank-you.html');
}

$email = trim((string) (isset($_POST['email']) ? $_POST['email'] : ''));
$name = trim((string) (isset($_POST['name']) ? $_POST['name'] : ''));

if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
  ops_redirect('index.html?error=email');
}

$resendKey = getenv('RESEND_API_KEY') ? getenv('RESEND_API_KEY') : '';
$resendFrom = getenv('RESEND_FROM') ? getenv('RESEND_FROM') : '';
$notifyEmail = getenv('LEAD_NOTIFY_EMAIL') ? getenv('LEAD_NOTIFY_EMAIL') : '';

$configFile = __DIR__ . '/config.php';
if (is_readable($configFile)) {
  $cfg = include $configFile;
  if (is_array($cfg)) {
    if ($resendKey === '' && !empty($cfg['RESEND_API_KEY'])) {
      $resendKey = $cfg['RESEND_API_KEY'];
    }
    if ($resendFrom === '' && !empty($cfg['RESEND_FROM'])) {
      $resendFrom = $cfg['RESEND_FROM'];
    }
    if ($notifyEmail === '' && !empty($cfg['LEAD_NOTIFY_EMAIL'])) {
      $notifyEmail = $cfg['LEAD_NOTIFY_EMAIL'];
    }
  }
}

if ($resendFrom === '') {
  $resendFrom = 'Ana at Tin Dog Digital <ana@tindogdigital.tech>';
}
if ($notifyEmail === '') {
  $notifyEmail = 'ERIC.ROUGH@TINDOGBREWING.COM';
}

$submitId = 'ops-' . gmdate('Ymd-His') . '-' . substr(hash('sha256', $email . microtime(true)), 0, 10);
$record = array(
  'savedAt' => gmdate('c'),
  'submitId' => $submitId,
  'source' => 'ops-checklist',
  'name' => $name,
  'email' => $email,
);
$raw = json_encode($record, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);

$inboxDir = __DIR__ . '/inbox';
if (!is_dir($inboxDir)) {
  @mkdir($inboxDir, 0755, true);
}
$inboxFile = $inboxDir . '/' . $submitId . '.json';
@file_put_contents($inboxFile, $raw);
@file_put_contents(
  $inboxDir . '/leads.jsonl',
  $raw . "\n",
  FILE_APPEND
);

if ($resendKey === '') {
  error_log('ops-checklist capture.php: RESEND_API_KEY not configured');
  ops_redirect('index.html?error=config');
}

$htmlPath = __DIR__ . '/deliver-email.html';
$html = @file_get_contents($htmlPath);
if ($html === false || $html === '') {
  error_log('ops-checklist capture.php: missing deliver-email.html');
  ops_redirect('index.html?error=send');
}

$safeName = htmlspecialchars($name, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
if ($name !== '') {
  $greeting = '<p>Hi ' . $safeName . ',</p>';
  $html = preg_replace(
    '/(<h1[^>]*>Your Free Ops Automation Checklist<\/h1>)/',
    $greeting . '$1',
    $html,
    1
  );
}

$text = "Your Free Ops Automation Checklist\n\n";
$text .= "TRACE the workflow first. Automate second.\n\n";
$text .= "T. Track: pick one workflow end to end.\n";
$text .= "R. Record: list every human touch (who, what, channel, minutes).\n";
$text .= "A. Audit: mark hand-copy between systems.\n";
$text .= "C. Cost: minutes / 60 x runs x loaded rate. Yearly is about weekly x 50.\n";
$text .= "E. Eliminate: pick the most expensive repetitive loop for a bot first.\n\n";
$text .= "Printable markdown is attached. Soft next steps:\n";
$text .= "Role map (free): https://tindogdigital.tech/role-map/\n";
$text .= "Slack Opportunity Audit ($299): https://tindogdigital.tech/slack-audit/\n\n";
$text .= "Ana · Tin Dog Digital\nana@tindogdigital.tech · tindogdigital.tech\n";
if ($name !== '') {
  $text = "Hi {$name},\n\n" . $text;
}

$payload = array(
  'from' => $resendFrom,
  'to' => array($email),
  'reply_to' => 'ana@tindogdigital.tech',
  'subject' => 'Your Free Ops Automation Checklist',
  'html' => $html,
  'text' => $text,
);

if (strcasecmp($notifyEmail, $email) !== 0 && $notifyEmail !== '') {
  $payload['bcc'] = array($notifyEmail);
}

$mdPath = __DIR__ . '/checklist.md';
$md = is_readable($mdPath) ? @file_get_contents($mdPath) : false;
if ($md !== false && $md !== '') {
  $payload['attachments'] = array(
    array(
      'filename' => 'ops-automation-checklist.md',
      'content' => base64_encode($md),
    ),
  );
}

$jsonPayload = json_encode($payload);
$resendBody = false;
$resendStatus = 0;
$resendErr = 'curl not available';

if (function_exists('curl_init')) {
  $ch = curl_init('https://api.resend.com/emails');
  curl_setopt_array($ch, array(
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => $jsonPayload,
    CURLOPT_HTTPHEADER => array(
      'Authorization: Bearer ' . $resendKey,
      'Content-Type: application/json',
    ),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 30,
  ));
  $resendBody = curl_exec($ch);
  $resendStatus = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
  $resendErr = curl_error($ch);
  curl_close($ch);
} else {
  $ctx = stream_context_create(array(
    'http' => array(
      'method' => 'POST',
      'header' => "Authorization: Bearer {$resendKey}\r\nContent-Type: application/json\r\n",
      'content' => $jsonPayload,
      'timeout' => 30,
      'ignore_errors' => true,
    ),
  ));
  $resendBody = @file_get_contents('https://api.resend.com/emails', false, $ctx);
  if (isset($http_response_header) && is_array($http_response_header)) {
    foreach ($http_response_header as $hdr) {
      if (preg_match('/^HTTP\/\S+\s+(\d+)/', $hdr, $m)) {
        $resendStatus = (int) $m[1];
        break;
      }
    }
  }
  $resendErr = $resendBody === false ? 'http request failed' : '';
}

if ($resendBody === false || $resendStatus < 200 || $resendStatus >= 300) {
  error_log('ops-checklist capture.php: Resend failed status=' . $resendStatus . ' err=' . $resendErr . ' body=' . substr((string) $resendBody, 0, 500));
  @file_put_contents(
    $inboxDir . '/errors.jsonl',
    json_encode(array(
      'at' => gmdate('c'),
      'submitId' => $submitId,
      'email' => $email,
      'error' => 'resend_failed',
      'status' => $resendStatus,
    ), JSON_UNESCAPED_SLASHES) . "\n",
    FILE_APPEND
  );
  ops_redirect('index.html?error=send');
}

$resendJson = json_decode((string) $resendBody, true);
$emailId = is_array($resendJson) && isset($resendJson['id']) ? $resendJson['id'] : null;
@file_put_contents(
  $inboxDir . '/sent.jsonl',
  json_encode(array(
    'sentAt' => gmdate('c'),
    'submitId' => $submitId,
    'email' => $email,
    'resendId' => $emailId,
  ), JSON_UNESCAPED_SLASHES) . "\n",
  FILE_APPEND
);

ops_redirect('thank-you.html');
