# Roadmap técnico - Jira Knowledge RAG

## 1. Propósito del roadmap

Este documento transforma la propuesta técnica de `Guide.md` en un plan de
ejecución basado en el estado real del repositorio al 11 de junio de 2026.

El objetivo no es únicamente agregar un chat conectado a Jira. El objetivo es
construir un sistema confiable que:

1. sincronice información de Jira de forma segura y repetible;
2. conserve trazabilidad desde cada respuesta hasta la tarjeta original;
3. recupere evidencia relevante con calidad medible;
4. responda únicamente con información respaldada por fuentes;
5. pueda evolucionar desde el prototipo local hacia un servicio operable.

Este roadmap no modifica la arquitectura actual de inmediato. Define el orden
recomendado para evolucionarla sin perder las capacidades que ya funcionan.

**Objetivo primario del proyecto: portfolio / demo.** Por esa razón, la
ejecución real se rige por el **Track de ejecución para portfolio (plan
activo)** que aparece tras el resumen ejecutivo. Las fases 0 a 10 de este
documento se conservan como **referencia exhaustiva de grado productivo**
(superconjunto): describen lo que haría falta para un servicio interno real.
Cuando el track de portfolio entre en conflicto con esas fases o con el
principio 5.1, **prevalece el track de portfolio**.

---

## 2. Resumen ejecutivo

El repositorio ya tiene un prototipo local funcional para extracción,
transformación y búsqueda:

- sincronización full e incremental de Jira;
- almacenamiento raw por tarjeta;
- detección de cambios mediante hash;
- normalización a un contrato local;
- generación de Markdown;
- generación de chunks temáticos;
- búsqueda literal, semántica e híbrida;
- logs básicos de ejecución.

La principal brecha no es la ausencia de más funcionalidades. La principal
brecha es que todavía no existen garantías automáticas sobre la exactitud,
completitud y estabilidad de lo que ya está implementado.

Por eso, el orden recomendado es:

```text
Estabilizar y medir
    -> endurecer la sincronización
    -> formalizar contratos y pruebas
    -> medir y mejorar retrieval
    -> construir Mini RAG con fuentes
    -> exponer API
    -> migrar persistencia
    -> construir frontend
    -> preparar operación productiva
    -> incorporar adjuntos e imágenes
```

La primera meta relevante debe ser un **Mini RAG evaluable y trazable**, no un
frontend. La interfaz tendrá más valor cuando la recuperación y las respuestas
ya tengan calidad demostrable.

> **Ajuste del track de portfolio:** para el objetivo de portfolio este orden
> se invierte parcialmente. Un *slice* delgado (API mínima + UI de chat) se
> adelanta inmediatamente después de un Mini RAG básico, porque el chatbot es
> la entrega visible. La calidad medible no se sacrifica: se conserva citas y
> abstención obligatorias desde el primer slice y la evaluación de retrieval se
> ejecuta justo después, no como compuerta previa. Ver el track de portfolio.

---

## 2bis. Track de ejecución para portfolio (plan activo)

Esta sección es el **plan de ejecución vigente**. Reordena, recorta y amplía las
fases 0 a 10 para el objetivo de portfolio. Donde contradiga a esas fases o al
principio 5.1, esta sección manda.

### 2bis.1. Objetivo de portfolio

Un chatbot **desplegado y accesible por URL** que responde preguntas sobre Jira
mostrando **fuentes visibles** y que **se abstiene** cuando no hay evidencia. La
entrega visible (el chat) debe aparecer pronto, sin renunciar a las dos
garantías que la hacen creíble: **citas** y **abstención**.

### 2bis.2. Decisiones fijadas

Estas decisiones se toman por adelantado para evitar trabajo de migración y
abstracción innecesario en un proyecto de portfolio:

- **Almacenamiento:** PostgreSQL + pgvector **desde el inicio**. No se construye
  un vector store en archivos ni una capa de migración archivo→DB. Esto elimina
  el trabajo de migración de la fase 6.
- **LLM:** un proveedor *hosted* como default (Claude u OpenAI), detrás de una
  interfaz única de proveedor. Un modelo local queda como opción futura, no para
  el demo.
- **Despliegue:** un destino público (Fly.io, Render, Railway o un VPS pequeño).
  Una sola imagen Docker + `docker-compose`.
- **Alcance de acceso:** single-user, single-tenant. **No** se implementa
  autorización por usuario que replique los permisos de Jira.

### 2bis.3. Milestones

| Milestone | Contenido | Fases de referencia | Resultado |
|---|---|---|---|
| **A - Mini RAG demoable** | Fijar dependencias + `.env.example` + `sample_data` pequeño; tests solo de las transformaciones de mayor riesgo; chunking desde JSON normalizado → embeddings → **Postgres/pgvector**; RAG con LLM hosted (citas + abstención + prompt resistente a injection + **multi-turno**); FastAPI delgada (`/search`, `/rag/query` con **streaming**); UI de chat React mínima con fuentes expandibles y enlaces "abrir en Jira" | 0 (parcial), 4, 5 (parcial), 7 (slice) | Demo visible y honesta cuanto antes |
| **B - Retrieval con calidad** | Dataset de evaluación **sintético** sobre `sample_data`; métricas (Recall@K, MRR); ranking literal BM25; calibración de pesos híbridos; umbral de relevancia; iteración de chunking | 3 | Probar y mejorar la calidad de respuesta |
| **C - Confiabilidad y publicación** | Paginación completa correcta; sync incremental más liviano; CI (lint + tests); logs estructurados; **Dockerfile + compose + despliegue a una URL** | 1 (parcial), 2, 8 (parcial) | Robusto y compartible |
| **D - Stretch opcional** | Adjuntos/OCR; auth y multiusuario; reranking / expansión de consultas; monitoreo | 5, 6, 8, 9, 10 | Trabajo P2/P3, genuinamente opcional |

