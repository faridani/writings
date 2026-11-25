# Reproduce the Riemann figures and animations

From the repository root, using Python 3.12 or newer:

```bash
python -m pip install -r riemann/requirements.txt
python riemann/generate_figures.py
python riemann/generate_animations.py
```

The generator uses the bundled zero table, so rebuilding does not require
network access after installing the dependencies. It creates all five
PNGs in `riemann/assets/` and refreshes `riemann/validation.json`. There are
no precomputed curve caches in the repository. The supplied dependency
versions were used to generate the committed figures.

The animation command rebuilds all 16 GIFs, including the original sieve,
and writes `riemann/animation_manifest.json`. That manifest records the
actual dimensions, frame counts, loop durations, file sizes, and SHA-256
hashes after decoding the saved files.

For a different output directory or thread count:

```bash
python riemann/generate_figures.py --output-dir output/riemann --threads 2
```

## What the figures show

- `prime_count_0_to_100.png`: the introductory exact prime-counting
  staircase, with $x$ from 0 to 100 and $y=\pi(x)$.
- `prime_count_and_logarithmic_integral.png`: the exact prime-counting
  staircase and the smooth logarithmic integral, over $2\le x\le100$.
- `zero_pair_progression.png`: the exact count and reconstructions from
  0, 10, 50, 200, 1,000 and 10,000 zero pairs, using identical axes over
  $20\le x\le40$.
- `primes_exact_vs_10000_zero_pairs.png`: the 10,000-pair reconstruction,
  with an overview, a close-up, and a magnified jump at the prime 29.
- `zeta_zeros.png`: the first few trivial zeros and the first ten
  conjugate pairs of nontrivial zeros in the complex plane.

## What the animations explain

Every animation loops and uses holds so its important stages can be read.
The source calculations determine the diagrams and curves; these are not
generated illustrations or interpolations invented to resemble a result.

| Animation | Concept | Generator group |
|---|---|---|
| [Factorization routes](assets/factorization_routes.gif) | Different decompositions of 60 give the same prime factors. | `primes` |
| [Trial division](assets/trial_division.gif) | Exact quotient/remainder tests distinguish 97 from 91. | `primes` |
| [Prime-count staircase](assets/prime_count_staircase.gif) | A moving cutoff adds one step at each prime through 100. | `primes` |
| [Sieve of Eratosthenes](assets/sieve_of_eratosthenes_1_to_100.gif) | Circle primes and cross their multiples, including repeated visits. | `sieve` |
| [Toy RSA](assets/rsa_toy_example.gif) | Tiny example keys encrypt 65 to 2790 and recover 65. | `primes` |
| [Modular arithmetic](assets/modular_arithmetic.gif) | Addition, multiplication, and an inverse on a modulo-7 clock. | `primes` |
| [Euler product](assets/euler_product.gif) | Adding prime factors reveals their products and approaches zeta at 2. | `zeta` |
| [Complex rotation](assets/complex_rotation.gif) | Rotating terms demonstrate cancellation in an eight-term partial sum. | `zeta` |
| [Analytic continuation](assets/analytic_continuation.gif) | A continued function can exist where its original series diverges. | `zeta` |
| [Zeta-zero pairs](assets/zeta_zero_pairs.gif) | Ten known conjugate pairs appear on the critical line. | `zeta` |
| [Conjugate waves](assets/conjugate_waves.gif) | Opposite imaginary parts cancel, leaving real oscillations. | `zeta` |
| [Prime-power counts](assets/prime_powers.gif) | Prime squares, cubes, and higher powers contribute weighted steps. | `reconstruction` |
| [Mobius correction](assets/mobius_correction.gif) | Successive corrections recover ordinary prime counts from weighted counts. | `reconstruction` |
| [Zero reconstruction](assets/zero_reconstruction.gif) | Actual finite formulas sharpen the staircase as the zero count grows. | `reconstruction` |
| [Zoom at prime 29](assets/gibbs_zoom.gif) | A fixed 10,000-pair curve reveals ringing under magnification. | `reconstruction` |
| [Prime-count error bound](assets/prime_count_error_bound.gif) | Sieve discrepancies are compared with the classical RH envelope. | `error` |

Rebuild just one group, or check the committed GIF files without rebuilding:

```bash
python riemann/generate_animations.py --group reconstruction
python riemann/generate_animations.py --verify-existing
```

The other groups are `primes`, `zeta`, `error`, and `sieve`. The individual
`animate_*.py` scripts can also be run directly. The default output directory
is `riemann/assets`; use `--output-dir` for a separate destination.
`animation_utils.py` supplies the common layout and a shared color palette
within each GIF. Optimized frame rectangles keep downloads small without
changing the mathematical positions or the animation's timing.

### Numerical conventions in the animations

- The prime-power and Mobius demonstrations use exact right-continuous
  weighted counts and prime counts. The zero-based reconstruction uses
  the midpoint convention described below. These conventions are named
  in the article captions so values at jumps are not confused.
- The zero-count animation evaluates each displayed count separately.
  It does not morph between different finite sums and label the morph as
  an evaluated formula. Its black reference staircase is independent.
- The zoom holds all 10,000 zero pairs fixed. Its dense nonuniform samples
  resolve the small oscillations around 29 as the axes change scale.
- The rotating vectors are finite illustrations at real part 1.5, where
  the defining series converges. They are not used to evaluate zeta in
  the critical strip. The conjugate-wave animation isolates a building
  block; it is not presented as the complete prime-counting formula.
- The error-bound animation computes sieve counts through one million
  and compares 6,000 integer cutoffs with the classical envelope for
  x at least 2657. That finite numerical check is not a proof of RH.
- The RSA example uses deliberately tiny, insecure numbers to show the
  arithmetic. It is not an implementation of a production encryption
  scheme.

## Animated sieve

Rebuild the 10 by 10 sieve animation separately:

```bash
python riemann/generate_sieve_animation.py
```

The script writes `assets/sieve_of_eratosthenes_1_to_100.gif`. It first
circles 1 in gray and labels it as not prime, then circles each prime in
green and visits its multiples one at a time, starting at twice the prime.
An amber highlight and a status message distinguish a new cross from a
number that was already crossed out. Repeated visits are intentional: the
animation shows every multiple, while the article's optimized sieve starts
at the square of each prime to avoid redundant work.

The final grid contains 25 circled primes, 74 crossed composite numbers,
and 1 marked separately. The GIF pauses at the finished grid and loops.
The generator needs Pillow and uses Matplotlib's bundled DejaVu fonts.

## Formula and conventions

The logarithmic integral is $\mathrm{li}(x)=\mathrm{Ei}(\log x)$
with the principal-value convention. It is **not** the shifted integral
$\int_2^xdt/\log t$.

For $y>1$, the truncated prime-power count is

$$
J_K(y)=\mathrm{Ei}(\log y)
-2\mathrm{Re}\sum_{n=1}^{K}\mathrm{Ei}\bigl((\tfrac12+i\gamma_n)\log y\bigr)
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
$\mathrm{Ei}(\rho\log y)$ directly. Forming $y^\rho$ first and then
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
