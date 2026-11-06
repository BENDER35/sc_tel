# Mejoras Aplicadas al Script sc_tel

## Resumen General
Se han aplicado mejoras significativas al script `cli.py` para mejorar su robustez, rendimiento y experiencia de usuario.

## Archivos Modificados/Creados

### 1. config.py (NUEVO)
Módulo de configuración que gestiona:
- Variables de entorno (TG_API_ID, TG_API_HASH, etc.)
- Configuración por defecto con valores configurables
- Guardado y carga de credenciales en config.json
- Branding de salida de formato
- Banderas de características (caché, proxy)

### 2. searcher.py (MEJORADO)
Motor de búsqueda con:
- **Lógica de reintentos exponenciales**: `._request_with_retry()` con backoff 2^n
- **Limitación de tasa**: Algoritmo de balde detokens para evitar bloqueos
- **Rotación de User-Agent**: Integración con `fake-useragent` o lista por defecto
- **Mejor dedupulación**: Huellas dactilares URL+título para evitar duplicados
- **Manejo de errores mejorado**: Logging en lugar de silencios `pass`
- **Google Search mejorado**: Clases CSS más robustas para extractores de fragmentos

### 3. tg_client.py (MEJORADO)
Validador API de Telegram Telethon con:
- **Manejo de flood waits**: Pausas automáticas cuando Telegram limita la tasa
- **Mejor clasificación de errores**: Mensajes amigables para errores de API
- **Validación de enlaces de invitación**: Sin necesidad de unirse al grupo
- **Resolución de username**: Metadatos completos (miembros, descripción, tipo)
- **Search global nativo**: Búsqueda en la base de datos pública de Telegram

### 4. cli.py (MEJORADO)
Interfaz de línea de comandos con:
- **Barra de progreso en todas las fases**: Búsqueda, API, validación
- **Exportación mejorada**: CSV, JSON, Markdown con formato correcto
- **Tabla Rich mejorada**: Coloreado por tipo, íconos de estado, columnas ordenables
- **Gestión de credenciales**: Preferencia por variables de entorno sobre archivo config.json
- **Mejor manejo de bandera --validate**: Flujo de validación optimizado

## Correcciones de Bugs
- `urls = set` → `urls = set()` en searcher.py
- `seen_urls = set()()` → `seen_urls = set()` en search_hybrid_web
- Errores de sintaxis en parámetros encoding ("utf-8" → "utf-8")
- Importación faltante de `click` y `Theme`

## Características Nuevas
1. **System logging**: Archivo `searcher.log` para debugging
2. **Rate limiting configurable**: `SC_TEL_RATE_LIMIT` por defecto 30 requests/min
3. **Fingerprint dedup**: URL + título primeros 50 chars para mejor deduplicación
4. **Modo API opcional**: Búsqueda nativa y validación profunda con Telethon
5. **Filtros avanzados**: Por tipo (grupo/canal/bot), estado en línea, etc.

## Estructura de Repositorios
- **GitHub**: https://github.com/BENDER35/sc_tel
- **GitHub Release**: v1.0.0 con sc_tel_release.zip
- **GitLab**: Repositorio necesario crear manualmente en https://gitlab.com/new

## Próximos Pasos Recomendados
1. Crear cuenta en my.telegram.org para API credentials
2. Configurar variables de entorno: `TG_API_ID` y `TG_API_HASH`
3. Probar con `--validate` para validación web en tiempo real
4. Explorar filtros `--groups` y `--channels`