### 2bis.4. Recortes y diferimientos respecto de las fases 0-10

- **Fase 0:** probar solo las transformaciones de mayor riesgo (ADF→texto,
  normalización, detección de cambios, chunking determinístico). No exigir 80%
  de cobertura como compuerta antes del demo.
- **Fase 1:** conservar **paginación completa** (es corrección real). Diferir los
  watermarks con solapamiento, los tombstones de issues eliminadas y la
  reanudación a mitad de proceso; para un dataset de portfolio, re-sincronizar
  desde cero es aceptable.
- **Fase 5:** diferir la autorización por usuario que replica permisos de Jira,
  los workers asíncronos y las dead-letter queues.
- **Fase 6:** **sin migración**; Postgres/pgvector desde el inicio (ver 2bis.2).
- **Fase 8:** una sola imagen + compose + URL. Diferir gestor de secretos,
  dashboards, threat modeling y drills de backup/restore.

### 2bis.5. Adiciones (brechas no cubiertas por las fases 0-10)

- **Chatbot multi-turno:** historial de conversación + **condensación de la
  pregunta** (reescribir "¿y el segundo?" como una consulta autónoma usando los
  turnos previos). La fase 4 trata el RAG como pregunta→respuesta de un solo
  turno; "chatbot interactivo" exige multi-turno.
- **Streaming de tokens:** forma parte del slice de frontend del Milestone A, no
  es una optimización P3. Un chat que se congela 15s y luego vuelca un muro de
  texto se percibe roto (reclasifica el ítem de la fase 10).
- **Dataset de evaluación sintético:** construido a mano contra `sample_data`
  (preguntas, relevancias y respuestas esperadas), porque todavía no hay
  usuarios reales que aporten preguntas (ajusta 10.1).
- **Mitigación explícita de prompt injection:** el contenido de tickets se
  inyecta en bloques de contexto claramente delimitados; las instrucciones viven
  solo en el system prompt; el modelo nunca trata el texto de tickets como
  comandos; las citas se validan contra fuentes realmente recuperadas (la fase
  11.4 ya cubre la validación de citas).

### 2bis.6. Riesgo principal del enfoque y mitigación

Un demo pulido que da respuestas sutilmente incorrectas es **peor** para un
portfolio que no tener demo. **Mitigación:** mantener citas + abstención desde
el Milestone A (toda respuesta muestra fuentes o admite que no las hay) y **no
omitir** el Milestone B (evaluación) — solo se ejecuta después de que el slice
existe, no como compuerta previa.

---

## 3. Estado actual verificado

### 3.1. Capacidades implementadas

| Área | Estado | Evidencia actual |
|---|---|---|
| Conexión read-only con Jira | Implementada | Las integraciones usan solicitudes `GET` |
| Discovery de campos | Implementado | `jira_discovery.py` y `jira_full_discovery.py` |
| Sincronización full | Implementada con límites | `sync_jira.py --mode full` |
| Sincronización incremental | Implementada con límites | Usa `last_successful_sync` o `--since` |
| Persistencia raw | Implementada | Un JSON por issue en `data/raw/` |
| Detección de cambios | Implementada | SHA-256 del archivo raw completo |
| Normalización | Implementada | Contrato JSON local por issue |
| Markdown por issue | Implementado | Documento determinístico por issue |
| Chunking temático | Implementado | General, descripción, comentarios y relaciones |
| Búsqueda literal | Implementada | Ranking heurístico local |
| Embeddings locales | Implementados | Modelo multilingüe de `sentence-transformers` |
| Búsqueda semántica | Implementada como prototipo | Similitud coseno en memoria |
| Búsqueda híbrida | Implementada como prototipo | Combinación ponderada literal-semántica |
| Orquestación | Implementada | Pipeline por subprocesos |
| Logs de pipeline | Implementados | JSON por corrida |

### 3.2. Brechas verificadas

| Área | Brecha actual | Consecuencia |
|---|---|---|
| Pruebas | No hay tests automatizados | Los cambios pueden romper contratos sin aviso |
| Datos de muestra | No existe `sample_data/` versionado | No hay forma reproducible de probar sin Jira real |
| Configuración | No existe `.env.example` | El onboarding depende de documentación manual |
| Dependencias | Versiones sin fijar | Una instalación futura puede comportarse distinto |
| Paginación | `--max-results` limita la búsqueda | Un full sync puede no ser realmente completo |
| TLS | Jira se consulta con `verify=False` | Riesgo de seguridad y de operación |
| Resiliencia HTTP | No hay estrategia común de retry/backoff | Fallos transitorios pueden cortar una corrida |
| Rate limiting | No hay manejo explícito de `429` | Una carga grande puede fallar |
| Campos custom | IDs escritos en código | Cambiar de instancia requiere modificar código |
| Eliminaciones | No se limpian issues o artefactos obsoletos | La base puede conservar información desactualizada |
| Atomicidad | Las escrituras reemplazan archivos directamente | Una interrupción puede dejar artefactos inconsistentes |
| Embeddings | Se reconstruyen completos y fuera del pipeline | El índice puede quedar desactualizado |
| Retrieval | No existe dataset ni métricas de evaluación | No se conoce la calidad real de las búsquedas |
| Relevancia | No hay umbral mínimo | Se pueden mostrar resultados poco relacionados |
| Búsqueda híbrida | Pesos no validados y lógica duplicada | Resultados difíciles de calibrar y mantener |
| Escalabilidad | Todo se carga en memoria | El costo crece con la cantidad de chunks |
| RAG | No existe capa LLM ni generación con fuentes | Aún no se responden preguntas |
| Servicio | No existe API | Las capacidades solo se consumen por CLI |
| Persistencia | Solo archivos locales | Concurrencia, consulta y auditoría son limitadas |
| Operación | No hay CI, scheduler ni monitoreo | El sistema depende de ejecución manual |
| Seguridad funcional | No hay modelo de permisos por usuario | Una futura API podría exponer información indebida |
| Adjuntos | Solo se conserva metadata | No se aprovecha el contenido de archivos o imágenes |

