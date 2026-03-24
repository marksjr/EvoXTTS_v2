<?php
/**
 * ===================================================================
 *  Cliente PHP para API Evo XTTS V2
 *  URL: http://localhost:8881
 * ===================================================================
 *
 * COMO FUNCIONA A SELEÇÃO DE VOZ:
 *
 *   O Evo XTTS V2 clona vozes. Não tem vozes embutidas.
 *   Você coloca arquivos .wav na pasta voices/ e eles viram vozes.
 *
 *   Exemplo:
 *     voices/mulher.wav        → voice: "mulher"
 *     voices/homem.wav         → voice: "homem"
 *     voices/narrador.wav      → voice: "narrador"
 *     voices/apresentadora.wav → voice: "apresentadora"
 *     voices/minha_voz.wav     → voice: "minha_voz"
 *
 *   Requisitos do .wav de referência:
 *     - Duração: 6 a 30 segundos (ideal 10-15s)
 *     - Uma só pessoa falando
 *     - Sem música de fundo
 *     - Sem muito ruído
 *     - Formato: WAV (qualquer sample rate)
 *
 *   Se colocar voz de mulher → fala com voz de mulher
 *   Se colocar voz de homem  → fala com voz de homem
 *
 * ===================================================================
 *
 * ENDPOINTS DISPONÍVEIS:
 *
 *   GET  /health      → Status da API, engine, device, vozes carregadas
 *   GET  /voices      → Lista todas as vozes disponíveis
 *   POST /tts         → Gera áudio completo (MP3 ou WAV)
 *   POST /tts/stream  → Gera áudio em streaming (chunks MP3)
 *
 * ===================================================================
 *
 * PARÂMETROS DO POST /tts:
 *
 *   text   (string)  Obrigatório. Texto em português (1 a 10000 caracteres)
 *   voice  (string)  Opcional. ID da voz (nome do .wav). Vazio = primeira voz disponível
 *   speed  (float)   Opcional. Velocidade: 0.5 (lento) a 2.0 (rápido). Padrão: 1.0
 *   format (string)  Opcional. "mp3" (padrão) ou "wav"
 *
 * ===================================================================
 */

class XTTSTTS
{
    private string $baseUrl;
    private int $timeout;

    /**
     * @param string $baseUrl  URL da API (padrão: http://localhost:8881)
     * @param int    $timeout  Timeout em segundos (padrão: 120)
     */
    public function __construct(string $baseUrl = 'http://localhost:8881', int $timeout = 120)
    {
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->timeout = $timeout;
    }

    // -----------------------------------------------------------------
    //  GET /health - Status da API
    // -----------------------------------------------------------------
    //  Retorna:
    //    status        → "ok" ou "loading"
    //    engine        → "Evo XTTS V2"
    //    device        → "cuda" ou "cpu"
    //    model_loaded  → true/false
    //    voices_loaded → número de vozes carregadas
    // -----------------------------------------------------------------
    public function health(): array
    {
        return json_decode($this->request('GET', '/health'), true);
    }

    // -----------------------------------------------------------------
    //  GET /voices - Lista vozes disponíveis
    // -----------------------------------------------------------------
    //  Retorna array de:
    //    id          → nome do arquivo .wav (sem extensão)
    //    name        → nome formatado
    //    gender      → "clonada"
    //    lang        → "pt-br"
    //    description → descrição da voz
    // -----------------------------------------------------------------
    public function voices(): array
    {
        return json_decode($this->request('GET', '/voices'), true);
    }

