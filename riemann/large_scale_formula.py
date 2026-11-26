"""Stable local evaluations of the paired explicit formula near large primes.

The older evaluator is deliberately restricted to 2 <= x <= 100. This
module evaluates the same finite formula in a separately validated regime:
centers near 10**6, 10**9, 10**12, and 10**15, with local offsets <= 500.

For a fixed window, M = floor(log2(window_max)) is held constant and

    F_K(x) = sum_{m=1}^M mu(m)/m * [Ei(log(x)/m)
             - 2 Re sum_{n=1}^K Ei(rho_n log(x)/m)
             - log(2) + sum_{j>=1} E1(2j log(x)/m)].

The prime list and an exact prime-count baseline are NOT inputs. Absolute
centers are returned as decimal strings so a caller can subtract an exact
large integer without first rounding both to binary64. Local increments
are evaluated directly, never by subtracting two enormous function values.

Writing v = log(p), delta = log1p(h/p), their integrand is

    dF_K/dv = sum_m mu(m)/m / v * [exp(v/m)
               - 2 Re sum_n exp(rho_n v/m) - 1/expm1(2v/m)].

A scaled Taylor series integrates this analytic expression. It resolves
the oscillations for p near one million and stays accurate when delta is
only about 10**-13 near one quadrillion. Each result is independently
checked with direct complex Ei values and Gauss-Legendre integration.

The input zero table's uncertainty is reported separately from numerical
checks and finite-zero truncation error. No numerical check here proves RH.
"""

from __future__ import annotations

import math
from pathlib import Path

import mpmath as mp
import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.special import exp1, expi


HERE = Path(__file__).resolve().parent
DEFAULT_COUNTS = (0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000)
TABLE_HEIGHT_ERROR = 3e-9
TAYLOR_DEGREE = 64
ASYMPTOTIC_TERMS = 20
ASYMPTOTIC_MIN = 128.0
LD = np.longdouble
CLD = np.clongdouble


def mobius_weights(limit: int) -> list[tuple[int, int]]:
    """Return (m, mu(m)); coefficients remain exact integers until division."""
    result = []
    for m in range(1, limit + 1):
        n, mu, divisor = m, 1, 2
        while divisor * divisor <= n:
            if n % divisor == 0:
                n //= divisor
                mu = -mu
                if n % divisor == 0:
                    mu = 0
                    break
                while n % divisor == 0:
                    n //= divisor
            divisor += 1
        if mu and n > 1:
            mu = -mu
        if mu:
            result.append((m, mu))
    return result


def _heights_as_strings(heights: np.ndarray | None) -> list[str]:
    if heights is None:
        return (HERE / "data" / "odlyzko_zeros_10000.txt").read_text().split()
    return [str(value) for value in np.asarray(heights)]


def _trivial_series(u: float) -> tuple[float, float, int]:
    # u is at least approximately log(2) in the validated windows.
    last = max(1, math.ceil(88 / (2 * u)))
    values = exp1(2 * u * np.arange(1, last + 1, dtype=float))
    total = float(np.sum(values, dtype=LD))
    tail = float(exp1(2 * u * (last + 1)) / (-np.expm1(-2 * u)))
    return total, tail, last


def _real_ei_values(
    v_mp: mp.mpf, m: int, gamma_text: list[str], rho: np.ndarray,
) -> tuple[np.ndarray, float]:
    """High precision at small arguments; long-double asymptotics elsewhere.

    Only the real part enters the paired formula, so the imaginary branch
    constant of Ei in the upper half-plane need not be represented.
    """
    u = LD(str(v_mp / m))
    z = rho * u
    low = np.flatnonzero(np.abs(z) < ASYMPTOTIC_MIN)
    values = np.empty(len(z), dtype=LD)
    for index in low:
        argument = (mp.mpf("0.5") + mp.j * mp.mpf(gamma_text[index])) * v_mp / m
        values[index] = LD(str(mp.re(mp.ei(argument))))
    start = len(low)
    high = z[start:]
    if len(high):
        term = np.ones_like(high)
        series = term.copy()
        for order in range(1, ASYMPTOTIC_TERMS):
            term *= LD(order) / high
            series += term
        values[start:] = (np.exp(high) / high * series).real

    # Direct mpmath samples straddle the asymptotic switch and reach the
    # largest phase; they are not the formula used by the asymptotic path.
    samples = sorted(set([0, min(start, len(z)-1), min(start+1, len(z)-1), len(z)-1]))
    worst = mp.mpf(0)
    for index in samples:
        argument = (mp.mpf("0.5") + mp.j * mp.mpf(gamma_text[index])) * v_mp / m
        reference = mp.re(mp.ei(argument))
        difference = abs(mp.mpf(str(values[index])) - reference)
        worst = max(worst, difference)
    return values, float(worst)


