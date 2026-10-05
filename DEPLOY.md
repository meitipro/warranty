# Deploying Warranty

Everything here runs on StudioNet. It is gasless, but `open()` is payable, so
the seller needs StudioNet test GEN. `scripts/demo.py` takes it from
StudioNet's own faucet. Nothing needs a private key in a file.

## 1 - Check the contract

```bash
pip install -r requirements-dev.txt
pytest tests/ -q
python scripts/schema_check.py contracts/warranty.py
GENVM_VERSION=v0.3.0-rc7 genvm-lint check contracts/warranty.py
```

`schema_check.py` runs the file through the live studionet runtime with
`gen_getContractSchemaForCode`, without deploying it. On Windows, set
`PYTHONIOENCODING=utf-8` first, or the linter dies printing its own tick.

## 2 - Run the demo

```bash
python scripts/demo.py
```

The genlayer CLI cannot attach value to a write, and `open()` is payable, so
the demo uses genlayer-py, whose `write_contract` takes `value`. It makes three
accounts in memory (`seller`, `buyer`, `stranger`), funds the seller with 2
test GEN, and deploys `contracts/warranty.py` exactly as it is in this
repository.

The data and the steps are in [`scripts/demo_data.py`](scripts/demo_data.py);
the same list drives the demo and `tests/test_runbook.py`. The terms:

| Covered defect | Payout |
|---|---|
| [0] The pump stops pushing water through the group head | 0.3 GEN |
| [1] The boiler does not heat water to brewing temperature | 0.3 GEN |
| [2] The steam wand leaks or produces no steam | 0.1 GEN |

Exclusions: damage from dropping the machine or knocking it over; liquid
spilled into the body or the electronics. The period is ten minutes.

The writes, in order:

| # | From | Call | Expected |
|---|---|---|---|
| 1 | seller | `open(espresso machine, buyer, 3 defects, 2 exclusions, 600)` with 0.7 GEN | ok: warranty 0 |
| 2 | stranger | `claim(0, <the pump>)` | refused: only the buyer may claim |
| 3 | buyer | `claim(0, <the pump hums, no water>)` | ok: defect 0, **paid** 0.3 GEN |
| 4 | buyer | `claim(0, <the same account>)` | refused: already decided |
| 5 | buyer | `claim(0, <knocked off the counter, the boiler stays cold>)` | ok: **none**, declined (an exclusion) |
| 6 | buyer | `claim(0, <the pump again, other words>)` | ok: defect 0, **already_paid**, nothing |
| 7 | buyer | `claim(0, <the steam wand>)` | refused: at most three claims |
| 8 | seller | `release(0)` | refused: the warranty runs until its end |
| 9 | buyer | `claim(0, <the steam wand>)` after the end | refused: the warranty ended |
| 10 | stranger | `release(0)` after the end | ok: 0.4 GEN back to the seller |

The script waits the period out before the last two steps, and stops at the
first step that does not do what the table says, because the demo claims
whatever it records. It reads the buyer's and the seller's balances from the
chain before and after, so the payout is evidence, not a claim.

It writes [`deployments/studionet.json`](deployments/studionet.json): every
transaction hash, its sender and status, each refusal's sentence, the
warranty, its terms and every claim as the chain holds them. Then:

```bash
pytest tests/test_runbook.py -v
```

`TestTheRecord` replays the rulings the validators agreed on through this
repository's contract and fails unless it pays, declines and releases exactly
what the deployed one did, and refuses exactly where it refused.

## 3 - Reads - free, no transaction

```bash
genlayer network set studionet
genlayer call <address> count
genlayer call <address> warranty --args 0
genlayer call <address> terms_of --args 0
genlayer call <address> claims_of --args 0
genlayer call <address> held_total
```

## 4 - Before the portal

```bash
python scripts/verify_deployment.py <address>
python scripts/measure.py --write
```

The first reads the deployed source back off chain, compares it with
`contracts/warranty.py` and lints the deployed bytes. The second runs the suite
and the mutation pass and writes the measured numbers and the live record into
README.md. Neither writes anything unless every check passes.