    // -----------------------------------------------------------------
    //  POST /tts - Gerar áudio
    // -----------------------------------------------------------------
    //  Parâmetros:
    //    text   → texto em português (obrigatório)
    //    voice  → ID da voz (opcional, usa primeira disponível)
    //    speed  → 0.5 a 2.0 (opcional, padrão 1.0)
    //    format → "mp3" ou "wav" (opcional, padrão "mp3")
    //
    //  Retorna: bytes do áudio
    // -----------------------------------------------------------------
    public function synthesize(
        string $text,
        string $voice = '',
        float $speed = 1.0,
        string $format = 'mp3',
        string $emotion = ''
    ): string {
        $payload = [
            'text'   => $text,
            'voice'  => $voice,
            'speed'  => $speed,
            'format' => $format,
        ];
        if ($emotion !== '') {
            $payload['emotion'] = $emotion;
        }
        return $this->request('POST', '/tts', json_encode($payload));
    }

    // -----------------------------------------------------------------
    //  Gerar áudio e salvar em arquivo
    // -----------------------------------------------------------------
    public function toFile(
        string $text,
        string $outputPath,
        string $voice = '',
        float $speed = 1.0,
        string $format = 'mp3',
        string $emotion = ''
    ): bool {
        $audio = $this->synthesize($text, $voice, $speed, $format, $emotion);
        return file_put_contents($outputPath, $audio) !== false;
    }

    // -----------------------------------------------------------------
    //  GET /emotions - Lista emoções disponíveis
    // -----------------------------------------------------------------
    public function emotions(): array
    {
        return json_decode($this->request('GET', '/emotions'), true);
    }

    // -----------------------------------------------------------------
    //  POST /tts/stream - Streaming (download progressivo)
    // -----------------------------------------------------------------
    //  Mesmo parâmetros do /tts mas sem "format" (sempre MP3)
    //  Retorna chunks de áudio progressivamente
    // -----------------------------------------------------------------
    public function streamToFile(
        string $text,
        string $outputPath,
        string $voice = '',
        float $speed = 1.0
    ): bool {
        $payload = json_encode([
            'text'  => $text,
            'voice' => $voice,
            'speed' => $speed,
        ]);

        $fp = fopen($outputPath, 'wb');
        if (!$fp) return false;

        $ch = curl_init($this->baseUrl . '/tts/stream');
        curl_setopt_array($ch, [
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => $payload,
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
            CURLOPT_TIMEOUT        => $this->timeout,
            CURLOPT_WRITEFUNCTION  => function ($ch, $data) use ($fp) {
                return fwrite($fp, $data);
            },
        ]);
        curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        fclose($fp);

        return $httpCode === 200;
    }

    private function request(string $method, string $endpoint, ?string $body = null): string
    {
        $ch = curl_init($this->baseUrl . $endpoint);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => $this->timeout,
            CURLOPT_CONNECTTIMEOUT => 5,
        ]);

        if ($method === 'POST') {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
            curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        }

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);

        if ($response === false) {
            throw new RuntimeException("Erro de conexao: $error");
        }
        if ($httpCode >= 400) {
            throw new RuntimeException("Erro HTTP $httpCode: $response");
        }

        return $response;
    }
}


// ===================================================================
//  EXEMPLOS DE USO
// ===================================================================

$tts = new XTTSTTS();


// === 1. STATUS DA API ===
echo "=== STATUS DA API ===\n";
$health = $tts->health();
echo "  Engine:          {$health['engine']}\n";
echo "  Device:          {$health['device']}\n";
echo "  Status:          {$health['status']}\n";
echo "  Modelo carregado: " . ($health['model_loaded'] ? 'Sim' : 'Nao') . "\n";
echo "  Vozes carregadas: {$health['voices_loaded']}\n\n";


// === 2. LISTAR TODAS AS VOZES ===
echo "=== VOZES DISPONÍVEIS ===\n";
echo "  (Cada arquivo .wav na pasta voices/ vira uma voz)\n\n";
$voices = $tts->voices();
foreach ($voices as $v) {
    echo "  ID: {$v['id']}\n";
    echo "    Nome:      {$v['name']}\n";
    echo "    Tipo:      {$v['gender']}\n";
    echo "    Idioma:    {$v['lang']}\n";
    echo "    Descricao: {$v['description']}\n\n";
}