def _increment_coefficients(
    v: np.longdouble, scale: np.longdouble, rho: np.ndarray,
    weights: list[tuple[int, int]], counts: tuple[int, ...],
) -> np.ndarray:
    """Coefficients in q=log1p(h/p)/scale, with exact zero constant term."""
    out = np.zeros((TAYLOR_DEGREE + 1, len(counts)), dtype=LD)
    ratio = scale / v
    positive = np.array([k for k in counts if k], dtype=int)
    slots = [i for i, k in enumerate(counts) if k]
    for m, mu in weights:
        weight = LD(mu) / LD(m)
        amplitude = np.exp(v / LD(m))
        zero_amplitudes = np.exp(rho * (v / LD(m)))
        _, _, last = _trivial_series(float(v / LD(m)))
        trivial_a = -2 * np.arange(1, last + 1, dtype=LD) / LD(m)
        trivial_amplitudes = np.exp(trivial_a * v)
        smooth_b = LD(1)
        zero_b = np.ones(len(rho), dtype=CLD)
        trivial_b = np.ones(last, dtype=LD)
        smooth_exp = LD(1)
        zero_exp = np.ones(len(rho), dtype=CLD)
        trivial_exp = np.ones(last, dtype=LD)
        for n in range(TAYLOR_DEGREE):
            if n:
                smooth_exp *= (scale / LD(m)) / LD(n)
                zero_exp *= (rho * (scale / LD(m))) / LD(n)
                trivial_exp *= (trivial_a * scale) / LD(n)
                smooth_b = smooth_exp - ratio * smooth_b
                zero_b = zero_exp - ratio * zero_b
                trivial_b = trivial_exp - ratio * trivial_b
            baseline = amplitude * smooth_b - np.sum(trivial_amplitudes * trivial_b, dtype=LD)
            current = np.full(len(counts), baseline, dtype=LD)
            if len(positive):
                partial = np.cumsum((zero_amplitudes * zero_b).real, dtype=LD)
                current[slots] -= 2 * partial[positive - 1]
            out[n + 1] += weight * ratio / LD(n + 1) * current
    return out


def _quadrature_increment(
    v: np.longdouble, delta: np.longdouble, rho: np.ndarray,
    weights: list[tuple[int, int]], count: int,
) -> float:
    """Independent integration of the unexpanded analytic derivative."""
    nodes, quadrature_weights = leggauss(32)
    total = LD(0)
    for node, quadrature_weight in zip(nodes, quadrature_weights):
        position = v + delta * (LD(node) + 1) / 2
        derivative = LD(0)
        for m, mu in weights:
            u = position / LD(m)
            bracket = np.exp(u) - 1 / np.expm1(2 * u)
            if count:
                bracket -= 2 * np.sum(np.exp(rho[:count] * u).real, dtype=LD)
            derivative += LD(mu) / LD(m) * bracket / position
        total += LD(quadrature_weight) * derivative
    return float(total * delta / 2)


