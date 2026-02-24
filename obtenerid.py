from telethon import TelegramClient
api_id = 33294466
api_hash = '921e396864d7e531149c8815221be47b'

client = TelegramClient('session_name',api_id,api_hash)

async def main():
    #entity = await client.get_entity('https://t.me/+F5Tr4lTM3sBjYzE5')#enlace del canal pago)
    entity = await client.get_entity('https://t.me/+WUemnZVDIwxkZmFh')#enlace del canal mio)
    print('ID interno del canal:', entity.id)
with client:
    client.loop.run_until_complete(main())