// === 3. VOZ HOMEM ===
echo "=== VOZ HOMEM ===\n";
$tts->toFile(
    "Olá! Eu sou a voz masculina. Esta é uma demonstração da síntese de voz "
    . "em português do Brasil usando o modelo XTTS versão dois com clonagem de voz.",
    __DIR__ . '/exemplo_homem.mp3',
    'homem'
);
echo "  Salvo em exemplo_homem.mp3\n\n";


// === 4. VOZ MULHER ===
echo "=== VOZ MULHER ===\n";
$tts->toFile(
    "Olá! Eu sou a voz feminina. Esta é uma demonstração da síntese de voz "
    . "em português do Brasil usando o modelo XTTS versão dois com clonagem de voz.",
    __DIR__ . '/exemplo_mulher.mp3',
    'mulher'
);
echo "  Salvo em exemplo_mulher.mp3\n\n";


// === 5. COMPARAÇÃO: MESMO TEXTO COM AS DUAS VOZES ===
$texto_comparacao = "O Brasil é o maior país da América do Sul. "
                  . "Com uma população de mais de duzentos milhões de habitantes, "
                  . "é também o quinto maior país do mundo em extensão territorial. "
                  . "Sua capital é Brasília, fundada em mil novecentos e sessenta.";

echo "=== COMPARAÇÃO (mesmo texto, vozes diferentes) ===\n";
$tts->toFile($texto_comparacao, __DIR__ . '/comparacao_homem.mp3', 'homem');
echo "  Homem → comparacao_homem.mp3\n";
$tts->toFile($texto_comparacao, __DIR__ . '/comparacao_mulher.mp3', 'mulher');
echo "  Mulher → comparacao_mulher.mp3\n\n";


// === 6. VELOCIDADES (voz homem) ===
echo "=== VELOCIDADES (voz: homem) ===\n";
$texto_vel = "Testando diferentes velocidades de fala com a voz masculina.";
$velocidades = [
    ['speed' => 0.7, 'label' => 'lenta',       'file' => 'homem_vel_070'],
    ['speed' => 1.0, 'label' => 'normal',       'file' => 'homem_vel_100'],
    ['speed' => 1.3, 'label' => 'rapida',       'file' => 'homem_vel_130'],
];
foreach ($velocidades as $v) {
    $tts->toFile($texto_vel, __DIR__ . "/{$v['file']}.mp3", 'homem', $v['speed']);
    echo "  speed={$v['speed']}  ({$v['label']})  -> {$v['file']}.mp3\n";
}
echo "\n";


// === 7. VELOCIDADES (voz mulher) ===
echo "=== VELOCIDADES (voz: mulher) ===\n";
$texto_vel = "Testando diferentes velocidades de fala com a voz feminina.";
$velocidades = [
    ['speed' => 0.7, 'label' => 'lenta',       'file' => 'mulher_vel_070'],
    ['speed' => 1.0, 'label' => 'normal',       'file' => 'mulher_vel_100'],
    ['speed' => 1.3, 'label' => 'rapida',       'file' => 'mulher_vel_130'],
];
foreach ($velocidades as $v) {
    $tts->toFile($texto_vel, __DIR__ . "/{$v['file']}.mp3", 'mulher', $v['speed']);
    echo "  speed={$v['speed']}  ({$v['label']})  -> {$v['file']}.mp3\n";
}
echo "\n";


// === 8. FORMATOS DE SAÍDA ===
echo "=== FORMATOS ===\n";
$tts->toFile("Teste em MP3 com voz masculina.", __DIR__ . '/formato_homem.mp3', 'homem', 1.0, 'mp3');
echo "  MP3 homem -> formato_homem.mp3\n";
$tts->toFile("Teste em WAV com voz feminina.", __DIR__ . '/formato_mulher.wav', 'mulher', 1.0, 'wav');
echo "  WAV mulher -> formato_mulher.wav\n\n";


