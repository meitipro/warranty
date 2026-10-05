"""Integration tests, run against StudioNet.

    pip install genlayer-py==0.18.0
    GENLAYER_STUDIO=1 pytest tests/test_integration.py -v

They are opt in. Without GENLAYER_STUDIO set they skip, so `pytest tests/ -q`
stays clean and offline on a reviewer's machine whatever is installed there,
and an unreachable network can never be mistaken for a broken contract.

They exercise the deterministic half on a real runtime, where the simulator is
weakest: the sender is derived from a signature rather than set by a test,
value really arrives with a payable call, an address passed as text is matched
against a real signer, and the free refusals before any model are shown to
cost no inference. The rulings themselves cost inference on every validator
and are on the record from scripts/demo.py.
"""

import os
import pathlib
import sys

import pytest

if not os.environ.get("GENLAYER_STUDIO"):
    pytest.skip("integration tests run against StudioNet and are opt in: set GENLAYER_STUDIO=1. "
                "Everything else runs offline with pytest tests/ -q", allow_module_level=True)

pytest.importorskip("genlayer_py", reason="pip install genlayer-py==0.18.0")

sys.path.insert(0, str(pathlib.Path(__file__).absolute().parent.parent / "scripts"))
from studio import GEN, Studio                               # noqa: E402

CODE = (pathlib.Path(__file__).absolute().parent.parent / "contracts" / "warranty.py").read_text(encoding="utf-8")
PRODUCT = "Espresso machine, integration run"
DEFECTS = "The pump stops pushing water through the group head|The boiler does not heat water"
PAYOUTS = f"{GEN // 10}|{GEN // 20}"
TOTAL = GEN // 10 + GEN // 20
EXCLUSIONS = "Damage from dropping the machine or knocking it over"
ACCOUNT = "The pump hums when I press the brew button but no water comes through the group head."


@pytest.fixture(scope="module")
def world():
    s = Studio()
    seller = s.account("seller", gen=1)
    buyer = s.account("buyer")
    address = s.deploy(seller, CODE, [])
    s.write(seller, address, "open", [PRODUCT, buyer.address, DEFECTS, PAYOUTS, EXCLUSIONS, 3600], value=TOTAL,
            step="open a warranty")
    return s, address, seller, buyer


def test_value_arrives_with_a_payable_call(world):
    s, address, seller, buyer = world
    w = s.read(address, "warranty", [0])
    assert w["status"] == "active" and w["funded"] == str(TOTAL) and w["held"] == str(TOTAL)
    assert w["seller"].lower() == seller.address.lower() and w["buyer"].lower() == buyer.address.lower()
    assert int(s.read(address, "held_total")) == TOTAL


def test_every_payout_must_be_paid_in_exactly(world):
    s, address, seller, buyer = world
    row = s.write(seller, address, "open", [PRODUCT, buyer.address, DEFECTS, PAYOUTS, EXCLUSIONS, 3600],
                  value=TOTAL + 1, step="overpay a warranty", expect="refused")
    assert "pay every payout in" in row["refusal"]


def test_only_the_buyer_may_claim_and_it_costs_no_inference(world):
    s, address, seller, _ = world
    row = s.write(seller, address, "claim", [0, ACCOUNT], step="the seller claims", expect="refused")
    assert "only the buyer named in the warranty" in row["refusal"]
    assert s.read(address, "claims_of", [0])["claims"] == []


def test_release_is_refused_before_the_end(world):
    s, address, _, buyer = world
    row = s.write(buyer, address, "release", [0], step="release too early", expect="refused")
    assert "the warranty runs until" in row["refusal"]


def test_an_unknown_warranty_is_a_refusal_not_the_newest_row(world):
    s, address, _, buyer = world
    row = s.write(buyer, address, "release", [99], step="release a warranty that does not exist", expect="refused")
    assert "no such warranty" in row["refusal"]
