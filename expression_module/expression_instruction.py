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