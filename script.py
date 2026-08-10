# SOFTWARE DESARROLLADO POR LEONARDO AGUILAR MARTINEZ PARA RECICLEY (RECUPERADORA DE MATERIALES OCAMPO
# DE TOLUCA) PRIMERA VERSION EJECUTANDOSE EN SYNOLOGY NAS (DSM 7.1.1-42928) CON PYTHON 3.9.16

import os
import re
import smtplib
from datetime import date, datetime
from email.mime.text import MIMEText
from collections import defaultdict

# ============ CONFIGURACIÓN ============

# Raíz común de "Calidad-Gestoría" - todo vive en volume4
_BASE_CALIDAD = "/volume4/Contraloría/1.Calidad-Gestoría"

# Archivo de texto con la lista blanca de carpetas a monitorear (una ruta
# relativa a _BASE_CALIDAD por linea, ver carpetas.txt junto a este script).
# Para agregar o quitar una carpeta monitoreada basta con editar ese archivo:
# no requiere tocar ni volver a desplegar script.py.
_ARCHIVO_CARPETAS = "carpetas.txt"


def _cargar_carpetas(nombre_archivo=_ARCHIVO_CARPETAS):
    """Lee la lista blanca de carpetas desde un archivo de texto plano junto
    a este script: una ruta relativa a _BASE_CALIDAD por linea. Ignora
    lineas vacias y comentarios (que inician con #)."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre_archivo)
    with open(ruta, encoding="utf-8") as f:
        return [
            f"{_BASE_CALIDAD}/{linea.strip()}"
            for linea in f
            if linea.strip() and not linea.strip().startswith("#")
        ]


# LISTA BLANCA: unicamente estas carpetas son monitoreadas (ver carpetas.txt)
CARPETAS = _cargar_carpetas()

DIAS_ALERTA = 30  

GMAIL_USER = "ti@recicleymx.com"
DESTINATARIO_PRINCIPAL = "legal.permisos@recicleymx.com"
CC = [
    "leonardogrl18@gmail.com"
]

# Destinatarios del correo de acuses (por defecto, los mismos que el principal)
DESTINATARIO_ACUSES = "legal.permisos@recicleymx.com"
CC_ACUSES = [
    "leonardogrl18@gmail.com"
]

# CONTRASEÑA UTILIZADA EN BASH (CONTRASEÑA DE APLICACIÓN DE GMAIL) PARA ENVIAR CORREOS DESDE EL SCRIPT
GMAIL_APP_PASS = os.environ.get("GMAIL_APP_PASS")

# PREFIJO QUE INDICA QUE EL DOCUMENTO ES UN ACUSE (SE REPORTA POR SEPARADO, NO EN LA ALERTA PRINCIPAL)
PREFIJO_ACUSE = "ACUSE_"
# ========================================

# REGEX PARA EXTRAER LA FECHA DE VENCIMIENTO DEL NOMBRE DEL ARCHIVO PDF
PATRON = re.compile(r"(\d{2}-\d{2}-\d{4})\.pdf$", re.IGNORECASE)


def escanear():
    """Recorre las carpetas y separa los documentos en dos listas:
    vencimientos (permisos normales) y acuses (nombre inicia con ACUSE_)."""
    vencimientos = []
    acuses = []

    for carpeta in CARPETAS:
        if not os.path.isdir(carpeta):
            print(f"Aviso: la carpeta no existe -> {carpeta}")
            continue
        for raiz, _, archivos in os.walk(carpeta):
            for nombre in archivos:
                m = PATRON.search(nombre)
                if not m:
                    continue
                try:
                    vence = datetime.strptime(m.group(1), "%d-%m-%Y").date()
                except ValueError:
                    continue

                restantes = (vence - date.today()).days
                if restantes > DIAS_ALERTA:
                    continue  # fuera del umbral, no interesa a ninguna de las dos listas

                estado = "VENCIDO" if restantes < 0 else f"{restantes} dias restantes"
                registro = (nombre, vence, estado, raiz)

                if nombre.upper().startswith(PREFIJO_ACUSE):
                    acuses.append(registro)
                else:
                    vencimientos.append(registro)

    return vencimientos, acuses


def _agrupar_por_carpeta(documentos):
    """Agrupa una lista de documentos por su carpeta contenedora,
    ordenando cada grupo por fecha de vencimiento (mas urgente primero)."""
    grupos = defaultdict(list)
    for nombre, vence, estado, carpeta in documentos:
        grupos[carpeta].append((nombre, vence, estado))
    for carpeta in grupos:
        grupos[carpeta].sort(key=lambda x: x[1])
    return dict(sorted(grupos.items()))


def _construir_cuerpo(documentos, encabezado):
    """Genera un cuerpo de correo en texto plano, legible y agrupado por carpeta."""
    total = len(documentos)
    grupos = _agrupar_por_carpeta(documentos)

    ANCHO = 70
    lineas = []
    lineas.append(encabezado)
    lineas.append(f"Generado: {datetime.now().strftime('%d-%m-%Y %H:%M')}")
    lineas.append("=" * ANCHO)
    lineas.append(f"Total de documentos: {total}")
    lineas.append("")

    for carpeta, items in grupos.items():
        lineas.append("-" * ANCHO)
        lineas.append(f"CARPETA: {carpeta}")
        lineas.append("-" * ANCHO)
        for nombre, vence, estado in items:
            lineas.append(f"  • {nombre}")
            lineas.append(f"      Vence: {vence.strftime('%d-%m-%Y')}   |   Estado: {estado}")
        lineas.append("")

    lineas.append("=" * ANCHO)
    lineas.append("Correo generado automaticamente por el sistema de alertas de Recicley.")
    return "\n".join(lineas)


def _enviar(destinatario_principal, cc, asunto, cuerpo):
    msg = MIMEText(cuerpo, "plain", "utf-8")
    msg["Subject"] = asunto
    msg["From"] = GMAIL_USER
    msg["To"] = destinatario_principal
    msg["Cc"] = ", ".join(cc)

    destinatarios_totales = [destinatario_principal] + cc

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(GMAIL_USER, GMAIL_APP_PASS)
        servidor.sendmail(GMAIL_USER, destinatarios_totales, msg.as_string())


def enviar_correo_vencimientos(documentos):
    asunto = f"Alerta: {len(documentos)} permiso(s) por vencer o vencidos"
    cuerpo = _construir_cuerpo(documentos, "ALERTA DE VENCIMIENTO DE PERMISOS")
    _enviar(DESTINATARIO_PRINCIPAL, CC, asunto, cuerpo)
    print("Correo de vencimientos enviado correctamente.")


def enviar_correo_acuses(documentos):
    asunto = f"Acuses en seguimiento: {len(documentos)} documento(s)"
    cuerpo = _construir_cuerpo(documentos, "LISTADO DE ACUSES EN SEGUIMIENTO")
    _enviar(DESTINATARIO_ACUSES, CC_ACUSES, asunto, cuerpo)
    print("Correo de acuses enviado correctamente.")


if __name__ == "__main__":
    if not GMAIL_APP_PASS:
        raise RuntimeError(
            "No se encontro GMAIL_APP_PASS en el entorno. "
            "Configura la variable en el Programador de tareas."
        )

    vencimientos, acuses = escanear()

    if vencimientos:
        enviar_correo_vencimientos(vencimientos)
    else:
        print("No hay permisos proximos a vencer.")

    if acuses:
        enviar_correo_acuses(acuses)
    else:
        print("No hay acuses proximos a vencer.")