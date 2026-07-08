import asyncio
import json


class UnrealClient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):

        self.reader, self.writer = (
            await asyncio.open_connection(
                self.host,
                self.port
            )
        )

    async def send(self, packet):

        if self.writer is None:
            raise RuntimeError(
                "Unreal not connected."
            )

        data = json.dumps(packet)

        self.writer.write(
            (data + "\n").encode()
        )

        await self.writer.drain()

    async def disconnect(self):

        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()