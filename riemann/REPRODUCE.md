# Reproduce the Riemann figures

From the repository root, using Python 3.12 or newer:

```bash
python -m pip install -r riemann/requirements.txt
python riemann/generate_figures.py
```

The generator uses the bundled zero table, so rebuilding does not require
network access after installing the dependencies. It creates all four
PNGs in `riemann/assets/` and refreshes `riemann/validation.json`. There are
no precomputed curve caches in the repository. The supplied dependency
versions were used to generate the committed figures.

For a different output directory or thread count:

```bash
python riemann/generate_figures.py --output-dir output/riemann --threads 2
```

## What the figures show

- `prime_count_and_logarithmic_integral.png`: the exact prime-counting
  staircase and the smooth logarithmic integral, over $2\le x\le100$.
- `zero_pair_progression.png`: the exact count and reconstructions from
  0, 10, 50, 200, 1,000 and 10,000 zero pairs, using identical axes over
  $20\le x\le40$.
- `primes_exact_vs_10000_zero_pairs.png`: the 10,000-pair reconstruction,
  with an overview, a close-up, and a magnified jump at the prime 29.
- `zeta_zeros.png`: the first few trivial zeros and the first ten
  conjugate pairs of nontrivial zeros in the complex plane.

## Formula and conventions

The logarithmic integral is $\operatorname{li}(x)=\operatorname{Ei}(\log x)$
with the principal-value convention. It is **not** the shifted integral
$\int_2^xdt/\log t$.

For $y>1$, the truncated prime-power count is

$$
J_K(y)=\operatorname{Ei}(\log y)
-2\operatorname{Re}\sum_{n=1}^{K}\operatorname{Ei}\bigl((\tfrac12+i\gamma_n)\log y\bigr)
-\log2+\sum_{j=1}^{\infty}E_1(2j\log y).
$$

The final positive series equals
$\int_y^{\infty}dt/[t(t^2-1)\log t]$. Let
$J(y)=\sum_{p^k\le y}1/k$. With the full zero sum, the result is
$J_0(y)=[J(y^-)+J(y^+)]/2$: it agrees with $J$ away from prime powers and
takes half the jump at an exact prime power. Here the subscript zero on
$J_0$ denotes the midpoint convention; it should not be confused with the
finite calculation at $K=0$, which keeps only the smooth terms.

The reconstructed ordinary prime count is

$$
\widehat\pi_K(x)=J_K(x)-\frac12J_K(x^{1/2})
-\frac13J_K(x^{1/3})-\frac15J_K(x^{1/5})+\frac16J_K(x^{1/6}).
$$

This is Möbius inversion with a **fixed** cutoff $M=6$ throughout
$2\le x\le100$. Since $100<2^7$, all higher terms in the full exact formula
vanish. Applying an $x$-dependent cutoff to a finite smooth approximation
would introduce artificial jumps at powers of 2. For small $x$, some
included $J_K(x^{1/m})$ terms approximate an exact value of zero; they
still have finite-sum fluctuations.

The complex expression is evaluated as
$\operatorname{Ei}(\rho\log y)$ directly. Forming $y^\rho$ first and then
taking a principal logarithm would wrap the phase and use the wrong
branch. The zero pairs include both positive and negative imaginary
parts. At a prime, the infinite formula gives the midpoint of the jump.
Finite sums exhibit ringing, and adding zeros need not improve every
individual point monotonically.

The list of primes enters only the exact comparison staircase and its
error calculation. The reconstruction uses zero heights, the displayed
fixed Möbius coefficients and the analytic correction terms.

## Numerical implementation and checks

`explicit_formula.py` provides two evaluators. `reconstruct_direct`
evaluates complex exponential integrals with SciPy. `reconstruct_fast`
evaluates the same finite formula using a Chebyshev approximation for
low-argument terms and a 14-term asymptotic expansion plus FINUFFT for
high-argument terms. The split keeps the latter arguments at modulus at
least 64 on the entire domain. This acceleration is tuned for
$2\le x\le100$ and this zero table.

Every rebuild checks all six accelerated curves against direct
special-function evaluation at 160 points, including half-integers,
seeded irregular points, points immediately beside prime jumps, the
jumps themselves, and both endpoints. It fails if any discrepancy exceeds
$10^{-8}$. The resulting report also gives mean and maximum errors
against the actual prime count at $2.5,3.5,\ldots,99.5$.

These sampled errors are not global error bounds: the finite curves have
larger discrepancies very close to jumps. Agreement between two
evaluators also does not remove the source table's finite precision.
`validation.json` therefore records the source's per-height uncertainty
and a conservative bound for its propagation through the finite formula,
separately from the comparison between evaluators. That bound is
conditional on the table's stated accuracy. None of these numerical
checks is a proof of the Riemann hypothesis.

## Sources

- [Riemann's 1859 paper, English translation](https://www.maths.tcd.ie/pub/HistMath/People/Riemann/Zeta/EZeta.pdf).
- [John Baez, Riemann's explicit formulas](https://math.ucr.edu/home/baez/mathematical/riemann_explicit_formula/explicit_formulas.html).
- [Odlyzko's zero tables](https://www-users.cse.umn.edu/~odlyzko/zeta_tables/), with local provenance in [data/SOURCE.md](data/SOURCE.md).
- [SciPy `expi`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.expi.html) and [SciPy `exp1`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.exp1.html).
- [FINUFFT documentation](https://finufft.readthedocs.io/).
