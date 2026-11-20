# Política de seguridad

## Versiones soportadas

Solo la rama `main` recibe correcciones de seguridad. No hay versiones publicadas con números de versión mantenidas por separado.

| Versión | Soportada |
|---|---|
| `main` | Sí |
| Cualquier otra | No |

## Cómo reportar una vulnerabilidad

**No abras un issue público** para reportar una vulnerabilidad: quedaría visible para todo el mundo antes de que exista una corrección.

Repórtala en privado usando la **notificación privada de vulnerabilidades** de GitHub:

1. Ve a la pestaña **Security** del repositorio.
2. Pulsa **Report a vulnerability**.
3. Describe el problema, los pasos para reproducirlo y el impacto que tiene.

También puedes ir directamente a `https://github.com/ZappaGit/transcriptionsTool/security/advisories/new`.

Qué incluir:

- La versión o commit afectado y el sistema operativo.
- Los pasos mínimos para reproducir el problema.
- El impacto (por ejemplo, ejecución de código, robo de cookies, escritura fuera de la carpeta de salida).
- Si ya sabes cómo corregirlo, una propuesta es bienvenida, pero no es obligatoria.

No incluyas en el reporte cookies, tokens ni cabeceras de sesión reales. Si son necesarios para reproducirlo, sustitúyelos por valores de ejemplo.

## Plazos de respuesta

Este es un proyecto mantenido por una sola persona. No hay plazos de respuesta garantizados. Se intentará revisar cada reporte, y se avisará en el propio aviso de seguridad cuando haya novedades.

## Alcance

Están dentro del alcance los fallos en el código de este repositorio (`transcribir.py`, `transcribir.cmd`, la configuración de dependencias y los workflows de `.github/`).

Quedan fuera:

- Vulnerabilidades en dependencias (yt-dlp, faster-whisper, ffmpeg...). Repórtalas a su proyecto. Si afectan a este repositorio, Dependabot abrirá una actualización.
- Problemas de la web de origen, de un proveedor de vídeo o de las cuentas de usuario.

## Divulgación

Se pide esperar a que exista una corrección antes de publicar detalles. Cuando se publique, se reconocerá a quien lo reportó si así lo desea.
