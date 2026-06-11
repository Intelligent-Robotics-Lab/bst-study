import json
import asyncio

from expression_module.expression_module import ExpressionModule
from logic.dtt import DTT
from agent_layer.Furhat.Lib import furhat_manager


async def test_behavior():
    # -----------------------------
    # INIT FURHATS (CRITICAL MISSING PIECE)
    # -----------------------------
    await furhat_manager.initialize_furhat()

    # -----------------------------
    # LOAD DATA
    # -----------------------------
    with open("data/trial_data.json", "r") as f:
        trial_data = json.load(f)["trial_data"]

    print("\nAvailable SDs:")
    for sd in trial_data.keys():
        print(" -", sd)

    current_sd = input("\nEnter SD: ").strip()

    trial = trial_data[current_sd]

    print("\nPick behavior:")
    print("1 = child")
    print("2 = prompted")
    print("3 = retry")

    choice = input("> ").strip()

    if choice == "1":
        behavior = trial["child_behavior"]
    elif choice == "2":
        behavior = trial.get("prompted_behavior")
    elif choice == "3":
        behavior = trial.get("retry_behavior")
    else:
        print("Invalid choice")
        return

    if behavior is None:
        print("No behavior available for this SD")
        return

    # -----------------------------
    # FORCE ROBOT SAFETY (optional but recommended)
    # -----------------------------
    behavior = dict(behavior)

    # IMPORTANT: ensures Furhat routing works
    # (you can remove this if initialize_furhat works correctly)
    # behavior["embodiment"] = "trainer"

    # -----------------------------
    # RUN
    # -----------------------------
    expr = ExpressionModule()
    dtt = DTT(agent="Furhat")

    await dtt.run_kid_behavior(expr, behavior)


if __name__ == "__main__":
    asyncio.run(test_behavior())