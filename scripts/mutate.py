"""Mutation pass: break every defence on purpose, confirm a test notices.

Passing tests prove nothing on their own. Each entry below is a small edit to
the contract that removes a defence. The suite must fail for every one of them,
and this script records WHICH test caught it, so the table in the README is
measured rather than claimed.

    python scripts/mutate.py            # run them all, print what caught what
    python scripts/mutate.py --md       # emit the markdown table for the README

An escaping mutation is a finding, not a nuisance: either a missing test, or a
later defence strict enough that an earlier test can no longer fail. The script
exits non-zero if anything escapes, and refuses to run on a red baseline.

Three rules keep the harness honest:

  * the unmutated suite must be green before anything is mutated;
  * a find string that is missing, or matches more than once, is a failure of
    the harness, never a skip, so refactoring cannot quietly turn a row off;
  * scripts/lift.py runs inside every mutated copy before the suite, so the lib
    parity test can never stand in for the behavioural test a mutation deserves.
"""

import argparse
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).absolute().parent.parent
TARGET = "warranty.py"

FENCE = '    return str(raw).replace("<", "(").replace(">", ")").replace("[", "(").replace("]", ")")'
PAID_IN = "        if paid_in != total:"

MUTATIONS = [
    # -- reading the answer
    ("a word is read as none", '        return ""\n    k = int(s)', "        return NONE\n    k = int(s)"),
    ("a defect past the list is accepted", '    if k < 0 or k >= n:\n        return ""', '    if k < 0:\n        return ""'),

    # -- the two orders
    ("the reversed answer is not read back into the frozen order",
     '            return {"defect": fold(fwd, unreverse(rev, n)), "because": because}',
     '            return {"defect": fold(fwd, rev), "because": because}'),
    ("the reversed pass is never asked",
     "            rev, _ = ask(product, reversed_names, excl, body, n)", "            rev, _ = ask(product, names, excl, body, n)"),
    ("a disagreement between the orders keeps the forward defect",
     "    return forward if forward == reverse_unreversed else NONE", "    return forward"),
    ("a disagreement between the orders takes the reversed defect",
     "    return forward if forward == reverse_unreversed else NONE", "    return reverse_unreversed"),
    ("the un-reversal is off by one", "    return str(n - 1 - int(choice))", "    return str(n - int(choice))"),

    # -- reading the model
    ("an unusable answer is not retried",
     "    for _ in range(2):\n        raw = gl.nondet.exec_prompt(", "    for _ in range(1):\n        raw = gl.nondet.exec_prompt("),
    ("an unusable answer is read as none",
     '    raise gl.vm.UserError(f"{ERR_LLM} the model named no covered defect and did not say none")',
     '    return NONE, ""'),
    ("an answer that is not an object crashes the block",
     "        if isinstance(raw, dict):\n            choice = normalise_choice", "        if True:\n            choice = normalise_choice"),

    # -- the validator
    ("the free structural layer is skipped",
     "            if not ruling_sound(proposed, n):\n                return False\n            try:", "            try:"),
    ("a validator agrees with a leader that raised",
     "                # An [LLM_ERROR] is never agreed with.\n                return False",
     "                # An [LLM_ERROR] is never agreed with.\n                return True"),
    ("a validator trusts the leader", '            return warranty_agrees(mine["defect"], proposed, n)', "            return True"),
    ("a validator whose own model failed agrees",
     "            except gl.vm.UserError:\n                return False", "            except gl.vm.UserError:\n                return True"),
    ("the structural check accepts a defect that does not exist", "    return int(s) < n", "    return True"),
    ("agreement is not exact", "and str(mine) == str(theirs)", "and str(mine) != '' "),
    ("the agreed ruling is not checked again before it pays",
     '        if not ruling_sound(choice, n):\n            raise gl.vm.UserError(f"{ERR_EXPECTED} the ruling names no covered defect")',
     '        if False:\n            raise gl.vm.UserError(f"{ERR_EXPECTED} the ruling names no covered defect")'),

    # -- before the model
    ("anyone may claim", "        if gl.message.sender_address != w.buyer:", "        if False:"),
    ("a claim is taken after the warranty ended", "        if self._now() > int(w.ends_at):", "        if False:"),
    ("a claim on the last second is refused", "        if self._now() > int(w.ends_at):", "        if self._now() >= int(w.ends_at):"),
    ("a warranty takes any number of claims", "        if int(w.n_claims) >= MAX_CLAIMS:", "        if False:"),
    ("a claim once every defect is paid still asks the model", "        if all(paid):", "        if False:"),
    ("a claim on a closed warranty is taken",
     '        if str(w.status) != ACTIVE:\n            raise gl.vm.UserError(f"{ERR_EXPECTED} this warranty is closed")\n        if self._now()',
     '        if False:\n            raise gl.vm.UserError(f"{ERR_EXPECTED} this warranty is closed")\n        if self._now()'),
    ("a decided account may be decided again", "        if seen > 0:", "        if False:"),
    ("the decided accounts care about capitalisation", "        d = digest(body.lower())", "        d = digest(body)"),
    ("the account is unbounded", "        if len(body) < MIN_ACCOUNT or len(body) > MAX_ACCOUNT:", "        if False:"),

    # -- what the contract decides
    ("none pays the first defect",
     "    if choice == NONE:\n        return DECLINED, 0\n    k = int(choice)", "    k = 0 if choice == NONE else int(choice)"),
    ("a defect already paid is paid again", "    if paid[k]:", "    if False:"),
    ("a payment is not remembered on its defect", "            self.defects[first + int(choice)].paid_by = u256(cid + 1)\n", ""),
    ("what was paid is not added to the warranty", "            w.paid_out = u256(int(w.paid_out) + pay)\n", ""),
    ("the buyer is not paid", "            self._send(w.buyer, pay)", "            pass"),
    ("the seller is paid instead of the buyer", "            self._send(w.buyer, pay)", "            self._send(w.seller, pay)"),
    ("a claim is not counted", "        w.n_claims = u256(int(w.n_claims) + 1)\n", ""),
    ("a decided account is not remembered", '        self.decided[f"{wid}:{d}"] = u256(cid + 1)\n', ""),
    ("claims are not linked", "            self.claims[int(w.last_claim)].next = u256(cid)", "            pass"),

    # -- opening
    ("every payout need not be paid in", PAID_IN, "        if False:"),
    ("an overpayment is kept", PAID_IN, "        if paid_in < total:"),
    ("the money held is not counted at open", "        self.held = u256(int(self.held) + total)", "        pass"),
    ("the seller may be the buyer", "        if who == gl.message.sender_address:", "        if False:"),
    ("a buyer that is not an address is accepted", "        if not looks_like_address(buyer):", "        if False:"),
    ("the terms refusal is ignored", '        if refusal != "":', "        if False:"),
    ("an empty list of defects is accepted",
     '    if len(defects) == 0 or (len(defects) == 1 and defects[0] == ""):', "    if False:"),
    ("more than six defects are accepted", "    if len(defects) > MAX_DEFECTS:", "    if False:"),
    ("a defect of any length is accepted", "        if len(d) < MIN_ITEM or len(d) > MAX_ITEM:", "        if False:"),
    ("two defects with the same wording are accepted",
     "    if len(set(d.lower() for d in defects)) != len(defects):", "    if False:"),
    ("a missing payout is accepted", "    if payouts is None or len(payouts) != len(defects):", "    if payouts is None:"),
    ("more than four exclusions are accepted", "    if len(exclusions) > MAX_EXCLUSIONS:", "    if False:"),
    ("an exclusion of any length is accepted", "        if len(x) < MIN_ITEM or len(x) > MAX_ITEM:", "        if False:"),
    ("a payout in any notation is read",
     '        if part == "" or len(part) > 28 or any(ch not in "0123456789" for ch in part):', '        if part == "":'),
    ("a payout of zero is accepted", "        if v < low or v > high:", "        if v > high:"),
    ("a missing defect is dropped and the payouts shift",
     '    return [clean_text(part) for part in str(text).split("|")]',
     '    return [clean_text(part) for part in str(text).split("|") if clean_text(part)]'),
    ("the product is unbounded", "        if len(p) < MIN_PRODUCT or len(p) > MAX_PRODUCT:", "        if False:"),
    ("the period is unbounded", "        if span < MIN_PERIOD or span > MAX_PERIOD:", "        if False:"),

    # -- releasing and the money
    ("release before the end is allowed", "        if now <= int(w.ends_at):", "        if False:"),
    ("a warranty is released twice",
     '        if str(w.status) != ACTIVE:\n            raise gl.vm.UserError(f"{ERR_EXPECTED} this warranty is closed")\n        now = self._now()',
     '        if False:\n            raise gl.vm.UserError(f"{ERR_EXPECTED} this warranty is closed")\n        now = self._now()'),
    ("release returns everything, paid or not", "        rest = int(w.funded) - int(w.paid_out) - int(w.refunded)",
     "        rest = int(w.funded)"),
    ("the seller is never refunded", "        self._send(w.seller, rest)", "        pass"),
    ("a payout beyond what is held is sent", "        if amount > int(self.held):", "        if False:"),
    ("the transfer is never made", "        _Payee(to).emit_transfer(value=u256(amount))", "        pass"),
    ("a zero payout is sent", "        if amount == 0:\n            return", "        if False:\n            return"),

    # -- the prompt boundary
    ("the fence is removed", FENCE, "    return str(raw)"),
    ("the fence leaves square brackets", FENCE, '    return str(raw).replace("<", "(").replace(">", ")")'),
    ("the account reaches the prompt unfenced", "{fence(account)}", "{account}"),
    ("the covered defects reach the prompt unfenced", 'f"[{k}] {fence(defects[k])}"', 'f"[{k}] {defects[k]}"'),
    ("the exclusions reach the prompt unfenced", 'f"- {fence(x)}"', 'f"- {x}"'),
    ("the product reaches the prompt unfenced", "{fence(product)}", "{product}"),
    ("the exclusions never reach the prompt", "\n<exclusions>\n{excluded}\n</exclusions>\n", "\n<exclusions>\n- (none listed)\n</exclusions>\n"),
    ("the prompt no longer reads an exclusion as none",
     "Answer none if the fault is not one of the covered defects, or if the account\nitself says the fault was caused by something listed in <exclusions>, even when\nthe fault would otherwise match a covered defect.",
     "Answer none if the fault is not one of the covered defects."),
    ("the prompt no longer states the range",
     "Number of covered defects: {n}. Answer with one number from 0 to {n - 1}, or none.", "Answer with a number, or none."),
    ("a leader's reason is stored as sent", '            why=sanitise_reason(res.get("because", "")), next=u256(0),',
     '            why=str(res.get("because", "")), next=u256(0),'),
    ("a leader's reason is stored uncapped", '    return " ".join("".join(out).split())[:limit]', '    return " ".join("".join(out).split())'),
    ("control characters are stored", '            out.append(" ")\n        else:', "            out.append(ch)\n        else:"),
]


