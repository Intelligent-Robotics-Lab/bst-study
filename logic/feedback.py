class Feedback:
    def __init__(self, agent):
        self.agent = agent

    def build(self, correctness, phase=None):

        if correctness == "Correct":
            text = "Good job engaging with the learner!"
        elif correctness == "Incorrect":
            text = "Let's try that again."
        else:
            text = "Nice try, keep going!"

        return {
            "embodiment": "trainer",
            "verbal": {
                "text": text
            },
            "nonverbals": [
                {
                    "channel": "face",
                    "action": "Happy",
                    "intensity": 0.8,
                    "timing": "during"
                }
            ]
        }