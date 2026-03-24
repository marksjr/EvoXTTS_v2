# Publicacao no GitHub

## Objetivo certo

Para usuario simples, publique uma Release portable.
Nao use o codigo-fonte puro como forma principal de distribuicao.

## Passo a passo recomendado

1. Execute `Instalar XTTS.bat`
2. Execute `Abrir XTTS.bat` e espere o modelo carregar por completo
3. Confirme que a interface abre e gera audio
4. Feche a aplicacao
5. Execute `system/build-portable.bat`
6. Pegue a pasta `dist/Evo-XTTS-V2-Windows-Portable`
7. Compacte em `.zip`
8. Publique esse `.zip` em GitHub Releases

## O que a release portable deve conter

- runtime Python
- codigo da aplicacao
- interface web
- cache local do modelo em `.tts`
- pasta `voices` vazia ou com apenas um placeholder
- scripts `Abrir XTTS.bat` e `Instalar XTTS.bat` quando fizer sentido

## O que nao deve ir para o repositorio

- `venv/`
- `.tts/`
- `dist/`
- vozes privadas em `voices/*.wav`
- audios gerados de teste
- arquivos temporarios

## Recomendacao de descricao da Release

Inclua:

- requisitos minimos
- passo a passo curto de uso
- aviso de que a primeira carga pode demorar
- observacao de que WAV e o formato recomendado
