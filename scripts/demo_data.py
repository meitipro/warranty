"""The demo's data, in one place.

scripts/demo.py sends exactly these values to StudioNet, and
tests/test_runbook.py replays them offline, so the demo on the explorer and the
demo the tests check cannot drift apart.

One warranty on an espresso machine, with three covered defects and two
exclusions. Each claim changes one thing, so each rule of the contract shows
once, on chain:

  PUMP          the pump fault, in the buyer's words: covered defect 0, paid
  DROPPED       the boiler fault, but the account says the machine was knocked
                off the counter: an exclusion, none, declined
  PUMP_AGAIN    the pump again, described differently: covered defect 0, which
                this warranty has already paid; the contract, not the model,
                pays nothing
  STEAM         a fourth claim: refused before any model is asked; after the
                period, refused again for the clock

Then the period runs out and a stranger releases the rest to the seller.
"""

GEN = 10 ** 18

PRODUCT = "Kestrel K2 espresso machine, serial KS2-40871"
DEFECTS = [
    # (covered defect, payout)
    ("The pump stops pushing water through the group head", 30 * GEN // 100),
    ("The boiler does not heat water to brewing temperature", 30 * GEN // 100),
    ("The steam wand leaks or produces no steam", 10 * GEN // 100),
]
EXCLUSIONS = [
    "Damage from dropping the machine or knocking it over",
    "Liquid spilled into the body or the electronics of the machine",
]
PERIOD = 600

PUMP = ("Since Tuesday the pump hums when I press the brew button, but no water at all comes through the "
        "group head, with fresh coffee and a clean basket.")
DROPPED = ("My cat knocked the machine off the kitchen counter last night, and since then the boiler stays "
           "cold and the water never heats up.")
PUMP_AGAIN = ("The pump has stopped working again: it buzzes when I start a shot but pushes no water through "
              "the group head at all.")
STEAM = ("The steam wand drips water constantly and produces no steam at all when I open the knob to "
         "froth milk.")


def joined(defects, exclusions):
    """(defects, payouts, exclusions) as the three pipe joined strings open() takes."""
    return ("|".join(d for d, _ in defects), "|".join(str(p) for _, p in defects), "|".join(exclusions))


def total(defects):
    return sum(p for _, p in defects)


# The demo, step by step, exactly as scripts/demo.py sends it and
# tests/test_runbook.py replays it: (who, method, arguments, expected, label).
# A step marked "after_end" waits until the warranty has ended. The buyer's
# address is filled in by whoever replays the steps.
STEPS = [
    ("seller", "open", (PRODUCT, "buyer", DEFECTS, EXCLUSIONS, PERIOD), "ok",
     "warranty 0 opened: three covered defects, every payout paid in"),
    ("stranger", "claim", (0, PUMP), "refused", "a stranger claims"),
    ("buyer", "claim", (0, PUMP), "ok", "the pump: covered defect 0, paid"),
    ("buyer", "claim", (0, PUMP), "refused", "the same account again"),
    ("buyer", "claim", (0, DROPPED), "ok", "the boiler, after a fall: excluded, declined"),
    ("buyer", "claim", (0, PUMP_AGAIN), "ok", "the pump again: already paid"),
    ("buyer", "claim", (0, STEAM), "refused", "a fourth claim"),
    ("seller", "release", (0,), "refused", "the seller releases before the end"),
    ("buyer", "claim", (0, STEAM), "refused", "a claim after the warranty ended", "after_end"),
    ("stranger", "release", (0,), "ok", "the rest released to the seller", "after_end"),
]

# What each ok claim is expected to be ruled, in order.
EXPECTED_RULINGS = ["0", "none", "0"]
