# Guía de scripts

Esta guía explica la responsabilidad, entradas, salidas y forma de uso de cada
script del proyecto. Todos calculan las rutas de datos desde la raíz del
repositorio. Se recomienda ejecutar los comandos desde esa raíz para que
`python-dotenv` también encuentre `.env` de forma confiable.

## Estructura de directorios

```
scripts/
  pipeline.py               ← orquestador principal
  jira/
    sync.py                 ← sincronización completa e incremental
    discovery.py            ← validación de conexión y campos
    full_discovery.py       ← muestra con detalle completo
  transform/
    detect_changes.py       ← detección de raws modificados
    normalize.py            ← conversión al contrato normalizado
    generate_markdown.py    ← documentos Markdown por tarjeta
    generate_chunks.py      ← unidades temáticas para búsqueda
  search/
    build_embeddings.py     ← índice vectorial local
    keyword_search.py       ← búsqueda literal
    semantic_search.py      ← búsqueda semántica
    hybrid_search.py        ← búsqueda combinada
```

## Mapa rápido

| Script | Función principal | Red |
|---|---|:---:|
| `pipeline.py` | Orquesta el procesamiento principal | Indirecta |
| `jira/sync.py` | Sincroniza tarjetas completas desde Jira | Sí |
| `transform/detect_changes.py` | Detecta raws nuevos o modificados | No |
| `transform/normalize.py` | Convierte raws al contrato normalizado | No |
| `transform/generate_markdown.py` | Genera documentos por tarjeta | No |
| `transform/generate_chunks.py` | Genera unidades temáticas para búsqueda | No |
| `search/build_embeddings.py` | Construye el índice vectorial local | Descarga modelo |
| `search/keyword_search.py` | Ejecuta búsqueda literal | No |
| `search/semantic_search.py` | Ejecuta búsqueda semántica | Descarga modelo |
| `search/hybrid_search.py` | Combina búsqueda semántica y literal | Descarga modelo |
| `jira/discovery.py` | Descubre conexión, campos y muestra de tarjetas | Sí |
| `jira/full_discovery.py` | Descarga una muestra con detalle completo | Sí |

## `pipeline.py`

**Propósito:** punto de entrada recomendado para extraer y transformar Jira.

Ejecuta, en orden:

1. `jira/sync.py`
2. `transform/detect_changes.py`
3. `transform/normalize.py`
4. `transform/generate_markdown.py`
5. `transform/generate_chunks.py`

**Entradas**

- Argumentos `--mode`, `--max-results` y opcionalmente `--since`.
- Configuración Jira consumida indirectamente por `sync_jira.py`.

**Salidas**

- Todas las salidas de los cinco pasos.
- `data/logs/pipeline_<run_id>.json`, actualizado después de cada etapa.

**Comportamiento importante**

- Usa `sys.executable`, por lo que los pasos corren dentro del mismo entorno.
- Captura tiempos, código de salida, `stdout` y `stderr`.
- Detiene el proceso al primer paso fallido.
- Normaliza valores como `--since "-1d"` para que `argparse` los acepte.
- No ejecuta `build_embeddings.py`.

```powershell
python scripts/pipeline.py --mode full --max-results 100
python scripts/pipeline.py --mode incremental --since "-1d"
```

## `jira/sync.py`

**Propósito:** buscar tarjetas del proyecto y guardar su detalle completo.

**Entradas**

- `.env`: `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`,
  `JIRA_PROJECT_KEY`.
- `--mode full|incremental`.
- `--max-results`, con default `20`.
- `--since`, opcional para modo incremental.

**Salidas**

- `data/raw/<ISSUE_KEY>.json`.
- `data/sync/sync_state.json`.

**Cómo funciona**

- `full` usa JQL `project = "<KEY>" ORDER BY updated DESC`.
- `incremental` agrega `updated >= "<since>"`.
- Sin `--since`, el incremental usa el último sync exitoso; si no existe, usa
  `-1d`.
- Primero busca keys mediante `/rest/api/3/search/jql`.
- Luego consulta cada tarjeta mediante `/rest/api/3/issue/<KEY>` con
  `fields=*all` y `expand=changelog,renderedFields,names,schema`.
- Guarda el estado solo después de terminar la sincronización.

El script solo usa `GET`, con timeout de 60 segundos. Actualmente deshabilita la
validación SSL mediante `verify=False`.

```powershell
python scripts/jira/sync.py --mode incremental --max-results 50
```

