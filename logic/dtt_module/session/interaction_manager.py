import asyncio

class InteractionManager:

    def __init__(self, agent):
        self.agent = agent

    async def speak_text(
        self,
        expr,
        text: str,
    ):

        packet_data = {
            "embodiment": "trainer",
            "verbal": {
                "text": text
            },
            "nonverbals": [
                {
                    "channel": "face",
                    "action": "Happy",
                    "intensity": 0.5,
                    "duration": 1.0,
                    "timing": "during",
                }
            ],
        }

        packet = expr.build(packet_data)

        await expr.execute(
            self.agent,
            packet_data["embodiment"],
            packet,
        )

        sleep_time = (
            len(text) / 14
        ) * 1.15

        await asyncio.sleep(
            sleep_time + 0.5
        )

    async def set_led(self, expr, color, action, flash, embodiment):
        turn = {
            "embodiment": "kid",
            "verbal": {
                "text": " "
            },
            "nonverbals": [
                {
                    "channel": "led",
                    "action": action,
                    "color": color,
                    "duration": 2.0
                }
            ]
        }

        packet = expr.build(turn)

        await expr.execute(
            agent_type=self.agent,
            embodiment=embodiment,
            packet=packet,
        )

        if flash:
            await asyncio.sleep(1.5)
            await self.set_led(expr=expr, color = "#00FF00", action = "on", flash=False, embodiment="kid")

        await asyncio.sleep(0.5)

    async def run_behavior(
        self,
        expr,
        behavior,
    ):

        packet = expr.build(behavior)

        await expr.execute(
            self.agent,
            behavior["embodiment"],
            packet,
        )

        sleep_time = min(
            (len(behavior["verbal"]["text"]) / 14) * 1.15,
            2.5
        )

        await asyncio.sleep(sleep_time + 0.5)
    