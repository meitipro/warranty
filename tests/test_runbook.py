"""
The demo, replayed offline.

scripts/demo.py puts the demo on StudioNet from scripts/demo_data.py (STEPS).
This file replays the same steps against the real contract in the simulator,
so a demo that could not succeed is caught before a single transaction is
spent on it.

When deployments/studionet.json exists, the replay goes further: it feeds the
simulator the rulings the validators actually agreed on, and checks that the
contract in this repository pays, declines and releases exactly what the
deployed one did, and refuses exactly where it refused.

    pytest tests/test_runbook.py -v
"""

import hashlib
import importlib.util
import json
import pathlib

import pytest

import glsim as S

CONTRACT_PATH = "contracts/warranty.py"
M = S.load_contract(CONTRACT_PATH)
RECORD = pathlib.Path("deployments/studionet.json")

_spec = importlib.util.spec_from_file_location("demo_data", "scripts/demo_data.py")
D = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D)

WHO = {"seller": "0x" + "a1" * 20, "buyer": "0x" + "b2" * 20, "stranger": "0x" + "d4" * 20}
T0 = 1_790_000_000
NAMES = [d for d, _ in D.DEFECTS]


def honest(names, forward):
    n = len(names)
    rev = forward if forward == "none" else str(n - 1 - int(forward))
    return {"[0] " + names[0]: {"defect": forward, "because": "replayed"},
            "[0] " + names[-1]: {"defect": rev, "because": "replayed"}}


def replay(rulings):
    """Run STEPS. `rulings` are the defects the ok claims come back with, in order."""
    c = S.deploy(CONTRACT_PATH)
    S.reset_transfers()
    queue = list(rulings)
    outcomes = []
    clock = T0
    for step in D.STEPS:
        actor, method, spec, expect, label = step[:5]
        clock += 30
        if "after_end" in step[5:]:
            clock = max(clock, M.seconds(c.warranty(0)["ends_at"]) + 20)
        S.set_time(M.iso(clock))
        S.set_mocks()
        value = 0
        if method == "open":
            product, _, defects, exclusions, period = spec
            args = [product, WHO["buyer"], *D.joined(defects, exclusions), period]
            value = D.total(defects)
        else:
            args = list(spec)
        if method == "claim" and expect == "ok":
            S.set_mocks(leader_prompts=honest(NAMES, queue.pop(0)))
        S.set_sender(WHO[actor])
        try:
            S.call(c, method, *args, value=value)
            outcomes.append(("ok", ""))
        except S.UserError as e:
            outcomes.append(("refused", e.message))
    return c, outcomes


class TestDemoData:
    def test_every_value_the_demo_sends_passes_the_bounds(self):
        names, payouts, exclusions = D.joined(D.DEFECTS, D.EXCLUSIONS)
        assert M.terms_refusal(M.split_list(names), M.parse_amounts(payouts, 1, M.MAX_AMOUNT),
                               M.parse_exclusions(exclusions)) == ""
        assert M.MIN_PRODUCT <= len(D.PRODUCT) <= M.MAX_PRODUCT and M.MIN_PERIOD <= D.PERIOD <= M.MAX_PERIOD
        for account in (D.PUMP, D.DROPPED, D.PUMP_AGAIN, D.STEAM):
            assert M.MIN_ACCOUNT <= len(M.clean_text(account)) <= M.MAX_ACCOUNT

    def test_each_claim_changes_one_thing(self):
        assert "pump" in D.PUMP and "group head" in D.PUMP                       # covered defect 0, in other words
        assert "boiler" in D.DROPPED and "knocked" in D.DROPPED                  # a covered fault, an excluded cause
        assert "knocking it over" in D.EXCLUSIONS[0]
        assert "pump" in D.PUMP_AGAIN and D.PUMP_AGAIN.lower() != D.PUMP.lower()  # the same defect, a new account
        assert "steam" in D.STEAM

    def test_the_period_outlasts_the_steps_meant_to_land_inside_it(self):
        """Six transactions after open are meant to find the warranty live; at
        up to 60 s each on StudioNet they land well inside the period."""
        assert D.PERIOD >= 7 * 60


class TestReplay:
    def test_the_demo_succeeds_and_refuses_exactly_where_it_says(self):
        _, outcomes = replay(D.EXPECTED_RULINGS)
        assert [o for o, _ in outcomes] == [s[3] for s in D.STEPS]

    def test_the_refusals_say_why(self):
        _, outcomes = replay(D.EXPECTED_RULINGS)
        msgs = [m for o, m in outcomes if o == "refused"]
        wants = ["only the buyer named in the warranty", "already decided as claim 0", "at most 3 claims",
                 "the warranty runs until", "the warranty ended at"]
        assert len(msgs) == len(wants)
        for msg, want in zip(msgs, wants):
            assert want in msg, (want, msg)

    def test_the_expected_rulings_pay_and_release_what_the_readme_says(self):
        c, _ = replay(D.EXPECTED_RULINGS)
        assert [(x["defect"], x["outcome"]) for x in c.claims_of(0)["claims"]] == [
            ("0", "paid"), ("none", "declined"), ("0", "already_paid")]
        pump = D.DEFECTS[0][1]
        w = c.warranty(0)
        assert (w["status"], w["paid_out"], w["refunded"]) == ("closed", str(pump), str(D.total(D.DEFECTS) - pump))
        assert S.transfers() == [(WHO["buyer"], pump), (WHO["seller"], D.total(D.DEFECTS) - pump)]
        assert c.held_total() == 0


@pytest.mark.skipif(not RECORD.exists(), reason="no deployment recorded yet: python scripts/demo.py")
class TestTheRecord:
    """The live run, checked against this repository."""

    def _record(self):
        return json.loads(RECORD.read_text(encoding="utf-8"))

    def test_the_record_is_of_this_source(self):
        here = hashlib.sha256(pathlib.Path(CONTRACT_PATH).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        assert self._record()["source_sha256"] == here, "the deployed contract is not this file; redeploy"

    def test_every_step_on_chain_did_what_the_demo_expected(self):
        steps = [s for s in self._record()["steps"] if s["step"] != "deploy"]
        assert [("ok" if s["ok"] else "refused") for s in steps] == [s[3] for s in D.STEPS]

    def test_this_contract_decides_what_the_deployed_one_decided(self):
        rec = self._record()
        agreed = [x["defect"] for x in rec["warranties"][0]["claims"]]
        c, outcomes = replay(agreed)
        assert [o for o, _ in outcomes] == [s[3] for s in D.STEPS]
        for k, w in enumerate(rec["warranties"]):
            mine = c.warranty(k)
            for field in ("status", "paid_out", "refunded"):
                assert str(mine[field]) == str(w["warranty"][field]), (k, field)
            assert [(x["defect"], x["outcome"], x["paid"]) for x in c.claims_of(k)["claims"]] == \
                [(x["defect"], x["outcome"], x["paid"]) for x in w["claims"]]

    def test_the_payout_reached_the_buyer(self):
        rec = self._record()
        b = rec["balances"]
        assert int(b["buyer_after"]) - int(b["buyer_before"]) == int(rec["warranties"][0]["warranty"]["paid_out"])
