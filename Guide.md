# Jira Knowledge RAG

Sistema experimental para extraer información de Jira, transformarla en documentación estructurada y prepararla para búsquedas inteligentes mediante técnicas de RAG.

El objetivo del proyecto es convertir tickets/issues de Jira en una base de conocimiento consultable, útil para reconstruir decisiones, historial, responsables, comentarios, adjuntos y trazabilidad de desarrollos.

---

## 1. Descripción general

**Jira Knowledge RAG** es un proyecto orientado a crear una capa de conocimiento sobre tableros de Jira.

El sistema permite:

* conectarse a Jira en modo solo lectura;
* extraer issues mediante la API oficial;
* normalizar campos relevantes;
* generar documentación Markdown por issue;
* dividir la información en chunks;
* realizar búsquedas locales por palabras clave;
* preparar embeddings para búsqueda semántica;
* sentar las bases para un futuro sistema RAG con LLM.

El proyecto nace como una prueba técnica para explorar cómo transformar información dispersa en tickets de Jira en una base documental más ordenada, consultable y aprovechable por IA.

---

## 2. Problema que busca resolver

En muchos equipos de desarrollo, gran parte del conocimiento queda distribuido en tarjetas de Jira:

* descripciones;
* comentarios;
* cambios de estado;
* adjuntos;
* subtareas;
* decisiones técnicas;
* bugs históricos;
* tickets relacionados;
* responsables;
* sprints;
* fechas;
* links con otras issues.

Con el tiempo, encontrar información se vuelve difícil.

Preguntas como estas suelen requerir revisar muchas tarjetas manualmente:

```text
¿Qué pasó con esta funcionalidad?
¿Quién resolvió este bug?
¿En qué sprint se trabajó?
¿Qué comentarios explican la solución?
¿Esta incidencia ya había ocurrido antes?
¿Qué tarjetas están relacionadas?
¿Qué adjuntos o capturas había en el ticket?
```

Este proyecto busca resolver ese problema generando una base de conocimiento estructurada sobre Jira.

---

## 3. Objetivos del proyecto

### Objetivos principales

* Extraer información de Jira de forma segura y read-only.
* Convertir issues en datos normalizados.
* Generar documentación Markdown automáticamente.
* Preparar chunks para búsqueda y RAG.
* Implementar búsqueda local sobre chunks.
* Implementar búsqueda semántica mediante embeddings.
* Diseñar una arquitectura escalable hacia un sistema con frontend, backend, base de datos y LLM.

### Objetivos secundarios

* Practicar integración con APIs externas.
* Diseñar pipelines de sincronización incremental.
* Implementar detección de cambios por hash.
* Construir una base sólida para un proyecto de portfolio.
* Explorar patrones reales de Retrieval-Augmented Generation.

---

## 4. Arquitectura conceptual

```text
Jira API
   |
   | read-only
   v
Issue Extractor
   |
   v
Raw JSON Storage
   |
   v
Normalizer
   |
   +----------------------+
   |                      |
   v                      v
Markdown Generator     Normalized JSON
   |
   v
Chunk Generator
   |
   v
Local Search / Semantic Search
   |
   v
Future RAG Layer
```

---

## 5. Flujo actual del sistema

El flujo actual es:

```text
1. Conectarse a Jira.
2. Buscar issues mediante JQL.
3. Obtener detalle completo de cada issue.
4. Guardar JSON crudo.
5. Normalizar campos importantes.
6. Generar Markdown por issue.
7. Generar chunks documentales.
8. Detectar cambios por hash.
9. Ejecutar pipeline full o incremental.
10. Buscar información sobre los chunks.
```

---

## 6. Modo read-only

El sistema está diseñado para operar en modo solo lectura.

Esto significa que únicamente utiliza operaciones de lectura contra Jira.

No realiza:

* creación de issues;
* edición de issues;
* cambio de estados;
* agregado de comentarios;
* eliminación de adjuntos;
* modificación de sprints;
* transición de tickets;
* escritura sobre Jira.

La idea es que Jira sea la fuente de información, no el destino de modificaciones.

---

## 7. Variables de entorno

El proyecto utiliza un archivo `.env` para configurar la conexión con Jira.

Ejemplo:

```env
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ
```

También se recomienda tener un archivo `.env.example`:

```env
JIRA_BASE_URL=
JIRA_EMAIL=
JIRA_API_TOKEN=
JIRA_PROJECT_KEY=
```

El archivo `.env` no debe subirse al repositorio.

---

## 8. Estructura del proyecto

