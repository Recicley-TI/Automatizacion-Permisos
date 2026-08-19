# Graph Report - Alerts  (2026-08-16)

## Corpus Check
- 2 files · ~3,137 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 32 nodes · 37 edges · 6 communities (4 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `57eda5da`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Automatización de Permisos — Sistema de Alertas de Vencimiento
- script.py
- _agrupar_por_categoria
- Configuración
- _cargar_carpetas
- escanear

## God Nodes (most connected - your core abstractions)
1. `Automatización de Permisos — Sistema de Alertas de Vencimiento` - 9 edges
2. `_construir_cuerpo()` - 5 edges
3. `_agrupar_por_categoria()` - 4 edges
4. `Configuración` - 4 edges
5. `_agrupar_por_carpeta()` - 3 edges
6. `_clave_orden_categoria()` - 3 edges
7. `_categoria_de()` - 3 edges
8. `_enviar()` - 3 edges
9. `enviar_correo_vencimientos()` - 3 edges
10. `enviar_correo_acuses()` - 3 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (6 total, 2 thin omitted)

### Community 0 - "Automatización de Permisos — Sistema de Alertas de Vencimiento"
Cohesion: 0.20
Nodes (9): Automatización de Permisos — Sistema de Alertas de Vencimiento, Contenido del repositorio, Convención de nombres de archivo, Ejecución, En el NAS (Synology DSM), Formato del correo, Pendientes conocidos, Qué hace (+1 more)

### Community 1 - "script.py"
Cohesion: 0.43
Nodes (7): _agrupar_por_carpeta(), _construir_cuerpo(), _enviar(), enviar_correo_acuses(), enviar_correo_vencimientos(), Agrupa una lista de documentos por su carpeta contenedora,     ordenando cada g, Genera un cuerpo de correo en texto plano, legible y agrupado por carpeta.

### Community 2 - "_agrupar_por_categoria"
Cohesion: 0.33
Nodes (6): _agrupar_por_categoria(), _categoria_de(), _clave_orden_categoria(), Extrae el numero inicial de una carpeta (p.ej. '18' de     '18.Cedula de Zonifi, Extrae el nombre de la carpeta numerada de primer nivel (p.ej.     '3.Licencias, Agrupa documentos (vencimientos o acuses) por su carpeta numerada de     primer

### Community 3 - "Configuración"
Cohesion: 0.50
Nodes (4): `carpetas.txt` — lista blanca de carpetas, Configuración, Variables de entorno, Variables dentro de `script.py`

## Knowledge Gaps
- **10 isolated node(s):** `Contenido del repositorio`, `Qué hace`, `Convención de nombres de archivo`, `Formato del correo`, ``carpetas.txt` — lista blanca de carpetas` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Automatización de Permisos — Sistema de Alertas de Vencimiento` connect `Automatización de Permisos — Sistema de Alertas de Vencimiento` to `Configuración`?**
  _High betweenness centrality (0.153) - this node is a cross-community bridge._
- **Why does `Configuración` connect `Configuración` to `Automatización de Permisos — Sistema de Alertas de Vencimiento`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **What connects `Contenido del repositorio`, `Qué hace`, `Convención de nombres de archivo` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._