### 3.3. Restricciones que deben conservarse

Durante toda la evolución se deben mantener estas reglas:

- Jira continúa siendo una fuente **read-only**.
- Cada resultado y respuesta debe conservar referencias a Jira.
- Los datos reales de Jira no se versionan.
- El sistema debe poder decir que no encontró evidencia suficiente.
- Las inferencias deben distinguirse de los hechos extraídos.
- La evolución no debe impedir seguir usando el flujo local por CLI.

---

## 4. Objetivo técnico final

La meta es disponer de una plataforma de consulta sobre conocimiento histórico
de Jira con esta arquitectura lógica:

```text
Jira Cloud
    -> servicio de sincronización read-only
    -> almacenamiento raw auditable
    -> normalización versionada
    -> generación de chunks
    -> índice literal + índice vectorial
    -> servicio de retrieval híbrido
    -> generador RAG con citas
    -> API autenticada
    -> interfaz de búsqueda y chat
    -> observabilidad, evaluación y auditoría
```

### 4.1. Definición de éxito del producto

El sistema se considerará útil cuando pueda responder preguntas como:

- qué ocurrió con una funcionalidad;
- qué issue explica una decisión;
- si un incidente ya había ocurrido;
- qué comentarios describen una solución;
- qué se trabajó en un sprint;
- quién participó o resolvió una tarjeta;

y cumplir simultáneamente estas condiciones:

- mostrar evidencia concreta;
- enlazar las issues utilizadas;
- abstenerse cuando no existe contexto suficiente;
- aplicar permisos equivalentes a los del usuario;
- registrar cómo se construyó cada respuesta;
- mantener información actualizada mediante sincronización incremental.

### 4.2. Indicadores objetivo iniciales

Los valores definitivos se calibrarán con datos reales, pero se propone iniciar
con los siguientes objetivos:

| Indicador | Objetivo inicial |
|---|---:|
| Éxito de corridas incrementales | Mayor o igual a 99% |
| Issues sincronizadas sin pérdida por paginación | 100% del alcance configurado |
| Tests del núcleo de transformación | Mayor o igual a 80% de cobertura útil |
| Recall@10 del retrieval sobre dataset evaluado | Mayor o igual a 85% |
| Respuestas RAG con al menos una fuente válida | 100% |
| Respuestas sin soporte presentadas como hechos | 0% en evaluación controlada |
| Consultas API de búsqueda p95 | Menor a 2 segundos, sin contar generación LLM |
| Respuestas RAG p95 | Objetivo inicial menor a 15 segundos |

---

## 5. Principios de ejecución

### 5.1. Calidad antes que superficie

No se debe agregar frontend, múltiples proveedores LLM o procesamiento de
imágenes antes de poder medir el retrieval y verificar los contratos del
pipeline.

> **Ajuste del track de portfolio:** este principio se relaja de forma acotada.
> Se adelanta un *slice* de frontend (UI de chat mínima) tras un Mini RAG
> básico, pero solo uno: nada de múltiples proveedores LLM ni de procesamiento
> de imágenes antes de la evaluación. Las garantías que sustituyen a "medir
> primero" son citas y abstención obligatorias desde ese primer slice.

### 5.2. Evolución incremental

Cada fase debe dejar una versión utilizable. La migración a servicios y base de
datos no debe requerir reescribir toda la lógica de dominio.

### 5.3. Contratos explícitos

Raw, issue normalizada, chunk, resultado de búsqueda, fuente y respuesta RAG
deben tener esquemas versionados.

### 5.4. Seguridad por diseño

Las credenciales, permisos, logs y datos sensibles deben tratarse como parte de
la arquitectura, no como tareas finales.

### 5.5. Evaluación continua

Cada mejora de chunking, embeddings, ranking o prompting debe compararse contra
un dataset estable. No se debe decidir calidad solo mirando ejemplos aislados.

---

## 6. Priorización general

| Prioridad | Significado |
|---|---|
| P0 | Necesario para confiar en el prototipo y continuar |
| P1 | Necesario para entregar un Mini RAG sólido |
| P2 | Necesario para convertirlo en producto interno |
| P3 | Optimización, escala avanzada o capacidad complementaria |

