<?php
if (!isset($_GET['url'])) {
    http_response_code(400);
    echo "URL parameter is missing.";
    exit;
}

$url = $_GET['url'];

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
$response = curl_exec($ch);

if (curl_errno($ch)) {
    http_response_code(500);
    echo "cURL error: " . curl_error($ch);
    curl_close($ch);
    exit;
}

$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$content_type = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
curl_close($ch);

if ($http_code != 200) {
    http_response_code($http_code);
    echo "Failed to fetch the URL. HTTP status code: " . $http_code;
    exit;
}

header('Content-Type: ' . $content_type);
echo $response;
?>