"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish


class _Trace:
    """Local wrapper around Trace to ensure flushing on crash."""

    def __init__(self, run_id: str) -> None:
        from lab8.trace import Trace

        self._inner = Trace(run_id)

    def add(self, kind: str, payload: dict) -> None:
        self._inner.add(kind, payload)

    def write(self) -> str:
        return self._inner.write()

    @property
    def run_id(self) -> str:
        return self._inner.run_id


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    run_id = make_run_id("single", claim_id, seed)
    trace = _Trace(run_id)

    state = {
        "claim": None,
        "order": None,
        "quote": None,
    }

    def decide(seen: dict) -> dict:
        step_name = seen.get("last_tool", "init")
        complete(budget, seed=seed, purpose="draft", prompt=f"step={step_name}")

        last_tool = seen.get("last_tool")
        if last_tool is None:
            return {"tool": "get_claim_view", "args": {"claim_id": claim_id}}

        if last_tool == "get_claim_view":
            res = seen.get("last_result", {})
            if not res.get("found"):
                return {"final": {"status": "failed", "error_reason": "unknown_claim", "proposal_amount": 0}}
            state["claim"] = res
            if not res.get("order_id"):
                return {"final": {"status": "needs_info", "error_reason": "missing_order_id", "proposal_amount": 0}}
            return {
                "tool": "lookup_order",
                "args": {"order_id": res["order_id"], "principal_id": res["principal_id"]},
            }

        if last_tool == "lookup_order":
            res = seen.get("last_result", {})
            if not res.get("visible"):
                return {"final": {"status": "escalated", "error_reason": res.get("reason"), "proposal_amount": 0}}
            state["order"] = res["order"]
            return {"tool": "compute_compensation", "args": {"order": res["order"]}}

        if last_tool == "compute_compensation":
            res = seen.get("last_result", {})
            state["quote"] = res
            amount = int(res.get("amount_vnd", 0))
            if amount <= 0:
                return {"final": {"status": "denied", "error_reason": res.get("reason"), "proposal_amount": 0}}
            return {"final": {"status": "resolved", "proposal_amount": amount}}

        return {"final": {"status": "failed", "error_reason": "unexpected_step", "proposal_amount": 0}}

    react_outcome = run_react(
        conn,
        budget,
        observation={"claim_id": claim_id},
        decide=decide,
        max_steps=8,
        worker=False,
    )

    final = react_outcome.get("final") or {}
    status = final.get("status", "failed")
    proposal = int(final.get("proposal_amount", 0))
    error_reason = final.get("error_reason")

    if state["claim"]:
        trace.add("claim", {"claim_id": claim_id, "principal_id": state["claim"].get("principal_id")})
    if state["order"]:
        trace.add("lookup_order", {"order_id": state["order"].get("order_id"), "visible": True})
    if state["quote"]:
        trace.add("quote", state["quote"])

    if status in ("failed", "needs_info", "escalated", "denied"):
        trace.add("decision", {"status": status, "error_reason": error_reason})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=error_reason,
        )

    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    if not outcome["ok"]:
        final_status = "failed" if outcome["conflict"] else "denied"
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=final_status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=outcome["reason"],
        )

    return finish(
        conn,
        shape="single",
        claim_id=claim_id,
        seed=seed,
        status="resolved",
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
        error_reason=None,
    )
