# test_sync_client.py  (throwaway, run from the bst env)

"""Isolation test: prove sync_client can talk to the platform,

WITHOUT any robot code. Run while the platform is up.

You will manually submit self-reports (or override) to release the gates."""

import asyncio

from logic.sync_client import SyncClient
 
SESSION_ID = "SyncTestTwo"   # create this session in the platform first
 
async def main():

    sync = SyncClient(session_id=SESSION_ID)

    try:

        print("register...")

        print(await sync.register(pb_order_group=1, support_condition=1))
 
        print("opening tutorial baseline gate...")

        print(await sync.stage_complete("tutorial"))
 
        print("waiting for go-ahead on tutorial gate "

              "(submit a baseline self-report for tutorial, or override)...")

        print(await sync.wait_for_go_ahead(scope="stage", stage="tutorial",

                                           checkpoint="baseline"))

        print("released! tutorial gate satisfied.")
 
        print("opening loop-2 post_kid_response gate...")

        print(await sync.kid_response_complete(loop_index=2, trial_name="Receptive Instruction"))

        print("waiting (submit a rehearsal self-report for loop 2, or override)...")

        print(await sync.wait_for_go_ahead(scope="loop", loop_index=2,

                                           checkpoint="post_kid_response"))

        print("released! loop-2 kid-response gate satisfied.")
 
        print("complete...")

        print(await sync.complete())

    finally:

        await sync.close()
 
asyncio.run(main())
 