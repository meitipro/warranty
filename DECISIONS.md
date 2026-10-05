# DECISIONS

Why Warranty is built the way it is. Each section names the alternative that
was rejected and what it would have cost.

## The model is asked which covered defect, never whether to pay

The obvious design asks "should the seller pay for this fault?" and pays on a
yes. It hands the model two jobs at once: recognising what the fault is, and
deciding whether the buyer deserves the money. The second is the seller's
discretion wearing a model's clothes, and a sympathetic account wins it.

So the model answers an index into a list the contract already holds: which
covered defect the account describes, or none. What that defect pays, and
whether it has already been paid, is the contract's own counting in `decide()`,
from storage the block never saw.
`tests/test_e2e.py::TestStorageShape::test_the_block_never_touches_storage_and_never_sees_an_amount`
fails if a payout is ever passed into the block, and
`test_the_model_is_never_shown_an_amount` checks every prompt of a real ruling.

## Exclusions are reasons for none, never answers

Every warranty has exclusions, and "user damage" is where most claims die. If
the exclusions were numbered options, the model would have to choose between
"the boiler is not heating" and "it was dropped" for an account that says
both, and the answer would depend on which it read first. Here the exclusions
are listed unnumbered, and the prompt states the rule: a fault the account
itself says was caused by an exclusion is none, even when it would otherwise
match a covered defect. The model is told not to guess at causes the account
does not mention, so an exclusion cannot be used to refuse a claim that never
gave one. The demo's second claim (the cat knocked the machine over, and now
the boiler stays cold) is written to test exactly that.

## Every payout is paid in at open

A warranty that pays from the seller's future goodwill is the problem this
contract exists to remove. `open()` is payable and refuses anything but the
exact sum of the payouts, so every covered defect can be paid the moment it is
ruled, whatever the seller does next.

## Each covered defect is paid once

A defect already paid by this warranty is `already_paid`: the contract checks
it, not the model, so the same fault reported twice in different words cannot
draw its payout twice. The demo's third claim is the pump again, described
differently, and pays nothing.

## What can be settled before the model is settled before the model

A claim by anyone but the buyer, after the period, beyond the third, once every
defect is paid, or with an account already decided, is refused for free and
stores nothing. No answer about the account could change those outcomes, so no
inference is spent on them. A static test pins every one of those checks before
the block.

## A defect that depends on the order is none, and none is declined

When the two presentation orders disagree, the folded value is `none`. Keeping
the forward answer would let the bias the reversed pass exists to catch decide
whether the seller pays. A buyer whose account is order-dependent can claim
once more, described so the defect is clear.

## Every judgment has a clock

The period is frozen at open. A claim is ruled in the transaction that files
it, so there is never a claim waiting for a ruling, and nothing can be claimed
or ruled once the period has ended: a late ruling can never take money that is
about to go back to the seller. After the period anyone may `release()` the
rest to the seller, so a buyer who never claims cannot strand it, and a seller
who has vanished cannot either.

## At most three claims, and each account decided once

A ruling is a consensus over model output, so re-claiming is re-rolling. Three
claims leave room for a second fault and for correcting a description, and no
room to try every wording. An account already decided on this warranty, in any
capitalisation and spacing, is refused: the answer stands.

## The seller cannot approve, refuse, or reduce a claim

The seller's only acts are opening the warranty and, like anyone else,
releasing it after it ends. The terms are the seller's judgment, made in
advance and paid for; the rulings apply them.

## Money moves at the root of the transaction

Payouts leave through one path, `_send()`, after the claim and the payout are
recorded. `held` is a counter of what live warranties are owed, never a scan,
and a payout beyond it is refused: unreachable while the accounting is right,
and the guard against ever paying one warranty's money to another's buyer. A
share of zero is not sent at all. Payouts use the external message form with
`value` only, the form studionet delivers.

## Tagging untrusted text is not a fence

The product, the covered defects, the exclusions and the account are all
written by a party with a stake in the answer. `fence()` replaces `< > [ ]` at
the prompt boundary only, so no caller text can close a block or forge a
numbered row; the contract numbers the defects itself, after fencing. Text is
stored exactly as sent.

## The reason string is leader-supplied

`because` is stored next to each claim, sanitised and capped, and is not part
of consensus. Nothing in the contract acts on it, and the view says so.

## Why the tests are built the way they are

- **Each node gets its own answers**, so a contract that assumes both nodes read the same thing is caught offline.
- **A leader can lie**, so the validator's checks are reachable, and the free layer is measured: a malformed ruling must cost the validator zero prompts, and the free refusals before the block must cost everyone zero prompts.
- **The runbook is a test.** The demo is replayed offline from `scripts/demo_data.py` before a transaction is spent, and once `deployments/studionet.json` exists the validators' real rulings are replayed through this file and the buyer's balance is checked against the payout.
- **Mutation testing.** `scripts/mutate.py` removes each defence and names the test that caught it.

## GenVM constraints this contract obeys

- the runner is pinned (`py-genlayer:1jb45aa8...`), never `test` or `latest`
- the class is named after the product, because `genvm-lint validate` does not see a class named `Contract`; the storage row is called `Cover` so no dataclass shares its name
- no `int`, `list`, `dict` or `tuple` as a storage type, and no collection inside a storage dataclass; TreeMap keys are strings
- every persistent field is declared in the class body, and every stored field is read somewhere
- the block returns a flat dict of strings, and never pays
- `gl.nondet` is reached only from `ask`, called only from inside the block
- the file is pure ASCII
- `genvm-lint` validates against GenVM `v0.3.0-rc7`, the release that ships the pinned runner; `scripts/verify_deployment.py` sets `GENVM_VERSION` accordingly
- `scripts/schema_check.py` validates the file against the live studionet runtime with `gen_getContractSchemaForCode` before a deploy is spent

## Not upgradable

There is no owner and no admin method. A warranty's terms and payouts are
frozen at `open()`, and a ruling on record stays the ruling.