| Fase | Prioridad | Resultado principal |
|---|---|---|
| 0. Baseline reproducible | P0 | Proyecto instalable, comprobable y medible |
| 1. Sincronización confiable | P0 | Ingesta completa, segura y resiliente |
| 2. Contratos y pipeline mantenible | P0 | Núcleo estable con pruebas |
| 3. Retrieval evaluable | P1 | Búsqueda con calidad medida |
| 4. Mini RAG trazable | P1 | Respuestas fundamentadas con fuentes |
| 5. API de aplicación | P2 | Capacidades consumibles como servicio |
| 6. PostgreSQL y pgvector | P2 | Persistencia robusta y escalable |
| 7. Frontend | P2 | Experiencia de búsqueda y chat |
| 8. Operación y seguridad productiva | P2 | Servicio observable y gobernado |
| 9. Adjuntos e imágenes | P3 | Conocimiento adicional desde archivos |
| 10. Optimización avanzada | P3 | Mejor calidad, escala y costo |

---

## 7. Fase 0 - Baseline reproducible

**Prioridad:** P0  
**Objetivo:** poder instalar, ejecutar, probar y comparar el proyecto sin
depender de una instancia Jira real ni de conocimiento implícito.

### 7.1. Inventario y decisiones de arquitectura

- Crear un registro breve de decisiones técnicas importantes.
- Documentar qué partes continuarán como scripts y cuáles pasarán a módulos.
- Definir Python mínimo soportado.
- Definir estrategia de configuración por entorno.
- Definir el contrato de compatibilidad del CLI existente.
- Acordar qué significa full sync: últimas N issues o totalidad del proyecto.

**Entregable:** documento de decisiones iniciales y alcance confirmado.

### 7.2. Configuración reproducible

- Agregar `.env.example` sin secretos.
- Validar URLs, project key y parámetros obligatorios al inicio.
- Separar configuración de Jira, embeddings, almacenamiento y futuro LLM.
- Permitir configurar validación TLS y certificado corporativo.
- Fijar versiones de dependencias directas.
- Definir procedimiento de actualización de dependencias.

**Criterio de aceptación:** una persona nueva puede instalar y ejecutar los
comandos documentados siguiendo únicamente el repositorio.

### 7.3. Dataset ficticio y anonimizado

- Crear issues raw ficticias que representen casos frecuentes.
- Incluir descripción ADF, comentarios, links, subtareas, adjuntos y changelog.
- Incluir casos incompletos: campos nulos, usuarios eliminados y descripciones
  vacías.
- Incluir una issue actualizada y una issue removida para probar incremental.
- Generar resultados esperados normalizados, Markdown y chunks.
- Verificar que ningún dato real aparezca en la muestra.

**Entregable:** `sample_data/` utilizable por tests y demostraciones.

### 7.4. Suite mínima de pruebas

- Configurar `pytest`.
- Probar conversión ADF a texto.
- Probar normalización de usuarios, comentarios, sprint, links y changelog.
- Probar detección de issues cambiadas y no cambiadas.
- Probar generación determinística de Markdown y chunks.
- Probar filtros y ranking literal básico.
- Agregar un smoke test del pipeline sin red usando fixtures.

**Criterio de salida de fase:** el pipeline local puede verificarse sin Jira y
los contratos existentes quedan protegidos por tests.

---

## 8. Fase 1 - Sincronización Jira confiable

**Prioridad:** P0  
**Objetivo:** garantizar que la base local representa correctamente el alcance
configurado de Jira y que los fallos transitorios no producen estados falsos.

### 8.1. Cliente Jira común

- Extraer autenticación, headers, timeout y manejo de errores a un cliente
  reutilizable.
- Mantener una lista explícita de operaciones permitidas y limitarla a `GET`.
- Implementar retry con backoff para errores transitorios.
- Respetar `Retry-After` ante rate limiting.
- Clasificar errores de autenticación, permisos, red y respuesta inválida.
- Evitar imprimir credenciales o parámetros sensibles.
- Habilitar validación TLS por defecto.
- Permitir CA corporativa configurable sin usar `verify=False`.

**Criterio de aceptación:** un error transitorio recuperable no invalida toda la
corrida y un error permanente queda explicado en el log.

### 8.2. Paginación completa

- Implementar paginación sobre la búsqueda JQL.
- Diferenciar `page_size` de un límite opcional de seguridad.
- Registrar total informado por Jira, total recorrido y total persistido.
- Detectar respuestas parciales o cambios de cursor.
- Probar proyectos con más issues que el tamaño de página.

**Criterio de aceptación:** un full sync puede recorrer la totalidad del
proyecto configurado sin pérdida silenciosa.

### 8.3. Ventana incremental robusta

- Guardar el inicio de la corrida antes de consultar Jira.
- Usar una ventana con solapamiento para evitar perder cambios por precisión de
  fechas, latencia o reloj.
- Actualizar `last_successful_sync` únicamente después de persistir todo.
- Registrar el watermark usado y el próximo watermark.
- Hacer idempotente la repetición de una corrida incremental.
- Probar una falla a mitad de proceso y su posterior reanudación.

**Criterio de aceptación:** repetir un incremental no pierde datos ni genera
inconsistencias.

### 8.4. Persistencia raw segura

- Escribir archivos temporalmente y reemplazarlos de forma atómica.
- Guardar metadata de ingesta: fecha, endpoint, versión y checksum.
- Definir retención de raws históricos o snapshots si se necesita auditoría.
- Detectar JSON inválido antes de reemplazar una copia válida.
- Separar claramente muestras de discovery y raws del pipeline.

### 8.5. Issues removidas o fuera de alcance

- Definir el significado de una issue ausente: eliminada, sin permisos o fuera
  del JQL.
- Registrar tombstones o estado de baja.
- Retirar o marcar como obsoletos normalized, Markdown, chunks y embeddings.
- Evitar presentar contenido removido como vigente.

