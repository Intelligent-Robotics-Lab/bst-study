import asyncio
import agent_layer.Furhat.furhat_behavior_components as kid

async def nr_problem_behavior(furhat):
    await asyncio.gather(
        kid.start_gesture(furhat=furhat, gesture="Shake", intensity=5, duration=1, number_repeat=3),
        kid.speak_text(furhat=furhat, message="NO", number_repeat=3, duration=1)
    )
    asyncio.sleep(3.5)

    await asyncio.gather(
        kid.start_gesture(furhat=furhat, gesture="GazeAway", intensity=3, duration=3, number_repeat=1),
        kid.speak_text(furhat=furhat, message="I don't want to", number_repeat=1, duration=2)
    )

async def pr_problem_behavior(furhat):
    await asyncio.gather(
        kid.start_gesture(furhat=furhat, gesture="Nod", intensity=3, duration=1, number_repeat=2),
        kid.speak_text(furhat=furhat, message="I want the ball give me give me the ball", number_repeat=1, duration=3)
    )
