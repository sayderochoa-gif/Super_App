# SismoWatch — Plataforma de Inteligencia Sísmica en Tiempo Real (SuperApp)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Apache Airflow](https://img.shields.io/badge/Airflow-2.8+-017CEE?logo=apacheairflow&logoColor=white)](https://airflow.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

**SismoWatch** es una solución de datos de punta a punta (`production-grade`) diseñada para ingestar, validar, auditar y enriquecer con IA la sismicidad global provista por el catálogo del **USGS (United States Geological Survey)**.

---

## 🌟 Características Principales

1. **Ingesta Continua y Resiliente (Airflow 2.8+):**
   - Ingesta cada 5 minutos del feed GeoJSON de USGS con políticas de reintento exponencial (`retries=3`, `retry_delay=30s`).
   - Idempotencia total: Inserciones y actualizaciones gestionadas mediante `UPSERT` en todas las capas.
2. **Arquitectura Lakehouse de Tres Capas:**
   - `raw`: Almacena el payload JSON crudo con metadatos de ingesta (`audit trail` inmutable).
   - `staging`: Datos extraídos, normalizados, aplanados y tipados.
   - `curated`: Datos verificados y analíticamente indexados para consultas sub-segundo.
3. **Quality Gate Bloqueante (Pandera):**
   - Validación estricta de coordenadas latitud `[-90, 90]`, longitud `[-180, 180]`, magnitud `[-2.0, 10.0]`, profundidad `[-5.0, 1000.0] km` y tiempo.
   - Enrutamiento automático de registros rechazados hacia `curated.quarantine` con causa explícita del fallo.
   - Registro de métricas de calidad en `curated.quality_audit`.
4. **Motor de IA y Detección de Anomalías:**
   - Detección de enjambres sísmicos y patrones anómalos multivariados con `IsolationForest`.
   - Síntesis de reportes ejecutivos diarios con LLM (OpenAI) anclado estrictamente a KPIs deterministas y motor de fallback automático en caso de timeout.
   - Mitigación activa contra Prompt Injection en campos de texto no confiables.
5. **Backend Asíncrono de Alto Rendimiento (FastAPI):**
   - SQLAlchemy 2.0 + asyncpg.
   - Autenticación JWT con Control de Acceso Basado en Roles (RBAC: `admin`, `viewer`).
   - Transmisión en tiempo real vía Server-Sent Events (SSE).
6. **Frontend Moderno (React + Vite + Leaflet + Tailwind CSS):**
   - Dashboard con indicadores KPIs en vivo y mapa interactivo global.
   - Marcadores coloreados por magnitud y tooltips detallados.
   - Visor de reportes ejecutivos IA con exportación en CSV y formato imprimible / PDF.
   - Pestaña de cuarentena y disparadores de backfill/regeneración exclusivos para administradores.

---

## 🚀 Despliegue Rápido con Docker Compose

### 1. Clonar y Configurar Entorno
```bash
cp .env.example .env
```

### 2. Levantar el Stack Completo
```bash
docker compose up -d --build
```

