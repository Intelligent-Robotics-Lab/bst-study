# test_log_trial.py  (throwaway; run from the bst env, no extra deps)

"""Offline checks for SyncClient.log_trial -- no platform, no pytest.

Two properties matter, and the second is the whole point of the method:

  1. It POSTs to .../sessions/{sid}/trials with the expected body.
  2. It NEVER raises. Every other SyncClient method calls raise_for_status();
     log_trial must swallow failures and return None, because recording a trial
     is bookkeeping, not control flow -- a platform hiccup must not kill an
     unrepeatable participant session.

We stub SyncClient._http so nothing hits the network. Run:  python test/test_log_trial.py
"""

import asyncio
import os
import sys

# Run from anywhere: put the repo root (this file's parent's parent) on the path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.sync_client import SyncClient

STEPS = [
    {"step_index": 1, "step_label": "sd", "actor": "user", "outcome": "recognized"},
    {"step_index": 2, "step_label": "reinforcement", "actor": "user", "outcome": "recognized"},
]


class _FakeResp:
    def __init__(self, payload=None, raise_exc=None):
        self._payload = payload or {}
        self._raise_exc = raise_exc

    def raise_for_status(self):
        if self._raise_exc:
            raise self._raise_exc

    def json(self):
        return self._payload


class _FakeHTTP:
    """Records the last POST; returns a canned response or raises on post()."""

    def __init__(self, resp=None, post_exc=None):
        self._resp = resp
        self._post_exc = post_exc
        self.calls = []

    async def post(self, url, json=None):
        self.calls.append((url, json))
        if self._post_exc:
            raise self._post_exc            # e.g. a connection error
        return self._resp

    async def aclose(self):
        pass


def _client(http):
    c = SyncClient(session_id="S1", base_url="http://platform:8080")
    c._http = http
    return c


async def _run():
    ok = True

    # 1) happy path: posts to /trials with the right body, returns the platform row
    http = _FakeHTTP(resp=_FakeResp({"trial_id": 7, "trial_number": 1}))
    c = _client(http)
    out = await c.log_trial(
        loop_index=2, trial_name="Receptive Instruction",
        response_correctness="no_response",
        reinforcement_delivered=True, error_correction_delivered=False,
        steps=STEPS,
    )
    url, body = http.calls[-1]
    assert url == "http://platform:8080/sessions/S1/trials", url
    assert "/sync/" not in url, "must hit /trials, not the gate endpoint"
    assert body["loop_index"] == 2 and body["trial_name"] == "Receptive Instruction"
    assert body["steps"] == STEPS
    assert out == {"trial_id": 7, "trial_number": 1}
    print("  [1] posts to /trials with the expected body, returns the row  OK")

    # 2) transport failure (platform down): must NOT raise, returns None
    http = _FakeHTTP(post_exc=ConnectionError("platform unreachable"))
    try:
        out = await _client(http).log_trial(
            loop_index=2, trial_name="x", response_correctness="correct",
            reinforcement_delivered=True, error_correction_delivered=False, steps=STEPS,
        )
        assert out is None
        print("  [2] transport failure is swallowed (returns None, no raise)  OK")
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"  [2] FAIL: log_trial raised on transport error: {exc!r}")

    # 3) HTTP error (e.g. 422 drift guard): must NOT raise, returns None
    http = _FakeHTTP(resp=_FakeResp(raise_exc=RuntimeError("422 Unprocessable Entity")))
    try:
        out = await _client(http).log_trial(
            loop_index=2, trial_name="Manding", response_correctness="correct",
            reinforcement_delivered=True, error_correction_delivered=False, steps=STEPS,
        )
        assert out is None
        print("  [3] 4xx/5xx is swallowed (returns None, no raise)  OK")
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"  [3] FAIL: log_trial raised on HTTP error: {exc!r}")

    print("ALL PASS" if ok else "FAILURES ABOVE")
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if asyncio.run(_run()) else 1)
