import asyncio
from agent_layer.agent_layer import agent_layer

# Example list of behaviors to call
behaviors = [{
    "agent_type": "Furhat",
    "embodiment": "kid",
    "text": "Hello, I am Furhat.",
    "head_gesture": "Nod",
    "text_duration": 5,
    "text_repeats": 1,
    "intensity": 3,
    "duration": 1,
    "num_repeats": 2,
    "attention_target": "user", # This paramter will likely not work until we have integration of other ideas
    "face_expression": "Happy",
    "voice": "Ivy-Neural (en-US) - Amazon Polly", # Temporary replacement idea until we have better control over pitch, intonation, etc.
    "listening": False,
    "interrupt": False,
    "gesture_timing": "during"
},
{
    "agent_type": "Furhat",
    "embodiment": "kid",
    "text": "I am happy to be here.",
    "text_duration": 5,
    "text_repeats": 1,
    "head_gesture": "BigSmile",
    "intensity": 3,
    "duration": 3,
    "num_repeats": 1,
    "attention_target": "user", 
    "face_expression": "Suprised",
    "voice": "Ivy-Neural (en-US) - Amazon Polly",
    "listening": False,
    "interrupt": False,
    "gesture_timing": "after"
},
{
    "agent_type": "Furhat",
    "embodiment": "kid",
    "text": "No, I don't want to do this.",
    "text_duration": 5,
    "text_repeats": 1,
    "head_gesture": "Shake",
    "intensity": 3,
    "duration": 1,
    "num_repeats": 2,
    "attention_target": "user",
    "face_expression": "Angry",
    "voice": "Ivy-Neural (en-US) - Amazon Polly",
    "listening": False,
    "interrupt": False,
    "gesture_timing": "before"
}]

# Example set of baseline behavior and waiting for response
pr_problem_behaviors = [{
    "agent_type": "Furhat",
    "embodiment": "kid",
    "text": "No, I don't want to.",
    "head_gesture": "Shake",
    "text_duration": 5,
    "text_repeats": 1,
    "intensity": 4,
    "duration": 1.25,
    "num_repeats": 3,
    "attention_target": "user", # This paramter will likely not work until we have integration of other ideas
    "face_expression": "Angry",
    "voice": "Ivy-Neural (en-US) - Amazon Polly", # Temporary replacement idea until we have better control over pitch, intonation, etc.
    "listening": False,
    "interrupt": False,
    "gesture_timing": "during"
},
{
    "agent_type": "Furhat",
    "embodiment": "kid",
    "text": "No... No... No",
    "text_duration": 5,
    "text_repeats": 1,
    "head_gesture": "Shake",
    "intensity": 3,
    "duration": 0.75,
    "num_repeats": 4,
    "attention_target": "user",
    "face_expression": "Angry",
    "voice": "Ivy-Neural (en-US) - Amazon Polly",
    "listening": False,
    "interrupt": True,
    "gesture_timing": "during"
},
{
    "agent_type": "Furhat",
    "embodiment": "kid",
    "text": "I won't do that... I won't do it.",
    "text_duration": 5,
    "text_repeats": 1,
    "head_gesture": "ExpressAnger",
    "intensity": 3,
    "duration": 2,
    "num_repeats": 1,
    "attention_target": "user",
    "face_expression": "neutral",
    "voice": "Ivy-Neural (en-US) - Amazon Polly",
    "listening": False,
    "interrupt": False,
    "gesture_timing": "after"
}]

async def main():
    await agent_layer(pr_problem_behaviors[0]["agent_type"], pr_problem_behaviors[0]["embodiment"], pr_problem_behaviors[0]["text"], pr_problem_behaviors[0]["text_duration"], pr_problem_behaviors[0]["text_repeats"], pr_problem_behaviors[0]["head_gesture"], pr_problem_behaviors[0]["intensity"], pr_problem_behaviors[0]["duration"], pr_problem_behaviors[0]["num_repeats"], 
        pr_problem_behaviors[0]["attention_target"], pr_problem_behaviors[0]["face_expression"], pr_problem_behaviors[0]["voice"], pr_problem_behaviors[0]["listening"], pr_problem_behaviors[0]["interrupt"], pr_problem_behaviors[0]["gesture_timing"])

    await asyncio.sleep(2)

    await agent_layer(pr_problem_behaviors[1]["agent_type"], pr_problem_behaviors[1]["embodiment"], pr_problem_behaviors[1]["text"], pr_problem_behaviors[1]["text_duration"], pr_problem_behaviors[1]["text_repeats"], pr_problem_behaviors[1]["head_gesture"], pr_problem_behaviors[1]["intensity"], pr_problem_behaviors[1]["duration"], pr_problem_behaviors[1]["num_repeats"], 
        pr_problem_behaviors[1]["attention_target"], pr_problem_behaviors[1]["face_expression"], pr_problem_behaviors[1]["voice"], pr_problem_behaviors[1]["listening"], pr_problem_behaviors[1]["interrupt"], pr_problem_behaviors[1]["gesture_timing"])

    await asyncio.sleep(2)

    await agent_layer(pr_problem_behaviors[2]["agent_type"], pr_problem_behaviors[2]["embodiment"], pr_problem_behaviors[2]["text"], pr_problem_behaviors[2]["text_duration"], pr_problem_behaviors[2]["text_repeats"], pr_problem_behaviors[2]["head_gesture"], pr_problem_behaviors[2]["intensity"], pr_problem_behaviors[2]["duration"], pr_problem_behaviors[2]["num_repeats"], 
        pr_problem_behaviors[2]["attention_target"], pr_problem_behaviors[2]["face_expression"], pr_problem_behaviors[2]["voice"], pr_problem_behaviors[2]["listening"], pr_problem_behaviors[2]["interrupt"], pr_problem_behaviors[2]["gesture_timing"])

    await asyncio.sleep(1)

    # await agent_layer(behaviors[0]["agent_type"], behaviors[0]["embodiment"], behaviors[0]["text"], behaviors[0]["text_duration"], behaviors[0]["text_repeats"], behaviors[0]["head_gesture"], behaviors[0]["intensity"], behaviors[0]["duration"], behaviors[0]["num_repeats"], 
    #                   behaviors[0]["attention_target"], behaviors[0]["face_expression"], behaviors[0]["voice"], behaviors[0]["listening"], behaviors[0]["interrupt"], behaviors[0]["gesture_timing"])

    # await asyncio.sleep(2)

    # await agent_layer(behaviors[1]["agent_type"], behaviors[1]["embodiment"], behaviors[1]["text"], behaviors[1]["text_duration"], behaviors[1]["text_repeats"], behaviors[1]["head_gesture"], behaviors[1]["intensity"], behaviors[1]["duration"], behaviors[1]["num_repeats"], 
    #                   behaviors[1]["attention_target"], behaviors[1]["face_expression"], behaviors[1]["voice"], behaviors[1]["listening"], behaviors[1]["interrupt"], behaviors[1]["gesture_timing"])

    # await asyncio.sleep(2)

    # await agent_layer(behaviors[2]["agent_type"], behaviors[2]["embodiment"], behaviors[2]["text"], behaviors[2]["text_duration"], behaviors[2]["text_repeats"], behaviors[2]["head_gesture"], behaviors[2]["intensity"], behaviors[2]["duration"], behaviors[2]["num_repeats"], 
    #                   behaviors[2]["attention_target"], behaviors[2]["face_expression"], behaviors[2]["voice"], behaviors[2]["listening"], behaviors[2]["interrupt"], behaviors[2]["gesture_timing"])

if __name__ == "__main__":
    asyncio.run(main())