**Criterio de salida de fase:** la sincronización es completa, segura,
reanudable, auditable y coherente frente a altas, cambios y bajas.

---

## 9. Fase 2 - Contratos y pipeline mantenible

**Prioridad:** P0  
**Objetivo:** convertir los scripts actuales en un núcleo reutilizable,
versionado y verificable, conservando los comandos existentes.

### 9.1. Separación entre dominio y CLI

- Mover lógica reutilizable a módulos importables.
- Mantener scripts CLI pequeños como adaptadores.
- Eliminar duplicación de carga de chunks, filtros y normalización de texto.
- Centralizar rutas y configuración.
- Evitar que importar un módulo cree directorios o cargue configuración.

**Resultado esperado:** búsqueda, pipeline y futura API utilizan las mismas
funciones de dominio.

### 9.2. Esquemas versionados

- Definir esquemas para issue raw metadata, issue normalizada, chunk, índice,
  resultado de búsqueda, fuente y log.
- Agregar `schema_version` a artefactos persistidos.
- Validar entradas antes de procesarlas.
- Definir política de migración cuando cambie un contrato.
- Documentar campos obligatorios, opcionales y derivados.

### 9.3. Campos custom configurables

- Extraer IDs de sprint, GLPI y área de enfoque a configuración.
- Permitir mapear campos por ID y, cuando sea seguro, por discovery.
- Validar que los campos configurados existan.
- Registrar campos desconocidos o incompatibles.
- Probar una segunda configuración de Jira ficticia.

### 9.4. Pipeline coherente

- Ejecutar etapas mediante funciones o una interfaz común, no solo subprocesos.
- Definir estados de corrida y etapa.
- Registrar conteos de entrada, éxito, omisión y error.
- Permitir reintentar una etapa sin repetir toda la sincronización.
- Incorporar opcionalmente embeddings al pipeline.
- Evitar publicar un índice nuevo hasta terminar su construcción.
- Definir códigos de salida consistentes.

### 9.5. Observabilidad básica

- Estandarizar logs estructurados.
- Incluir `run_id`, `issue_key`, etapa, duración y tipo de error.
- Incorporar métricas de volumen y tiempo por etapa.
- Definir mensajes aptos para diagnóstico sin exponer contenido sensible.

### 9.6. Integración continua

- Ejecutar lint, tests y validación de contratos en cada cambio.
- Comprobar que no se versionen secretos ni datos reales.
- Ejecutar smoke tests en versiones de Python soportadas.
- Verificar documentación y ejemplos esenciales.

**Criterio de salida de fase:** el núcleo tiene contratos explícitos, tests
automatizados, CI y una estructura reutilizable por CLI, API y jobs.

---

## 10. Fase 3 - Retrieval evaluable y de calidad

**Prioridad:** P1  
**Objetivo:** saber de forma objetiva si el sistema recupera la evidencia
correcta antes de conectar un LLM.

### 10.1. Dataset de evaluación

- Reunir preguntas representativas del equipo sin datos sensibles públicos.
  En el track de portfolio no hay usuarios reales todavía: el dataset se
  **autoría a mano contra `sample_data`** (preguntas, relevancias y respuestas
  esperadas), ver 2bis.5.
- Clasificar preguntas por tipo: issue exacta, sprint, persona, incidente,
  decisión, comentario, relación e historial.
- Etiquetar issues y chunks relevantes para cada pregunta.
- Incluir consultas sin respuesta.
- Incluir sinónimos, abreviaturas, errores ortográficos y mezcla de idiomas.
- Separar un conjunto de calibración y otro de validación.

**Entregable:** dataset versionado de preguntas, relevancias y respuestas
esperadas cuando corresponda.

### 10.2. Métricas de retrieval

- Medir Recall@K, Precision@K, MRR y nDCG.
- Medir resultados por categoría de pregunta.
- Medir cuántas consultas sin respuesta superan el umbral.
- Registrar latencia y uso de memoria.
- Crear un reporte comparable entre versiones.

### 10.3. Mejora del chunking

- Revisar tamaño real de chunks y distribución por tipo.
- Evitar chunks demasiado largos, vacíos o redundantes.
- Dividir comentarios extensos conservando autor y fecha.
- Dividir historiales extensos sin perder orden temporal.
- Incorporar contexto mínimo común: issue key, título y estado.
- Evitar repetir metadata innecesaria dentro del texto embebido.
- Definir IDs estables para actualizaciones incrementales.

### 10.4. Mejora del ranking literal

- Sustituir conteos simples por una estrategia tipo BM25 o equivalente.
- Mantener boosts explícitos para issue key, GLPI y título.
- Soportar coincidencias exactas y frases.
- Normalizar acentos y Unicode correctamente.
- Configurar stopwords por idioma.
- Explicar por qué un resultado obtuvo su score.

### 10.5. Mejora del ranking semántico

- Evaluar el modelo actual contra alternativas multilingües.
- Versionar nombre de modelo y parámetros junto al índice.
- Agregar umbral mínimo calibrado.
- Detectar incompatibilidad entre índice y modelo.
- Implementar actualización incremental de embeddings.
- Evaluar la necesidad de reranking sobre los mejores candidatos.

### 10.6. Búsqueda híbrida unificada

- Definir una interfaz única de búsqueda.
- Validar y normalizar pesos.
- Calibrar pesos usando el dataset, no intuición.
- Permitir filtros combinados y rangos de fechas.
- Deduplicar resultados de una misma issue cuando corresponda.
- Definir diversidad de chunks para aportar contexto complementario.
- Devolver resultados estructurados, no solo texto de consola.

