import asyncio

import child_behavior_library as child_library
import child_behavior_components as child


FURHAT_CHILD_IP = "141.210.88.11"

async def main():
    furhat = await child.connect_furhat(FURHAT_CHILD_IP)
    await child_library.nr_problem_behavior(furhat=furhat)
    
    asyncio.sleep(6)

    await child_library.pr_problem_behavior(furhat=furhat)

    asyncio.sleep(3)

    furhat.disconnect()

if __name__ == "__main__":
    asyncio.run(main())