PYTEST = [sys.executable, "-m", "pytest", "tests/", "-x", "-q", "--no-header", "-p", "no:cacheprovider"]


def copy_repo(tmp):
    dst = pathlib.Path(tmp) / "repo"
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(
        "__pycache__", ".pytest_cache", ".git", "artifacts", "*.pyc"))
    return dst


def run_one(label, find, replace):
    with tempfile.TemporaryDirectory() as tmp:
        dst = copy_repo(tmp)
        target = dst / "contracts" / TARGET
        src = target.read_text(encoding="utf-8")
        hits = src.count(find)
        if hits == 0:
            return "PATTERN NOT FOUND", None
        if hits > 1:
            return "PATTERN NOT UNIQUE", None
        target.write_text(src.replace(find, replace, 1), encoding="utf-8", newline="\n")
        subprocess.run([sys.executable, "scripts/lift.py"], cwd=dst, capture_output=True)
        proc = subprocess.run(PYTEST, cwd=dst, capture_output=True, text=True)
        if proc.returncode == 0:
            return "ESCAPED", None
        text = proc.stdout + proc.stderr
        m = re.search(r"^(?:FAILED|ERROR) (\S+?)::(\S+?)(?:\[|\s|$)", text, re.M)
        if m:
            return "caught", m.group(2).split("::")[-1]
        m = re.search(r"^E\s+(\w*(?:Error|Exception))", text, re.M)
        if m:
            return "caught", m.group(1) + " at import"
        return "caught", "unnamed failure"


