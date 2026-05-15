import json
import asyncio
from expression_module.expression_module import ExpressionModule


class Instruction:

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

        #Instruction phase should allow for play back and user interaction in order to maintain participant attention and engagement
        print("Executing instruction module")

        with open("data/instruction_data.json", "r") as f:
            data = json.load(f)

        steps = data["steps"]

        # Create expression module once
        expr = ExpressionModule()

        for step in steps:

            packet = expr.build(step)
            #From Perception check to see if user wants to repeat the last step for clarity if the ASR ever picks up user audio that says to stop or repeat or something similar have it replay the current step in the insturction phase
            await expr.execute(agent_type=self.agent, embodiment=step["embodiment"],packet=packet)

            # optional pacing between teaching steps
            await asyncio.sleep(1.0)