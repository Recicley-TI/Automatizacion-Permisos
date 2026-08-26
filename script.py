# SOFTWARE DESARROLLADO POR LEONARDO AGUILAR MARTINEZ PARA RECICLEY (RECUPERADORA DE MATERIALES OCAMPO
# DE TOLUCA) PRIMERA VERSION EJECUTANDOSE EN SYNOLOGY NAS (DSM 7.1.1-42928) CON PYTHON 3.9.16

import os
import re
import smtplib
from datetime import date, datetime
from email.mime.text import MIMEText
from collections import defaultdict

# ============ CONFIGURACIÓN ============

# Raíz común de "Contraloría" - todo vive en volume4. Cada linea de
# carpetas.txt es relativa a esta raiz y arranca con el area dentro de
# Contraloría (1.Calidad-Gestoría, 6.Ventas, 3.Comercial, etc.), lo que
# permite monitorear carpetas de mas de un area sin tocar este script.
_BASE_CONTRALORIA = "/volume4/Contraloría"

# Archivo de texto con la lista blanca de carpetas a monitorear (una ruta
# relativa a _BASE_CONTRALORIA por linea, ver carpetas.txt junto a este
# script). Para agregar o quitar una carpeta monitoreada basta con editar
# ese archivo: no requiere tocar ni volver a desplegar script.py.
_ARCHIVO_CARPETAS = "carpetas.txt"


