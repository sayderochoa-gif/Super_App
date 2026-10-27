"""
Base de Conocimiento Especializada en Sismología y Prevención de Desastres.
Provee respuestas rigurosas, estructuradas y limpias sin asteriscos triples ni desorden.
"""

import re
from typing import Optional


def sanitize_response(text: str) -> str:
    """
    Limpia y ordena cualquier respuesta:
    - Elimina completamente los asteriscos triples (***) o residuos de markdown sucio.
    - Asegura espaciado uniforme y viñetas ordenadas.
    """
    if not text:
        return ""

    # Eliminar triples asteriscos
    clean = re.sub(r"\*{3,}", "", text)
    # Reemplazar combinaciones de negrita-cursiva sucias
    clean = re.sub(r"\*\*\s*\*", "", clean)
    clean = re.sub(r"\*\s*\*\*", "", clean)
    # Limpiar dobles espacios redundantes en saltos de línea
    clean = re.sub(r"[ \t]+$", "", clean, flags=re.MULTILINE)
    # Asegurar un máximo de 2 saltos de línea consecutivos
    clean = re.sub(r"\n{3,}", "\n\n", clean)

    return clean.strip()


SEISMIC_KNOWLEDGE_BASE = {
    "que_hacer_antes": """🛡️ GUÍA DE PREVENCIÓN: ¿QUÉ HACER ANTES DE UN SISMO?

La preparación previa reduce hasta un 80% las probabilidades de sufrir lesiones durante un terremoto.

1. Plan Familiar de Emergencia:
• Reúne a tu familia para acordar un punto de encuentro exterior en caso de evacuación.
• Designa a un contacto fuera de tu ciudad como punto de enlace telefónico.
• Realiza simulacros periódicos en el hogar, escuela y lugar de trabajo.

2. Identificación y Aseguramiento del Entorno:
• Identifica las zonas seguras internas: columnas maestras, vigas estructurales y marcos firmes.
• Localiza las llaves de paso principales de gas, agua y el interruptor general de electricidad; aprende a cerrarlos rápidamente.
• Fija a muros o pisos los muebles altos, libreros, estanterías, calentadores de agua y televisores.
• Retira objetos pesados o de vidrio colocados en partes altas de las repisas.

3. Rutas de Evacuación Despejadas:
• Mantén siempre libres de obstáculos pasillos, escaleras y puertas de salida.
• Verifica que las puertas de acceso exterior puedan abrirse sin necesidad de buscar llaves en la oscuridad.

4. Preparación de Suministros:
• Mantén lista y accesible tu Mochila de Emergencia de las 72 horas cerca de la puerta principal.""",

    "que_hacer_durante": """🚨 PROTOCOLO DE SEGURIDAD: ¿QUÉ HACER DURANTE UN SISMO?

La regla de oro es mantener la calma y actuar con rapidez siguiendo las recomendaciones de protección civil.

1. Protocolo Internacional: Agacharse, Cubrirse y Sujetarse
• AGACHARSE: Ponte de rodillas para evitar que el movimiento sísmico te derribe al suelo.
• CUBRIRSE: Protégete bajo una mesa o escritorio resistente. Si no hay muebles cerca, cúbrete la cabeza y el cuello con ambos brazos pegado a una pared interior o columna estructural.
• SUJETARSE: Sujétate firmemente del mueble protector hasta que el movimiento telúrico cese por completo.

2. Si estás dentro de un edificio o vivienda:
• NO salgas corriendo ni intentes bajar escaleras mientras el suelo se mueve; la mayoría de las lesiones ocurren por caídas de vidrios, mampostería o escombros en los accesos exteriores.
• Aléjate de ventanas, ventanales, espejos y lámparas colgantes.
• NUNCA utilices ascensores durante ni inmediatamente después del sismo.

3. Si te encuentras en la calle o vía pública:
• Aléjate de postes eléctricos, cables de alta tensión, marquesinas, anuncios publicitarios y cornisas de edificios.
• Dirígete con calma hacia áreas abiertas como parques, plazas o calles amplias.

4. Si vas conduciendo un vehículo:
• Disminuye gradualmente la velocidad y detén la marcha en una zona segura, lejos de puentes, pasos a desnivel o cables caídos.
• Permanece dentro del vehículo con las luces intermitentes encendidas hasta que termine el temblor.

5. Si estás cerca de la costa:
• Si el sismo es tan intenso que dificulta mantenerte en pie, o dura más de 20 segundos, EVACUA INMEDIATAMENTE hacia zonas altas (+30 metros sobre el nivel del mar) ante la posibilidad inminente de un tsunami.""",

    "que_hacer_despues": """📋 ACCIONES CRÍTICAS: ¿QUÉ HACER DESPUÉS DE UN SISMO?

Las horas posteriores a un evento sísmico son fundamentales para prevenir accidentes secundarios.

1. Evaluación y Seguridad Inmediata:
• Revisa si tú o las personas a tu alrededor presentan heridas; aplica primeros auxilios básicos de ser necesario.
• No enciendas fósforos, encendedores ni aparatos eléctricos hasta verificar que no existan fugas de gas.
• Si hueles a gas o escuchas un silbido, cierra la llave de paso de inmediato, abre ventanas y desaloja el inmueble.

2. Inspección Estructural del Inmueble:
• Inspecciona visualmente si hay grietas diagonales profundas en muros de carga, columnas o techos.
• Si observas daño estructural severo, no reingreses al inmueble y espera la evaluación de bomberos o protección civil.

3. Prevención ante Réplicas:
• Las réplicas son habituales y pueden terminar de colapsar estructuras ya debilitadas por el sismo principal. Mantente alerta y preparado para volver a protegerte.

4. Comunicación y Canales Oficiales:
• Utiliza mensajes de texto (SMS) o mensajería de datos en lugar de llamadas telefónicas para evitar saturar las líneas de emergencia.
• Infórmate únicamente a través de canales y autoridades oficiales (USGS, Protección Civil, Servicio Sismológico Nacional, Cruz Roja). No difundas rumores ni noticias falsas.""",

    "mochila_emergencia": """🎒 MOCHILA DE EMERGENCIA (KIT DE SUPERVIVENCIA DE LAS 72 HORAS)

Cada hogar debe contar con una mochila impermeable, liviana y de fácil acceso que garantice la supervivencia durante las primeras 72 horas.

1. Agua y Alimentación:
• Agua embotellada: 2 a 3 litros por persona por día (mínimo para 3 días).
• Alimentos no perecibles: enlatados con abre fácil, barras energéticas, frutos secos, galletas de avena.

2. Botiquín de Primeros Auxilios:
• Gasas estériles, vendas, esparadrapo, alcohol o antiséptico, tijeras, guantes de nitrilo.
• Analgésicos básicos (paracetamol/ibuprofeno) y medicamentos recetados indispensables para tratamientos crónicos (insulina, hipertensión, etc.).

3. Comunicación e Iluminación:
• Linterna LED (preferiblemente con dinamo o con pilas de repuesto selladas).
• Radio portátil a pilas AM/FM para sintonizar comunicados de emergencia.
• Silbato resistente (clave para emitir señales sonoras si quedas atrapado).
• Batería externa (power bank) con cable para teléfono celular.

4. Documentos y Dinero:
• Copias en bolsa plástica impermeable o memoria USB de: cédulas/DNI, pasaportes, escrituras, pólizas de seguro y recetas médicas.
• Dinero en efectivo de baja denominación (los cajeros automáticos y terminales electrónicas suelen perder energía).

5. Abrigo y Artículos Personales:
• Manta térmica aluminizada, cambio de ropa abrigadora e impermeable ligero.
• Papel higiénico, toallitas húmedas, mascarillas y gel antibacterial.
• Duplicado de las llaves del hogar y del vehículo.""",

    "tsunamis_prevencion": """🌊 PREVENCIÓN Y PROTOCOLO DE TSUNAMI

Un tsunami es una serie de olas marinas generadas principalmente por sismos de gran magnitud (habitualmente M > 7.0) con epicentro submarino o costero poco profundo.

1. Señales Naturales de Alerta:
• Un sismo fuerte y prolongado que te impide mantenerte de pie en una zona costera.
• Retiro repentino y notable del agua del mar, dejando expuesto el fondo marino, arrecifes o peces.
• Un sonido estruendoso similar al de un tren de carga o turbina de avión que proviene del océano.

2. Protocolo de Evacuación Inmediata:
• Ante cualquiera de estas señales naturales, NO esperes una alerta formal por sirenas o mensajes: evacúa de inmediato a pie hacia zonas altas (al menos 30 metros sobre el nivel del mar) o tierra adentro (mínimo 1 a 2 kilómetros de la costa).
• Evita evacuar en automóvil, ya que las vías costeras se congestionan con rapidez.

3. Regla Fundamental:
• La primera ola no siempre es la más grande ni la más peligrosa. El tren de olas puede continuar golpeando la costa durante varias horas.
• No regreses a la costa hasta que las autoridades marítimas y de protección civil emitan el aviso oficial de cese de alerta.""",

    "que_es_un_sismo": """🌍 ¿QUÉ ES UN SISMO Y POR QUÉ OCURRE?

Un sismo, terremoto o temblor es la vibración y movimiento de la corteza terrestre producido por la liberación repentina de energía elástica acumulada en el interior de la Tierra.

1. Origen Físico:
• La litosfera terrestre está dividida en grandes fragmentos llamados placas tectónicas.
• Estas placas se desplazan continuamente a velocidades de varios centímetros por año.
• Cuando las placas se traban o chocan por fricción a lo largo de una falla geológica, la energía mecánica se acumula en las rocas.
• Al superarse el límite de resistencia de la roca, se produce una fractura súbita que libera la energía en forma de ondas sísmicas en todas las direcciones.

2. Puntos Clave del Evento:
• HIPOCENTRO (o foco): Punto subterráneo exacto en la corteza terrestre donde se inicia la ruptura de la falla y la liberación de energía. Su profundidad se mide en kilómetros (sismos superficiales: 0 a 70 km; intermedios: 70 a 300 km; profundos: > 300 km).
• EPICENTRO: Punto en la superficie terrestre situado verticalmente sobre el hipocentro, donde habitualmente se percibe el movimiento con mayor intensidad.""",

    "placas_y_fallas": """🗺️ PLACAS TECTÓNICAS, FALLAS Y EL CINTURÓN DE FUEGO

1. Tipos de Bordes Tectónicos:
• Límites Convergentes (Subducción): Una placa oceánica más densa se hunde bajo una placa continental (ejemplo: Placa de Nazca bajo la Placa Sudamericana, o Placa de Cocos bajo la Norteamericana). Genera los terremotos más potentes del planeta y fosas marinas profundas.
• Límites Transformantes (Deslizamiento Lateral): Las placas se deslizan horizontalmente una junto a otra sin destruir ni crear corteza (ejemplo: Falla de San Andrés en California).
• Límites Divergentes (Dorsales): Las placas se separan, permitiendo el ascenso de magma y creación de nueva corteza oceánica (ejemplo: Dorsal Mesoatlántica).

2. El Cinturón de Fuego del Pacífico (Ring of Fire):
• Región en forma de herradura de 40.000 kilómetros que rodea las costas del Océano Pacífico.
• Concentra más del 75% de los volcanes activos del mundo y cerca del 90% de los sismos mundiales, incluyendo el 81% de los terremotos más intensos jamás registrados.""",

    "ondas_sismicas": """〰️ TIPOS DE ONDAS SÍSMICAS

La energía liberada en el hipocentro se propaga por el planeta mediante ondas elásticas clasificadas en dos grupos principales:

1. Ondas de Cuerpo (viajan por el interior de la Tierra):
• ONDAS P (Primarias o Compresionales):
  - Son las más veloces (entre 5 y 8 km/s).
  - Comprimen y dilatan el material en la misma dirección de propagación.
  - Pueden atravesar sólidos, líquidos y gases.
  - Son las primeras en llegar a las estaciones sismológicas y no suelen causar daños graves.
• ONDAS S (Secundarias o de Cizalla):
  - Viajan a menor velocidad que las P (entre 3 y 5 km/s).
  - Mueven el terreno perpendicularmente a la dirección de avance (arriba-abajo o lateral).
  - Solo se propagan en medios SÓLIDOS (no atraviesan líquidos).
  - Provocan un movimiento más brusco y perceptible.

2. Ondas Superficiales (viajan por la superficie terrestre):
• ONDAS RAYLEIGH: Movimiento elíptico retrógrado similar al oleaje marino.
• ONDAS LOVE: Movimiento horizontal transversal violento.
• Son las responsables del mayor porcentaje de daño y colapso en edificaciones e infraestructura.""",

    "escalas_sismicas": """📏 ESCALAS DE MEDICIÓN: MAGNITUD VS INTENSIDAD

Es un error común confundir magnitud con intensidad. Miden aspectos totalmente distintos de un sismo:

1. MAGNITUD (Energía Liberada):
• Escala de Magnitud de Momento (Mw): Es el estándar científico actual utilizado por el USGS. Mide la rigidez de la roca fracturada, el área de ruptura y el desplazamiento medio de la falla.
• Escala de Richter (ML): Escala empírica basada en la amplitud máxima registrada por un sismógrafo Wood-Anderson. Se satura en eventos mayores a M 7.0, por lo que la ciencia migró a Mw.
• Es una escala LOGARÍTMICA: Cada incremento de 1 unidad de magnitud representa aproximadamente 32 veces más energía liberada (un sismo M 6.0 libera unas 32 veces más energía que uno M 5.0, y unas 1.000 veces más que uno M 4.0).
• Un sismo tiene un único valor de magnitud.

2. INTENSIDAD (Efectos y Daños en la Superficie):
• Escala de Mercalli Modificada (MMI): Se mide en números romanos del I al XII.
• I: Instrumental (no perceptible por humanos).
• IV - V: Moderado (se sienten vibraciones como paso de camiones, balanceo de lámparas).
• VII - VIII: Dañino a severo (grietas en muros, caída de chimeneas, daño en edificios comunes).
• XII: Destrucción total (ondas visibles en el suelo, colapso generalizado).
• La intensidad varía según la distancia al epicentro, el tipo de suelo y la calidad constructiva.""",

    "prediccion_mitos": """🔬 ¿SE PUEDEN PREDECIR LOS SISMOS? (CIENCIA VS MITOS)

1. La Realidad Científica:
• A la fecha, NINGÚN científico, institución sismológica, universidad o tecnología en el mundo puede predecir con exactitud el día, hora y lugar de un terremoto.
• Los sismos son fenómenos no lineales de alta complejidad que involucran tensiones a decenas de kilómetros bajo tierra sin señales precursoras universales comprobadas.
• Si recibes cadenas en WhatsApp o redes sociales que afirmen 'se espera un gran terremoto mañana a las 15:00 horas', son totalmente FALSAS.

2. ¿Qué son los Sistemas de Alerta Temprana (ej. ShakeAlert, SASMEX)?
• NO son sistemas de predicción. Son sistemas de detección ultrarrápida.
• Detectan la onda P (la más rápida y menos destructiva) en las estaciones cercanas al epicentro y envían una señal radial o digital a la velocidad de la luz hacia las ciudades antes de que arriben las ondas S y superficiales destructivas.
• Proporcionan un margen de 10 a 60 segundos vitales para evacuar, detener trenes, cortar suministros de gas o colocarse en zonas seguras.""",

    "enjambre_sismico": """🐝 ¿QUÉ ES UN ENJAMBRE SÍSMICO?

Un enjambre sísmico es una secuencia de numerosos sismos que ocurren en un área geográfica determinada durante un periodo de días, semanas o meses, sin que se identifique un sismo principal claramente dominante.

• A diferencia de las secuencias convencionales (Sismo Principal seguido de Réplicas decrecientes), en un enjambre los eventos suelen tener magnitudes similares (ejemplo: múltiples sismos de M 2.5 a M 4.2 continuos).
• Causas habituales: Movimiento de fluidos hidrotermales o magma en zonas volcánicas, o reacomodo paulatino de fallas geológicas con fricción segmentada.
• No necesariamente indican que ocurrirá un terremoto mayor, pero requieren monitoreo instrumental continuo.""",

    "admin_vista_y_paneles": """🛠️ VISTA DEL ADMINISTRADOR: PANELES Y FUNCIONALIDADES

Como Administrador de SismoWatch, tu interfaz incluye acceso total a la plataforma y sus 4 apartados principales:

1. Telemetría Sísmica (Dashboard Principal):
• Globo Terráqueo 3D interactivo con texturas de alta resolución, propagación de ondas sísmicas, rotación automática y zoom dinámico.
• Tarjetas de KPIs en tiempo real: total de sismos en 24h, magnitud máxima, magnitud promedio y contador de alertas de tsunami (protocolo costero).
• Stream en vivo (SSE): recepción instantánea de sismos procesados.
• Feed de eventos con filtros por magnitud, región y botones de exportación a CSV y PDF.

2. Reportes IA (Panel Exclusivo de Admin):
• Resumen ejecutivo diario narrativo redactado automáticamente por Inteligencia Artificial generativa.
• Métricas estructuradas clave (sismos totales, sismo más potente, zona más activa, profundidad media).
• Detección analítica de anomalías: identificación de enjambres sísmicos y picos de actividad mediante analítica avanzada y Z-Score.
• Botón de acción 'Regenerar Reporte' para recalcular el informe en cualquier momento.
• Descarga de informes ejecutivos en formato PDF y exportación en CSV.

3. Pipeline & Calidad (Panel Exclusivo de Admin):
• Orquestación con Apache Airflow: monitor de estado de los 4 DAGs en tiempo real.
• SLA de Frescura de Datos: supervisión del tiempo transcurrido desde la última ingesta (SLA objetivo < 1.0 hora).
• Compuerta de Calidad (Pandera Data Quality): porcentaje de calidad y auditorías automáticas de esquemas.
• Tabla de Cuarentena: inspección de registros descartados con el motivo detallado de rechazo.
• Botón de acción 'Ejecutar Backfill' para rellenar datos históricos del USGS.

4. Agente Sísmico (SeismoAgent):
• Asistente analítico inteligente para consultas en lenguaje natural, estadísticas agregadas, protocolos de prevención y ejecución de consultas SQL de solo lectura.""",

    "admin_acciones_disponibles": """⚡ ACCIONES QUE PUEDES REALIZAR COMO ADMINISTRADOR

Tu rol de Administrador te otorga privilegios avanzados y acciones exclusivas en la plataforma:

1. Ejecutar Backfill Histórico:
• Puedes alimentar la base de datos con sismos históricos del USGS indicando fecha de inicio, fecha de fin y magnitud mínima.
• Dónde: en la vista 'Pipeline & Calidad', haz clic en el botón 'Ejecutar Backfill'.
• Detrás de escena: se dispara de forma asíncrona el DAG 'dag_backfill_historical' en Apache Airflow.

2. Forzar la Regeneración de Reportes IA:
• Si deseas un nuevo análisis narrativo y detección de anomalías actualizado de inmediato con los datos más recientes.
• Dónde: en la vista 'Reportes IA', haz clic en 'Regenerar Reporte'.
• Detrás de escena: se ejecuta inmediatamente el DAG 'dag_ai_daily_report'.

3. Auditar Registros en Cuarentena:
• Puedes revisar todos los sismos que no superaron las reglas de validación de calidad de datos de Pandera.
• Dónde: en la pestaña 'Cuarentena' dentro de 'Pipeline & Calidad'.
• Qué puedes ver: ID del evento, fecha de rechazo, motivo del fallo (ej. latitud fuera de rango, fecha futura, ID nulo) y carga JSON original.

4. Monitorear y Administrar Airflow:
• Supervisar los 4 DAGs: 'dag_ingestion_realtime', 'dag_transformation_quality', 'dag_ai_daily_report' y 'dag_backfill_historical'.
• Acceso directo al Webserver de Airflow en http://localhost:8080 (usuario: 'airflow', contraseña: 'airflow').

5. Exportar Reportes e Informes:
• Generar PDFs profesionales de los reportes diarios o exportar tablas de sismos filtrados a CSV.

6. Consultas SQL Libres y Seguras en SeismoAgent:
• Puedes escribir sentencias SELECT directas en este chat para analizar correlaciones geográficas, temporales o de severidad.""",

    "admin_cuarentena_explicacion": """📦 SISTEMA DE CALIDAD Y TABLA DE CUARENTENA

El módulo de calidad de SismoWatch implementa contratos de datos estrictos mediante Pandera y SQLAlchemy para evitar la contaminación de la capa curated:

1. ¿Por qué un sismo entra en cuarentena?
• Coordenadas fuera de rango: Latitud no perteneciente a [-90, 90] o Longitud fuera de [-180, 180].
• Magnitud anómala: Valores extremos fuera del rango físico [-2.0, 10.0].
• Timestamps del futuro: Eventos cuya marca de tiempo sea superior a la hora UTC actual.
• Integridad de clave primaria: Registros sin ID oficial o IDs vacíos.

2. ¿Qué pasa con los registros rechazados?
• No se eliminan silenciosamente: se enrutan a la tabla 'quarantine' para trazabilidad y auditoría.
• La compuerta calcula un Quality Score (%) que se refleja en los KPIs del Pipeline.
• Como Administrador, puedes inspeccionar la causa exacta en la vista 'Pipeline & Calidad'.""",

    "admin_backfill_guia": """🚀 GUÍA: ¿CÓMO EJECUTAR UN BACKFILL HISTÓRICO?

El Backfill Histórico permite poblar la base de datos con sismos de días, semanas o meses anteriores:

1. Paso a paso desde la interfaz:
• Dirígete a la sección 'Pipeline & Calidad' en el menú lateral izquierdo.
• En la cabecera, pulsa el botón 'Ejecutar Backfill'.
• Se abrirá un modal donde defines:
  - Fecha de inicio (Start Date) en formato YYYY-MM-DD.
  - Fecha de fin (End Date) en formato YYYY-MM-DD.
  - Magnitud mínima (Min Magnitude), por defecto 2.5 para filtrar micro-sismos.
• Pulsa 'Iniciar Backfill'.

2. Procesamiento:
• La API envía la solicitud a Airflow, la cual ejecuta 'dag_backfill_historical'.
• Los datos se descargan por lotes desde la API oficial del USGS, pasan la compuerta de calidad Pandera y se guardan en la capa curated sin duplicados (UPSERT)."""
}