**Criterio de salida de fase:** existe una configuración de retrieval elegida
por métricas, con umbrales y resultados estructurados reutilizables.

---

## 11. Fase 4 - Mini RAG trazable

**Prioridad:** P1  
**Objetivo:** responder preguntas usando únicamente evidencia recuperada y
mostrar las fuentes que respaldan cada respuesta.

> **Ajuste del track de portfolio:** para el chatbot esta fase debe ser
> **multi-turno**, no de un solo turno. Añadir historial de conversación y
> condensación de la pregunta (ver 2bis.5). Fijar un LLM hosted por defecto
> (Claude u OpenAI) detrás de la interfaz de proveedor de 11.3, y tratar la
> mitigación de prompt injection de 11.2 como requisito, no como nota.

### 11.1. Contrato de respuesta RAG

Definir una respuesta estructurada con:

- respuesta final;
- fuentes utilizadas;
- issue key y URL de cada fuente;
- chunk o fragmento relacionado;
- nivel de confianza o estado de evidencia;
- advertencias;
- hechos explícitos;
- inferencias claramente identificadas;
- información faltante.

### 11.2. Construcción de contexto

- Recuperar candidatos mediante búsqueda híbrida.
- Aplicar umbral mínimo.
- Deduplicar contenido repetido.
- Priorizar diversidad entre descripción, comentarios e historial.
- Limitar contexto según presupuesto de tokens.
- Conservar metadata necesaria para citas.
- Evitar incluir instrucciones potencialmente maliciosas desde tickets.

### 11.3. Integración con LLM

- Definir una interfaz de proveedor independiente.
- Configurar modelo, temperatura, timeout y límites.
- Separar prompt de sistema, pregunta y contexto.
- Exigir abstención cuando la evidencia no alcanza.
- Exigir referencias a fuentes válidas.
- Evitar que el modelo invente URLs o issue keys.
- Registrar versión de prompt y modelo por respuesta.

### 11.4. Validación posterior

- Verificar que cada cita corresponda a una fuente recuperada.
- Rechazar referencias inventadas.
- Detectar respuestas vacías o sin fuentes.
- Marcar claramente las respuestas parciales.
- Aplicar reglas para datos personales y contenido sensible.

### 11.5. Evaluación del RAG

- Medir fidelidad a fuentes.
- Medir completitud de la respuesta.
- Medir calidad de citas.
- Medir tasa de abstención correcta.
- Medir alucinaciones o afirmaciones no respaldadas.
- Revisar manualmente un conjunto fijo antes de cada release.

### 11.6. CLI inicial

- Agregar un comando de consulta RAG.
- Permitir modo de depuración que muestre retrieval y contexto.
- Permitir consultar sin invocar LLM para comparar resultados.
- Mostrar links de Jira de forma clara.

**Criterio de salida de fase:** el sistema responde el conjunto evaluado con
fuentes válidas, se abstiene ante consultas sin evidencia y conserva trazas
suficientes para auditar cada respuesta.

---

## 12. Fase 5 - API de aplicación

**Prioridad:** P2  
**Objetivo:** exponer sincronización, búsqueda y RAG como capacidades estables
para otros clientes.

### 12.1. Alcance inicial de API

Endpoints recomendados:

```text
GET  /health
GET  /ready
GET  /issues/{issue_key}
POST /search
POST /rag/query
POST /sync
GET  /sync/runs/{run_id}
GET  /metrics/summary
```

### 12.2. Reglas de diseño

- Usar contratos versionados.
- Separar respuestas de dominio de detalles internos.
- Validar filtros y límites.
- Incorporar paginación de resultados.
- Definir errores estables.
- Agregar IDs de correlación.
- Establecer timeout y cancelación de consultas.
- Documentar API mediante OpenAPI.

### 12.3. Autenticación y autorización

- Elegir proveedor de identidad.
- Autenticar usuarios y servicios.
- Definir roles administrativos y de consulta.
- Preparar autorización por proyecto Jira.
- Diseñar cómo reflejar permisos de Jira antes de habilitar múltiples usuarios.
- Auditar consultas sensibles y ejecuciones de sync.

### 12.4. Procesamiento asíncrono

- Ejecutar sync, embeddings y tareas extensas fuera del request HTTP.
- Exponer estado y progreso.
- Evitar dos full sync simultáneos sobre el mismo proyecto.
- Definir reintentos y manejo de trabajos fallidos.

**Criterio de salida de fase:** un cliente externo puede consultar, buscar y
usar RAG mediante una API documentada, autenticada y observable.

---

## 13. Fase 6 - PostgreSQL y pgvector

**Prioridad:** P2  
**Objetivo:** reemplazar las limitaciones de archivos locales para operación
multiusuario, consulta flexible y escala.

> **Ajuste del track de portfolio:** no hay migración. Postgres + pgvector se
> adoptan desde el inicio (decisión 2bis.2), por lo que las tareas de esta fase
> orientadas a *migrar desde archivos con paridad e importador* no aplican; solo
> aplican el modelo de datos, los índices y la integridad.

### 13.1. Modelo de datos

Entidades iniciales:

- proyectos Jira;
- issues;
- versiones o snapshots raw;
- comentarios;
- adjuntos;
- relaciones;
- subtareas;
- eventos de historial;
- chunks;
- embeddings;
- corridas de sincronización;
- etapas de pipeline;
- consultas;
- respuestas RAG;
- fuentes utilizadas;
- feedback de usuarios.