def _cargar_carpetas(nombre_archivo=_ARCHIVO_CARPETAS):
    """Lee la lista blanca de carpetas desde un archivo de texto plano junto
    a este script: una ruta relativa a _BASE_CONTRALORIA por linea. Ignora
    lineas vacias y comentarios (que inician con #)."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre_archivo)
    with open(ruta, encoding="utf-8") as f:
        return [
            f"{_BASE_CONTRALORIA}/{linea.strip()}"
            for linea in f
            if linea.strip() and not linea.strip().startswith("#")
        ]


# LISTA BLANCA: unicamente estas carpetas son monitoreadas (ver carpetas.txt)
CARPETAS = _cargar_carpetas()

DIAS_ALERTA = 30  

GMAIL_USER = "ti@recicleymx.com"
DESTINATARIO_PRINCIPAL = "legal.permisos@recicleymx.com"
CC = [
    "aux.contraloria@recicleymx.com",
    "contraloriainterna1@recicleymx.com"
]

# CONTRASEÑA UTILIZADA EN BASH (CONTRASEÑA DE APLICACIÓN DE GMAIL) PARA ENVIAR CORREOS DESDE EL SCRIPT
GMAIL_APP_PASS = os.environ.get("GMAIL_APP_PASS")

# PREFIJO QUE INDICA QUE EL DOCUMENTO ES UN ACUSE (SE REPORTA POR SEPARADO, NO EN LA ALERTA PRINCIPAL)
PREFIJO_ACUSE = "ACUSE_"
# ========================================

# REGEX PARA EXTRAER LA FECHA DE VENCIMIENTO DEL NOMBRE DEL ARCHIVO PDF
# Exige el formato exacto NOMBRE_ARCHIVO_DD-MM-AAAA.pdf: la fecha debe venir
# precedida de un guion bajo e inmediatamente seguida de ".pdf" y el fin del
# nombre. Cualquier variante (sin guion bajo, doble extension .pdf.pdf, texto
# despues de la fecha, etc.) se ignora - no se lee.
PATRON = re.compile(r"_(\d{2}-\d{2}-\d{4})\.pdf$", re.IGNORECASE)


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

                es_acuse = nombre.upper().startswith(PREFIJO_ACUSE)

                if restantes < 0:
                    # Un acuse atrasado esta "pendiente" de recibirse, no "vencido"
                    # como un permiso o licencia.
                    estado = "PENDIENTE" if es_acuse else "VENCIDO"
                else:
                    estado = f"{restantes} dias restantes"

                registro = (nombre, vence, estado, raiz)

                if es_acuse:
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


def _clave_orden_categoria(categoria):
    """Extrae el numero inicial de una carpeta (p.ej. '18' de
    '18.Cedula de Zonificación') para poder ordenar categorias en orden
    numerico y no alfabetico (donde '18' quedaria antes que '2')."""
    m = re.match(r"(\d+)", categoria)
    return int(m.group(1)) if m else float("inf")


def _categoria_de(raiz):
    """Extrae el nombre del tramite (p.ej. '3.Licencias de Funcionamiento' o,
    en el area de Ventas, '1.Convenios Clientes') a partir de la ruta
    absoluta de un documento, para poder agrupar y enviar un correo por
    tramite. El primer segmento de la ruta (relativa a _BASE_CONTRALORIA) es
    el area (1.Calidad-Gestoría, 6.Ventas, 3.Comercial, ...); el segundo es
    el tramite dentro de esa area."""
    resto = raiz[len(_BASE_CONTRALORIA):].lstrip("/")
    partes = resto.split("/")
    return partes[1] if len(partes) > 1 else partes[0]


def _agrupar_por_categoria(documentos):
    """Agrupa documentos (vencimientos o acuses) por su carpeta numerada de
    primer nivel (1. Permisos de Recolección, 2. Permisos Planta de
    Separación, etc.), en orden numerico."""
    grupos = defaultdict(list)
    for registro in documentos:
        _, _, _, raiz = registro
        grupos[_categoria_de(raiz)].append(registro)
    return dict(sorted(grupos.items(), key=lambda kv: _clave_orden_categoria(kv[0])))


# Iconos de estado: rojo para lo ya atrasado (VENCIDO o PENDIENTE),
# ambar para lo que todavia esta dentro del umbral de aviso.
_ICONO_ATRASADO = "⛔"
_ICONO_PROXIMO = "⚠️"


def _construir_seccion(documentos, titulo):
    """Genera el bloque de texto de una seccion (vencimientos o acuses),
    agrupado por carpeta. Devuelve una lista de lineas."""
    grupos = _agrupar_por_carpeta(documentos)
    lineas = [f"{titulo} ({len(documentos)})", ""]
    for carpeta, items in grupos.items():
        lineas.append(f"📁 {carpeta}")
        ancho_estado = max(len(estado) for _, _, estado in items)
        for nombre, vence, estado in items:
            icono = _ICONO_ATRASADO if estado in ("VENCIDO", "PENDIENTE") else _ICONO_PROXIMO
            lineas.append(f"   {icono} {nombre}")
            lineas.append(
                f"        {estado.ljust(ancho_estado)}  (vence {vence.strftime('%d-%m-%Y')})"
            )
        lineas.append("")
    return lineas


def _construir_cuerpo(categoria, vencimientos, acuses):
    """Genera el cuerpo de correo en texto plano de una categoria, con las
    secciones de vencimientos y acuses unidas (se omite la seccion vacia)."""
    total = len(vencimientos) + len(acuses)

    ANCHO = 60
    SEP = "━" * ANCHO

    lineas = [
        SEP,
        f"  ALERTAS Y ACUSES — {categoria}",
        f"  Generado: {datetime.now().strftime('%d-%m-%Y %H:%M')}"
        f"      Total: {total} documentos",
        SEP,
        "",
    ]

    if vencimientos:
        lineas += _construir_seccion(vencimientos, f"{_ICONO_ATRASADO} VENCIMIENTOS DE PERMISOS")
    if acuses:
        lineas += _construir_seccion(acuses, "📋 ACUSES EN SEGUIMIENTO")

    lineas.append(SEP)
    lineas.append("Correo generado automáticamente por el sistema de alertas de Recicley.")
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


def enviar_correo(categoria, vencimientos, acuses):
    """Envia un unico correo por categoria con las alertas de vencimiento
    y los acuses en seguimiento juntos."""
    partes = []
    if vencimientos:
        partes.append(f"{len(vencimientos)} vencimiento(s)")
    if acuses:
        partes.append(f"{len(acuses)} acuse(s)")

    asunto = f"Alertas: {' y '.join(partes)} — {categoria}"
    cuerpo = _construir_cuerpo(categoria, vencimientos, acuses)
    _enviar(DESTINATARIO_PRINCIPAL, CC, asunto, cuerpo)
    print(f"Correo enviado correctamente ({categoria}).")


if __name__ == "__main__":
    if not GMAIL_APP_PASS:
        raise RuntimeError(
            "No se encontro GMAIL_APP_PASS en el entorno. "
            "Configura la variable en el Programador de tareas."
        )

    vencimientos, acuses = escanear()

    v_por_categoria = _agrupar_por_categoria(vencimientos)
    a_por_categoria = _agrupar_por_categoria(acuses)
    categorias = sorted(
        set(v_por_categoria) | set(a_por_categoria), key=_clave_orden_categoria
    )

    if categorias:
        for categoria in categorias:
            enviar_correo(
                categoria,
                v_por_categoria.get(categoria, []),
                a_por_categoria.get(categoria, []),
            )
    else:
        print("No hay permisos ni acuses proximos a vencer.")