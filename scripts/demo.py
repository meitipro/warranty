"""Deploy Warranty to StudioNet and put every path on the explorer.

    pip install genlayer-py==0.18.0
    python scripts/demo.py

The run deploys contracts/warranty.py exactly as it is in this repository,
then sends the steps in scripts/demo_data.py (STEPS), including the ones that
end in a refusal, and writes what happened to deployments/studionet.json: every
transaction hash, its status, the refusal sentence where there was one, the
warranty, its terms and every claim as the chain holds them, and the buyer's
and the seller's balances read from the chain around the payouts. Nothing in
that file is typed by hand.

Why a script and not the genlayer CLI: `genlayer write` cannot attach value to
a call, and open() is payable. genlayer-py's write_contract can.

The three accounts are made in memory for this run and the seller is funded
from StudioNet's own faucet. They hold test GEN and nothing else, and no key is
written to disk.
"""

import datetime
import hashlib
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).absolute().parent))
import demo_data as D                                       # noqa: E402
from studio import EXPLORER, Studio                         # noqa: E402

ROOT = pathlib.Path(__file__).absolute().parent.parent
SOURCE = ROOT / "contracts" / "warranty.py"
OUT = ROOT / "deployments" / "studionet.json"


def utc_seconds(iso):
    t = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return int(t.timestamp())


def wait_past(iso, label):
    """Sleep until the chain clock has passed `iso`, with a margin, because
    the contract compares against the time of the transaction that arrives."""
    target = utc_seconds(iso) + 20
    left = target - int(time.time())
    if left > 0:
        print(f"  waiting {left}s for {label} ({iso})")
        time.sleep(left)


def args_for(method, spec, buyer):
    if method == "open":
        product, _, defects, exclusions, period = spec
        return [product, buyer, *D.joined(defects, exclusions), period], D.total(defects)
    return list(spec), 0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    code = SOURCE.read_text(encoding="utf-8")
    s = Studio()

    print("\naccounts (in memory, StudioNet test GEN only)")
    who = {
        "seller": s.account("seller", gen=2),
        "buyer": s.account("buyer"),
        "stranger": s.account("stranger"),
    }
    before = {name: s.balance(who[name].address) for name in ("seller", "buyer")}

    print("\ndeploy")
    address = s.deploy(who["seller"], code, [])

    print("\nthe demo")
    for step in D.STEPS:
        actor, method, spec, expect, label = step[:5]
        if "after_end" in step[5:]:
            wait_past(s.read(address, "warranty", [spec[0]])["ends_at"], "the warranty to end")
        args, value = args_for(method, spec, who["buyer"].address)
        s.write(who[actor], address, method, args, value=value, step=label, expect=expect)

    after = {name: s.balance(who[name].address) for name in ("seller", "buyer")}
    n = int(s.read(address, "count"))
    warranties = [{
        "warranty": s.read(address, "warranty", [k]),
        "terms": s.read(address, "terms_of", [k]),
        "claims": s.read(address, "claims_of", [k])["claims"],
    } for k in range(n)]
    record = {
        "network": "studionet",
        "chain_id": 61999,
        "contract": address,
        "explorer": f"{EXPLORER}/address/{address}",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "constructor": {},
        "accounts": {name: a.address for name, a in who.items()},
        "balances": {f"{name}_{when}": str(v[name]) for when, v in (("before", before), ("after", after))
                     for name in ("seller", "buyer")},
        "held_after": str(s.read(address, "held_total")),
        "steps": s.log,
        "warranties": warranties,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=2, default=str) + "\n", encoding="utf-8", newline="\n")

    print(f"\n  contract   {address}")
    print(f"  explorer   {EXPLORER}/address/{address}")
    for k, w in enumerate(warranties):
        print(f"  warranty {k}  {w['warranty']['status']:<7} paid out {int(w['warranty']['paid_out']) / D.GEN:.3f} GEN  "
              f"refunded {int(w['warranty']['refunded']) / D.GEN:.3f} GEN  "
              f"rulings {[(c['defect'], c['outcome']) for c in w['claims']]}")
    print(f"  buyer      {before['buyer'] / D.GEN:.3f} -> {after['buyer'] / D.GEN:.3f} GEN")
    print(f"  held       {record['held_after']} wei")
    print(f"  written    {OUT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
