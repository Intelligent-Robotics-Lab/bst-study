import asyncio
import httpx

class LaunchClient:
    def __init__(self, session_id, base_url):
        self.base = f"{base_url}/sessions/{session_id}/launch"
        self._http = httpx.AsyncClient(timeout=5.0)

    async def get_config(self):
        r = await self._http.get(f"{self.base}/config"); r.raise_for_status(); return r.json()
    async def get_status(self):
        r = await self._http.get(f"{self.base}/status"); r.raise_for_status(); return r.json()
    async def ack(self, phase):
        await self._http.post(f"{self.base}/ack", json={"phase": phase})
    async def error(self, message):
        await self._http.post(f"{self.base}/error", json={"message": message})

    async def wait_for_start(self, poll=0.5):
        """Block until the operator presses Start in the console."""
        while True:
            s = await self.get_status()
            if s.get("status") == "start_requested":
                return s
            await asyncio.sleep(poll)