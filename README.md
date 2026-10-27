# SeismoAgent: Agente Relacional para Monitoreo y Análisis Sísmico (USGS)

Sistema autónomo y modular de telemetría y análisis sísmico en tiempo real. Integra la ingesta continua de eventos telúricos desde los servicios geológicos oficiales del **USGS (United States Geological Survey)**, normalización en un modelo relacional en Tercera Forma Normal (3NF) y un agente conversacional equipado con ejecución segura de SQL (*Safe SQL Engine*) e inferencia analítica de lenguaje natural.

---

## 1. Arquitectura y Estructura del Proyecto

El sistema está diseñado bajo una arquitectura en capas desacopladas (Ingesta HTTP $\rightarrow$ Normalización y Persistencia ORM $\rightarrow$ Herramientas de Análisis $\rightarrow$ Orquestador del Agente $\rightarrow$ Interfaces CLI y API):

```text
agentebot/
├── .env.example             # Plantilla de variables de entorno (BD, endpoints, LLM)
├── .env                     # Variables de entorno locales activas
├── requirements.txt         # Dependencias de producción (SQLAlchemy, Pydantic, etc.)
├── README.md                # Documentación técnica del repositorio
├── explic.md                # Guía técnica y ejecutiva para defensa y sustentación
├── config.py                # Configuración tipada con Pydantic Settings
├── main.py                  # CLI ejecutable con modo interactivo y banderas automatizadas
├── database/
│   ├── __init__.py          # Exportación del paquete de base de datos
│   ├── connection.py        # Configuración de Engine SQLAlchemy, sessions y WAL en SQLite
│   └── models.py            # Modelos declarativos 3NF (Location, Earthquake, ImpactMetric)
├── services/
│   ├── __init__.py          # Exportación de servicios de datos
│   ├── usgs_client.py       # Cliente HTTP con timeout, reintentos y parsing de GeoJSON
│   └── ingestion.py         # Pipeline de normalización espacial, parsing temporal y UPSERT
└── agent/
    ├── __init__.py          # Exportación del agente y herramientas
    ├── tools.py             # Herramientas analíticas, safe SQL executor y esquemas OpenAI
    ├── knowledge.py         # Base de conocimiento sismológica, prevención y control de formato
    └── core.py              # Orquestador del agente: Function Calling LLM y motor de reglas offline
```

---

## 2. Requisitos Previos

- **Python:** Versión 3.10 o superior (recomendado Python 3.11 o 3.12).
- **Gestor de Paquetes:** `pip` y soporte para entornos virtuales (`venv`).
- **Motor de Base de Datos:**
  - **SQLite:** Incluido por defecto en la biblioteca estándar de Python (sin instalación adicional).
  - **PostgreSQL:** Opcional para entornos distribuidos de alta concurrencia.
- **Acceso de Red:** Salida HTTPS hacia `earthquake.usgs.gov`.
- **Credenciales OpenAI:** Opcional. Si no se suministra `OPENAI_API_KEY`, el sistema conmuta automáticamente a su motor determinista offline sin degradación de servicio ni errores de ejecución.

---

## 3. Instalación y Configuración

### Paso 1: Clonar el Repositorio y Crear Entorno Virtual

```bash
cd agentebot
python3 -m venv .venv
source .venv/bin/activate
```

*(En Windows PowerShell: `.venv\Scripts\Activate.ps1`)*

### Paso 2: Instalación de Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 3: Configurar Variables de Entorno

Copia el archivo de plantilla a `.env`:

```bash
cp .env.example .env
```

Configura los parámetros según el entorno de despliegue:

```ini
# Base de datos relacional (por defecto SQLite local)
DATABASE_URL=sqlite:///./seismic_agent.db

# Endpoint oficial de USGS (Feed de la última hora)
USGS_FEED_URL=https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson

# Configuración del LLM (Opcional)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# Registro de eventos
LOG_LEVEL=INFO
```

---

## 4. Puesta en Marcha

El archivo [`main.py`](main.py) actúa como el punto de entrada unificado para operaciones automatizadas o sesiones interactivas.

### A. Interfaz Interactiva (REPL Conversacional)

Inicia la consola interactiva ejecutando:

```bash
python main.py
```

Comandos internos disponibles dentro del REPL:
- `sync` : Dispara la ingesta inmediata de la última telemetría del USGS.
- `stats` : Computa métricas agregadas del catálogo (magnitud media, sismo más potente, zonas activas).
- `tsunami` : Filtra eventos con alerta o protocolo de tsunami activado.
- `schema` : Imprime la definición DDL de las tablas relacionales.
- `sql <consulta>` : Ejecuta consultas directas de solo lectura (ej. `sql SELECT count(*) FROM earthquakes`).
- `reset` : Limpia el contexto conversacional del agente.
- `help` : Muestra la guía de comandos.
- `exit` o `quit` : Finaliza la ejecución.

También admite cualquier consulta en lenguaje natural:
- *"¿Cuáles fueron los sismos más fuertes de la última hora?"*
- *"¿Qué medidas de prevención debo tomar durante un terremoto?"*
- *"Muéstrame sismos con magnitud mayor a 3.0"*

### B. Ejecución por Banderas CLI (Automatización & Cron Jobs)

Para integraciones con pipelines, tareas programadas en crontab o DAGs de Apache Airflow:

```bash
# Sincronización desatendida del feed USGS
python main.py --sync

# Extracción de estadísticas en consola
python main.py --stats

# Consulta puntual de eventos con alerta de tsunami
python main.py --tsunami

# Ejecución de una consulta específica en un solo paso
python main.py --query "¿Cuáles son las 3 zonas con mayor sismicidad?"

# Sincronización con un feed alternativo (ej. sismos de las últimas 24 horas)
python main.py --feed "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson" --sync
```

---

## 5. Fuente de Datos (USGS API)

- **Endpoint Primario:**  
  `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson`
- **Formato:** GeoJSON estándar (RFC 7946) con array `features[]` y metadatos en `metadata`.
- **Frecuencia de Actualización del USGS:** El feed se regenera cada 60 segundos con los sismos registrados y revisados globalmente.
- **Feeds Alternativos Soportados:**
  - Últimas 24 horas (M1.0+): `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/1.0_day.geojson`
  - Últimos 7 días (M4.5+): `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson`

---

## 6. Seguridad y Políticas de Ejecución SQL

La herramienta interna `execute_safe_sql` garantiza la integridad de la base de datos ante consultas dinámicas generadas por el agente o el usuario:
1. **Solo Lectura:** Únicamente se permiten declaraciones que inicien con `SELECT` o `WITH` (CTE).
2. **Aislamiento de Literales:** Las cadenas entre comillas son ignoradas al evaluar palabras reservadas para evitar falsos positivos en cláusulas de texto.
3. **Bloqueo de Inyecciones y Modificaciones:** Se rechazan tajantemente palabras clave DDL/DML (`DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, `TRUNCATE`, `PRAGMA`, etc.) y encadenamiento de comandos mediante punto y coma (`;`).
4. **Paginación Forzada:** Si la consulta omite la cláusula `LIMIT`, el motor agrega automáticamente `LIMIT 50`.