```text
jira-knowledge-rag/
  data/
    raw/
    normalized/
    markdown/
    chunks/
    embeddings/
    fields/
    sync/
    hashes/
    logs/

  scripts/
    jira_discovery.py
    sync_jira.py
    detect_changed_issues.py
    normalize_issues.py
    generate_markdown.py
    generate_chunks.py
    search_chunks.py
    build_embeddings.py
    semantic_search.py
    hybrid_search.py
    pipeline.py

  sample_data/
    raw/
    normalized/
    markdown/
    chunks/

  .env.example
  .gitignore
  requirements.txt
  README.md
```

---

## 9. Componentes principales

### 9.1. Jira Discovery

Script inicial para validar conexión con Jira.

Responsabilidades:

* probar autenticación;
* obtener datos del usuario autenticado;
* listar campos disponibles;
* extraer un conjunto pequeño de issues;
* guardar JSON crudo.

Archivo sugerido:

```text
scripts/jira_discovery.py
```

---

### 9.2. Jira Sync

Script de sincronización principal.

Responsabilidades:

* ejecutar búsquedas JQL;
* obtener issues completos;
* guardar raw JSON;
* soportar modo full;
* soportar modo incremental.

Archivo:

```text
scripts/sync_jira.py
```

Modos:

```bash
python scripts/sync_jira.py --mode full --max-results 50
```

```bash
python scripts/sync_jira.py --mode incremental --max-results 50
```

---

### 9.3. Normalizer

Convierte la estructura cruda de Jira en un modelo propio más limpio.

Entrada:

```text
data/raw/ISSUE-123.json
```

Salida:

```text
data/normalized/ISSUE-123.json
```

Ejemplo de salida normalizada:

```json
{
  "issue_key": "DEMO-123",
  "title": "Update invoice validation",
  "issue_type": "Story",
  "status": "Done",
  "priority": "Medium",
  "sprint": "SPRINT-12",
  "assignee": "Jane Doe",
  "reporter": "John Smith",
  "created_at": "2026-01-10T10:00:00.000-0300",
  "updated_at": "2026-01-15T18:30:00.000-0300",
  "description": "Implement validation rules for invoices.",
  "comments": [],
  "attachments": [],
  "issue_links": [],
  "subtasks": [],
  "history": [],
  "jira_url": "https://example.atlassian.net/browse/DEMO-123"
}
```

---

### 9.4. Markdown Generator

Genera documentación legible por cada issue.

Entrada:

```text
data/normalized/
```

Salida:

```text
data/markdown/
```

Ejemplo:

```text
data/markdown/DEMO-123.md
```

Estructura del Markdown:

```md
# DEMO-123 - Update invoice validation

## 1. Datos generales

## 2. Descripción original

## 3. Clasificación

## 4. Comentarios

## 5. Adjuntos / imágenes

## 6. Subtareas

## 7. Tarjetas relacionadas

## 8. Historial de cambios

## 9. Resumen estructurado para IA

## 10. Fuente
```

---

### 9.5. Chunk Generator

Divide cada issue en bloques más pequeños para búsqueda y RAG.

Tipos de chunks:

* `general`;
* `description`;
* `comment_X`;
* `attachments`;
* `history`;
* `issue_links`;
* `subtasks`;
* futuro `image_analysis`.

Ejemplo:

```json
{
  "id": "DEMO-123::description",
  "issue_key": "DEMO-123",
  "chunk_type": "description",
  "text": "Description of the issue...",
  "metadata": {
    "issue_key": "DEMO-123",
    "status": "Done",
    "sprint": "SPRINT-12",
    "jira_url": "https://example.atlassian.net/browse/DEMO-123"
  }
}
```

---

### 9.6. Local Search

Buscador simple por palabras clave sobre los chunks.

Archivo:

```text
scripts/search_chunks.py
```

Ejemplo:

```bash
python scripts/search_chunks.py "invoice validation"
```

Con filtros:

```bash
python scripts/search_chunks.py "invoice" --status "Done"
```

---

### 9.7. Semantic Search

Buscador semántico basado en embeddings.

Archivo:

```text
scripts/semantic_search.py
```

Permite encontrar información aunque la consulta no use exactamente las mismas palabras que el issue original.

Ejemplo:

```bash
python scripts/semantic_search.py "automatic invoice checks"
```

---

### 9.8. Hybrid Search

Combina búsqueda literal y búsqueda semántica.

Archivo:

```text
scripts/hybrid_search.py
```

La búsqueda híbrida es útil porque:

* la búsqueda literal funciona mejor para códigos, tickets, sprints o nombres exactos;
* la búsqueda semántica funciona mejor para preguntas naturales;
* combinarlas suele dar mejores resultados.

Ejemplo:

```bash
python scripts/hybrid_search.py "automatic invoice validation"
```

---

### 9.9. Pipeline

Ejecuta todo el flujo completo.

Archivo:

```text
scripts/pipeline.py
```

Ejemplo full:

```bash
python scripts/pipeline.py --mode full --max-results 50
```

