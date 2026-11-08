# 📚 sc_tel: Guía Didáctica en Español

## Bienvenido a sc_tel

sc_tel es un buscador avanzado de grupos y canales de Telegram que funciona directamente desde tu terminal. Esta guía te enseñará a aprovechar todas sus características, desde búsquedas básicas hasta la validación profunda con la API de Telegram.

---

## 🔍 Nivel 1: Búsquedas Básicas (Sin Credenciales)

### Objetivo
Aprender a buscar grupos y canales de Telegram simplemente con una palabra clave, sin necesidad de configurar credenciales.

### ¿Qué aprenderás?
- Búsquedas rápidas con palabras clave
- Cómo filtrar resultados por tipo (grupos/canales)
- Los comandos básicos de la CLI

### Ejercicio Práctico 1
```bash
# Busca grupos sobre "python programming"
python cli.py "python programming"

# Busca canales sobre "noticias"
python cli.py "noticias" --channels
```

### Ejercicio Práctico 2
```bash
# Busca con validación web (sin API)
python cli.py "cryptocurrency" --validate
```

---

## 🎛️ Nivel 2: Filtros y Opciones Avanzadas

### Objetivo
Dominar los filtros y opciones disponibles para refinar tus búsquedas.

### ¿Qué aprenderás?
- Filtrar solo grupos (`--groups`)
- Filtrar solo canales (`--channels`)
- Limitar el número de resultados (`--max-results` o `-n`)
- Combinar opciones para búsquedas específicas

### Ejercicio Práctico 3
```bash
# Solo grupos sobre "musik"
python cli.py "musik" --validate --groups

# Solo canales sobre "tecnologia" con límite de 10 resultados
python cli.py "tecnologia" --validate --channels --max-results 10
```

### Ejercicio Práctico 4
```bash
# Exporta resultados a CSV
python cli.py "inteligencia artificial" --validate --output mis_grupos.csv
```

---

## 🔐 Nivel 3: Modo API de Telegram (Validación Profunda)

### Objetivo
Utilizar tu cuenta de Telegram para obtener detalles más precisos y búsqueda nativa.

### ¿Qué aprenderás?
- Cómo obtener tus credenciales en my.telegram.org
- Configurar `api_id` y `api_hash`
- Búsqueda nativa en la base de datos de Telegram
- Validación de enlaces de invitación sin unirte

### Primeros Pasos con la API
1. Ve a [my.telegram.org](https://my.telegram.org)
2. Inicia sesión con tu cuenta de Telegram
3. Obtiene tu `api_id` y `api_hash`
4. Ejecuta: `python cli.py "tu_busqueda" --api`
5. Cuando se te pida, introduce tus credenciales
6. Opcionalmente, guárdalas en `config.json`

### Ejercicio Práctico 5
```bash
# Búsqueda nativa con API
python cli.py "ciberseguridad" --api

# Validación de enlace de invitación
python cli.py "https://t.me/joinhash123" --api
```

---

## 📁 Nivel 4: Exportación y Análisis de Datos

### Objetivo
Aprender a exportar y analizar los resultados obtenidos.

### Formatos Soportados
- **CSV**: Para análisis en Excel o Python/pandas
- **JSON**: Para procesamiento con herramientas de datos
- **Markdown**: Para documentación o compartición formateada

### Ejercicios Prácticos
```bash
# Exporta a CSV
python cli.py "python" --validate --output mis_resultados.csv

# Exporta a JSON
python cli.py "python" --validate --output mis_resultados.json

# Exporta a Markdown
python cli.py "python" --validate --output mis_resultados.md
```

### Análisis Rápido con Python
Después de exportar a CSV, puedes analizar los datos:
```python
import csv

with open('mis_resultados.csv', 'r', encoding='utf-8') as f:
    lector = csv.DictReader(f)
    for fila in lector:
        print(f"Título: {fila['Título / Nombre']}")
        print(f"Tipo: {fila['Tipo']}")
        print(f"Miembros: {fila['Miembros']}")
        print("---")
```

---

## ⚠️ Consejos y Buenas Prácticas

### Para Mejores Resultados
1. **Usa palabras clave específicas**: En lugar de "python", prueba "python programming" o "python learning"
2. **Combina válidación y filtros**: `python cli.py "python" --validate --groups`
3. **Respetar límites**: El script tiene delays automáticos para no sobrecargar los servidores
4. **Usa la API cuando necesites precisión**: Para detalles de grupos privados o conteos exactos

### Problemas Comunes
- **No se encuentran resultados**: Prueba con palabras clave diferentes o reduce el número de resultados
- **Errores de conexión**: El script tiene reintentos automáticos, pero si persiste, verifica tu conexión a internet
- **Flood wait**: Si usas la API frecuentemente, Telegram puede limitar tu tasa. Espere el tiempo sugerido e inténtalo de nuevo

---

## 🚀 Atajos y Consejos Rápidos

| Comando | Efecto |
| --- | --- |
| `python cli.py "texto"` | Búsqueda básica rápida |
| `python cli.py "texto" --validate` | Con validación web de metadatos |
| `python cli.py "texto" --api` | Con API nativa de Telegram |
| `python cli.py "texto" --groups` | Solo grupos |
| `python cli.py "texto" --channels` | Solo canales |
| `python cli.py "texto" -n 5` | Máximo 5 resultados |
| `python cli.py "texto" -o archivo.md` | Exporta a Markdown |

---

## 📞 ¿Dónde Obtener Ayuda?

- **Documentación**: Revisa el archivo `MEJORAS_APLICADAS.md` para mejoras técnicas
- **Reportes**: Si encuentras bugs, revisa `searcher.log` generado en el directorio
- **Actualizaciones**: El script recibe mejoras periódicas; verifica `git pull` para obtener la última versión

---

*Desarrollado con ❤️ para ofrecer una experiencia interactiva premium en entornos Linux. Diseñado con paletas HSL oscuras y glassmorphism visual en terminales modernas.*