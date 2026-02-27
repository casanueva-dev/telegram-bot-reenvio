import os
import asyncio
import logging
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import MessageService, MessageMediaWebPage, MessageActionChatEditPhoto
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import EditPhotoRequest
from telethon.tl.types import InputChatUploadedPhoto

# Activar logging para ver actividad en Render
logging.basicConfig(level=logging.INFO)

# Variables de entorno
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
source_channel = int(os.getenv("SOURCE_CHANNEL"))
target_channel = int(os.getenv("TARGET_CHANNEL"))

client = TelegramClient('session_name', api_id, api_hash)

CHECKPOINT_FILE = "checkpoint.txt"
DELAY = 3  # segundos de pausa entre cada envío

def get_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return int(f.read().strip())
    return None

def save_checkpoint(message_id):
    with open(CHECKPOINT_FILE, "w") as f:
        f.write(str(message_id))

def limpiar_texto(texto):
    import re
    if not texto:
        return ""
    texto = re.sub(r'\S*@\S*', '', texto)           # quita menciones
    texto = re.sub(r'http\S+|www\.\S+', '', texto)  # quita enlaces
    return texto.strip()

def segunda_mitad(texto):
    mitad = len(texto) // 2
    return texto[mitad:]

async def copiar_historial():
    source = await client.get_entity(source_channel)
    target = await client.get_entity(target_channel)

    yesterday = datetime.utcnow() - timedelta(days=1)

    last_id = get_checkpoint()
    if last_id:
        iterator = client.iter_messages(source, reverse=True, min_id=last_id)
    else:
        iterator = client.iter_messages(source, reverse=True, offset_date=yesterday)

    async for message in iterator:
        try:
            if isinstance(message, MessageService):
                continue

            if message.media and not isinstance(message.media, MessageMediaWebPage):
                caption = ""
                if message.text:
                    texto = segunda_mitad(message.text) if len(message.text) > 4000 else message.text
                    caption = limpiar_texto(texto)
                await client.send_file(target, message.media, caption=caption)
                await asyncio.sleep(DELAY)
            elif message.text:
                texto = segunda_mitad(message.text) if len(message.text) > 4000 else message.text
                texto_limpio = limpiar_texto(texto)
                if texto_limpio:
                    await client.send_message(target, texto_limpio)
                    await asyncio.sleep(DELAY)

            save_checkpoint(message.id)
            logging.info(f"Historial: reenviado mensaje {message.id}")

        except FloodWaitError as e:
            logging.warning(f"FloodWait: esperando {e.seconds} segundos...")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logging.error(f"Error en copiar_historial: {e}")

@client.on(events.NewMessage(chats=source_channel))
async def handler(event):
    try:
        target = await client.get_entity(target_channel)

        # 🔥 Detectar cambio de foto de perfil
        if isinstance(event.message, MessageService) and isinstance(event.message.action, MessageActionChatEditPhoto):
            file = await event.download_media()
            if file:
                await client(EditPhotoRequest(
                    channel=target_channel,
                    photo=InputChatUploadedPhoto(
                        file=await client.upload_file(file)
                    )
                ))
                logging.info("Foto de perfil sincronizada con el canal origen")
            return  # no procesar más este evento

        # Procesar mensajes normales
        if isinstance(event.message, MessageService):
            return

        if event.message.media and not isinstance(event.message.media, MessageMediaWebPage):
            caption = ""
            if event.message.text:
                texto = segunda_mitad(event.message.text) if len(event.message.text) > 4000 else event.message.text
                caption = limpiar_texto(texto)
            await client.send_file(target, event.message.media, caption=caption)
            await asyncio.sleep(DELAY)
        elif event.message.text:
            texto = segunda_mitad(event.message.text) if len(event.message.text) > 4000 else event.message.text
            texto_limpio = limpiar_texto(texto)
            if texto_limpio:
                await client.send_message(target, texto_limpio)
                await asyncio.sleep(DELAY)

        save_checkpoint(event.message.id)
        logging.info(f"Tiempo real: reenviado mensaje {event.message.id}")

    except FloodWaitError as e:
        logging.warning(f"FloodWait en tiempo real: esperando {e.seconds} segundos...")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logging.error(f"Error en handler: {e}")

async def main():
    async with client:
        logging.info("Bot iniciado, conectando a Telegram...")
        await copiar_historial()  # copiar solo una vez
        await client.run_until_disconnected()  # luego solo escucha lo nuevo

if __name__ == "__main__":
    asyncio.run(main())
