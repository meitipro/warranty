# Warranty - a product warranty with its payouts paid in before the sale closes

A GenLayer Intelligent Contract for a warranty the seller cannot talk their way
out of. The seller opens a warranty for one buyer with a short list of covered
defects, each worth a fixed payout, a short list of exclusions, and a period,
and pays every payout in up front. During the period the buyer describes a
fault in their own words. Validators decide **one thing: which covered defect
the account describes, or none**, reading the exclusions too. The contract does
the rest in the same transaction: the payout for that defect, once. The model
is never shown an amount, and the seller cannot approve, refuse or reduce a
claim.

- **Contract:** [`contracts/warranty.py`](contracts/warranty.py)
- **Tests:** `pip install pytest && pytest tests/ -q` - nothing else to install
- **Deployed:** see [It is live](#it-is-live-and-every-path-is-on-chain) below, and [`deployments/studionet.json`](deployments/studionet.json)
- **Every transaction and the wallet that sent it:** [EVIDENCE.md](EVIDENCE.md), read back from the chain
- **Run the demo yourself:** [DEPLOY.md](DEPLOY.md)
- **Verify a deployment:** `python scripts/verify_deployment.py 0x...` - compares the on-chain source with this file and lints it
- **Decisions:** [DECISIONS.md](DECISIONS.md)
- **License:** MIT

---

## It is live, and every path is on chain

<!-- measured:deployment:start -->
Deployed on studionet at [`0x6fB2b29E061e06E95EFB1AF15e35b1cC1FE68Da8`](https://explorer-studio.genlayer.com/address/0x6fB2b29E061e06E95EFB1AF15e35b1cC1FE68Da8) (deploy [`0xf1772b8d...`](https://explorer-studio.genlayer.com/tx/0xf1772b8dd9084ca53b57c36dd54c03643ae156f9352360be9f650bb51d7e1c61)). Every value below was read back from the chain by `scripts/demo.py` and written to [`deployments/studionet.json`](deployments/studionet.json); none of it is typed by hand.

| Warranty | Status | Paid to the buyer | Returned to the seller | Still held |
|---|---|---|---|---|
| 0: Kestrel K2 espresso machine, serial KS2-40871 | closed | 0.3 GEN | 0.4 GEN | 0 GEN |

The terms, frozen at open:

| Covered defect | Payout |
|---|---|
| [0] The pump stops pushing water through the group head | 0.3 GEN |
| [1] The boiler does not heat water to brewing temperature | 0.3 GEN |
| [2] The steam wand leaks or produces no steam | 0.1 GEN |

Exclusions: Damage from dropping the machine or knocking it over; Liquid spilled into the body or the electronics of the machine.

Every claim, the covered defect the validators named, and what the contract decided:

| Warranty | Account | Defect | Decided | Paid |
|---|---|---|---|---|
| 0 | Since Tuesday the pump hums when I press the brew button, but no water at all comes thr... | [0] The pump stops pushing water through the group head | **paid** | 0.3 GEN |
| 0 | My cat knocked the machine off the kitchen counter last night, and since then the boile... | none | **declined** | 0 GEN |
| 0 | The pump has stopped working again: it buzzes when I start a shot but pushes no water t... | [0] The pump stops pushing water through the group head | **already_paid** | 0 GEN |

The buyer's balance, read from the chain before and after: 0 GEN -> 0.3 GEN.

Every transaction, in order, refusals included:

| Step | Outcome | Transaction |
|---|---|---|
| warranty 0 opened: three covered defects, every payout paid in | ok | [`0xf1480f97...`](https://explorer-studio.genlayer.com/tx/0xf1480f97ec836702d02a9e76133e188cfac03754fdaec86d905c90d8568f476a) |
| a stranger claims | refused: only the buyer named in the warranty may claim | [`0x1a3dba37...`](https://explorer-studio.genlayer.com/tx/0x1a3dba37c99ed24b92d7e338eaffb9d1fb2d9bac38af0123a6dc46bd5d54a125) |
| the pump: covered defect 0, paid | ok | [`0xf25a3269...`](https://explorer-studio.genlayer.com/tx/0xf25a32698d1964ffd267481f24061e76e67f29ace71b3b68982a57e7f515e1cc) |
| the same account again | refused: this account was already decided as claim 0; that answer stands | [`0x49663ffe...`](https://explorer-studio.genlayer.com/tx/0x49663ffe211ba9950e0b18d5f8512e968a10c2ba13a93af81625bf80f75005aa) |
| the boiler, after a fall: excluded, declined | ok | [`0x006142bf...`](https://explorer-studio.genlayer.com/tx/0x006142bfdf37f6e9a8393b43181e39c7181e7942d948923caeefeaef42b0e2f9) |
| the pump again: already paid | ok | [`0x66867ff0...`](https://explorer-studio.genlayer.com/tx/0x66867ff034404f21f11349a1e1a1ced59cff6e09dfa0a39fcefe72a4c7fcc351) |
| a fourth claim | refused: a warranty takes at most 3 claims | [`0x7af6e429...`](https://explorer-studio.genlayer.com/tx/0x7af6e4298d9810eb8967d6c135d09b7ac0272581ad9d05b0e5f6540ebc8f8891) |
| the seller releases before the end | refused: the warranty runs until 2026-10-05T23:32:16Z | [`0x905b6ae7...`](https://explorer-studio.genlayer.com/tx/0x905b6ae7e189f561b562156ce06582084300a6358ab45310c3dbedc1f19cecad) |
| a claim after the warranty ended | refused: the warranty ended at 2026-10-05T23:32:16Z; nothing can be claimed or ruled after it | [`0xcb8b0e1f...`](https://explorer-studio.genlayer.com/tx/0xcb8b0e1f11ae548861e0101dfd1eeac248c38dede79d6e75750321d2004b8cf3) |
| the rest released to the seller | ok | [`0x4d4b5f87...`](https://explorer-studio.genlayer.com/tx/0x4d4b5f871dc300890a66284832400950e684761d521aca6ac6eb0f75af3990ca) |

After the last step the contract holds `0` wei.
`tests/test_runbook.py::TestTheRecord` replays these rulings through this repository's contract and fails unless it pays, declines and releases exactly what the deployed one did.
<!-- measured:deployment:end -->

## The problem

A warranty is a promise from the party who pays if it is kept. The buyer
describes the fault; the seller decides whether it is covered; and "that is
user damage" ends most claims, because the seller is judge in its own case and
nobody goes to court over a coffee machine.

Asking a model "should the seller pay?" does not fix it. It hands the model
coverage **and** money, with nothing frozen to judge against. Warranty splits
them: the covered defects, the exclusions and each payout are fixed and paid in
before the buyer ever needs them; the model answers only *which covered defect
is this*; and whether that defect has already been paid is counted, not judged.

## How consensus is used

### Before any model: could any answer change the outcome?

The contract refuses for free, before a single prompt, what no ruling could
change: a claim by anyone but the buyer, a claim after the period, a fourth
claim, a claim once every covered defect has been paid, and an account it has
already decided.

### The ruling

Otherwise the block sees the product, the numbered covered defects, the
exclusions and the buyer's account, and names one covered defect by its number,
or `none`:

```
<covered_defects>
[0] The pump stops pushing water through the group head
[1] The boiler does not heat water to brewing temperature
[2] The steam wand leaks or produces no steam
</covered_defects>

<exclusions>
- Damage from dropping the machine or knocking it over
- Liquid spilled into the body or the electronics of the machine
</exclusions>

<account>
My cat knocked the machine off the kitchen counter last night, and since then the boiler stays cold ...
</account>

answer: {"defect": "none", "because": "..."}
```

The exclusions are never an answer, only a reason for `none`: a fault the
account itself says was caused by an exclusion is `none`, even when it would
otherwise match a covered defect. The model is told to judge what the account
describes, not to guess at causes it does not mention.

### Both orders

The leader asks **twice**, with the covered defects in their frozen order and
then reversed and renumbered, and maps the second answer back. The same defect
in both orders stands; anything else is `none`. A fault that only matches a
defect when that defect is listed first does not clearly match it, and the
claimant carries the burden of showing that it does. The uncertainty goes into
the **value** (declined), never into the comparison.

### The validator, in two layers

1. **Structural, and free.** The ruling is `none` or a covered defect that
   exists. A malformed ruling is refused before the validator spends a single
   prompt.
2. **Exact agreement.** The validator asks both orders itself and compares.

An unusable answer is retried once inside the block and then raised as
`[LLM_ERROR]`, which a validator never agrees with, so a broken model can never
pay anyone. There is no equivalence principle and no tolerance anywhere.

## What the contract decides, not the model

| The validators said | The contract checks | Outcome | Paid |
|---|---|---|---|
| `none` | - | **declined** | nothing |
| covered defect *k* | *k* was already paid on this warranty | **already_paid** | nothing |
| covered defect *k* | otherwise | **paid** | *k*'s frozen payout, now |

Every payout is held from the moment the warranty opens, so a covered defect
can always be paid, and each one is paid at most once.

## The state machine

```
active   claims until ends_at; at most three; each account decided once
closed   after ends_at; whatever no claim took went back to the seller
```

### Every way out

| Situation | Route |
|---|---|
| the account was declined | claim once more, described so the covered defect can be recognised, or appeal the `claim` transaction |
| the same account again | refused: it was already decided, and that answer stands |
| the period ran out | `release()` returns the rest to the seller; nothing can be claimed or ruled after it |
| the seller has vanished | anyone may `release()` once the period has ended |

## Who may write

| Method | Caller | Why |
|---|---|---|
| `open(product, buyer, defects, payouts, exclusions, period)` | anyone, paying every payout in | the caller becomes the seller |
| `claim(id, account)` | the buyer named at open, during the period, at most three times | the only party the warranty is for, and the one paid |
| `release(id)` | anyone, deliberately, after `ends_at` | it reads no model and can only return what no claim can take any more |

`tests/test_e2e.py::TestStorageShape::test_every_gated_write_checks_the_sender`
fails if `claim()` stops refusing everyone but the buyer.

## The API

| View | Returns |
|---|---|
| `count()` | number of warranties |
| `status(id)` | `active` or `closed`: one word for another contract |
| `warranty(id)` | seller, buyer, status, funded, paid out, refunded, still held, the period |
| `terms_of(id)` | every covered defect with its payout and the claim that was paid for it, and the exclusions |
| `claims_of(id)` | every claim: the account, the defect named, the outcome, what it paid, and the leader's reason |
| `held_total()` | wei owed to active warranties; equals the contract's balance while the accounting is right |

## Running the tests

```bash
pip install pytest
pytest tests/ -q
```

<!-- measured:tests:start -->
Measured: **147 passed**, 1 skipped. The skipped tests are the opt-in StudioNet integration tests, which run with `GENLAYER_STUDIO=1`.
<!-- measured:tests:end -->

The suite runs on [`tests/glsim.py`](tests/glsim.py), a small GenVM stand-in
that executes the real contract file, gives the leader and the validator their
own mock answers, can make a leader lie, rolls back storage and value
transfers on a refusal, and refuses what GenVM refuses.

- [`tests/test_logic.py`](tests/test_logic.py) - the pure rules: parsing payouts and exclusions, the terms' shape, `decide()`, the answer, the un-reversal, the fold, the agreement, the fence and the prompt, and that `lib/warranty_consensus.py` is the contract's own code
- [`tests/test_e2e.py`](tests/test_e2e.py) - the contract executed: the free refusals (zero prompts), each payout to the wei, a defect paid once, the exclusions in the prompt, the amount the model never sees, order-dependence, a leader that invents or hides a covered defect, `[LLM_ERROR]` never agreed with, the period on its last second, releasing, and static checks over the parsed source
- [`tests/test_runbook.py`](tests/test_runbook.py) - the demo replayed offline before a transaction is spent, and the live record replayed through this code, including the buyer's balance
- [`tests/test_integration.py`](tests/test_integration.py) - opt in, `GENLAYER_STUDIO=1`: value, senders, and the free refusals on a real runtime

### The tests have teeth

[`scripts/mutate.py`](scripts/mutate.py) removes every defence one at a time
and names the test that caught each mutant. It refuses to run on a red
baseline and exits non-zero if anything escapes.

<!-- measured:mutations:start -->
Measured: **72 mutations, 72 caught, 0 escaped.**

| Mutation | Caught by |
|---|---|
| a word is read as none | `test_an_unusable_answer_is_an_error_and_never_a_ruling` |
| a defect past the list is accepted | `test_an_unusable_answer_is_an_error_and_never_a_ruling` |
| the reversed answer is not read back into the frozen order | `test_a_covered_defect_is_paid_its_frozen_payout_at_once` |
| the reversed pass is never asked | `test_a_covered_defect_is_paid_its_frozen_payout_at_once` |
| a disagreement between the orders keeps the forward defect | `test_a_defect_that_depends_on_the_order_is_none` |
| a disagreement between the orders takes the reversed defect | `test_a_defect_that_depends_on_the_order_is_none` |
| the un-reversal is off by one | `test_once_every_defect_is_paid_a_claim_is_refused_for_free` |
| an unusable answer is not retried | `test_an_unusable_answer_is_an_error_and_never_a_ruling` |
| an unusable answer is read as none | `test_an_unusable_answer_is_an_error_and_never_a_ruling` |
| an answer that is not an object crashes the block | `test_an_unusable_answer_is_an_error_and_never_a_ruling` |
| the free structural layer is skipped | `test_a_ruling_that_names_no_covered_defect_is_refused_with_zero_validator_prompts` |
| a validator agrees with a leader that raised | `test_an_unusable_answer_is_an_error_and_never_a_ruling` |
| a validator trusts the leader | `test_nodes_that_rule_differently_do_not_agree_and_nothing_is_stored` |
| a validator whose own model failed agrees | `test_a_validator_whose_model_fails_does_not_agree` |
| the structural check accepts a defect that does not exist | `test_a_ruling_that_names_no_covered_defect_is_refused_with_zero_validator_prompts` |
| agreement is not exact | `test_nodes_that_rule_differently_do_not_agree_and_nothing_is_stored` |
| the agreed ruling is not checked again before it pays | `test_the_agreed_ruling_is_checked_again_before_it_pays` |
| anyone may claim | `test_only_the_buyer_may_claim` |
| a claim is taken after the warranty ended | `test_a_claim_lands_on_the_last_second_and_is_refused_after_it_for_free` |
| a claim on the last second is refused | `test_a_claim_lands_on_the_last_second_and_is_refused_after_it_for_free` |
| a warranty takes any number of claims | `test_a_warranty_takes_three_claims_at_most` |
| a claim once every defect is paid still asks the model | `test_once_every_defect_is_paid_a_claim_is_refused_for_free` |
| a claim on a closed warranty is taken | `test_anyone_may_release_after_the_end_and_the_seller_gets_the_rest` |
| a decided account may be decided again | `test_an_account_already_decided_is_refused_however_it_is_spaced` |
| the decided accounts care about capitalisation | `test_an_account_already_decided_is_refused_however_it_is_spaced` |
| the account is unbounded | `test_the_account_length_bounds` |
| none pays the first defect | `test_an_account_already_decided_is_refused_however_it_is_spaced` |
| a defect already paid is paid again | `test_a_defect_already_paid_is_decided_by_the_contract_not_the_model` |
| a payment is not remembered on its defect | `test_once_every_defect_is_paid_a_claim_is_refused_for_free` |
| what was paid is not added to the warranty | `test_a_covered_defect_is_paid_its_frozen_payout_at_once` |
| the buyer is not paid | `test_a_covered_defect_is_paid_its_frozen_payout_at_once` |
| the seller is paid instead of the buyer | `test_a_covered_defect_is_paid_its_frozen_payout_at_once` |
| a claim is not counted | `test_a_claim_lands_on_the_last_second_and_is_refused_after_it_for_free` |
| a decided account is not remembered | `test_an_account_already_decided_is_refused_however_it_is_spaced` |
| claims are not linked | `test_a_defect_already_paid_is_decided_by_the_contract_not_the_model` |
| every payout need not be paid in | `test_every_payout_must_be_paid_in_exactly` |
| an overpayment is kept | `test_every_payout_must_be_paid_in_exactly` |
| the money held is not counted at open | `test_a_warranty_opens_with_its_terms_frozen_and_every_payout_held` |
| the seller may be the buyer | `test_the_seller_cannot_be_the_buyer` |
| a buyer that is not an address is accepted | `test_a_buyer_that_is_not_an_address_is_refused` |
| the terms refusal is ignored | `test_malformed_terms_are_refused` |
| an empty list of defects is accepted | `test_every_shape_error_is_refused_with_its_reason` |
| more than six defects are accepted | `test_malformed_terms_are_refused` |
| a defect of any length is accepted | `test_malformed_terms_are_refused` |
| two defects with the same wording are accepted | `test_malformed_terms_are_refused` |
| a missing payout is accepted | `test_malformed_terms_are_refused` |
| more than four exclusions are accepted | `test_malformed_terms_are_refused` |
| an exclusion of any length is accepted | `test_malformed_terms_are_refused` |
| a payout in any notation is read | `test_malformed_terms_are_refused` |
| a payout of zero is accepted | `test_malformed_terms_are_refused` |
| a missing defect is dropped and the payouts shift | `test_malformed_terms_are_refused` |
| the product is unbounded | `test_the_other_bounds` |
| the period is unbounded | `test_the_other_bounds` |
| release before the end is allowed | `test_release_is_refused_until_the_warranty_ends` |
| a warranty is released twice | `test_anyone_may_release_after_the_end_and_the_seller_gets_the_rest` |
| release returns everything, paid or not | `test_anyone_may_release_after_the_end_and_the_seller_gets_the_rest` |
| the seller is never refunded | `test_anyone_may_release_after_the_end_and_the_seller_gets_the_rest` |
| a payout beyond what is held is sent | `test_a_payout_beyond_what_is_held_is_refused` |
| the transfer is never made | `test_a_covered_defect_is_paid_its_frozen_payout_at_once` |
| a zero payout is sent | `test_a_warranty_paid_out_in_full_releases_nothing_and_sends_no_empty_transfer` |
| the fence is removed | `test_caller_text_is_stored_verbatim_and_fenced_only_at_the_prompt` |
| the fence leaves square brackets | `test_caller_text_is_stored_verbatim_and_fenced_only_at_the_prompt` |
| the account reaches the prompt unfenced | `test_caller_text_is_stored_verbatim_and_fenced_only_at_the_prompt` |
| the covered defects reach the prompt unfenced | `test_caller_text_is_stored_verbatim_and_fenced_only_at_the_prompt` |
| the exclusions reach the prompt unfenced | `test_caller_text_is_stored_verbatim_and_fenced_only_at_the_prompt` |
| the product reaches the prompt unfenced | `test_every_value_interpolated_into_the_prompt_is_fenced_or_ours` |
| the exclusions never reach the prompt | `test_the_exclusions_reach_the_prompt_and_are_never_an_answer` |
| the prompt no longer reads an exclusion as none | `test_the_exclusions_reach_the_prompt_and_are_never_an_answer` |
| the prompt no longer states the range | `test_the_prompt_states_the_count_and_never_an_amount` |
| a leader's reason is stored as sent | `test_the_reason_is_not_compared_and_a_lying_leader_s_is_sanitised` |
| a leader's reason is stored uncapped | `test_the_reason_is_not_compared_and_a_lying_leader_s_is_sanitised` |
| control characters are stored | `test_clean_text_collapses_whitespace_and_control_characters` |
<!-- measured:mutations:end -->

## Design rules applied

- **Settle what can be settled before the model:** a claim no ruling could pay is refused for free.
- **The coarsest answer that still carries the judgment:** an index into the covered defects, or none; exclusions are reasons, never answers.
- **No single call reveals what only the contract should see:** no payout ever enters the prompt.
- **Uncertainty in the value, never in the comparison:** an order-dependent defect is none, and none is declined.
- **Every judgment has a clock:** nothing can be claimed or ruled after the period, and the rest goes back to the seller.
- **Money moves at the root of the transaction,** state first, through one guarded path.
- **Tagging untrusted text is not a fence:** `fence()` at the prompt boundary, rows numbered by the contract.
- **The deployment is the submission:** `scripts/verify_deployment.py` reads the deployed source back and lints it.

## Further reading in this repository

- [DECISIONS.md](DECISIONS.md) - why each rule is the way it is
- [DEPLOY.md](DEPLOY.md) - the demo, step by step
- [SUBMISSION.md](SUBMISSION.md) - what to check before submitting
- [`lib/warranty_consensus.py`](lib/warranty_consensus.py) - the claim rules, generated from the contract

## Related work

- [Mandate](https://github.com/meitipro/mandate) - a treasury that pays only what its charter allows
- [Tally](https://github.com/meitipro/tally) - an invoice paid line by line, only for what the order ordered
- [Tender](https://github.com/meitipro/tender) - the cheapest bid that meets every requirement