def compute_window(
    prime: int, offsets: np.ndarray, counts: tuple[int, ...] = DEFAULT_COUNTS,
    heights: np.ndarray | None = None,
) -> dict[str, object]:
    """Return decimal center values and stable local increment curves.

    Results:
      centers_decimal[K]: F_K(prime), as a decimal string;
      increments[K]: F_K(prime+h)-F_K(prime), for each supplied offset h;
      metadata: cutoff, numerical cross-checks, and zero-table uncertainties.

    To plot absolute count errors, subtract an exact midpoint from the
    decimal center with Decimal or mpmath BEFORE converting to float.

    The input guard allows integer centers from 10**6 through 2**53, but
    the four demonstration centers are the ones tested and documented.
    The per-call checks do not establish accuracy at every allowed input.
    """
    if not isinstance(prime, (int, np.integer)) or prime < 1_000_000 or prime > 2**53:
        raise ValueError("Center must be an integer from one million through 2**53.")
    prime = int(prime)
    offsets = np.asarray(offsets, dtype=float)
    if offsets.ndim != 1 or not len(offsets) or not np.all(np.isfinite(offsets)):
        raise ValueError("Offsets must be a finite nonempty vector.")
    if np.max(np.abs(offsets)) > 500:
        raise ValueError("This local evaluator is validated for offsets of at most 500.")
    counts = tuple(int(k) for k in counts)
    gamma_text = _heights_as_strings(heights)
    if not counts or min(counts) < 0 or max(counts) > len(gamma_text):
        raise ValueError("Requested zero counts exceed the supplied data.")
    needed = max(counts)
    # Keep at least one term internally for the K=0-only validation path.
    gamma_text = gamma_text[:max(needed, 1)]
    gamma = np.array(gamma_text, dtype=LD)
    if np.any(gamma <= 0) or np.any(np.diff(gamma) <= 0):
        raise ValueError("Zero heights must be positive and strictly increasing.")
    rho = LD("0.5") + CLD(1j) * gamma
    maximum = prime + max(0, math.ceil(float(offsets.max())))
    cutoff = maximum.bit_length() - 1
    weights = mobius_weights(cutoff)
    deltas = np.log1p(offsets.astype(LD) / LD(prime))
    scale = LD(np.max(np.abs(deltas)))
    if gamma[-1] * scale > 8:
        raise ValueError("The local phase interval exceeds the validated Taylor range.")

    with mp.workdps(55):
        v_mp = mp.log(prime)
        v = LD(str(v_mp))
        baseline = mp.mpf(0)
        zero_sums = {k: mp.mpf(0) for k in counts}
        scipy_sums = {k: mp.mpf(0) for k in counts}
        component_check = 0.0
        trivial_tail = 0.0
        for m, mu in weights:
            u = v_mp / m
            correction, tail, _ = _trivial_series(float(u))
            baseline += mp.mpf(mu) / m * (mp.ei(u) - mp.log(2) + mp.mpf(str(correction)))
            trivial_tail += abs(mu) / m * tail
            values, error = _real_ei_values(v_mp, m, gamma_text, rho)
            component_check = max(component_check, error)
            partial = np.cumsum(2 * values, dtype=LD)
            direct = np.cumsum(2 * expi(np.asarray(rho, dtype=complex) * float(u)).real, dtype=LD)
            for count in counts:
                if count:
                    zero_sums[count] += mp.mpf(mu) / m * mp.mpf(str(partial[count - 1]))
                    scipy_sums[count] += mp.mpf(mu) / m * mp.mpf(str(direct[count - 1]))
        centers = {k: mp.nstr(baseline - zero_sums[k], 42) for k in counts}
        scipy_center_difference = max(float(abs(zero_sums[k] - scipy_sums[k])) for k in counts)
        # A direct mpmath sum checks the absolute center for the first ten
        # pairs without using the asymptotic implementation.
        check_count = min(10, needed)
        mp_correction = mp.mpf(0)
        for m, mu in weights:
            terms = [mp.re(mp.ei((mp.mpf("0.5") + mp.j * mp.mpf(t)) * v_mp / m))
                     for t in gamma_text[:check_count]]
            mp_correction += mp.mpf(2 * mu) / m * mp.fsum(terms)
        # The ten-pair correction may not be requested, so use a dedicated
        # high-precision reference only when it is in the requested set.
        mp_center_difference = (float(abs(zero_sums[check_count] - mp_correction))
                                if check_count in zero_sums else None)

    if scale:
        coefficients = _increment_coefficients(v, scale, rho, weights, counts)
        q = deltas / scale
        values = np.polynomial.polynomial.polyval(q, coefficients)
        shorter = np.polynomial.polynomial.polyval(q, coefficients[:49])
        taylor_check = float(np.max(np.abs(values - shorter)))
        increments = {k: np.asarray(values[i], dtype=float) for i, k in enumerate(counts)}
        quadrature_errors = []
        for index in sorted(set([int(np.argmin(offsets)), int(np.argmax(offsets))])):
            reference = _quadrature_increment(v, deltas[index], rho, weights, needed)
            quadrature_errors.append(abs(reference - increments[needed][index]))
        quadrature_check = max(quadrature_errors, default=0.0)
    else:
        increments = {k: np.zeros_like(offsets) for k in counts}
        taylor_check = quadrature_check = 0.0

    # These are empirical numerical gates, distinct from a certified error
    # analysis and from the much larger finite-zero truncation error.
    assert component_check < 2e-8, component_check
    assert scipy_center_difference < 2e-4, scipy_center_difference
    assert mp_center_difference is None or mp_center_difference < 2e-7, mp_center_difference
    assert taylor_check < 1e-10, taylor_check
    assert quadrature_check < 2e-8, quadrature_check

    eps = LD(str(TABLE_HEIGHT_ERROR))
    reciprocals = np.cumsum(1 / np.sqrt(LD("0.25") + (gamma - eps)**2), dtype=LD)
    amplitude_factor = sum(LD(abs(mu)) / m * np.exp(v / (2 * m)) for m, mu in weights)
    half_width = LD(np.max(np.abs(offsets)))
    lower = LD(prime) - half_width
    increment_factor = sum(LD(abs(mu)) / (m*m) * lower**(LD(1)/(2*m)-1)
                           for m, mu in weights)
    table_center_bounds = {k: float(2 * eps * amplitude_factor * reciprocals[k-1]) if k else 0.0
                           for k in counts}
    table_increment_bounds = {k: float(2 * eps * k * half_width * increment_factor) for k in counts}
    return {
        "prime": prime, "mobius_cutoff": cutoff, "counts": counts,
        "offsets": offsets, "centers_decimal": centers, "increments": increments,
        "metadata": {
            "longdouble_significand_bits": int(np.finfo(LD).nmant + 1),
            "taylor_degree": TAYLOR_DEGREE,
            "maximum_local_zero_phase": float(gamma[-1] * scale),
            "mpmath_sample_Ei_max_absolute_difference": component_check,
            "direct_SciPy_center_max_absolute_difference": scipy_center_difference,
            "direct_mpmath_first_ten_center_difference": mp_center_difference,
            "degree_48_vs_64_increment_max_difference": taylor_check,
            "independent_quadrature_increment_max_difference": quadrature_check,
            "trivial_series_tail_bound": trivial_tail,
            "zero_height_table_error_assumption": TABLE_HEIGHT_ERROR,
            "zero_table_center_error_bounds": table_center_bounds,
            "zero_table_increment_error_bounds": table_increment_bounds,
        },
    }
