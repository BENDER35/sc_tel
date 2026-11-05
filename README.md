# ⚡ sc_tel: Buscador Premium de Grupos de Telegram en Terminal ⚡

Un script avanzado e interactivo en Python para buscar y validar grupos, supergrupos y canales de Telegram de cualquier temática, utilizando una estrategia híbrida: **Web Scraping/Dorking** y **Telegram Client API (Telethon)**.

---

## Características Principales

1. **Búsqueda Web Híbrida (Sin Credenciales):**
   * Realiza búsquedas mediante dorking inteligente en motores de búsqueda para recolectar enlaces de Telegram (`t.me/...` o `t.me/joinchat/...`).
   * No requiere configurar ninguna API ni tener cuenta de Telegram para la búsqueda inicial.
2. **Validación Web en Tiempo Real:**
   * Extrae títulos reales, descripciones y recuento de miembros de las páginas de vista previa de Telegram de forma automática y respetuosa con los límites del servidor.
3. **Validación con API de Telegram (Opcional - Telethon):**
   * Integración directa con la API oficial de Telegram (`api_id` y `api_hash`).
   * Valida enlaces de invitación (`joinchat` y `+`) sin necesidad de unirse a ellos para obtener detalles precisos de grupos privados/públicos.
   * Realiza búsquedas globales y nativas directamente dentro de la base de datos de Telegram (`contacts.SearchRequest`).
4. **Interfaz CLI Espectacular:**
   * Tablas a color de alta definición en la terminal con la librería `rich`.
   * Barras de progreso interactivas y spinners de estado.
   * Filtros dinámicos para buscar únicamente **Canales** o **Grupos**.
5. **Exportación Flexible:**
   * Exporta instantáneamente los resultados a archivos **CSV**, **JSON** o **Markdown** ordenados.

---

## Requisitos de Instalación

El script utiliza un entorno virtual de Python. Puedes instalarlo y prepararlo con los siguientes comandos:

```bash
# Navega al directorio
cd /home/bender/Descargas/sc_tel

# Asegúrate de que el entorno virtual esté activo
source busq_grup_tel/bin/activate

# Instala las dependencias (ya realizadas durante la inicialización)
pip install -r requirements.txt
```

---

## Guía de Uso

Ejecuta el script usando `python cli.py` seguido de la palabra clave de búsqueda.

### 1. Búsqueda Rápida Básica
Busca grupos/canales sobre una temática. Devolverá enlaces encontrados en la web:
```bash
python cli.py "python programming"
```

### 2. Búsqueda con Validación Web (Sin API de Telegram)
Obtén metadatos como el título del chat, número de miembros y tipo raspando la página de previsualización de `t.me`:
```bash
python cli.py "cryptocurrency" --validate
```

### 3. Búsqueda con Filtros de Tipo
Filtra para ver solo grupos o solo canales:
```bash
# Mostrar únicamente grupos
python cli.py "musica" --validate --groups

# Mostrar únicamente canales
python cli.py "noticias" --validate --channels
```

### 4. Exportar Resultados
Guarda los resultados directamente en un formato estructurado (`.csv`, `.json` o `.md`):
```bash
python cli.py "inteligencia artificial" --validate --output resultados.csv
```

### 5. Modo API Avanzado (Validación Profunda y Búsqueda Nativa)
Usa tu cuenta de Telegram para comprobar enlaces de invitación privada y buscar globalmente en la red nativa:
```bash
python cli.py "cybersecurity" --api
```
*La primera vez que utilices el parámetro `--api`, el script te pedirá tu `api_id` y `api_hash` de [my.telegram.org](https://my.telegram.org) y creará una sesión segura en tu máquina. Se te pedirá opcionalmente guardar las credenciales en `config.json` para no tener que escribirlas de nuevo.*

---

## Opciones Disponibles en la Consola

| Opción | Comando Corto | Descripción |
| --- | --- | --- |
| `--max-results` | `-n` | Número máximo de resultados a buscar (por defecto: 30). |
| `--validate` | `-v` | Valida páginas web `t.me` para extraer títulos y miembros en tiempo real. |
| `--api` | `-a` | Conecta a la API de Telegram usando Telethon (búsqueda nativa y validación de invitación). |
| `--output` | `-o` | Guarda los resultados en un archivo (`.json`, `.csv`, `.md`). |
| `--groups` | | Filtra y muestra únicamente grupos de Telegram. |
| `--channels` | | Filtra y muestra únicamente canales de Telegram. |

---

## Créditos y Estilo

Desarrollado con ❤️ para ofrecer una experiencia interactiva premium en entornos Linux. Diseñado con paletas HSL oscuras y glassmorphism visual en terminales modernas.
