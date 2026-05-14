import json
import asyncio
from expression_module.expression_module import ExpressionModule

class Modeling:

    def __init__(self, agent=None):
        self.agent = agent

    async def execute(self):
        #Receive From Perception Layer 
        #High Level Verbals and NonVerbals

        #Recieves from Perception:
        # - Whos turn is it
        # - What SD was said
        # - What is the Object held (If Applicable)
        # - What is the Emotion displayed (If Applicable) 

        #Recieves from Trial Manager
        # - Correctness, Ex: Correct, No Response, Incorrect
        # - Challenge, Ex: None, Low, Medium, High
        # - Verbal, Ex: Text, Volume
        # - Nonverbals, Ex: Shake Head, Nod Head, Smile
        # - Problem Behavior Type, Ex: Positive Reinforcement, Negative Reinforcement, Automatic Reinforcement

        #Modeling consists of the trainer robot leading the user through an example session of DTT acting as the BT/User
        print("Executing instruction module")

        with open("instruction_data.json", "r") as f:
            data = json.load(f)

        steps = data["steps"]

        # Create expression module once
        expr = ExpressionModule()

        for step in steps:

            packet = expr.build(step)

            await expr.execute(packet)

            # optional pacing between teaching steps
            await asyncio.sleep(1.0)