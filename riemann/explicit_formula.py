"""Numerical versions of Riemann's explicit formula on 2 <= x <= 100.

The reconstruction functions do not use the list of primes. The separate
sieve below provides the comparison staircase and validation reference.

For y > 1 and rho_n = 1/2 + i gamma_n, the paired, truncated formula is

    J_K(y) = Ei(log y) - 2 Re sum_{n=1}^K Ei(rho_n log y)
             - log(2) + sum_{j>=1} E1(2 j log y).

The last series equals integral_y^infinity dt/[t (t^2-1) log t].
Mobius inversion removes prime powers:

    pi_K(x) = sum_{m=1}^6 mu(m)/m J_K(x**(1/m)).

The fixed cutoff 6 is sufficient on this domain: 100 < 2**7, and the
complete J(y) vanishes for 1 < y < 2. Keeping the cutoff fixed also avoids
artificial jumps when a new term switches on in a finite approximation.

Ei(rho * log y) is evaluated directly. Taking the principal log after
forming y**rho would wrap its phase and implement the wrong branch.
At a prime the full formula converges to the midpoint of the prime-count
jump. Finite sums ring near jumps; convergence is not pointwise monotone.

References:
https://www.maths.tcd.ie/pub/HistMath/People/Riemann/Zeta/EZeta.pdf
https://math.ucr.edu/home/baez/mathematical/riemann_explicit_formula/explicit_formulas.html
https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.expi.html
https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.exp1.html
"""

from __future__ import annotations

from math import factorial, isqrt
from pathlib import Path

import numpy as np
from numpy.polynomial.chebyshev import chebval
from scipy.fft import dct
from scipy.special import exp1, expi


DOMAIN = (2.0, 100.0)
MOBIUS_WEIGHTS = ((1, 1.0), (2, -0.5), (3, -1 / 3), (5, -0.2), (6, 1 / 6))
ASYMPTOTIC_TERMS = 14
ASYMPTOTIC_ARGUMENT_MIN = 64.0
CHEBYSHEV_DEGREE = 1024


def load_zero_heights(path: Path) -> np.ndarray:
    """Read the bundled first 10,000 positive imaginary parts."""
    heights = np.loadtxt(path, dtype=float)
    if (heights.shape != (10000,) or not np.all(np.isfinite(heights))
            or heights[0] <= 0 or not np.all(np.diff(heights) > 0)):
        raise ValueError("Expected exactly 10,000 increasing positive zero heights.")
    return heights


def sieve_primes(limit: int) -> np.ndarray:
    """Exact reference data, never used inside the explicit formula."""
    if limit < 2:
        return np.array([], dtype=int)
    is_prime = np.ones(limit + 1, dtype=bool)
    is_prime[:2] = False
    for p in range(2, isqrt(limit) + 1):
        if is_prime[p]:
            is_prime[p * p::p] = False
    return np.flatnonzero(is_prime)


def trivial_zero_correction(u: np.ndarray, tol: float = 1e-13) -> np.ndarray:
    """Return sum_{j>=1} E1(2ju), with a geometric tail bound."""
    u = np.asarray(u, dtype=float)
    if not np.all(np.isfinite(u)) or np.any(u <= 0):
        raise ValueError("The correction requires positive, finite log arguments.")
    total = np.zeros_like(u)
    denominator = -np.expm1(-2 * u)
    for j in range(1, 10001):
        term = exp1(2 * j * u)
        total += term
        # E1(z+a) <= exp(-a) E1(z), so this bounds the remaining tail.
        if np.max(term / denominator) < tol:
            return total
    raise RuntimeError("The trivial-zero correction did not converge.")


def _check_inputs(x: np.ndarray, heights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=float)
    heights = np.asarray(heights, dtype=float)
    if (x.ndim != 1 or x.size == 0 or not np.all(np.isfinite(x))
            or np.any(x < DOMAIN[0]) or np.any(x > DOMAIN[1])):
        raise ValueError("Use a nonempty vector of x values in [2, 100].")
    if (heights.ndim != 1 or not np.all(np.isfinite(heights))
            or np.any(heights <= 0) or np.any(np.diff(heights) <= 0)):
        raise ValueError("Zero heights must be increasing, positive and finite.")
    return x, heights