## `transform/detect_changes.py`

**Propósito:** evitar reprocesar tarjetas cuyo raw no cambió.

**Entradas**

- Todos los archivos `data/raw/*.json`.
- `data/hashes/raw_hashes.json`, si existe.

**Salidas**

- `data/hashes/raw_hashes.json`, reemplazado con los hashes actuales.
- `data/sync/changed_issues.json`, lista de keys nuevas o modificadas.

Calcula SHA-256 sobre los bytes completos de cada archivo. Una tarjeta se marca
como modificada cuando no tiene hash previo o el hash cambió. Si no hay raws,
informa la situación y no escribe nuevos archivos de estado.

```powershell
python scripts/transform/detect_changes.py
```

## `transform/normalize.py`

**Propósito:** reducir la respuesta extensa y variable de Jira a un contrato
local consistente.

**Entradas**

- `data/raw/<ISSUE_KEY>.json`.
- `data/sync/changed_issues.json`, si existe.
- `JIRA_BASE_URL` para construir el enlace de la tarjeta.

**Salidas**

- `data/normalized/<ISSUE_KEY>.json`.

Si existe `changed_issues.json`, procesa únicamente esas keys. Si no existe,
procesa todos los raws. Si la lista existe pero está vacía, no hace trabajo.

**Transformaciones**

- Elige un nombre legible para usuarios.
- Convierte descripciones y comentarios ADF a texto plano.
- Obtiene el último sprint cuando Jira entrega una lista.
- Normaliza comentarios, adjuntos, links y subtareas.
- Aplana cada ítem del changelog.
- Infiere quién resolvió la tarjeta buscando transiciones a estados finales.
- Agrega referencias al raw y a Jira.

**Campos custom conocidos**

- Sprint: `customfield_10020`
- Ticket GLPI: `customfield_10270`
- Área de enfoque: `customfield_10237`

```powershell
python scripts/transform/normalize.py
```

## `transform/generate_markdown.py`

**Propósito:** crear una representación legible y trazable por tarjeta.

**Entradas**

- `data/normalized/<ISSUE_KEY>.json`.
- `data/sync/changed_issues.json`, si existe.

**Salidas**

- `data/markdown/<ISSUE_KEY>.md`.

El documento incluye datos generales, descripción, clasificación, comentarios,
adjuntos, subtareas, relaciones, historial, resumen estructurado y fuentes. El
resumen es determinístico: no invoca IA.

Al igual que la normalización, procesa solo cambios si existe el listado y
procesa todo cuando el listado todavía no fue creado.

```powershell
python scripts/transform/generate_markdown.py
```

## `transform/generate_chunks.py`

**Propósito:** dividir cada tarjeta en unidades temáticas recuperables.

**Entradas**

- `data/normalized/<ISSUE_KEY>.json`.
- `data/sync/changed_issues.json`, si existe.

**Salidas**

- `data/chunks/<ISSUE_KEY>.json`, una lista de chunks por tarjeta.

Siempre intenta crear chunks `general` y `description`. También crea, cuando
hay contenido:

- Un chunk `comment_<n>` por comentario.
- Un chunk `attachments`.
- Un chunk `history`.
- Un chunk `issue_links`.
- Un chunk `subtasks`.

Cada chunk tiene un ID estable `<ISSUE_KEY>::<chunk_type>`, texto y metadata
repetida para filtros. Los adjuntos se representan por metadata; su contenido
no se descarga.

```powershell
python scripts/transform/generate_chunks.py
```

## `search/build_embeddings.py`

**Propósito:** construir un índice vectorial local a partir de todos los chunks.

**Entradas**

