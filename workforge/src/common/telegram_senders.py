import asyncio
from typing import List, Optional
import logging
import aiohttp

logger = logging.getLogger(__name__)

async def asend_messages(
    bot_token: str,
    channel_id: str,
    messages: List[str],
    client_session: Optional[aiohttp.ClientSession] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
    **kwargs,
) -> List[dict]:

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    parse_mode = kwargs.get("parse_mode")
    own_session = client_session is None

    async def send_one(session: aiohttp.ClientSession, msg: str, attempts=2):
        body = {
            "chat_id": channel_id,
            "text": msg,
        }
        if parse_mode:
            body["parse_mode"] = parse_mode
        try:
            async with session.post(url, json=body) as resp:
                resp.raise_for_status()
                return await resp.json()
        except Exception as e:
            if attempts:
                attempts -= 1
                await asyncio.sleep(1)
                return await send_one(session, msg)
            logger.critical(f"Failed to send message to {channel_id}: {e}")
            raise e

    async def runner(session: aiohttp.ClientSession):
        if semaphore:

            async def limited(msg: str):
                async with semaphore:
                    return await send_one(session, msg)

            tasks = [limited(m) for m in messages]
        else:
            tasks = [send_one(session, m) for m in messages]
        return await asyncio.gather(*tasks)

    if own_session:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            return await runner(session)
    else:
        return await runner(client_session)
