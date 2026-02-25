import json
from channels.generic.websocket import AsyncWebsocketConsumer


class MunsiRequestConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]

        if user.is_anonymous or user.role != "gd_munsi":
            await self.close()
        else:
            self.group_name = f"munsi_{user.id}"

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def new_request(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_request",
            "data": event["data"]
        }))