#!/usr/bin/env python3
"""Verify the exact local prime data with Python's standard library.

Run from the repository root:
    python riemann/verify_large_prime_windows.py

An optional positional argument selects another JSON file. This checks local
primality, complete prime lists, certificates, and count alignment. The globally
sourced pi(10^k) anchor counts are accepted as inputs, not recomputed.
"""

import argparse
import json
import sys
from fractions import Fraction
from math import gcd, prod
from pathlib import Path


MR_BASES = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
ANCHORS = (10**6, 10**9, 10**12, 10**15)


def require(condition, message):
    """Keep checks active even when Python runs with -O."""
    if not condition:
        raise ValueError(message)


def integer(value, name):
    require(type(value) is int, f"{name} must be an integer")
    return value


def is_prime_u64(n):
    """Deterministic Miller-Rabin for integers below 2^64.

    These seven bases are also used by SymPy's 64-bit isprime implementation:
    https://github.com/sympy/sympy/blob/1.14.0/sympy/ntheory/primetest.py
    """
    integer(n, "primality input")
    require(0 <= n < 2**64, "primality input outside the proven 64-bit range")
    if n < 2:
        return False
    for q in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % q == 0:
            return n == q
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for base in MR_BASES:
        a = base % n
        if a == 0:
            continue
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def verify_certificates(certificates, focal_primes):
    """Prove focal primality using the full-factorization Lucas criterion.

    Each q dividing n-1 must itself be certified. The modular-power and gcd
    conditions force every prime divisor of n to be 1 modulo n-1, hence n
    must be prime. No probabilistic test or external package enters this proof.
    """
    verified = set()

    def visit(key):
        if key in verified:
            return
        certificate = certificates[key]
        n = integer(certificate["n"], f"certificate {key}")
        require(str(n) == key, f"noncanonical certificate key {key}")
        if certificate["type"] == "base_prime_2":
            require(n == 2, "only 2 may use the base certificate")
        else:
            require(n > 2 and certificate["type"] == "full_factorization_lucas",
                    f"invalid certificate type for {n}")
            factors = certificate["n_minus_1_factorization"]
            require(bool(factors), f"missing factors for {n}")
            for q, exponent in factors:
                integer(q, f"factor of {n}-1")
                integer(exponent, f"factor exponent for {n}")
                require(2 <= q < n and exponent >= 1,
                        f"invalid factor or exponent for {n}")
            require(len({q for q, _ in factors}) == len(factors),
                    f"repeated factor in certificate for {n}")
            require(prod(q**e for q, e in factors) == n - 1,
                    f"incomplete factorization for {n}")
            for q, _ in factors:
                visit(str(q))  # q < n ensures acyclic recursion.
            a = integer(certificate["witness"], f"Lucas witness for {n}")
            require(1 < a < n and pow(a, n - 1, n) == 1,
                    f"invalid Fermat congruence for {n}")
            require(all(gcd(pow(a, (n - 1) // q, n) - 1, n) == 1
                        for q, _ in factors), f"invalid Lucas gcd for {n}")
        verified.add(key)

    for p in focal_primes:
        visit(str(p))
    require(verified == set(certificates), "unused or unverified certificate")
    return len(verified)


def verify(data):
    require(data["schema_version"] == 1, "unsupported schema version")
    windows = data["windows"]
    require(len(windows) == 4, "expected exactly four prime windows")
    require(tuple(w["anchor"] for w in windows) == ANCHORS,
            "expected anchors 10^6, 10^9, 10^12, 10^15 in that order")
    rows = data["anchor_count_source"]["rows"]
    require(set(rows) == {str(a) for a in ANCHORS}, "anchor table keys differ")
    metadata = data["primality_validation"]
    require(tuple(metadata["deterministic_64bit_miller_rabin_bases"]) == MR_BASES,
            "Miller-Rabin bases differ from the proven set")
    checked, witnesses, summaries = 0, 0, []

    for window in windows:
        for name in ("anchor", "anchor_exponent", "focal_prime", "pi_anchor",
                     "pi_before_prime", "pi_at_prime", "window_radius",
                     "window_start", "window_end", "pi_before_window"):
            integer(window[name], name)
        a, p = window["anchor"], window["focal_prime"]
        lo, hi = window["window_start"], window["window_end"]
        count = window["pi_anchor"]
        require(a == 10**window["anchor_exponent"], f"anchor exponent near {p}")
        require(window["window_radius"] == 500 and (lo, hi) == (p - 500, p + 500),
                f"window must be exactly p +/- 500 near {p}")
        require(window["endpoints_inclusive"] is True and lo <= a < p <= hi,
                f"invalid inclusive window near {p}")
        require(integer(rows[str(a)], "source anchor count") == count > 0,
                f"source anchor mismatch near {p}")

        primes = window["primes"]
        require(all(type(q) is int for q in primes), f"noninteger prime near {p}")
        actual = [n for n in range(lo, hi + 1) if is_prime_u64(n)]
        require(primes == actual, f"prime list is incomplete or incorrect near {p}")
        offsets = window["prime_offsets_from_focal"]
        require(all(type(d) is int for d in offsets) and offsets == [q - p for q in primes],
                f"prime offsets disagree near {p}")
        require(next((q for q in primes if q > a), None) == p,
                f"{p} is not the first prime after its anchor")
        before = window["pi_before_window"]
        require(before + sum(q <= a for q in primes) == count,
                f"window baseline disagrees with anchor near {p}")
        require(before + sum(q < p for q in primes) == window["pi_before_prime"] == count,
                f"left limit at {p} is inconsistent")
        require(before + sum(q <= p for q in primes) == window["pi_at_prime"] == count + 1,
                f"prime step at {p} is inconsistent")
        midpoint = Fraction(2 * count + 1, 2)
        require(window["pi_midpoint"] == midpoint
                and window["pi_midpoint_exact"] == f"{count}.5",
                f"midpoint at {p} is inconsistent")

        validation = window["validation"]
        require(validation["focal_lucas_certificate"] == str(p),
                f"wrong focal certificate near {p}")
        require(validation["window_integers_checked"] == hi - lo + 1,
                f"incorrect checked-integer count near {p}")
        require(validation["no_primes_between_anchor_and_focal"] is True,
                f"incorrect first-prime claim near {p}")
        if "intervening_composites_with_proper_factors" in validation:
            composites = validation["intervening_composites_with_proper_factors"]
            require([c["n"] for c in composites] == list(range(a + 1, p)),
                    f"composite witness coverage is incomplete near {p}")
            for composite in composites:
                n = integer(composite["n"], "composite witness input")
                f = integer(composite["proper_factor"], "composite factor")
                require(1 < f < n and n % f == 0, f"invalid composite witness for {n}")
            witnesses += len(composites)
        checked += hi - lo + 1
        summaries.append(f"  p={p:,}: {len(primes)} primes; pi(p-)={count:,}; midpoint={count:,}.5")

    certificates = verify_certificates(data["lucas_certificates"],
                                       [w["focal_prime"] for w in windows])
    require(certificates == metadata["verified_certificate_count"],
            "certificate count differs from recorded count")
    require(checked == 4004, "expected 4,004 checked window integers")
    return summaries, checked, witnesses, certificates


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("data", nargs="?", type=Path,
                        default=Path(__file__).resolve().parent / "data" / "large_prime_windows.json",
                        help="JSON data path (defaults to the bundled data)")
    args = parser.parse_args()
    try:
        # Parse decimal half-integers as exact rational values, without floats.
        data = json.loads(args.data.read_text(encoding="utf-8"), parse_float=Fraction)
        summaries, checked, witnesses, certificates = verify(data)
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 1
    print("PASS: all four exact local prime windows verified.")
    print("\n".join(summaries))
    print(f"Checked {checked:,} integers, {witnesses} composite witnesses, "
          f"and {certificates} recursive Lucas certificates.")
    print("Global pi(anchor) counts are sourced inputs; they were not recomputed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
