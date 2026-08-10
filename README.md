# Automatización de Permisos — Sistema de Alertas de Vencimiento

Script en Python que corre en el Synology NAS de Recicley (`Recicley_Server`) y revisa periódicamente el
repositorio de permisos, licencias y documentos afines, para avisar por correo cuando algo está por vencer o
ya venció. También da seguimiento, por separado, a los acuses de recibo relacionados con esos trámites.

> Documentación técnica completa (arquitectura, configuración del NAS, capturas de pantalla):
> [`Documentacion_NAS_Alertas_Vencimiento.pdf`](./Documentacion_NAS_Alertas_Vencimiento.pdf)

## Contenido del repositorio

| Archivo | Qué es |
|---|---|
| `script.py` | El script. Escanea, clasifica y envía los correos. |
| `carpetas.txt` | Lista blanca de carpetas a monitorear — un dato, no código. Editar aquí para agregar o quitar rutas. |
| `Documentacion_NAS_Alertas_Vencimiento.pdf` | Documentación técnica extendida, con capturas de la configuración del NAS. |

## Qué hace

1. Lee `carpetas.txt` y arma la lista de rutas a revisar (73 rutas actualmente, agrupadas por trámite).
2. Recorre cada ruta —y sus subcarpetas— buscando archivos `.pdf` cuyo nombre termine **exactamente** en
   `_DD-MM-AAAA.pdf` (ver convención abajo).
3. Calcula cuántos días faltan para el vencimiento de cada uno.
4. Descarta los que están fuera del umbral (`DIAS_ALERTA`, hoy en 30 días) y clasifica el resto como
   *"N días restantes"* o, si ya se pasó la fecha, *"VENCIDO"* (permisos/licencias) o *"PENDIENTE"* (acuses).
5. Separa los resultados en dos grupos según el nombre del archivo:
   - **Vencimientos** — permisos y licencias normales.
   - **Acuses** — archivos cuyo nombre inicia con `ACUSE_`, que se reportan aparte.
6. Por cada grupo no vacío, agrupa los documentos por carpeta, ordena por fecha (más urgente primero) y arma
   un correo de texto plano, legible, con íconos de estado (ver más abajo).
7. Envía el correo de vencimientos al destinatario principal (con copias), y —si aplica— el de acuses de
   forma independiente, a sus propios destinatarios.

## Convención de nombres de archivo

Para que el script pueda leer la fecha, cada documento debe llamarse **exactamente** así:

```
NOMBRE_ARCHIVO_DD-MM-AAAA.pdf
```

Ejemplos:

```
LICENCIA_AMBIENTAL_30-11-2026.pdf
PERMISO_TRANSPORTE_RESIDUOS_15-08-2025.pdf
ACUSE_PERMISO_TRANSPORTE_15-08-2025.pdf   ← se reporta como acuse, no como vencimiento
```

El patrón es estricto por diseño (`PATRON = re.compile(r"_(\d{2}-\d{2}-\d{4})\.pdf$")`): la fecha debe venir
precedida de un guion bajo (`_`) e inmediatamente seguida de `.pdf`, sin nada más. Si el nombre no cumple ese
formato exacto, **el script lo ignora silenciosamente** (no aparece en ningún correo). Casos que se rechazan:

| Nombre | Por qué se rechaza |
|---|---|
| `PERMISO28-07-2026.pdf` | Falta el `_` antes de la fecha |
| `PERMISO_28-07-2026.pdf.pdf` | Doble extensión — no termina en `_DD-MM-AAAA.pdf` |
| `PERMISO_28-07-2026 copia.pdf` | Hay texto después de la fecha |

## Formato del correo

