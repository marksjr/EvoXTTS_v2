<?php

declare(strict_types=1);

/**
 * Evo XTTS V2 PHP API example.
 *
 * Usage:
 *   php examples/api.php
 *
 * Requirements:
 * - PHP with cURL enabled
 * - Local API running at http://localhost:8881
 * - At least one .wav file inside the voices/ folder
 */
final class EvoXTTSApi
{
    public function __construct(
        private string $baseUrl = 'http://localhost:8881',
        private int $timeout = 300,
    ) {
        $this->baseUrl = rtrim($this->baseUrl, '/');
    }

    public function health(): array
    {
        return $this->requestJson('GET', '/health');
    }

    public function voices(): array
    {
        return $this->requestJson('GET', '/voices');
    }

    public function languages(): array
    {
        return $this->requestJson('GET', '/languages');
    }

    public function emotions(): array
    {
        return $this->requestJson('GET', '/emotions');
    }

    public function tts(
        string $text,
        string $voice = '',
        string $language = 'pt',
        float $speed = 1.0,
        string $format = 'wav',
        ?string $emotion = null,
    ): string {
        $payload = [
            'text' => $text,
            'voice' => $voice,
            'language' => $language,
            'speed' => $speed,
            'format' => $format,
        ];

        if ($emotion !== null && $emotion !== '') {
            $payload['emotion'] = $emotion;
        }

        return $this->requestBinary('POST', '/tts', $payload);
    }

    public function ttsToFile(
        string $outputPath,
        string $text,
        string $voice = '',
        string $language = 'pt',
        float $speed = 1.0,
        string $format = 'wav',
        ?string $emotion = null,
    ): void {
        $audio = $this->tts($text, $voice, $language, $speed, $format, $emotion);
        file_put_contents($outputPath, $audio);
    }

    public function streamToFile(
        string $outputPath,
        string $text,
        string $voice = '',
        string $language = 'pt',
        float $speed = 1.0,
        ?string $emotion = null,
    ): void {
        $payload = [
            'text' => $text,
            'voice' => $voice,
            'language' => $language,
            'speed' => $speed,
        ];

        if ($emotion !== null && $emotion !== '') {
            $payload['emotion'] = $emotion;
        }

        $fp = fopen($outputPath, 'wb');
        if ($fp === false) {
            throw new RuntimeException("Could not open output file: {$outputPath}");
        }

        $ch = curl_init($this->baseUrl . '/tts/stream');
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_TIMEOUT => $this->timeout,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
            CURLOPT_WRITEFUNCTION => static function ($ch, string $chunk) use ($fp): int {
                fwrite($fp, $chunk);
                return strlen($chunk);
            },
        ]);

        curl_exec($ch);
        $httpCode = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        fclose($fp);

        if ($error !== '') {
            @unlink($outputPath);
            throw new RuntimeException("Connection error: {$error}");
        }

        if ($httpCode >= 400) {
            @unlink($outputPath);
            throw new RuntimeException("HTTP error {$httpCode} while calling /tts/stream");
        }
    }

    private function requestJson(string $method, string $endpoint, ?array $payload = null): array
    {
        $response = $this->request($method, $endpoint, $payload);
        $decoded = json_decode($response, true);

        if (!is_array($decoded)) {
            throw new RuntimeException("Invalid JSON response from {$endpoint}");
        }

        return $decoded;
    }

    private function requestBinary(string $method, string $endpoint, ?array $payload = null): string
    {
        return $this->request($method, $endpoint, $payload);
    }

    private function request(string $method, string $endpoint, ?array $payload = null): string
    {
        $ch = curl_init($this->baseUrl . $endpoint);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => $this->timeout,
            CURLOPT_CONNECTTIMEOUT => 10,
        ]);

        if ($method === 'POST') {
            curl_setopt_array($ch, [
                CURLOPT_POST => true,
                CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
                CURLOPT_POSTFIELDS => json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
            ]);
        }

        $response = curl_exec($ch);
        $httpCode = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);

        if ($response === false) {
            throw new RuntimeException("Connection error: {$error}");
        }

        if ($httpCode >= 400) {
            throw new RuntimeException("HTTP error {$httpCode}: {$response}");
        }

        return $response;
    }
}

function printSection(string $title): void
{
    echo PHP_EOL . "=== {$title} ===" . PHP_EOL;
}

try {
    $api = new EvoXTTSApi();

    printSection('HEALTH');
    print_r($api->health());

    printSection('LANGUAGES');
    print_r($api->languages());

    printSection('EMOTIONS');
    print_r($api->emotions());

    printSection('VOICES');
    $voices = $api->voices();
    print_r($voices);

    $voiceId = $voices[0]['id'] ?? '';
    if ($voiceId === '') {
        throw new RuntimeException('No voices available. Add a .wav file to voices/ before running this example.');
    }

    printSection('GENERATE WAV');
    $api->ttsToFile(
        __DIR__ . '/example_pt.wav',
        'Ola. Este arquivo foi gerado pela API PHP do Evo XTTS V2.',
        $voiceId,
        'pt',
        1.0,
        'wav'
    );
    echo "Saved: examples/example_pt.wav" . PHP_EOL;

    printSection('GENERATE MP3');
    $api->ttsToFile(
        __DIR__ . '/example_en.mp3',
        'Hello. This MP3 file was generated through the Evo XTTS V2 PHP API example.',
        $voiceId,
        'en',
        1.0,
        'mp3'
    );
    echo "Saved: examples/example_en.mp3" . PHP_EOL;

    printSection('GENERATE STREAMING MP3');
    $api->streamToFile(
        __DIR__ . '/stream_en.mp3',
        'This file was generated using the streaming endpoint.',
        $voiceId,
        'en',
        1.0
    );
    echo "Saved: examples/stream_en.mp3" . PHP_EOL;

    printSection('HOW TO USE');
    echo "1. Start the local API at http://localhost:8881" . PHP_EOL;
    echo "2. Place one or more .wav voice files in voices/" . PHP_EOL;
    echo "3. Run: php examples/api.php" . PHP_EOL;
    echo "4. Check the generated files inside examples/" . PHP_EOL;
} catch (Throwable $e) {
    fwrite(STDERR, 'Error: ' . $e->getMessage() . PHP_EOL);
    exit(1);
}