// === 9. EMOÇÕES ===
echo "=== EMOÇÕES DISPONÍVEIS ===\n";
$emotions = $tts->emotions();
foreach ($emotions as $e) {
    echo "  {$e['id']}: {$e['description']}\n";
}
echo "\n";

$texto_emocao = "Esta é uma demonstração de como a emoção altera o tom da voz gerada.";
$emocoes = ['neutro', 'animado', 'calmo', 'serio', 'triste', 'raiva'];

echo "=== GERANDO TODAS AS EMOÇÕES (voz: homem) ===\n";
foreach ($emocoes as $em) {
    $tts->toFile($texto_emocao, __DIR__ . "/emocao_{$em}.mp3", 'homem', 1.0, 'mp3', $em);
    echo "  [{$em}] -> emocao_{$em}.mp3\n";
}
echo "\n";


// === 10. STREAMING ===
echo "=== STREAMING ===\n";
$tts->streamToFile(
    "Este audio foi gerado usando streaming progressivo com a voz masculina.",
    __DIR__ . '/stream_homem.mp3',
    'homem'
);
echo "  Homem streaming -> stream_homem.mp3\n";
$tts->streamToFile(
    "Este audio foi gerado usando streaming progressivo com a voz feminina.",
    __DIR__ . '/stream_mulher.mp3',
    'mulher'
);
echo "  Mulher streaming -> stream_mulher.mp3\n\n";


// === 11. EXEMPLOS CURL ===
echo "=== COMANDOS CURL ===\n\n";

echo "  # Status da API:\n";
echo "  curl http://localhost:8881/health\n\n";

echo "  # Listar vozes:\n";
echo "  curl http://localhost:8881/voices\n\n";

echo "  # Gerar com voz HOMEM:\n";
echo "  curl -X POST http://localhost:8881/tts \\\n";
echo "    -H \"Content-Type: application/json\" \\\n";
echo "    -d '{\"text\":\"Ola mundo!\",\"voice\":\"homem\"}' \\\n";
echo "    --output homem.mp3\n\n";

echo "  # Gerar com voz MULHER:\n";
echo "  curl -X POST http://localhost:8881/tts \\\n";
echo "    -H \"Content-Type: application/json\" \\\n";
echo "    -d '{\"text\":\"Ola mundo!\",\"voice\":\"mulher\"}' \\\n";
echo "    --output mulher.mp3\n\n";

echo "  # Gerar com velocidade rapida:\n";
echo "  curl -X POST http://localhost:8881/tts \\\n";
echo "    -H \"Content-Type: application/json\" \\\n";
echo "    -d '{\"text\":\"Ola mundo!\",\"voice\":\"homem\",\"speed\":1.3}' \\\n";
echo "    --output rapido.mp3\n\n";

echo "  # Gerar WAV:\n";
echo "  curl -X POST http://localhost:8881/tts \\\n";
echo "    -H \"Content-Type: application/json\" \\\n";
echo "    -d '{\"text\":\"Ola mundo!\",\"voice\":\"mulher\",\"format\":\"wav\"}' \\\n";
echo "    --output mulher.wav\n\n";

echo "  # Gerar com EMOCAO:\n";
echo "  curl -X POST http://localhost:8881/tts \\\n";
echo "    -H \"Content-Type: application/json\" \\\n";
echo "    -d '{\"text\":\"Que noticia incrivel!\",\"voice\":\"homem\",\"emotion\":\"animado\"}' \\\n";
echo "    --output animado.mp3\n\n";

echo "  # Listar emocoes disponiveis:\n";
echo "  curl http://localhost:8881/emotions\n\n";

echo "  # Streaming:\n";
echo "  curl -X POST http://localhost:8881/tts/stream \\\n";
echo "    -H \"Content-Type: application/json\" \\\n";
echo "    -d '{\"text\":\"Texto longo aqui...\",\"voice\":\"homem\",\"emotion\":\"calmo\"}' \\\n";
echo "    --output stream.mp3\n\n";

echo "Pronto!\n";