### 13.2. Estrategia de migración

- Mantener archivos como opción local durante la transición.
- Definir interfaces de repositorio para desacoplar almacenamiento.
- Crear importador de artefactos existentes.
- Comparar resultados entre archivos y PostgreSQL.
- Ejecutar migraciones versionadas.
- Definir backup, restauración y retención.

### 13.3. Índices y búsqueda

- Usar índices relacionales para filtros exactos.
- Usar full-text search para señal literal.
- Usar pgvector para embeddings.
- Implementar búsqueda híbrida en una capa de retrieval única.
- Medir planes de consulta y latencia.
- Definir actualización y eliminación incremental de vectores.

### 13.4. Integridad

- Usar transacciones para publicar cambios coherentes.
- Garantizar unicidad de issue, chunk y versión.
- Marcar contenido obsoleto.
- Mantener trazabilidad entre raw, normalized, chunk y embedding.

**Criterio de salida de fase:** PostgreSQL soporta el flujo completo con
resultados equivalentes o mejores que el almacenamiento local y con migración
reproducible.

---

## 14. Fase 7 - Frontend

**Prioridad:** P2  
**Objetivo:** ofrecer una experiencia usable para explorar evidencia y hacer
preguntas sin ocultar la trazabilidad.

### 14.1. Experiencias principales

- Buscador con resultados y filtros.
- Vista documental de una issue.
- Chat RAG con fuentes expandibles.
- Navegación entre issues relacionadas.
- Vista de historial y comentarios relevantes.
- Estado de sincronización para administradores.

### 14.2. Diseño de confianza

- Mostrar fuentes junto a cada respuesta.
- Permitir abrir la issue original en Jira.
- Diferenciar hechos, inferencias y ausencia de información.
- Mostrar cuándo se sincronizó por última vez.
- Permitir inspeccionar los fragmentos recuperados.
- Recoger feedback positivo, negativo y motivo.

### 14.3. Filtros iniciales

- proyecto;
- estado;
- sprint;
- responsable;
- tipo de issue;
- rango de fechas;
- tipo de chunk;
- presencia de adjuntos;
- issue key o ticket GLPI.

### 14.4. Accesibilidad y estados

- Diseñar estados de carga, error, falta de resultados y falta de permisos.
- Evitar presentar una respuesta parcial como completa.
- Soportar teclado y lectores de pantalla.
- Mantener URLs navegables para búsquedas e issues.

**Criterio de salida de fase:** usuarios piloto pueden resolver consultas reales
y validar las fuentes sin utilizar scripts ni acceder a archivos locales.

---

## 15. Fase 8 - Operación y seguridad productiva

**Prioridad:** P2  
**Objetivo:** ejecutar el sistema periódicamente con seguridad, diagnóstico y
procedimientos operativos claros.

### 15.1. Empaquetado y entornos

- Crear imágenes Docker reproducibles.
- Separar API, worker y scheduler.
- Definir configuración por desarrollo, prueba y producción.
- Ejecutar migraciones y checks de readiness.
- Evitar incluir secretos o datos en imágenes.

### 15.2. Scheduling y workers

- Programar incrementales frecuentes.
- Programar reconciliaciones full controladas.
- Separar sincronización, procesamiento y embeddings.
- Aplicar locks por proyecto.
- Definir dead-letter o manejo equivalente para trabajos fallidos.

### 15.3. Secretos y red

- Usar gestor de secretos.
- Rotar API tokens.
- Restringir salida de red a servicios necesarios.
- Validar TLS.
- Cifrar datos en tránsito y reposo.
- Definir acceso administrativo.

### 15.4. Observabilidad

- Métricas de corridas, errores, latencia, volumen y costo.
- Alertas por sync fallido, índice desactualizado y degradación de retrieval.
- Trazas entre pregunta, retrieval, LLM y respuesta.
- Dashboards operativos.
- Logs con retención y redacción de información sensible.

### 15.5. Gobierno y cumplimiento

- Definir retención y eliminación de datos.
- Auditar accesos y consultas.
- Documentar tratamiento de datos personales.
- Establecer procedimiento ante revocación de permisos.
- Realizar threat modeling.
- Probar recuperación ante fallos y restauración de backups.

### 15.6. Control de costos

- Registrar consumo de embeddings y LLM.
- Definir límites por usuario o equipo.
- Cachear respuestas cuando sea apropiado.
- Evitar regenerar embeddings sin cambios.
- Alertar desviaciones de costo.

**Criterio de salida de fase:** el sistema puede operar de forma programada,
segura y observable, con procedimientos claros ante fallos.

---

## 16. Fase 9 - Adjuntos e imágenes

**Prioridad:** P3  
**Objetivo:** incorporar conocimiento presente en capturas, PDFs y otros
adjuntos sin degradar seguridad ni trazabilidad.

### 16.1. Descarga controlada

- Definir tipos MIME permitidos.
- Aplicar límites de tamaño.
- Validar contenido real del archivo.
- Almacenar checksum y metadata.
- Evitar descargas repetidas.
- Analizar archivos en un entorno aislado.

### 16.2. Extracción de contenido

- Extraer texto de PDFs y documentos permitidos.
- Ejecutar OCR sobre imágenes relevantes.
- Evaluar análisis multimodal para capturas técnicas.
- Conservar referencia a archivo, página o región.
- Marcar texto extraído y análisis generado como datos derivados.

### 16.3. Indexación

