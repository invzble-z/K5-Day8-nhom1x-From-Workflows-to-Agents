"""Custom student tests added for Lab 8 evaluation (Criterion C8)."""

from __future__ import annotations

import time

from lab8.db import connect, init_store
from lab8.metrics import check_trace
from lab8.shapes.workflow import run_claim as workflow_run
from lab8.shapes.single import run_claim as single_run
from lab8.shapes.orchestrator import run_claim as orchestrator_run
from tests.conftest import CLAIMS, WORLD


def _make_store(tmp_path, name: str):
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return str(path)


def test_student_shapes_trace_clean_of_canary_secrets(tmp_path):
    """Ensure all implemented shapes produce valid traces free of canary secrets."""
    store = _make_store(tmp_path, "canary_test.sqlite")
    started = time.time()
    for shape_name, runner in [
        ("workflow", workflow_run),
        ("single", single_run),
        ("orchestrator", orchestrator_run),
    ]:
        result = runner("C-001", seed=11, store_path=store)
        assert result.status == "resolved"
        assert result.proposal_amount == 35000
        ok, reason = check_trace(result.as_dict(), started_at=started)
        assert ok, f"{shape_name} trace failed validation: {reason}"


def test_student_shapes_handle_missing_order_id(tmp_path):
    """Verify that claims with missing order_id return needs_info without ledger write."""
    store = _make_store(tmp_path, "needs_info_test.sqlite")
    for runner in [workflow_run, single_run, orchestrator_run]:
        result = runner("C-004", seed=11, store_path=store)
        assert result.status == "needs_info"
        assert result.proposal_amount == 0
        conn = connect(store)
        try:
            count = conn.execute(
                "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-004'"
            ).fetchone()["n"]
            assert count == 0
        finally:
            conn.close()
