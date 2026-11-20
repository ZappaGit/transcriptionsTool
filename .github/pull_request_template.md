## Qué cambia

<!-- Resumen breve y motivo del cambio. -->

## Cómo se ha probado

<!-- Comandos ejecutados y resultado. Si es un cambio de transcripción, indica el modelo y el vídeo usados. -->

- [ ] Smoke test: `uv run python transcribir.py "https://www.youtube.com/watch?v=jNQXAC9IVRw" --salida $env:TEMP\humo` produce la misma salida que `transcripciones/Me at the zoo - jNQXAC9IVRw.txt` (o se explica la diferencia)
- [ ] `uv run python transcribir.py --help` funciona
- [ ] El código, los comentarios y los mensajes de usuario siguen en español

## Seguridad y privacidad

- [ ] No añade secretos, cookies, tokens, rutas personales ni correos
- [ ] No añade archivos generados (audio, vídeo, transcripciones, modelos)
- [ ] Si añade una dependencia, explica por qué y su licencia en la descripción

## Notas para quien revisa

<!-- Puntos delicados, decisiones tomadas o pruebas que no se han podido hacer. -->
