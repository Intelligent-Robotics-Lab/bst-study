import asyncio
import httpx
 
 
class SyncClient:
    def __init__(self, session_id: str, base_url: str = "http://141.210.88.210:8080"):
        self.session_id = session_id
        self.base = f"{base_url}/sessions/{session_id}/sync"
        self._http = httpx.AsyncClient(timeout=5.0)
 
    async def close(self):
        await self._http.aclose()
  
    async def register(self, pb_order_group: int, support_condition: int):
        """Once at startup: confirm both systems agree on this session+condition."""
        r = await self._http.post(
            f"{self.base}/register",
            json={"pb_order_group": pb_order_group,
                  "support_condition": support_condition},
        ) 

        r.raise_for_status()
        return r.json()
 
    async def stage_complete(self, stage: str):
        """End of tutorial/instruction/modeling: opens that stage's baseline gate."""
        r = await self._http.post(f"{self.base}/stage-complete",
                                   json={"stage": stage})
        r.raise_for_status()
        return r.json()
 
    async def kid_response_complete(self, loop_index: int, trial_name: str | None = None):
        """Child has finished responding on this loop (before feedback):
        opens the post_kid_response gate."""
        r = await self._http.post(f"{self.base}/kid-response-complete",
                                   json={"loop_index": loop_index,
                                         "trial_name": trial_name})
        r.raise_for_status()
        return r.json()
 
    async def feedback_delivered(self, loop_index: int, trial_name: str | None = None,
                                 evaluation_summary: str | None = None):
        """Trainer feedback delivered on this loop: opens the post_feedback gate."""
        r = await self._http.post(f"{self.base}/feedback-delivered",
                                   json={"loop_index": loop_index,
                                         "trial_name": trial_name,
                                         "evaluation_summary": evaluation_summary})
        r.raise_for_status()
        return r.json()
 
    async def complete(self):
        """End of the whole DTT: bst's part is done."""
        r = await self._http.post(f"{self.base}/complete", json={})
        r.raise_for_status()
        return r.json()
 
    # --- wait method ------------------------------------------------------
 
    async def wait_for_go_ahead(self, scope: str, checkpoint: str,
                                stage: str | None = None,
                                loop_index: int | None = None,
                                poll_interval: float = 0.3):

        """Block until the platform says proceed=true for this gate.
        Polls GET /go-ahead every poll_interval seconds. Returns when the
        self-report was submitted OR the operator overrode the gate.
        This is what makes the robot PAUSE at a measurement point."""

        params = {"scope": scope, "checkpoint": checkpoint}

        if stage is not None:
            params["stage"] = stage

        if loop_index is not None:
            params["loop_index"] = loop_index

        while True:
            r = await self._http.get(f"{self.base}/go-ahead", params=params)
            r.raise_for_status()
            data = r.json()

            if data.get("proceed") is True:
                return data

            await asyncio.sleep(poll_interval)
 