# Submission

One submission, under **Builder -> Intelligent Contracts**. This repository is
one standalone primitive.

---

## Before you submit, in order

1. **Measure, do not estimate.**

   ```bash
   python scripts/measure.py --write
   ```

   Runs the suite and the full mutation pass, renders the live record, and
   writes all three into README.md. It refuses to write anything if the suite
   is red, a mutation escapes, or the record is of a different contract file.

2. **Prove the address is evidence for this repository.**

   ```bash
   python scripts/verify_deployment.py <address>
   ```

   Reads the source back off chain, compares it with `contracts/warranty.py`
   and runs `genvm-lint check` on those bytes.

3. **Open the explorer page and check it.** It must show the deploy, the three
   rulings with a consensus result beside them, the release, and the five
   refusals, each with its reason.

---

## On chain

The address, every transaction, every ruling and every payout are in the
[README](README.md#it-is-live-and-every-path-is-on-chain), rendered from
[`deployments/studionet.json`](deployments/studionet.json), and every
transaction with the wallet that sent it is in [EVIDENCE.md](EVIDENCE.md).

## What to say in the portal

**What it does.** Warranty is a product warranty with its payouts paid in
before the sale closes. The seller freezes a list of covered defects, each with
a fixed payout, and a list of exclusions, and pays every payout in. During the
period the buyer describes a fault in their own words. Validators decide which
covered defect it is, or none, in both presentation orders, reading the
exclusions as reasons for none, and the contract pays that defect's payout
once, in the same transaction.

**Why it needs GenLayer.** Whether "the pump hums but no water comes through
the group head" is a pump failure, and whether "the cat knocked it off the
counter and now the boiler stays cold" falls under an exclusion, is a judgment
in natural language, and the seller who pays is the one party who cannot be
trusted to make it. Independent validators must agree before any money moves,
and the seller cannot approve, refuse or reduce a claim.

**What it learned from earlier work.** What code can settle is settled before
the model: a claim no ruling could pay costs no inference. The model is asked
for an index into a list the contract holds, never an amount, and never shown
one. Every judgment has a clock: nothing is claimed or ruled after the period.
The uncertainty goes into the value (an order-dependent defect is none), and
money moves at the root of the transaction.
