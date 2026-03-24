# Texto pronto para a primeira Release

## Titulo sugerido

Evo XTTS V2 - Windows Portable v1.0.0

## Descricao da Release

Primeira release portable do Evo XTTS V2 para Windows.

Esta versao foi preparada para usuario comum: basta extrair a pasta, colocar um arquivo `.wav` dentro de `voices` e clicar em `Abrir XTTS.bat`.

## O que esta incluido

- interface web local
- API FastAPI
- runtime Python dentro da release
- cache local do modelo ja incluido
- suporte a GPU NVIDIA quando disponivel
- fallback para CPU quando necessario

## Como usar

1. Baixe o arquivo `.zip`
2. Extraia a pasta
3. Coloque um `.wav` dentro de `voices`
4. Clique em `Abrir XTTS.bat`
5. Aguarde o navegador abrir

## Observacoes

- O formato recomendado e WAV
- MP3 e opcional e pode exigir `ffmpeg`
- A primeira carga ainda pode levar algum tempo enquanto o modelo e as vozes sao preparados

## Requisitos

- Windows 10 ou 11
- GPU NVIDIA recomendada, mas nao obrigatoria