def normalize_text(text: str) -> str:
    """Normalize text removing accents and punctuation for robust matching."""
    t = text.lower()
    t = re.sub(r"[¿?¡!.,;:\"'()\-—]", " ", t)
    t = t.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    return re.sub(r"\s+", " ", t).strip()


def query_seismic_knowledge(query: str, user_role: str = "viewer") -> Optional[str]:
    """
    Evalúa la consulta del usuario y retorna información sismológica, de prevención
    o de administración según el rol y tema consultado.
    """
    q = normalize_text(query)

    # Consultas específicas de la vista y acciones de Administrador
    if (any(w in q for w in ["accion", "acciones", "que puedo hacer", "que hace", "mis permisos", "permisos", "privilegios", "puedo ejecutar"]) and
        any(w in q for w in ["admin", "administrador", "como admin", "en mi rol", "en la plataforma"])):
        return sanitize_response(SEISMIC_KNOWLEDGE_BASE["admin_acciones_disponibles"])

    if any(w in q for w in ["que veo en mi vista", "vista de admin", "vista admin", "paneles de admin", "paneles tengo", "que apartados tengo", "que hay en mi vista", "mi vista", "mis paneles"]):
        return sanitize_response(SEISMIC_KNOWLEDGE_BASE["admin_vista_y_paneles"])

    if any(w in q for w in ["como hacer un backfill", "como ejecutar backfill", "backfill historico", "que es el backfill", "rellenar datos", "datos historicos"]):
        return sanitize_response(SEISMIC_KNOWLEDGE_BASE["admin_backfill_guia"])

    if any(w in q for w in ["tabla de cuarentena", "que es la cuarentena", "por que se rechazan", "registros en cuarentena", "calidad de datos", "pandera"]):
        return sanitize_response(SEISMIC_KNOWLEDGE_BASE["admin_cuarentena_explicacion"])

    if any(w in q for w in ["airflow", "dags", "credenciales de airflow", "usuario de airflow", "contraseña de airflow", "puerto 8080"]):
        return sanitize_response(
            "✈️ ORQUESTACIÓN Y AIRFLOW EN SISMOWATCH\n\n"
            "El sistema cuenta con Apache Airflow para la orquestación periódica de datos:\n\n"
            "1. DAGs Activos:\n"
            "• dag_ingestion_realtime: Ingesta periódica horaria desde el USGS.\n"
            "• dag_transformation_quality: Validación de esquemas y reglas de calidad con Pandera.\n"
            "• dag_ai_daily_report: Generación de resumen ejecutivo con IA generativa.\n"
            "• dag_backfill_historical: Carga histórica parametrizada bajo demanda.\n\n"
            "2. Acceso al Webserver de Airflow:\n"
            "• URL: http://localhost:8080\n"
            "• Usuario: airflow\n"
            "• Contraseña: airflow"
        )

    # Prevención: Antes
    if any(w in q for w in ["antes de un sismo", "antes del sismo", "preparar", "preparacion", "antes del temblor", "plan familiar", "medidas preventivas", "prevencion"]):
        if "mochila" not in q and "tsunami" not in q:
            return sanitize_response(SEISMIC_KNOWLEDGE_BASE["que_hacer_antes"])

    # Prevención: Durante
    if any(w in q for w in ["durante un sismo", "durante el sismo", "durante el temblor", "que hacer en un sismo", "que hacer durante", "que hacer si hay un terremoto", "agacharse", "cubrirse", "en pleno sismo"]):
        return sanitize_response(SEISMIC_KNOWLEDGE_BASE["que_hacer_durante"])

    # Prevención: Después
    if any(w in q for w in ["despues de un sismo", "despues del sismo", "despues del temblor", "luego del terremoto", "fugas de gas", "post sismo"]):
        return sanitize_response(SEISMIC_KNOWLEDGE_BASE["que_hacer_despues"])

    # Mochila de emergencia / Kit
    if any(w in q for w in ["mochila de emergencia", "mochila", "kit de emergencia", "kit de supervivencia", "72 horas", "que llevar"]):
        return sanitize_response(SEISMIC_KNOWLEDGE_BASE["mochila_emergencia"])

    # Tsunamis
    if any(w in q for w in ["protocolo tsunami", "tsunami prevencion", "evacuacion costera", "que hacer en un tsunami", "como actuar en tsunami"]):
        return sanitize_response(SEISMIC_KNOWLEDGE_BASE["tsunamis_prevencion"])

    # Qué es un sismo / origen
    if any(w in q for w in ["que es un sismo", "que es un terremoto", "que es un temblor", "por que ocurren", "por que tiembla", "como se produce", "origen de los sismos", "hipocentro", "epicentro"]):
        return sanitize_response(SEISMIC_KNOWLEDGE_BASE["que_es_un_sismo"])

    # Placas tectónicas y fallas
    if any(w in q for w in ["placas tectonicas", "placa tectonica", "cinturon de fuego", "anillo de fuego", "falla geologica", "san andres", "subduccion"]):
        return sanitize_response(SEISMIC_KNOWLEDGE_BASE["placas_y_fallas"])

    # Ondas sísmicas
    if any(w in q for w in ["ondas sismicas", "onda p", "onda s", "ondas p y s", "ondas rayleigh", "ondas love", "tipo de ondas"]):
        return sanitize_response(SEISMIC_KNOWLEDGE_BASE["ondas_sismicas"])

    # Escalas sísmicas
    if any(w in q for w in ["escala richter", "magnitud vs intensidad", "mercalli", "escala de momento", "mw", "diferencia entre magnitud"]):
        return sanitize_response(SEISMIC_KNOWLEDGE_BASE["escalas_sismicas"])

    # Predicción y mitos
    if any(w in q for w in ["se pueden predecir", "predecir terremotos", "predecir sismos", "alerta temprana", "shakealert", "sasmex"]):
        return sanitize_response(SEISMIC_KNOWLEDGE_BASE["prediccion_mitos"])

    # Enjambre sísmico
    if any(w in q for w in ["enjambre sismico", "enjambre sísmico", "que es un enjambre", "secuencia de sismos"]):
        return sanitize_response(SEISMIC_KNOWLEDGE_BASE["enjambre_sismico"])

    return None
