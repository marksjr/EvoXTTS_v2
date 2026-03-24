# Checklist antes de subir para GitHub

## Repositorio

- [ ] `venv/` fora do repositorio
- [ ] `.tts/` fora do repositorio
- [ ] `dist/` fora do repositorio
- [ ] nenhum `.wav` privado em `voices/`
- [ ] README atualizado com instrucoes simples
- [ ] docs de instalacao e troubleshooting presentes

## Teste do codigo-fonte

- [ ] `Instalar XTTS.bat` funciona
- [ ] `Abrir XTTS.bat` funciona
- [ ] interface abre no navegador
- [ ] `/health` retorna `ok`
- [ ] gera audio WAV

## Teste da release portable

- [ ] `system/build-portable.bat` gera a pasta final
- [ ] a pasta portable abre em outra maquina ou ambiente limpo
- [ ] o modelo ja esta incluido na release
- [ ] a pessoa consegue usar sem instalar Python manualmente
