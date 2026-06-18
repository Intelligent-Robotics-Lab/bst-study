import asyncio

from Perception.sample_interaction import (
    SampleInteractionAgent,
)

from Perception.perception_client import (
    PerceptionClient,
)


class PerceptionManager:

    def __init__(
        self,
        server_host="141.210.88.210",
        server_port=8000,
        silence_timeout=2.0,
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.silence_timeout = silence_timeout

        self.agent = None
        self.client = None
        self.task = None

    async def run_perception(
        self,
        client,
        agent,
    ):

        async for event in client.events():

            event_type = event.get(
                "event_type"
            )

            payload = event.get(
                "payload",
                {},
            )

            if event_type == "asr_update":

                agent.handle_asr(
                    payload
                )

            elif event_type == "emotion_update":

                agent.handle_emotion(
                    payload
                )

    async def start(self):

        self.agent = (
            SampleInteractionAgent(
                silence_timeout=
                self.silence_timeout
            )
        )

        self.client = (
            PerceptionClient(
                server_host=
                self.server_host,
                server_port=
                self.server_port,
            )
        )

        self.task = asyncio.create_task(
            self.run_perception(
                self.client,
                self.agent,
            )
        )

        return self.task

    async def stop(self):

        if self.task:

            self.task.cancel()

    @property
    def state(self):

        return self.agent.state