def reconstruct_direct(
    x: np.ndarray,
    heights: np.ndarray,
    counts: tuple[int, ...],
    batch_size: int = 512,
) -> dict[int, np.ndarray]:
    """Evaluate the finite formula directly with SciPy Ei.

    Batching limits memory. This is the independent numerical check for
    the accelerated evaluator; it uses no NUFFT or Chebyshev interpolation.
    """
    x, heights = _check_inputs(x, heights)
    if not counts or min(counts) < 0 or max(counts) > len(heights):
        raise ValueError("Requested zero counts exceed the supplied table.")
    if batch_size < 1:
        raise ValueError("batch_size must be positive.")
    rho = 0.5 + 1j * heights[:max(counts)]
    curves = {k: np.zeros_like(x) for k in counts}
    for start in range(0, len(x), batch_size):
        stop = min(start + batch_size, len(x))
        v = np.log(x[start:stop])
        for m, weight in MOBIUS_WEIGHTS:
            u = v / m
            baseline = expi(u) - np.log(2.0) + trivial_zero_correction(u)
            sums = np.cumsum(2 * expi(rho[:, None] * u[None, :]).real, axis=0)
            for k in counts:
                zero_sum = sums[k - 1] if k else 0.0
                curves[k][start:stop] += weight * (baseline - zero_sum)
    return curves


def reconstruct_fast(
    x: np.ndarray,
    heights: np.ndarray,
    threads: int = 2,
) -> tuple[np.ndarray, dict[str, float]]:
    """Accelerate the SAME finite explicit formula, without using primes.

    The smooth part and low-argument Ei terms are interpolated on a
    Chebyshev grid in log(x). For |rho log(x)/m| >= 64, use 14 terms of
    Ei's asymptotic expansion and evaluate the separated exponential sums
    with type-3 NUFFTs. The imaginary branch constant disappears when
    conjugate zeros are paired. This is a numerical approximation, not
    a rigorous interval evaluation; generate_figures.py checks it against
    the direct special-function calculation on specified sample points.

    FINUFFT is imported only here, leaving the direct method usable with
    NumPy and SciPy alone. The acceleration parameters are tuned for this
    fixed domain and the supplied table of 10,000 zero heights.
    """
    x, heights = _check_inputs(x, heights)
    if threads < 1:
        raise ValueError("threads must be positive.")
    if len(heights) == 0:
        return reconstruct_direct(x, heights, (0,))[0], {}
    import finufft

    v = np.log(x)
    a, b = np.log(DOMAIN)
    center, radius = (a + b) / 2, (b - a) / 2
    normalized = (v - center) / radius
    nodes = np.cos(np.pi * np.arange(CHEBYSHEV_DEGREE + 1) / CHEBYSHEV_DEGREE)
    vnodes = center + radius * nodes
    rho = 0.5 + 1j * heights
    out = np.zeros_like(v)
    tails: dict[str, float] = {}

    for m, weight in MOBIUS_WEIGHTS:
        u, unodes = v / m, vnodes / m
        split = np.searchsorted(np.abs(rho), ASYMPTOTIC_ARGUMENT_MIN / (a / m))
        low = rho[:split]
        smooth = expi(unodes) - np.log(2.0) + trivial_zero_correction(unodes)
        if len(low):
            smooth -= 2 * np.sum(expi(low[:, None] * unodes[None, :]).real, axis=0)
        coefficients = dct(smooth, type=1) / CHEBYSHEV_DEGREE
        coefficients[[0, -1]] *= 0.5
        tails[str(m)] = float(np.max(np.abs(coefficients[-128:])))
        j_values = chebval(normalized, coefficients)

        high = rho[split:]
        if len(high):
            rho_scale = abs(high[0])
            orders = np.arange(1, ASYMPTOTIC_TERMS + 1)
            # Normalize each coefficient row, retaining NUFFT precision
            # despite the wide range of powers of rho in the expansion.
            strengths = np.ascontiguousarray((rho_scale / high[None, :]) ** orders[:, None])
            source_scale = heights[-1] / 3.0
            sources = np.ascontiguousarray(heights[split:] / source_scale)
            targets = np.ascontiguousarray(u * source_scale)
            sums = finufft.nufft1d3(
                sources, strengths, targets, eps=1e-13, isign=1, nthreads=threads,
            )
            real_sum = np.zeros_like(u)
            for k in range(ASYMPTOTIC_TERMS):
                real_sum += factorial(k) * sums[k].real / (rho_scale * u) ** (k + 1)
            j_values -= 2 * np.exp(u / 2) * real_sum
        out += weight * j_values
    return out, tails