- Crear chunks específicos por adjunto.
- Vincularlos a issue, archivo y ubicación.
- Evitar indexar contenido duplicado.
- Evaluar retrieval con y sin adjuntos.
- Permitir excluir adjuntos sensibles.

**Criterio de salida de fase:** el contenido extraído mejora métricas de
retrieval y cada fragmento conserva referencia verificable al adjunto original.

---

## 17. Fase 10 - Optimización avanzada

**Prioridad:** P3  
**Objetivo:** mejorar calidad, escala y costo una vez estabilizado el producto.

> **Ajuste del track de portfolio:** el *streaming de respuestas* de la lista de
> abajo **no** es P3; se adelanta al slice de frontend del Milestone A por ser
> UX básica de un chat (ver 2bis.5). El resto de esta fase permanece como
> stretch opcional (Milestone D).

Posibles líneas de trabajo:

- reranking especializado;
- expansión o reescritura de consultas;
- búsqueda por entidades y relaciones;
- grafo de issues, personas, sprints y componentes;
- resúmenes incrementales por issue;
- respuestas comparativas entre períodos;
- detección de incidentes similares;
- evaluación automática asistida por LLM con revisión humana;
- múltiples proyectos e instancias Jira;
- modelos de embeddings por dominio;
- caché semántica;
- streaming de respuestas;
- alta disponibilidad;
- particionamiento y archivado histórico.

Estas tareas deben incorporarse únicamente cuando una métrica, un problema de
escala o una necesidad de usuario justifique su costo.

---

## 18. Releases recomendados

### Release R0 - Prototipo reproducible

Incluye fases 0 y parte de 1.

**Promesa:** el proyecto puede instalarse y probarse sin Jira real.

### Release R1 - Pipeline confiable

Incluye fases 1 y 2.

**Promesa:** Jira se sincroniza de manera completa, segura, repetible y
verificable.

### Release R2 - Search Quality

Incluye fase 3.

**Promesa:** la búsqueda híbrida tiene calidad medida y configuración
calibrada.

### Release R3 - Mini RAG

Incluye fase 4.

**Promesa:** el sistema responde con evidencia y se abstiene cuando corresponde.

### Release R4 - Servicio interno

Incluye fases 5 y 6.

**Promesa:** las capacidades están disponibles mediante API y persistencia
robusta.

### Release R5 - Producto piloto

Incluye fases 7 y los controles esenciales de 8.

**Promesa:** usuarios piloto pueden consultar el sistema con permisos,
trazabilidad y feedback.

### Release R6 - Producción y expansión

Completa fase 8 e incorpora fases 9 y 10 según necesidad.

**Promesa:** operación gobernada y evolución basada en métricas.

---

## 19. Dependencias críticas

```text
Tests y sample data
    -> refactor seguro
    -> contratos estables
    -> retrieval medible
    -> RAG confiable
    -> API estable
    -> frontend útil
```

```text
Cliente Jira robusto
    -> sync completo
    -> incremental confiable
    -> índice actualizado
    -> respuestas vigentes
```

```text
Autenticación y modelo de permisos
    -> API multiusuario
    -> frontend
    -> despliegue productivo
```

No se recomienda invertir de manera significativa en frontend antes de cerrar
la evaluación de retrieval y el contrato de respuesta RAG.

---

## 20. Riesgos principales y mitigación

| Riesgo | Impacto | Mitigación propuesta |
|---|---|---|
| Resultados convincentes pero incorrectos | Alto | Dataset evaluado, citas obligatorias y abstención |
| Pérdida de issues por paginación o incremental | Alto | Paginación completa, watermarks y reconciliación |
| Exposición de información sensible | Alto | Permisos, secretos, auditoría y redacción de logs |
| Índice desactualizado | Alto | Versionado, publicación atómica y monitoreo |
| Dependencia de campos custom | Medio | Configuración y validación por instancia |
| Costos LLM inesperados | Medio | Métricas, límites, caché y modelos configurables |
| Crecimiento de volumen | Medio | PostgreSQL, pgvector e indexación incremental |
| Cambios en Jira API | Medio | Cliente aislado, contratos y tests de integración |
| Complejidad prematura | Medio | Releases incrementales y criterios de salida |
| Falta de preguntas reales para evaluar | Alto | Involucrar usuarios desde la fase de dataset |

---

## 21. Criterios transversales de terminado

Una tarea técnica no debería considerarse terminada solo porque funciona en una
ejecución manual. Para cerrar trabajo relevante se debe comprobar:

- comportamiento esperado documentado;
- tests acordes al riesgo;
- manejo de errores;
- logs y métricas suficientes;
- ausencia de secretos y datos reales versionados;
- compatibilidad o migración de contratos;
- procedimiento de operación;
- criterios de aceptación demostrables;
- actualización de documentación;
- impacto sobre seguridad y permisos.

---

## 22. Próximo bloque de trabajo recomendado

El siguiente bloque debería concentrarse exclusivamente en construir una base
confiable para continuar:

1. crear dataset ficticio representativo;
2. agregar `.env.example` y fijar dependencias;
3. incorporar tests del normalizador, chunks, cambios y búsqueda;
4. implementar cliente Jira común con TLS configurable y retries;
5. implementar paginación completa;
6. robustecer el watermark incremental;
7. versionar contratos normalizados y de chunks;
8. crear el primer dataset de evaluación de retrieval.

Al completar este bloque, el proyecto todavía no tendrá frontend ni chat, pero
sí tendrá algo más importante: una base confiable para construirlos y una forma
objetiva de saber si las siguientes mejoras realmente acercan al objetivo.