Ejemplo incremental:

```bash
python scripts/pipeline.py --mode incremental --max-results 50
```

El pipeline ejecuta:

```text
sync Jira
↓
detect changes
↓
normalize issues
↓
generate Markdown
↓
generate chunks
```

---

## 10. Sincronización full e incremental

### Full sync

Se usa para la primera carga o una reconstrucción completa.

```bash
python scripts/pipeline.py --mode full --max-results 100
```

### Incremental sync

Se usa para ejecutar el proceso de manera periódica, por ejemplo con un cron diario.

```bash
python scripts/pipeline.py --mode incremental --max-results 100
```

La sincronización incremental busca únicamente issues modificados desde la última sincronización.

---

## 11. Detección de cambios por hash

El sistema calcula un hash sobre cada JSON crudo.

Si el hash cambia, significa que el issue fue modificado.

Esto permite:

* evitar reprocesar issues sin cambios;
* regenerar Markdown solo cuando corresponde;
* regenerar chunks solo cuando corresponde;
* preparar el sistema para futuras tareas programadas.

---

## 12. Logs del pipeline

Cada ejecución del pipeline puede generar un log con:

* fecha de inicio;
* fecha de fin;
* modo usado;
* cantidad de issues sincronizados;
* cantidad de issues modificados;
* estado final;
* errores;
* salida de cada paso.

Ejemplo:

```json
{
  "run_id": "20260610_153000",
  "mode": "incremental",
  "started_at": "2026-06-10T15:30:00",
  "finished_at": "2026-06-10T15:30:12",
  "status": "success",
  "summary": {
    "changed_issues_count": 3,
    "changed_issues": ["DEMO-123", "DEMO-124", "DEMO-125"]
  }
}
```

---

## 13. Imágenes y adjuntos

El sistema contempla adjuntos desde la etapa de normalización.

En la primera versión se guarda metadata:

* nombre del archivo;
* tipo MIME;
* tamaño;
* autor;
* fecha;
* URL;
* si es imagen o no.

Ejemplo:

```json
{
  "filename": "error_screenshot.png",
  "mime_type": "image/png",
  "size": 245832,
  "author": "Jane Doe",
  "created_at": "2026-01-12T09:30:00.000-0300",
  "content_url": "https://example.atlassian.net/rest/api/3/attachment/content/12345",
  "is_image": true
}
```

En una etapa futura se podría agregar:

```text
image download
↓
OCR
↓
multimodal analysis
↓
image_analysis chunk
↓
RAG
```

Ejemplo futuro:

```json
{
  "id": "DEMO-123::image_analysis_1",
  "chunk_type": "image_analysis",
  "text": "The image shows an error message in the invoice validation screen.",
  "metadata": {
    "issue_key": "DEMO-123",
    "filename": "error_screenshot.png"
  }
}
```

---

## 14. Base de datos futura

La versión actual usa archivos locales para prototipado.

Para una versión más robusta, se podría migrar a:

```text
PostgreSQL + pgvector
```

La base relacional guardaría:

* issues;
* comments;
* attachments;
* changelog;
* issue links;
* chunks;
* embeddings;
* sync logs;
* user queries.

La extensión `pgvector` permitiría guardar embeddings y hacer búsqueda semántica directamente desde PostgreSQL.

---

## 15. Futuro RAG con LLM

El siguiente paso natural sería implementar una capa RAG.

Flujo esperado:

```text
User question
↓
Hybrid search over chunks
↓
Top relevant chunks
↓
Prompt builder
↓
LLM
↓
Answer with sources
```

Ejemplo de respuesta esperada:

```text
The issue DEMO-123 implemented invoice validation rules.
It was completed in sprint SPRINT-12 and assigned to Jane Doe.

Sources:
- DEMO-123 description
- DEMO-123 comments
- Jira: https://example.atlassian.net/browse/DEMO-123
```

Reglas deseables para el RAG:

* answer only using retrieved context;
* include sources;
* do not invent missing data;
* say when information is not available;
* separate facts from inferred information;
* include Jira links.

---

## 16. Tecnologías utilizadas

### Actual

* Python
* Requests
* python-dotenv
* JSON
* Markdown
* NumPy
* sentence-transformers
* Local file storage

### Futuro posible

* FastAPI or Django REST Framework
* PostgreSQL
* pgvector
* React
* OpenAI API
* Azure OpenAI
* Azure AI Search
* Docker
* Celery / Redis
* OCR / multimodal models

---

## 17. Instalación

```bash
git clone https://github.com/your-user/jira-knowledge-rag.git
cd jira-knowledge-rag
python -m venv venv
```

Activar entorno virtual:

Windows:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Crear `.env` desde `.env.example`:

```bash
cp .env.example .env
```