### 3. Servicios Disponibles
| Servicio | URL / Puerto | Credenciales por Defecto |
| :--- | :--- | :--- |
| **Frontend Web SPA** | [http://localhost:3000](http://localhost:3000) | Ver sección de roles abajo |
| **Backend REST & SSE API** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger interactivo con soporte JWT |
| **Airflow Webserver** | [http://localhost:8080](http://localhost:8080) | `airflow` / `airflow` |
| **PostgreSQL Database** | `localhost:5432` | `postgres` / `postgres_master_pass` |

---

## 🔐 Modelo de Roles y Credenciales Preconfiguradas

El sistema implementa RBAC estricto a nivel de endpoints y vistas UI:

| Rol | Usuario | Contraseña | Permisos y Accesos |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@sismowatch.com` | `AdminSismoWatch2025!` | **Acceso Total:** Dashboard, reportes IA, exportación, inspección detallada de cuarentena (con visor de payload crudo), disparador manual de backfill (`POST /api/admin/backfill`) y regeneración de reporte (`POST /api/admin/reports/regenerate`). |
| **Viewer** | `viewer@sismowatch.com` | `ViewerSismoWatch2025!` | **Solo Lectura:** Dashboard, telemetría sísmica, mapa interactivo, lectura de reportes IA, exportación (CSV/PDF) y stream SSE. **Bloqueado:** Cuarentena y botones de administración ocultos en UI y protegidos con `403 Forbidden` en la API. |
| **Visitante** | *Sin token* | *N/A* | Redirección obligatoria a `/login`. Cualquier petición a `/api/*` responde `401 Unauthorized`. |

---

## 🧪 Ejecución de Pruebas Automatizadas

El proyecto incluye una suite completa de pruebas con Pytest:

```bash
# Activar entorno virtual
source .venv/bin/activate

# Ejecutar la suite completa
pytest -v tests/
```

### Pruebas Incluidas:
1. `tests/test_transformations.py`: Valida el aplanamiento de GeoJSON anidado, extracción de coordenadas y conversión epoch UTC.
2. `tests/test_quality_rules.py`: Valida que registros correctos pasen y registros físicamente imposibles (e.g. latitud 150°, magnitud 15.0) se aíslen con su causa exacta en cuarentena.
3. `tests/test_dag_integrity.py`: Valida sintaxis, grafos acíclicos y estructura de los 4 DAGs de Airflow.
4. `tests/test_api_rbac.py`: Valida códigos de estado `401 Unauthorized` para visitantes, `403 Forbidden` para viewers en rutas restringidas y `200 OK` para administradores.

---

## 🛡️ Auditoría de Seguridad (Bandit)

Para validar la ausencia de vulnerabilidades estáticas en el backend:

```bash
bandit -r backend/ -ll
```
*Resultado: 0 vulnerabilidades de severidad Media o Alta detectadas.*

---

## 📁 Estructura del Código

```text
sismowatch/
├── docker-compose.yml          # Orquestación completa de 6 contenedores
├── .env.example                # Plantilla de variables de entorno seguras
├── .gitignore                  # Reglas de exclusión para Git
├── README.md                   # Guía de despliegue y referencia
├── docs/
│   └── ARQUITECTURA.md         # Documento detallado de diseño y diagramas Mermaid
├── sql/
│   └── init-db.sql             # Esquemas (raw, staging, curated), roles y DDL
├── airflow/
│   ├── Dockerfile              # Imagen Airflow 2.8 con dependencias científicas
│   ├── requirements.txt        # Pandera, Pandas, Scikit-learn, etc.
│   ├── dags/
│   │   ├── dag_ingestion_realtime.py     # Ingesta cada 5 min desde USGS
│   │   ├── dag_transformation_quality.py # Staging, Pandera Gate y Curated
│   │   ├── dag_ai_daily_report.py        # KPIs deterministas, IsolationForest y LLM
│   │   └── dag_backfill_historical.py    # Backfill parametrizado por ventana
│   └── plugins/
│       ├── quality_engine.py   # Pandera schemas, validación y frescura
│       ├── ai_engine.py        # KPIs, detección de enjambres y post-validación
│       └── db_utils.py         # Utilidades de base de datos e idempotencia UPSERT
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI entrypoint, CORS y seed automático
│       ├── config.py           # Configuración Pydantic Settings
│       ├── database.py         # SQLAlchemy 2.0 async engine
│       ├── security.py         # Bcrypt, JWT, sanitización y RBAC
│       ├── models/             # Curated, Staging, Raw, Users, Quarantine
│       ├── schemas/            # Pydantic v2 DTOs
│       ├── services/           # KPIs, Airflow REST client, SSE broadcaster, exports
│       └── routers/            # auth, kpis, events, stats, reports, stream, admin
├── frontend/
│   ├── Dockerfile              # Multi-stage build Nginx
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx             # Orquestación de pestañas y cliente SSE
│       ├── context/            # AuthContext (JWT & roles)
│       ├── services/           # Cliente HTTP Axios/Fetch
│       └── components/         # Navbar, Login, Dashboard, SeismicMap, Reports, Pipeline
└── tests/
    ├── conftest.py             # Fixtures compartidas y mock tokens
    ├── test_transformations.py # Pruebas de aplanamiento GeoJSON
    ├── test_quality_rules.py   # Pruebas de Pandera Quality Gate y Cuarentena
    ├── test_dag_integrity.py   # Pruebas de sintaxis y ciclos de Airflow DAGs
    └── test_api_rbac.py        # Pruebas de autorización RBAC (401, 403, 200)
```
