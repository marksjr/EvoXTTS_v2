# Instalacao no Windows

## Opcao 1: usuario comum

Use a versao portable da Release do GitHub.

1. Baixe o `.zip`
2. Extraia a pasta
3. Coloque um arquivo `.wav` dentro de `voices`
4. Clique em `Abrir XTTS.bat`
5. Aguarde a abertura do navegador

## Opcao 2: codigo-fonte

1. Instale Python 3.11
2. Abra a pasta do projeto
3. Clique em `Instalar XTTS.bat`
4. Quando terminar, clique em `Abrir XTTS.bat`

## O que esperar na primeira inicializacao

Na primeira inicializacao o projeto pode levar algum tempo para:

- carregar o modelo XTTS
- preparar CUDA ou CPU
- carregar as vozes da pasta `voices`

O navegador so deve abrir quando a API estiver pronta.

## MP3 opcional

Se quiser exportar MP3, instale `ffmpeg`:

```powershell
winget install ffmpeg
```
