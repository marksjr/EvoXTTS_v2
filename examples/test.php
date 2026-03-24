<?php
$t = "Poeta português que viveu entre 1888 e 1935. Não se deixe enganar: para cada um nessa festa ele está se apresentando com um nome diferente. Já se apresentou como Álvaro de Campos, Ricardo Reis, Alberto Caeiro e Bernardo Soares. Não são só nomes inventados. Esses são os principais heterônimos do autor. Possuem toda uma biografia própria e vasta obra em seus nomes. Cada um com sua personalidade literária própria, o que permitiu Pessoa de vagar por vários estilos literários";


$ch = curl_init('http://localhost:8881/tts');
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_TIMEOUT => 300,
    CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
    CURLOPT_POSTFIELDS => json_encode([
        'text' => $t,
        //'voice' => 'homem',
		'voice' => 'mulher',
        'format' => 'wav',
        //'emotion' => 'raiva',
    ]),
]);

$audio = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);
curl_close($ch);

if ($audio === false) {
    echo "Erro de conexao: $error\n";
}
elseif ($httpCode >= 400) {
    echo "Erro HTTP $httpCode: $audio\n";
}
else {
    file_put_contents(__DIR__ . '/normal.wav', $audio);
    echo "Salvo em normal.wav (" . strlen($audio) . " bytes)\n";
}
