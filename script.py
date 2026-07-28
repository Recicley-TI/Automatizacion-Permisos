# SOFTWARE DESARROLLADO POR LEONARDO AGUILAR MARTINEZ PARA RECICLEY (RECUPERADORA DE MATERIALES OCAMPO
# DE TOLUCA) PRIMERA VERSION EJECUTANDOSE EN SYNOLOGY NAS (DSM 7.1.1-42928) CON PYTHON 3.9.16

import os
import re
import smtplib
from datetime import date, datetime
from email.mime.text import MIMEText

# ============ CONFIGURACIÓN ============
CARPETAS = [
    "/volume3/Destrucciones/PRUEBAS CODIGO"
]

DIAS_ALERTA = 1  

GMAIL_USER = "ti@recicleymx.com"
DESTINATARIO_PRINCIPAL = "legal.permisos@recicleymx.com"
CC = [
    "leonardogrl18@gmail.com"
]

# CONTRASEÑA UTILIZADA EN BASH (CONTRASEÑA DE APLICACIÓN DE GMAIL) PARA ENVIAR CORREOS DESDE EL SCRIPT
GMAIL_APP_PASS = os.environ.get("GMAIL_APP_PASS")
# ========================================

# REGEX PARA EXTRAER LA FECHA DE VENCIMIENTO DEL NOMBRE DEL ARCHIVO PDF
PATRON = re.compile(r"(\d{2}-\d{2}-\d{4})\.pdf$", re.IGNORECASE)

def escanear():
    resultados = []
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
                if restantes <= DIAS_ALERTA: #LOGICA VENCIMIENTO
                    estado = "VENCIDO" if restantes < 0 else f"{restantes} dias restantes"
                    resultados.append((nombre, vence, estado, raiz))
    return resultados

def enviar_correo(documentos):
    if not GMAIL_APP_PASS:
        raise RuntimeError(
            "No se encontro GMAIL_APP_PASS en el entorno. "
            "Configura la variable en el Programador de tareas."
        )

    lineas = [
        f"- {n} | vence {v.strftime('%d-%m-%Y')} | {e} | carpeta: {c}"
        for n, v, e, c in documentos
    ]
    cuerpo = "Documentos que requieren atencion:\n\n" + "\n".join(lineas)

    msg = MIMEText(cuerpo, "plain", "utf-8")
    msg["Subject"] = f"Alerta: {len(documentos)} documento(s) por vencer o vencidos"
    msg["From"] = GMAIL_USER
    msg["To"] = DESTINATARIO_PRINCIPAL
    msg["Cc"] = ", ".join(CC)

    destinatarios_totales = [DESTINATARIO_PRINCIPAL] + CC

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(GMAIL_USER, GMAIL_APP_PASS)
        servidor.sendmail(GMAIL_USER, destinatarios_totales, msg.as_string())

    print("Correo enviado correctamente.")

if __name__ == "__main__":
    documentos = escanear()
    if documentos:
        enviar_correo(documentos)
    else:
        print("No hay documentos proximos a vencer.")