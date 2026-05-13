import asyncio
from logic.instruction import Instruction


async def main():

    print("\n==============================")
    print("STARTING EXPRESSION PIPELINE TEST")
    print("==============================\n")

    instruction_system = Instruction(agent="Furhat")

    await instruction_system.execute()

    print("\n==============================")
    print("TEST COMPLETE")
    print("==============================\n")


if __name__ == "__main__":
    asyncio.run(main())