# Troubleshooting

## O navegador abre mas a interface nao responde

Force recarregamento com `Ctrl+F5`.

## Nenhuma voz aparece

Verifique se existe ao menos um arquivo `.wav` dentro da pasta `voices`.

## A API nao sobe

Execute `Instalar XTTS.bat` novamente e depois tente `Abrir XTTS.bat`.

## Erro com GPU

Confirme se `nvidia-smi` funciona no Windows.
Se a GPU nao estiver disponivel, o projeto pode cair para CPU.

## MP3 nao funciona

Instale `ffmpeg`.

```powershell
winget install ffmpeg
```

## Primeira inicializacao demora muito

Isso e esperado quando o modelo ainda esta sendo preparado ou quando as vozes estao sendo cacheadas.
