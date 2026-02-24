
import os
from telethon import TelegramClient, events
from telethon.tl.types import MessageService, MessageMediaWebPage

#si esto no funciona ponerlo con los valores fijos
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
source_channel = int(os.getenv("SOURCE_CHANNEL"))
target_channel = int(os.getenv("TARGET_CHANNEL"))


client = TelegramClient('session_name', api_id, api_hash)

CHECKPOINT_FILE = "checkpoint.txt"

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

    last_id = get_checkpoint()

    # Si hay checkpoint, usar min_id; si no, copiar todo
    if last_id:
        iterator = client.iter_messages(source, reverse=True, min_id=last_id)
    else:
        iterator = client.iter_messages(source, reverse=True)

    async for message in iterator:
        if isinstance(message, MessageService):
            continue

        if message.media and not isinstance(message.media, MessageMediaWebPage):
            caption = ""
            if message.text:
                texto = segunda_mitad(message.text) if len(message.text) > 4000 else message.text
                caption = limpiar_texto(texto)
            await client.send_file(target, message.media, caption=caption)
        elif message.text:
            texto = segunda_mitad(message.text) if len(message.text) > 4000 else message.text
            await client.send_message(target, limpiar_texto(texto))

        # Guardar checkpoint
        save_checkpoint(message.id)

@client.on(events.NewMessage(chats=source_channel))
async def handler(event):
    target = await client.get_entity(target_channel)
    if isinstance(event.message, MessageService):
        return

    if event.message.media and not isinstance(event.message.media, MessageMediaWebPage):
        caption = ""
        if event.message.text:
            texto = segunda_mitad(event.message.text) if len(event.message.text) > 4000 else event.message.text
            caption = limpiar_texto(texto)
        await client.send_file(target, event.message.media, caption=caption)
    elif event.message.text:
        texto = segunda_mitad(event.message.text) if len(event.message.text) > 4000 else event.message.text
        await client.send_message(target, limpiar_texto(texto))

    # Guardar checkpoint también en tiempo real
    save_checkpoint(event.message.id)

with client:
    client.start()
    client.loop.run_until_complete(copiar_historial())
    client.run_until_disconnected()