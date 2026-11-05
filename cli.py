"""
sc_tel: Buscador Premium de Grupos de Telegram en Terminal.

Un script avanzado e interactivo en Python para buscar y validar grupos,
supergrupos y canales de Telegram de cualquier temática, utilizando una
estrategia híbrida: Web Scraping/Dorking y Telegram Client API (Telethon).

Características:
- Búsqueda web híbrida sin necesidad de credenciales
- Validación web en tiempo real de páginas t.me
- Validación profunda con API de Telegram (Telethon)
- Filtros dinámicos para canales y grupos
- Exportación a CSV, JSON y Markdown
- Interfaz CLI espectacular con Rich
"""

import os
import sys
import json
import click
import asyncio
import logging
from typing import Optional, Dict, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.theme import Theme
from rich.markup import escape

# Import configuration module
from config import load_config, get_api_credentials, save_config, OUTPUT_DEFAULT_FORMAT

# Import our custom search modules
from searcher import search_hybrid_web, parse_telegram_preview

# Import Telegram validator module
from tg_client import TelegramValidator

# Initialize Rich Console with a premium dark/cyberpunk theme
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
    "brand": "bold royal_blue1",
    "accent": "bold magenta",
})
console = Console(theme=custom_theme)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("searcher.log", encoding="utf-8"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print the welcome banner with ASCII art."""
    console.print("\n")
    console.print(Panel(
        Text.assemble(
            (" ⚡ ANTIGRAVITY TELEGRAM SEARCHER ⚡ \n", "bold royal_blue1"),
            ("El buscador de grupos y canales definitivo en tu terminal\n", "italic white"),
            ("Búsqueda Web Híbrida + API de Telegram (Telethon)", "dim white")
        ),
        border_style="royal_blue1",
        expand=False
    ))


@click.command()
@click.argument("query", required=True)
@click.option("--max-results", "-n", default=30, help="Número máximo de resultados a buscar.")
@click.option("--validate", "-v", is_flag=True, help="Validar páginas web t.me para extraer títulos y miembros reales.")
@click.option("--api", "-a", is_flag=True, help="Usar la API oficial de Telegram para una validación profunda y búsqueda nativa.")
@click.option("--output", "-o", type=click.Path(), help="Exportar resultados a un archivo (.csv, .json, .md).")
@click.option("--groups", "filter_type", flag_value="groups", help="Filtrar y mostrar solo grupos.")
@click.option("--channels", "filter_type", flag_value="channels", help="Filtrar y mostrar solo canales.")
def main(query, max_results, validate, api, output, filter_type):
    """
    Busca grupos y canales de Telegram basados en una palabra clave (QUERY).
    
    Examples:
        python cli.py "python programming" --validate
        python cli.py "cocina facil" --api --output cocina.csv
    """
    print_banner()
    
    # Maximum results cap
    max_results = min(max_results, 100)  # Limit to prevent excessive searching
    
    # Run async main loop
    results = asyncio.run(run_search_async(
        query=query,
        max_results=max_results,
        validate=validate,
        api_mode=api,
        filter_type=filter_type
    ))
    
    if results:
        display_results_table(results)
        
        if output:
            export_results(results, output)
    else:
        console.print("\n[warning]No se obtuvieron resultados válidos.[/]")


async def run_search_async(query, max_results, validate, api_mode, filter_type):
    """
    Executes the search in asynchronous phases:
    1. Web search hybrid (DDGS + Google)
    2. Telegram API search (if enabled)
    3. Validation phase
    4. Filtering and final results
    """
    results = []
    
    # 1. WEB SEARCH PHASE
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30, complete_style="royal_blue1"),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        task_search = progress.add_task("[cyan]Buscando enlaces de Telegram en la web...", total=100)
        
        # Simulate search engine scraping progress
        progress.update(task_search, completed=20)
        web_results = search_hybrid_web(query, max_results=max_results)
        progress.update(task_search, completed=80)
        
        if not web_results:
            progress.update(task_search, completed=100)
            console.print("[warning]![/warning] No se encontraron resultados web iniciales.")
        else:
            progress.update(task_search, completed=100)
            console.print(f"[success]✓[/success] Se encontraron [bold info]{len(web_results)}[/] enlaces web potenciales.")
    
    # 2. TELEGRAM API SEARCH PHASE (if enabled)
    tg_validator = None
    api_results = []
    
    if api_mode:
        # Get credentials from environment, config, or prompt
        api_id, api_hash = get_api_credentials()
        
        if not api_id or not api_hash:
            console.print("\n[warning]⚠️ Se requieren credenciales de Telegram API (my.telegram.org) para búsqueda nativa y validación profunda.[/]")
            if Confirm.ask("¿Quieres configurar las credenciales ahora?"):
                api_id = Prompt.ask("Introduce tu API ID")
                api_hash = Prompt.ask("Introduce tu API HASH")
                if Confirm.ask("¿Deseas guardar estas credenciales localmente en `config.json`?"):
                    save_config(api_id, api_hash)
            else:
                console.print("[warning]! Continuando en modo Web Scraping / Validación Web (sin API).[/]")
                api_mode = False
        
        if api_mode:
            try:
                tg_validator = TelegramValidator(api_id, api_hash)
                
                with console.status("[brand]Conectando con la API de Telegram (Telethon)...[/]") as status:
                    try:
                        await tg_validator.connect()
                        console.print("[success]✓[/success] Conectado exitosamente a Telegram.")
                    except Exception as e:
                        console.print(f"[error]✕ Error de conexión API:[/] {e}")
                        console.print("[warning]! Desactivando modo API. Continuando sin credenciales.[/]")
                        tg_validator = None
                        api_mode = False
                
                if tg_validator:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console
                    ) as progress:
                        task_api = progress.add_task("[cyan]Realizando búsqueda global nativa en Telegram...", total=None)
                        try:
                            api_results = await tg_validator.search_global(query, limit=max_results)
                            console.print(f"[success]✓[/success] Búsqueda global nativa devolvió [bold info]{len(api_results)}[/] resultados.")
                        except Exception as e:
                            console.print(f"[warning]![/warning] No se pudo realizar la búsqueda nativa: {e}")
            
            except Exception as e:
                console.print(f"[error]✕ Error inesperado en modo API:[/] {e}")
                api_mode = False
                tg_validator = None
    
    # Combine results and remove duplicates
    combined = []
    seen_urls = set()
    seen_fingerprints = set()
    
    # Prioritize API results as they are more complete
    # First add API results
    for item in api_results:
        url = item.get("url")
        if url:
            # Create fingerprint for dedup: url + title first 50 chars
            fingerprint = f"{url}|{item.get('title', '')[:50].lower()}" if item.get('title') else url
            if url not in seen_urls and fingerprint not in seen_fingerprints:
                seen_urls.add(url)
                seen_fingerprints.add(fingerprint)
                combined.append(item)
    
    # Then add web results
    for item in web_results:
        url = item.get("url")
        if url:
            title = item.get("title", "")
            fingerprint = f"{url}|{title[:50].lower()}" if title else url
            if url not in seen_urls and fingerprint not in seen_fingerprints:
                seen_urls.add(url)
                seen_fingerprints.add(fingerprint)
                combined.append(item)
    
    if not combined:
        console.print("\n[warning]No se encontraron resultados que coincidan con la búsqueda.[/]")
        if tg_validator:
            try:
                await tg_validator.disconnect()
            except:
                pass
        return []
    
    # 3. VALIDATION PHASE
    validated_results = []
    
    if validate or api_mode:
        console.print(f"\n[brand]Iniciando fase de validación ({'API de Telegram' if api_mode else 'Scraping Web'})...[/]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30, complete_style="accent"),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task_val = progress.add_task("[magenta]Validando enlaces encontrados...", total=len(combined))
            
            for idx, item in enumerate(combined):
                url = item.get("url")
                
                # Fetch details depending on API / Web validation
                details = None
                if api_mode and tg_validator:
                    # Use Telegram API validator
                    details = await tg_validator.validate_link(url)
                    # Respectful pause to avoid flood waits
                    await asyncio.sleep(0.3)
                    
                    # Check if we got flood wait error and handle
                    if details and details.get("error") and "Flood wait" in str(details.get("error")):
                        console.print(f"[warning]⚠️ Flood wait detectado, pausando validaciones...[/]")
                        # Wait longer and continue
                        await asyncio.sleep(5)
                else:
                    # Web validation via scraping preview
                    details = parse_telegram_preview(url)
                    # Respectful scraping delay
                    await asyncio.sleep(random.uniform(0.5, 1.2))
                
                if details and details.get("valid", False):
                    # Merge information into final result
                    final_item = {
                        "url": url,
                        "title": details.get("title") or item.get("title") or "Sin título",
                        "description": details.get("description") or item.get("snippet") or "Sin descripción",
                        "type": details.get("type", "Desconocido"),
                        "members": details.get("members"),
                        "online": details.get("online"),
                        "status": "Válido",
                        "source": item.get("source", "Mezclado"),
                        "invite_hash": details.get("invite_hash"),
                        "username": details.get("username"),
                    }
                    validated_results.append(final_item)
                else:
                    # If validation failed but web search returned it,
                    # keep it as unverified (only in non-strict API mode)
                    if not api_mode:
                        validated_results.append({
                            "url": url,
                            "title": item.get("title") or "Sin título",
                            "description": item.get("snippet") or "Sin descripción",
                            "type": "Desconocido",
                            "members": None,
                            "status": "No verificado",
                            "source": item.get("source"),
                            "invite_hash": item.get("invite_hash"),
                            "username": item.get("username"),
                        })
                    # In API mode, we skip invalid results entirely
                
                # Update progress
                progress.advance(task_val, amount=100 // len(combined) if combined else 0)
    else:
        # No validation, just use the search engine raw results
        for item in combined:
            validated_results.append({
                "url": item.get("url"),
                "title": item.get("title") or "Sin título",
                "description": item.get("snippet") or "Sin descripción",
                "type": "Grupo/Canal" if "/joinchat/" in item.get("url", "") or "/+" in item.get("url", "") else "Público",
                "members": None,
                "status": "No verificado",
                "source": item.get("source"),
                "invite_hash": item.get("invite_hash"),
                "username": item.get("username"),
            })
    
    # 4. Apply filters (only-groups or only-channels)
    final_filtered = []
    for r in validated_results:
        ctype = r.get("type", "").lower()
        if filter_type == "groups":
            if any(kw in ctype for kw in ["grupo", "chat", "group"]):
                final_filtered.append(r)
        elif filter_type == "channels":
            if any(kw in ctype for kw in ["canal", "channel"]):
                final_filtered.append(r)
        else:
            final_filtered.append(r)
    
    # Close Telegram client if applicable
    if tg_validator:
        try:
            await tg_validator.disconnect()
        except Exception:
            pass
    
    return final_filtered


def display_results_table(results):
    """
    Renders the beautiful results table using Rich.
    Includes enhanced formatting with status icons, type coloring, and member counts.
    """
    table = Table(
        title=f"\n[brand]Resultados Encontrados ({len(results)})[/brand]", 
        header_style="bold royal_blue1",
        border_style="dim white",
        show_lines=True
    )
    
    table.add_column("Estado", justify="center", style="bold")
    table.add_column("Título / Nombre", style="brand", width=25)
    table.add_column("Enlace", style="cyan", no_wrap=True)
    table.add_column("Tipo", justify="center")
    table.add_column("Miembros", justify="right", style="green")
    table.add_column("Descripción / Resumen", style="dim white", width=40)
    
    for r in results:
        status = r.get("status", "No verificado")
        status_icon = "✅" if status == "Válido" else "⏳" if status == "No verificado" else "🔍"
        
        title = r.get("title", "Sin título")
        url = r.get("url", "")
        ctype = r.get("type", "Desconocido")
        
        # Color code type tag with better mapping
        type_style_map = {
            "canal": "bold magenta",
            "supergrupo": "bold magenta",
            "canal público": "bold magenta",
            "grupo": "bold orange3",
            "grupo público": "bold orange3",
            "supergrupo público": "bold orange3",
            "bot": "bold green",
            "usuario/bot": "bold green",
        }
        
        # Find matching style
        type_style = "bold cyan"  # default
        for key, style in type_style_map.items():
            if key in ctype.lower():
                type_style = style
                break
        
        type_display = f"[{type_style}]{ctype}[/]"
        
        # Format members count with online indicator
        members = r.get("members")
        if members is not None:
            members_str = f"{members:,}"
            online = r.get("online")
            if online:
                members_str += f"\n[dim]{online:,} en línea[/dim]"
        else:
            members_str = "-"
        
        desc = r.get("description", "Sin descripción")
        # Truncate description if too long
        if len(desc) > 80:
            desc = desc[:77] + "..."
        
        # Escape user-generated text to prevent Rich markup errors
        title = escape(title)
        desc = escape(desc)
        url = escape(url)
        
        table.add_row(
            status_icon,
            title,
            url,
            type_display,
            members_str,
            desc
        )
    
    console.print(table)


def export_results(results, file_path):
    """
    Exports search results to CSV, JSON, or Markdown depending on file extension.
    Uses the configuration module for default format settings.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == ".json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
        elif ext == ".csv":
            if not results:
                console.print("[warning]No hay resultados para exportar a CSV.[/]")
                return
            
            # Determine fieldnames from results keys
            fieldnames = list(results[0].keys()) if results else []
            
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
        elif ext in [".md", ".markdown"]:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# Resultados de búsqueda de Telegram\n\n")
                f.write(f"Total encontrados: {len(results)}\n\n")
                f.write("| Título | Tipo | Miembros | Enlace | Descripción |\n")
                f.write("| --- | --- | --- | --- | --- |\n")
                for r in results:
                    title = r.get("title", "Sin título").replace("|", "\\|")
                    ctype = r.get("type", "Desconocido")
                    members = r.get("members", "-")
                    url = r.get("url", "")
                    desc = r.get("description", r.get("snippet", "Sin descripción")).replace("|", "\\|")
                    f.write(f"| {title} | {ctype} | {members} | [{url}]({url}) | {desc} |\n")
        else:
            # Fallback to JSON with configured default format
            default_format = OUTPUT_DEFAULT_FORMAT or ".json"
            fallback_ext = default_format if default_format.startswith(".") else f".{default_format}"
            logger.warning(f"Formato de salida desconocido '{ext}', usando {fallback_ext}")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
        
        console.print(f"\n[success]✓[/success] Resultados exportados exitosamente a [bold cyan]{file_path}[/bold cyan]")
    except Exception as e:
        console.print(f"\n[error]✕ Error al exportar resultados:[/] {e}")
        logger.error(f"Export error: {e}", exc_info=True)


if __name__ == "__main__":
    main()