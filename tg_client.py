"""
Telegram API Validator using Telethon.

Provides functionality to:
- Connect to Telegram API with proper session management
- Validate invite links (joinchat and +) without joining
- Resolve usernames to get full metadata
- Search Telegram's global public database
- Handle flood waits and speed limits gracefully
"""

import asyncio
import logging
import os
import re
from typing import Optional, Dict, Any

from telethon import TelegramClient, functions, types
from telethon.errors import (
    rpcbaseerrors,
    FloodWaitError,
    RPCError,
    UsernameNotOccupiedError,
    FloodWaitError as TelethonFloodWaitError,
)

# Configure logging
logger = logging.getLogger(__name__)


class TelegramValidator:
    """
    Telegram API Validator using Telethon.
    
    Features:
    - Session persistence with automatic phone/code prompting
    - Flood wait handling with automatic pauses
    - Comprehensive error classification
    - Parallel validation capabilities
    - Username and invite link validation
    """
    
    def __init__(self, api_id: int, api_hash: str, 
                 session_name: str = "sc_tel_session",
                 phone: str = None):
        """
        Initialize the Telegram validator.
        
        Args:
            api_id: Telegram API ID from my.telegram.org
            api_hash: Telegram API hash from my.telegram.org
            session_name: Name for the session file (default: sc_tel_session)
            phone: Phone number with country code (e.g., "+521234567890")
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.phone = phone
        self.client = None
        self._flood_wait_count = 0
    
    async def connect(self) -> TelegramClient:
        """
        Initialize and start the Telethon client.
        Handles phone prompting, code entry, and 2FA if needed.
        
        Returns:
            Connected TelegramClient instance
            
        Raises:
            Exception: If connection fails after all attempts
        """
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        await self.client.connect()
        
        # If not authorized, prompt for phone and code
        if not await self.client.is_user_authorized():
            # Send code request
            await self.client.send_code_request(self.phone or input("Número de teléfono: "))
            
            # Get the code from user
            code = input("Código de verificación: ")
            try:
                await self.client.sign_in(self.phone or input("Número de teléfono: "), code)
            except RPCError as e:
                # Handle phone number password (2FA)
                if "PRIVATE_CODE" in str(e) or "2FA" in str(e).upper():
                    password = input("Contraseña de 2FA: ")
                    await self.client.sign_in(self.phone or input("Número de teléfono: "), password)
                else:
                    raise
        
        logger.info("Conectado exitosamente a Telegram API")
        return self.client
    
    async def disconnect(self):
        """Gracefully disconnect the Telegram client."""
        if self.client:
            try:
                await self.client.disconnect()
                logger.info("Desconectado de Telegram API")
            except Exception as e:
                logger.warning(f"Error al desconectar: {e}")
    
    async def _handle_flood_wait(self, error: FloodWaitError) -> None:
        """
        Handle Telegram flood wait errors by pausing execution.
        
        Args:
            error: The FloodWaitError instance
        """
        wait_seconds = error.value
        logger.warning(f"Flood wait requerido: {wait_seconds} segundos")
        self._flood_wait_count += 1
        
        # Wait with a small buffer
        await asyncio.sleep(wait_seconds + 5)
        
        # Log the incident
        if self._flood_wait_count == 1:
            logger.warning("Se detecto wait por límite de tasa. Reducirá la frecuencia de requests.")
        elif self._flood_wait_count <= 3:
            logger.info(f"Wait #{self._flood_wait_count} completado, reanudando...")
    
    async def check_invite_link(self, invite_hash: str) -> Dict[str, Any]:
        """
        Validates an invite link (joinchat or +link) without joining it.
        
        Returns comprehensive chat information including:
        - Validity status
        - Chat title and description
        - Member count
        - Chat type (group, supergroup, channel)
        - Restriction status
        - Whether already joined
        
        Args:
            invite_hash: The invite hash from joinchat/... or +link
            
        Returns:
            Dictionary with validation results
        """
        if not self.client:
            raise RuntimeError("Cliente de Telegram no conectado.")
        
        try:
            # CheckChatInviteRequest returns ChatInvite, ChatInviteAlready, or ChatInvitePeek
            result = await self.client(functions.messages.CheckChatInviteRequest(hash=invite_hash))
            
            # Handle ChatInviteAlready (user already in chat)
            if isinstance(result, types.ChatInviteAlready):
                chat = result.chat
                member_count = getattr(chat, 'participants_count', None)
                # Determine chat type properly
                if isinstance(chat, types.Channel):
                    if getattr(chat, 'megagroup', False):
                        chat_type = "Supergrupo Público"
                    else:
                        chat_type = "Canal Público"
                elif isinstance(chat, types.Chat):
                    chat_type = "Grupo Público"
                else:
                    chat_type = "Chat Desconocido"
                
                return {
                    "valid": True,
                    "title": chat.title,
                    "description": getattr(chat, 'about', "Sin descripción"),
                    "type": chat_type,
                    "members": member_count,
                    "joined": True,
                    "restricted": getattr(chat, 'restricted', False),
                    "participants_count": getattr(chat, 'participants_count', None),
                    "is_megagroup": isinstance(chat, types.Channel) and getattr(chat, 'megagroup', False),
                }
            
            # Handle ChatInvite (valid invite, not joined yet)
            elif isinstance(result, types.ChatInvite):
                member_count = getattr(result, 'participants_count', None)
                if hasattr(result, 'megagroup') and result.megagroup:
                    chat_type = "Supergrupo Público"
                elif hasattr(result, 'channel') and result.channel:
                    chat_type = "Canal Público"
                else:
                    chat_type = "Grupo Público"
                
                return {
                    "valid": True,
                    "title": getattr(result, 'title', 'Sin título'),
                    "description": getattr(result, 'about', "Sin descripción"),
                    "type": chat_type,
                    "members": member_count,
                    "joined": False,
                    "restricted": getattr(result, 'restricted', False),
                    "is_megagroup": getattr(result, 'megagroup', False),
                    "channel": getattr(result, 'channel', None),
                }
            
            # Handle ChatInvitePeek (valid invite, peeking allowed)
            elif isinstance(result, types.ChatInvitePeek):
                chat = result.chat
                member_count = getattr(chat, 'participants_count', None)
                if isinstance(chat, types.Channel):
                    if getattr(chat, 'megagroup', False):
                        chat_type = "Supergrupo Público"
                    else:
                        chat_type = "Canal Público"
                elif isinstance(chat, types.Chat):
                    chat_type = "Grupo Público"
                else:
                    chat_type = "Chat Desconocido"
                
                return {
                    "valid": True,
                    "title": chat.title,
                    "description": getattr(chat, 'about', "Sin descripción"),
                    "type": chat_type,
                    "members": member_count,
                    "joined": False,
                    "restricted": getattr(chat, 'restricted', False),
                    "is_megagroup": isinstance(chat, types.Channel) and getattr(chat, 'megagroup', False),
                }
            
            # Unexpected result type
            else:
                logger.warning(f"Tipo de resultado inesperado: {type(result)}")
                return {
                    "valid": False,
                    "error": f"Tipo de resultado inesperado: {type(result).__name__}",
                    "title": "",
                    "description": "",
                    "type": "Desconocido",
                    "members": None,
                    "joined": False,
                }
        
        except TelethonFloodWaitError as e:
            await self._handle_flood_wait(e)
            # Retry after waiting
            if self.client:
                return await self.check_invite_link(invite_hash)
            return {"valid": False, "error": "Flood wait durante reintentos"}
        
        except rpcbaseerrors.BadRequestError as e:
            error_str = str(e)
            if "INVITE_HASH_EXPIRED" in error_str:
                return {"valid": False, "error": "El enlace de invitación ha expirado o es inválido."}
            elif "CHANNEL_PRIVATE" in error_str:
                return {"valid": False, "error": "El canal/grupo es privado y requiere invitación."}
            elif "USER_DEACTIVATED" in error_str:
                return {"valid": False, "error": "El usuario asociado al enlace ha sido dado de baja."}
            else:
                logger.warning(f"BadRequestError: {error_str}")
                return {"valid": False, "error": f"Error de enlace: {error_str}"}
        
        except RPCError as e:
            logger.error(f"RPCError validating invite link: {e}")
            return {"valid": False, "error": f"Error de API de Telegram: {str(e)[:100]}"}
        
        except Exception as e:
            logger.error(f"Unexpected error validating invite link: {e}")
            return {"valid": False, "error": f"Error inesperado: {str(e)[:100]}"}
    
    async def check_username(self, username: str) -> Dict[str, Any]:
        """
        Resolves a public username to get its metadata.
        
        Supports:
        - Public channels and groups
        - Supergroups (megagroups)
        - Individual users and bots
        - Full metadata extraction (members, description, about, etc.)
        
        Args:
            username: Telegram username (without @ prefix)
            
        Returns:
            Dictionary with entity metadata
        """
        if not self.client:
            raise RuntimeError("Cliente de Telegram no conectado.")
        
        # Clean username - remove @ if present and @s
        clean_username = username.lstrip("@")
        clean_username = re.sub(r"[?&].*$", "", clean_username)  # Remove query params
        
        try:
            entity = await self.client.get_entity(clean_username)
            
            # Determine type and extract metadata
            chat_type = "Usuario"
            member_count = None
            description = "Sin descripción"
            
            if isinstance(entity, types.Channel):
                if entity.megagroup:
                    chat_type = "Supergrupo Público"
                else:
                    chat_type = "Canal Público"
                
                # Get full channel info for detailed metadata
                try:
                    full_info = await self.client(functions.channels.GetFullChannelRequest(channel=entity))
                    member_count = full_info.full_chat.participants_count
                    description = full_info.full_chat.about or "Sin descripción"
                except RPCError as e:
                    logger.warning(f"No se pudieron obtener detalles completos: {e}")
                    member_count = getattr(entity, 'participants_count', None)
                    description = getattr(entity, 'about', "Sin descripción")
            
            elif isinstance(entity, types.Chat):
                chat_type = "Grupo Público"
                try:
                    full_info = await self.client(functions.messages.GetFullChatRequest(chat_id=entity.id))
                    # Get participants list
                    participants = getattr(full_info, 'full_chat', {})
                    participants_list = getattr(participants, 'participants', [])
                    member_count = len(getattr(participants_list, 'participants', [])) if participants_list else None
                    description = getattr(full_info, 'full_chat', {}).get('about', "Sin descripción")
                except RPCError as e:
                    logger.warning(f"No se pudieron obtener detalles del chat: {e}")
                    member_count = None
                    description = "Sin descripción"
            
            elif isinstance(entity, types.User):
                chat_type = "Usuario" if not entity.bot else "Bot"
                
                # Get full user info
                try:
                    full_info = await self.client(functions.users.GetFullUserRequest(id=entity))
                    description = full_info.full_user.about or "Sin descripción"
                except RPCError as e:
                    logger.warning(f"No se pudieron obtener detalles del usuario: {e}")
                    description = getattr(entity, 'about', "Sin descripción")
                
                # Add bot flag info
                if entity.bot:
                    chat_type = "Bot"
            
            else:
                logger.warning(f"Tipo de entidad inesperado: {type(entity)}")
                chat_type = "Desconocido"
            
            return {
                "valid": True,
                "title": getattr(entity, 'title', f"{getattr(entity, 'first_name', '')} {getattr(entity, 'last_name', '')}".strip()),
                "description": description,
                "type": chat_type,
                "members": member_count,
                "username": clean_username,
                "restricted": getattr(entity, 'restricted', False),
                "bot": getattr(entity, 'bot', False),
                "id": getattr(entity, 'id', None),
            }
        
        except UsernameNotOccupiedError:
            logger.warning(f"Username no encontrado: {clean_username}")
            return {
                "valid": False,
                "error": f"Username '{clean_username}' no encontrado o no disponible.",
                "title": "",
                "description": "",
                "type": "Desconocido",
                "members": None,
                "username": clean_username,
            }
        
        except RPCError as e:
            error_str = str(e)
            logger.error(f"RPCError checking username {username}: {error_str}")
            # Provide more user-friendly error messages
            if "FLOOD" in error_str.upper():
                return {"valid": False, "error": "Límite de tasa excedido. Espere antes de intentar nuevamente."}
            elif "USERNAME_INVALID" in error_str:
                return {"valid": False, "error": f"Username '{username}' es inválido."}
            elif "PEER_INVALID" in error_str:
                return {"valid": False, "error": "No se pudo resolver el peer. El usuario podría no existir."}
            else:
                return {"valid": False, "error": f"Error de API: {error_str[:100]}"}
        
        except Exception as e:
            logger.error(f"Unexpected error checking username {username}: {e}")
            return {
                "valid": False,
                "error": f"Error inesperado: {str(e)[:100]}",
                "title": "",
                "description": "",
                "type": "Desconocido",
                "members": None,
                "username": username,
            }
    
    async def search_global(self, query: str, limit: int = 50) -> list:
        """
        Natively searches Telegram global public database for channels/groups.
        
        Uses contacts.SearchRequest to find public chats matching the query.
        Returns results with URL, title, type, member count, etc.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of result dictionaries from Telegram's global search
        """
        if not self.client:
            raise RuntimeError("Cliente de Telegram no conectado.")
        
        results = []
        try:
            # contacts.SearchRequest returns contacts.Found
            # This searches across usernames, titles, and descriptions
            found = await self.client(functions.contacts.SearchRequest(q=query, limit=limit))
            
            # Process chats (which are Channels or Chats)
            for chat in found.chats:
                try:
                    chat_type = "Grupo/Supergrupo"
                    if isinstance(chat, types.Channel):
                        chat_type = "Supergrupo Público" if chat.megagroup else "Canal Público"
                    elif isinstance(chat, types.Chat):
                        chat_type = "Grupo Público"
                    
                    username = getattr(chat, 'username', None)
                    # Build proper URL
                    url = f"https://t.me/{username}" if username else None
                    
                    # Get additional info if possible
                    participants_count = getattr(chat, 'participants_count', None)
                    
                    results.append({
                        "url": url,
                        "title": chat.title,
                        "type": chat_type,
                        "username": username,
                        "members": participants_count,
                        "valid": True,
                        "source": "Telegram Global Search",
                        "participants_count": participants_count,
                    })
                except Exception as e:
                    logger.debug(f"Error processing chat in search: {e}")
                    continue
        
        except RPCError as e:
            logger.error(f"RPCError in global search: {e}")
            # Return what we have so far
        except Exception as e:
            logger.error(f"Unexpected error in global search: {e}")
        
        return results
    
    async def validate_link(self, url: str) -> Dict[str, Any]:
        """
        Generic validator that routes to check_invite_link or check_username.
        
        Handles all Telegram URL formats:
        - t.me/joinchat/XXXXXX (invite links)
        - t.me/+XXXXXX (alternative invite format)
        - t.me/username (public usernames/channels)
        - t.me/+username (alternative username format)
        
        Args:
            url: Telegram URL to validate
            
        Returns:
            Dictionary with validation results
        """
        # Normalize URL - ensure it has a protocol
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        # Extract the relevant part from the URL
        # Handle various URL formats
        url_clean = url.rstrip("/")
        
        if "/joinchat/" in url_clean:
            # Extract invite hash from joinchat URL
            invite_hash = url_clean.split("/joinchat/")[-1]
            # Remove any query parameters
            invite_hash = invite_hash.split("?")[0].split("&")[0]
            return await self.check_invite_link(invite_hash)
        
        elif "/+" in url_clean:
            # Extract invite hash from + format
            invite_hash = url_clean.split("/+")[-1]
            invite_hash = invite_hash.split("?")[0].split("&")[0]
            return await self.check_invite_link(invite_hash)
        
        else:
            # It's likely a username-based URL
            # Extract username from URL path
            # t.me/username or t.me/+username
            path_parts = url_clean.replace("https://t.me/", "").replace("http://t.me/", "").split("/")
            username = path_parts[-1] if path_parts else ""
            
            # Remove query parameters and hashes
            username = re.sub(r"[?&].*$", "", username)
            username = username.split("#")[0]
            
            # Remove + prefix if present
            username = username.lstrip("+")
            
            if username:
                return await self.check_username(username)
            else:
                return {
                    "valid": False,
                    "error": "No se pudo extraer un username válido de la URL.",
                    "title": "",
                    "description": "",
                    "type": "Desconocido",
                    "members": None,
                }