def baseline_is_green():
    with tempfile.TemporaryDirectory() as tmp:
        dst = copy_repo(tmp)
        proc = subprocess.run(PYTEST, cwd=dst, capture_output=True, text=True)
        return proc.returncode == 0, (proc.stdout + proc.stderr)[-2000:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", action="store_true", help="emit the README table")
    args = ap.parse_args()

    green, tail = baseline_is_green()
    if not green:
        print("the unmutated suite is not green; every mutation would look caught:\n" + tail, file=sys.stderr)
        return 2

    rows, escaped = [], []
    for label, find, replace in MUTATIONS:
        status, test = run_one(label, find, replace)
        if status == "caught":
            rows.append((label, test))
            if not args.md:
                print("  caught   %-70s %s" % (label, test), flush=True)
        else:
            escaped.append((label, status))
            print("  %-8s %s" % (status, label), file=sys.stderr, flush=True)

    if args.md:
        print("| Mutation | Caught by |")
        print("|---|---|")
        for label, test in rows:
            print("| %s | `%s` |" % (label, test))
    else:
        print()
        print("  %d mutations, %d caught, %d escaped" % (len(MUTATIONS), len(rows), len(escaped)))
    return 1 if escaped else 0


if __name__ == "__main__":
    sys.exit(main())