Configurar variables de Jira.

---

## 18. Uso básico

### Discovery inicial

```bash
python scripts/jira_discovery.py
```

### Pipeline full

```bash
python scripts/pipeline.py --mode full --max-results 50
```

### Pipeline incremental

```bash
python scripts/pipeline.py --mode incremental --max-results 50
```

### Buscar en chunks

```bash
python scripts/search_chunks.py "invoice validation"
```

### Generar embeddings

```bash
python scripts/build_embeddings.py
```

### Búsqueda semántica

```bash
python scripts/semantic_search.py "automatic invoice checks"
```

### Búsqueda híbrida

```bash
python scripts/hybrid_search.py "automatic invoice validation"
```

---

## 19. Datos sensibles y seguridad

Este proyecto puede conectarse a Jira y extraer información potencialmente sensible.

Por eso, no se deben subir al repositorio:

```text
.env
data/raw/
data/normalized/
data/markdown/
data/chunks/
data/embeddings/
data/logs/
data/sync/
data/hashes/
data/fields/
```

El repositorio público debería incluir únicamente:

* código;
* `.env.example`;
* documentación;
* datos mock o anonimizados en `sample_data/`.

Ejemplo de `.gitignore`:

```gitignore
.env
__pycache__/
*.pyc

data/raw/
data/normalized/
data/markdown/
data/chunks/
data/embeddings/
data/logs/
data/sync/
data/hashes/
data/fields/

venv/
.env.local
```

---

## 20. Dataset de ejemplo

Para portfolio se recomienda incluir datos ficticios.

Ejemplo:

```text
sample_data/
  raw/
    DEMO-123.json
  normalized/
    DEMO-123.json
  markdown/
    DEMO-123.md
  chunks/
    DEMO-123.json
```

Esto permite mostrar el funcionamiento sin exponer información real de ninguna empresa.

---

## 21. Roadmap

### Etapa 1 — Prototipo local

* Conexión read-only a Jira.
* Extracción de issues.
* Normalización.
* Markdown.
* Chunks.
* Búsqueda local.
* Logs.
* Pipeline incremental.

### Etapa 2 — Búsqueda semántica

* Embeddings locales.
* Índice vectorial local.
* Búsqueda semántica.
* Búsqueda híbrida.

### Etapa 3 — Mini RAG

* Recuperar top chunks.
* Armar contexto.
* Conectar con LLM.
* Responder con fuentes.

### Etapa 4 — Backend

* API con FastAPI o Django.
* Endpoints de búsqueda.
* Endpoints de consulta RAG.
* Persistencia en PostgreSQL.

### Etapa 5 — Frontend

* Dashboard.
* Buscador.
* Vista de issue documentada.
* Chat con fuentes.
* Filtros por sprint, estado, responsable, proyecto.

### Etapa 6 — Producción

* PostgreSQL + pgvector.
* Jobs programados.
* Docker.
* Manejo de permisos.
* Auditoría.
* Procesamiento de imágenes.
* Integración con Azure/OpenAI.

---

## 22. Posibles consultas

Ejemplos de preguntas que el sistema busca soportar:

```text
What was done in sprint SPRINT-12?
Which issues are related to invoice validation?
Who resolved issue DEMO-123?
Which tickets include screenshots?
What comments explain the solution?
Was this bug reported before?
Which issues are linked to this feature?
What changed in this issue over time?
```

---

## 23. Valor técnico del proyecto

Este proyecto demuestra conocimientos en:

* integración con APIs REST;
* autenticación por token;
* diseño de pipelines de datos;
* normalización de información;
* generación automática de documentación;
* procesamiento incremental;
* detección de cambios por hash;
* modelado para RAG;
* chunking;
* búsqueda local;
* embeddings;
* búsqueda semántica;
* arquitectura evolutiva hacia sistemas con IA;
* buenas prácticas de seguridad para datos sensibles.

---

## 24. Estado actual

Estado del prototipo:

```text
✅ Jira read-only extraction
✅ Raw JSON storage
✅ Field discovery
✅ Normalized JSON
✅ Markdown generation
✅ Enriched issue documentation
✅ Full sync
✅ Incremental sync
✅ Hash-based change detection
✅ Pipeline orchestration
✅ Execution logs
✅ Chunk generation
✅ Local keyword search
🟡 Semantic search prototype
🟡 Hybrid search prototype
🔜 Mini RAG with LLM
🔜 PostgreSQL + pgvector
🔜 Web/API layer
🔜 Frontend
```

---

## 25. Nota

Este proyecto está pensado como una versión genérica y segura para portfolio.

No incluye datos reales de empresas.

Para usarlo con una instancia real de Jira, se deben configurar credenciales propias y asegurarse de respetar las políticas de seguridad y privacidad correspondientes.
