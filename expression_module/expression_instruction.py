import asyncio
import agent_layer.agent_layer as agent_layer

class ExpressionModuleInstruction:
    """"This class represents the low-level expression instruction that will be exhibited by the agent."""
    # Eventually, this class will take in inputs from the perception module to make decisions about what the agent should do.
    def __init__(self, text, nonverbals):
        self.instruction_text = text
        self.nonverbals = nonverbals

    async def execute(self):
        # For now, use the passed text and nonverbals as the instruction to be executed by the agent layer. 
        # In the future, this is where the logic for interpreting the instruction and determining the appropriate behavior will be implemented.
        print("In the execution of the expression module instruction")
        await agent_layer.agent_layer(text=self.instruction_text, nonverbals=self.nonverbals, agent_type="Furhat")

    def create_behavior():
        verbal = VerbalComponent(text=self.text)
        nonverbal = NonverbalComponent()
        behavior = Behavior(verbal=verbal, nonverbals=nonverbal)


class Behavior:
    def __init__(self, verbal=None, nonverbals=None):
        self.verbal = verbal
        self.nonverbals = nonverbals or []


class VerbalComponent:
    def __init__(self, text, duration=None, num_repeat=1):
        self.text = text
        self.duration = duration
        self.num_repeat = num_repeat


class NonverbalComponent:
    def __init__(self, name, intensity=1.0, duration=1.0, num_repeat=1):
        self.name = name
        self.intensity = intensity
        self.duration = duration
        self.num_repeat = num_repeat


class BehaviorBuilder:

    @staticmethod
    def build(request):

        # Choose verbal response
        verbal_text = request["verbals"][0]

        verbal = VerbalComponent(
            text=verbal_text,
            duration=len(verbal_text) * 0.08
        )

        nonverbals = []

        for nv in request["nonverbals"]:

            duration = 1.0

            # Example logic
            if request["challenge_level"] > 3:
                duration *= 1.5

            if request["correctness"] == "incorrect":
                duration *= 1.2

            nonverbals.append(
                NonverbalComponent(
                    name=nv["name"],
                    intensity=nv["intensity"],
                    duration=duration
                )
            )

        return Behavior(
            verbal=verbal,
            nonverbals=nonverbals
        )