# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from dotenv import load_dotenv
import sys
import uuid
from http import HTTPStatus
import traceback
from datetime import datetime
load_dotenv()

from aiohttp import web
from aiohttp.web import Request, Response, json_response
from botbuilder.core import (
    BotFrameworkAdapterSettings,
    TurnContext,
    BotFrameworkAdapter,
    MemoryStorage,
    
    ConversationState,
    UserState
)
from typing import Dict
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity, ActivityTypes, ConversationReference
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication

from bot import MyBot
from config import DefaultConfig

MEMORY = MemoryStorage()


CONVERSATION_STATE = ConversationState(MEMORY)

USER_STATE = UserState(MEMORY)

CONFIG = DefaultConfig()

# Create adapter.
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
#SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
#ADAPTER = BotFrameworkAdapter(SETTINGS)
ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(CONFIG))



# Catch-all for errors.
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )
    # Send a trace activity if we're talking to the Bot Framework Emulator
    if context.activity.channel_id == "emulator":
        # Create a trace activity that contains the error object
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        # Send a trace activity, which will be displayed in Bot Framework Emulator
        await context.send_activity(trace_activity)


CONVERSATION_REFERENCES: Dict[str, ConversationReference] = dict()

ADAPTER.on_turn_error = on_error

# If the channel is the Emulator, and authentication is not in use, the AppId will be null.
# We generate a random AppId for this case only. This is not required for production, since
# the AppId will have a value.
APP_ID = CONFIG.APP_ID if CONFIG.APP_ID else str(uuid.uuid4())

# Create the Bot
BOT = MyBot(CONVERSATION_STATE, USER_STATE, CONVERSATION_REFERENCES)


async def messages2(req: Request) -> Response:
    return await ADAPTER.process(req, BOT)

# Listen for incoming requests on /api/messages
async def messages(req: Request) -> Response:
    # Main bot message handler.
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
        
    else:
        return Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    if response:
        return json_response(data=response.body, status=response.status)
    return Response(status=201)

# Send a message to all conversation members.
# This uses the shared Dictionary that the Bot adds conversation references to.
async def _send_proactive_message(body):
    print('_send_proactive_message')
    for conversation_reference in CONVERSATION_REFERENCES.values():
        await ADAPTER.continue_conversation(
            conversation_reference,
            lambda turn_context: BOT.proactiveMessage(turn_context, body),
            APP_ID,
        )

async def notify(req: Request) -> Response:  # pylint: disable=unused-argument
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
        print(body)
    await _send_proactive_message(body)
    return Response(status=HTTPStatus.OK, text="Proactive messages have been sent")

async def force_exception(req: Request) -> Response:  # pylint: disable=unused-argument
    if 1 == 1:
        raise Exception("Forced Exception")
    return Response(status=HTTPStatus.OK, text="This is never reached")

async def health(req: Request) -> Response:  # pylint: disable=unused-argument
    return Response(status=HTTPStatus.OK, text="Healthy")


APP = web.Application(middlewares=[aiohttp_error_middleware])
APP.router.add_post("/api/messages", messages2)
APP.router.add_get("/api/notify", notify)
APP.router.add_post("/api/notify", notify)
APP.router.add_get("/api/health", health)
APP.router.add_get("/api/exception", force_exception)


if __name__ == "__main__":
    try:
        web.run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        raise error
