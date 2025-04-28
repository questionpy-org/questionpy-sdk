#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import logging
import os
import traceback

from aiohttp import ClientConnectionResetError, ClientConnectorError, ClientSession, web
from aiohttp.typedefs import Handler
from aiohttp.web_urldispatcher import MatchInfoError

VITE_DEV_SERVER = os.getenv("VITE_DEV_SERVER", "http://localhost:5173").rstrip("/")
WS_HEADERS = ("sec-websocket-extensions", "sec-websocket-key", "sec-websocket-version")

log = logging.getLogger("questionpy-sdk:web-server")


async def _proxy_websocket(request: web.Request) -> web.WebSocketResponse:
    url = f"{VITE_DEV_SERVER}{request.rel_url}"
    protocols = request.headers.get("sec-websocket-protocol", "").split(",")
    headers = ((k, v) for k, v in request.headers.items() if k in WS_HEADERS and v is not None)

    resp = web.WebSocketResponse(protocols=protocols)
    await resp.prepare(request)

    # Connect to the Vite dev server and relay messages
    async with (
        ClientSession() as session,
        session.ws_connect(url, headers=headers, protocols=protocols) as ws_client,
    ):
        try:
            async for msg in ws_client:
                if msg.type == web.WSMsgType.TEXT:
                    await resp.send_str(msg.data)
                elif msg.type == web.WSMsgType.BINARY:
                    await resp.send_bytes(msg.data)
                elif msg.type == web.WSMsgType.CLOSE:
                    await resp.close()
                    break
        except ClientConnectionResetError:
            await resp.close()

        return resp


@web.middleware
async def vite_devserver_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    # If request matched any route, we let it pass through
    if not isinstance(request.match_info, MatchInfoError):
        return await handler(request)

    # Handle Websocket connection (used by HMR, dev tools, etc.)
    if request.path == "/" and request.headers.get("upgrade", "").lower() == "websocket":
        return await _proxy_websocket(request)

    # Everything else is proxied to Vite
    try:
        async with (
            ClientSession() as session,
            session.request(
                method=request.method,
                url=f"{VITE_DEV_SERVER}{request.rel_url}",
                headers=request.headers,
                allow_redirects=False,
                data=await request.read(),
            ) as resp,
        ):
            headers = {key: value for key, value in resp.headers.items() if key.lower() != "transfer-encoding"}
            return web.Response(status=resp.status, body=await resp.read(), headers=headers)
    except ClientConnectorError:
        msg = "Could not connect to Vite dev server. Is it running?"
        log.exception(msg)
        return web.Response(status=500, text=msg)
    except Exception:
        msg = "Unhandled error while proxying to Vite dev server."
        log.exception(msg)
        return web.Response(status=500, text=f"{msg}\n\n{traceback.format_exc()}")
