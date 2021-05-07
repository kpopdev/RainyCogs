import json
import logging
import discord
import websockets
import asyncio
import datetime
from redbot.core import commands


class IPN(commands.Cog):
    # init method or constructor
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bot = bot
        self.socket_task = self.bot.loop.create_task(self.wsrun())
        self.log = logging.getLogger("red")

        #loop = asyncio.get_event_loop()
        #loop.run_until_complete(self.wsrun())

    async def listen(self, websocket, path):
        try:
            self.log.debug("[IPN] Client connection established")
            while True:
                msg = await websocket.recv()
                data = json.loads(data)

                self.log.debug(f"[IPN] < {msg}")
                embed = discord.Embed(color=0xEE2222, title='Instant Payment Notification')
                # embed.description = msg

                for key, value in data.items():
                    embed.add_field(name=key, value=value)

                embed.set_thumbnail(url='https://upload.wikimedia.org/wikipedia/commons/a/a4/Paypal_2014_logo.png')
                await self.bot.get_channel(830267832889114644).send(embed=embed)

                await websocket.send("Hello")
        except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.ConnectionClosed):
            self.log.debug("[IPN] Client connection closed")

    async def wsrun(self):
        try:
            await websockets.serve(self.listen, "localhost", 8887)
            self.log.debug("[IPN] PayPal IPN websocket server started on port 8887")
            while True:
                await asyncio.sleep(1)
        except asyncio.exceptions.TimeoutError:
            self.log.warning("[IPN] Attempting to reconnect due to connection timeout")
            await self.wsrun()
        except websockets.exceptions.ConnectionClosed:
            self.log.warning("[IPN] Attempting to reconnect due to connection closed")
            await self.wsrun()
        except Exception as e:
            self.log.warning("[IPN] Attempting to reconnect due to: " + str(e))
            await self.wsrun()

    def cog_unload(self):
        self.socket_task.cancel()
        self.bot.loop.create_task(self.websocket.close())


#IPN(None)
