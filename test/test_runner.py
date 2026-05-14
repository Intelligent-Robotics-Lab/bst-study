import asyncio
from logic.instruction import Instruction
from logic.modeling import Modeling


async def main():

    print("\n==============================")
    print("STARTING EXPRESSION PIPELINE TEST")
    print("==============================\n")

    instruction_system = Modeling(agent="Furhat")

    await instruction_system.execute()

    print("\n==============================")
    print("TEST COMPLETE")
    print("==============================\n")


if __name__ == "__main__":
    asyncio.run(main())