El cuerpo es texto plano (compatible con cualquier cliente, sin riesgo de filtros de spam por HTML), agrupado
por carpeta y con íconos de estado para que se lea de un vistazo: ⛔ para lo ya atrasado (`VENCIDO` /
`PENDIENTE`), ⚠️ para lo que todavía está dentro del umbral de aviso.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ALERTA DE VENCIMIENTO DE PERMISOS
  Generado: 10-08-2026 09:00      Total: 3 documentos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 /volume4/.../1.Recuperadora.../Coahuila
   ⛔ PERMISO_TRANSPORTE_15-08-2025.pdf
        VENCIDO            (vence 15-08-2025)
   ⚠️ LICENCIA_AMBIENTAL_30-11-2026.pdf
        12 dias restantes  (vence 30-11-2026)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Correo generado automáticamente por el sistema de alertas de Recicley.
```

## Configuración

### `carpetas.txt` — lista blanca de carpetas

Una ruta por línea, **relativa** a la raíz común (`_BASE_CALIDAD` en `script.py`, hoy
`/volume4/Contraloría/1.Calidad-Gestoría`). Las líneas vacías y las que empiezan con `#` se ignoran:

```
# 1. Permisos de Recolección y Traslado - Recicley MX
1.Permisos de Recolección y Traslado/2.Recicley MX S.A. de .C.V/Estado de México
1.Permisos de Recolección y Traslado/2.Recicley MX S.A. de .C.V/Queretaro
...
```

Para monitorear una carpeta nueva: **agrega una línea a `carpetas.txt`**. No hace falta tocar `script.py` ni
volver a desplegarlo — el script la lee cada vez que arranca.

### Variables de entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `GMAIL_APP_PASS` | Sí | Contraseña de aplicación de Google para la cuenta remitente (`ti@recicleymx.com`). Nunca se escribe en el código; el script aborta con error si falta. |

### Variables dentro de `script.py`

| Variable | Descripción |
|---|---|
| `DIAS_ALERTA` | Umbral de días para activar la alerta (30 por defecto). |
| `GMAIL_USER` | Cuenta remitente. |
| `DESTINATARIO_PRINCIPAL` / `CC` | A quién llega el correo de vencimientos. |
| `DESTINATARIO_ACUSES` / `CC_ACUSES` | A quién llega el correo de acuses. |
| `PREFIJO_ACUSE` | Prefijo que identifica un acuse (`ACUSE_`). |

## Ejecución

Requiere Python 3.9+ (corre en producción con 3.9.16) y solo librerías estándar — no hay dependencias que
instalar.

```bash
export GMAIL_APP_PASS="la-contraseña-de-aplicación"
python3 script.py
```

### En el NAS (Synology DSM)

El script corre vía el **Programador de tareas** de DSM, una vez al día, con un wrapper que inyecta la
credencial antes de invocar Python:

```bash
#!/bin/bash
export GMAIL_APP_PASS="xxxxxxxxxxxxxxxx"
python3 "/volume1/scripts/script.py"
```

> **Importante al desplegar:** `carpetas.txt` debe copiarse a la **misma carpeta** que `script.py` en el NAS
> (`/volume1/scripts/`). El script la busca de forma relativa a su propia ubicación; si falta, no arranca.

Detalle completo de la configuración del NAS (SMTP, panel de red, tarea programada, capturas de pantalla) en
[`Documentacion_NAS_Alertas_Vencimiento.pdf`](./Documentacion_NAS_Alertas_Vencimiento.pdf).

## Seguridad

- La contraseña de correo nunca está en el código: se inyecta como variable de entorno en el momento de la
  ejecución.
- Se usa una contraseña de aplicación de Google, específica para esta integración.
- La conexión SMTP siempre va bajo SSL/TLS (`smtp.gmail.com:465`).
- El script solo opera sobre la lista blanca de `carpetas.txt` — nunca recorre el NAS completo.

## Pendientes conocidos

- Confirmar la periodicidad definitiva de ejecución (diaria o semanal).
- Evaluar, a futuro, extraer la fecha de vencimiento del contenido del PDF como validación adicional.

---
Recicley MX · Departamento de TI