- Todos los archivos `data/chunks/*.json`.
- Modelo `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.

**Salidas**

- `data/embeddings/chunk_embeddings.npy`.
- `data/embeddings/chunks_index.json`.

Carga solo chunks con texto no vacío, genera embeddings normalizados y guarda la
matriz NumPy junto con un snapshot de los chunks en el mismo orden. El índice se
reemplaza por completo en cada ejecución.

El modelo puede descargarse durante la primera ejecución. Debe reconstruirse el
índice después de cambiar chunks para que las búsquedas semántica e híbrida
reflejen los datos actuales.

```powershell
python scripts/search/build_embeddings.py
```

## `search/keyword_search.py`

**Propósito:** búsqueda local literal sin modelo ni índice vectorial.

**Entradas**

- Consulta posicional.
- Todos los archivos `data/chunks/*.json`.
- Filtros opcionales `--status`, `--sprint`, `--issue-key`, `--chunk-type`.

**Salidas**

- Resultados impresos en consola; no escribe archivos.

Normaliza texto a minúsculas, elimina acentos comunes, separa términos y quita
stopwords. Puntúa coincidencias en el texto y metadata, con bonus para título,
key Jira y GLPI. Solo muestra chunks con score mayor que cero.

```powershell
python scripts/search/keyword_search.py "error permisos" --status "Finalizada" --limit 5
```

## `search/semantic_search.py`

**Propósito:** recuperar chunks por significado, aunque no compartan palabras
exactas con la consulta.

**Entradas**

- Consulta posicional.
- `data/embeddings/chunk_embeddings.npy`.
- `data/embeddings/chunks_index.json`.
- Los mismos filtros opcionales que la búsqueda literal.

**Salidas**

- Ranking impreso en consola; no escribe archivos.

Codifica la consulta con el mismo modelo multilingüe. Como los vectores están
normalizados, usa producto punto como similitud coseno. Los filtros se aplican
antes del ranking.

No aplica umbral mínimo: muestra hasta `--limit` candidatos aunque la similitud
sea baja.

```powershell
python scripts/search/semantic_search.py "usuarios que no pueden acceder" --limit 5
```

## `search/hybrid_search.py`

**Propósito:** combinar recuperación semántica con señales literales fuertes,
como keys, tickets GLPI y nombres concretos.

**Entradas**

- Las mismas entradas que `semantic_search.py`.
- `--semantic-weight`, default `0.65`.
- `--literal-weight`, default `0.35`.

**Salidas**

- Ranking combinado impreso en consola; no escribe archivos.

Calcula ambos scores sobre los candidatos filtrados, normaliza cada lista entre
0 y 1 y obtiene:

```text
score final = score semántico normalizado * semantic_weight
            + score literal normalizado * literal_weight
```

Los pesos no se validan ni se fuerzan a sumar `1`.

```powershell
python scripts/search/hybrid_search.py "PE20-1034 autenticación" `
  --semantic-weight 0.4 `
  --literal-weight 0.6
```

## `jira/discovery.py`

**Propósito:** validar una nueva configuración Jira y descubrir campos útiles.

**Entradas**

- Las cuatro variables Jira del `.env`.

**Salidas**

- `data/fields/jira_fields.json`.
- Hasta 10 tarjetas recientes en `data/raw/`.
- Diagnóstico de conexión y campos relevantes en consola.

Ejecuta tres tareas:

1. Consulta `/rest/api/3/myself` para validar usuario y conexión.
2. Consulta `/rest/api/3/field`, guarda todos los campos y destaca nombres
   relacionados con sprint, GLPI, resolución, módulo y área.
3. Busca 10 tarjetas recientes y guarda la respuesta incluida en la búsqueda.

La muestra no necesariamente tiene el mismo nivel de detalle que
`sync_jira.py`, porque no realiza una consulta individual por tarjeta.
Además, escribe en el mismo `data/raw/` del pipeline y puede sobrescribir una
respuesta completa con una muestra parcial. Después del discovery conviene
ejecutar nuevamente `sync_jira.py` o `pipeline.py`.

```powershell
python scripts/jira/discovery.py
```

## `jira/full_discovery.py`

**Propósito:** inspeccionar la estructura completa de una muestra reciente.

**Entradas**

- Las cuatro variables Jira del `.env`.

**Salidas**

- Detalle completo de hasta 20 tarjetas recientes en `data/raw/`.

Primero busca las keys recientes y luego consulta cada tarjeta individualmente
con los mismos `fields` y `expand` usados por `sync_jira.py`. La cantidad está
fijada en el código y no expone argumentos CLI.

```powershell
python scripts/jira/full_discovery.py
```

## Dependencias entre scripts

```text
jira/discovery.py -----------------------------> data/fields + muestra raw
jira/full_discovery.py ------------------------> muestra raw completa

jira/sync.py
  -> transform/detect_changes.py
  -> transform/normalize.py
  -> transform/generate_markdown.py
  -> transform/generate_chunks.py
       -> search/keyword_search.py
       -> search/build_embeddings.py
            -> search/semantic_search.py
            -> search/hybrid_search.py
```

Para una operación normal, usar `pipeline.py`, luego `build_embeddings.py` y
finalmente el buscador apropiado.
