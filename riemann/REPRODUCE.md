# Reproduce the Riemann figures and animations

From the repository root, using Python 3.12 or newer:

```bash
python -m pip install -r riemann/requirements.txt
python riemann/generate_figures.py
python riemann/generate_animations.py
```

The generators use bundled data, so rebuilding does not require network
access after installing the dependencies. The figure command creates the
five original PNGs in `riemann/assets/` and refreshes
`riemann/validation.json`. There are no precomputed curve caches in the
repository. The supplied dependency versions were used to generate the
committed figures.

The animation command rebuilds all 20 GIFs, including the original sieve
and the four large-prime experiments. It also saves four PNG snapshots
of the final 10,000-pair stages, making **20 GIFs and nine PNGs** in total
across the two commands. It writes `riemann/animation_manifest.json`,
which records actual dimensions, frame counts, loop durations, file
sizes, and SHA-256 hashes after decoding the saved GIFs. The large-prime
group also writes `riemann/large_prime_validation.json`.

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
- `large_prime_1m.png`, `large_prime_1b.png`, `large_prime_1t.png`, and
  `large_prime_1000t.png`: final 10,000-pair snapshots near the four large
  primes. Each preserves the actual counting error above an explicitly
  aligned local-shape comparison. These PNGs are produced by the
  `large-primes` animation group.

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
| [Near one million](assets/large_prime_1m.gif) | Fourteen zero-pair counts near 1,000,003 reveal broad curvature and unresolved prime steps. | `large-primes` |
| [Near one billion](assets/large_prime_1b.gif) | The absolute estimate changes while the local shape is almost straight. | `large-primes` |
| [Near one trillion](assets/large_prime_1t.gif) | A local shape comparison is separated from the error in the accumulated count. | `large-primes` |
| [Near 1,000 trillion](assets/large_prime_1000t.gif) | Fixed zero heights give an extremely broad oscillation scale near one quadrillion. | `large-primes` |

Rebuild just one group, or check the committed GIF files without rebuilding:

```bash
python riemann/generate_animations.py --group reconstruction
python riemann/generate_animations.py --group large-primes
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
- The large-prime animations likewise evaluate 14 actual finite sums,
  using offsets from −200 to +200. Their upper panels retain the absolute
  count error; their lower panels explicitly remove the center error to
  expose local shape. Every upper panel keeps its symmetric-log scale
  fixed through the animation. The lower panels use a common linear
  scale. An exact midpoint marker appears at the focal prime.
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

For the original plots on $2\le x\le100$, the reconstructed ordinary
prime count is

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

### Small-number windows

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

### Large-prime windows

Rebuild only the four new GIFs and their four final PNGs, or check the
exact reference data independently:

```bash
python riemann/generate_animations.py --group large-primes
python riemann/verify_large_prime_windows.py
```

`animate_large_primes.py` also runs directly with the usual `--output-dir`
option. The plotted offsets are $-200\le h\le200$, where $x=p+h$. The
reconstruction is sampled every 0.25 in the offset coordinate; the exact
staircase uses the integer locations of the primes. The 14 evaluated
zero-pair counts are `0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000,
5000, 10000`. Every stage is a separately evaluated finite formula, and
the final stage receives a longer hold before the animation loops.

#### Exact references

The four focal primes are the first primes strictly above their
power-of-ten anchors. The source counts at those anchors are:

| Anchor | Source value of the exact prime count | Focal prime | Fixed Möbius cutoff |
|---:|---:|---:|---:|
| 1,000,000 | 78,498 | 1,000,003 | 19 |
| 1,000,000,000 | 50,847,534 | 1,000,000,007 | 29 |
| 1,000,000,000,000 | 37,607,912,018 | 1,000,000,000,039 | 39 |
| 1,000,000,000,000,000 | 29,844,570,422,669 | 1,000,000,000,000,037 | 49 |

These counts come from [Tomás Oliveira e Silva's computational
table](https://sweet.ua.pt/tos/primes.html), specifically its
[`pi(10^k)` data](https://sweet.ua.pt/tos/primes/1d00.txt.gz). The repository
uses the published counts; it does not recompute the four global totals.

`data/large_prime_windows.json` records the source URLs and hashes, exact
local prime lists, and recursive Lucas primality certificates. Its
reference windows extend 500 integers in each direction, providing a
margin beyond the plotted ±200. All 4,004 integers were checked against
both SymPy's primality test and a separate deterministic Miller–Rabin
implementation for this integer range. The standalone verifier uses
Python integer arithmetic to recheck the window lists, 27 recursive
Lucas certificates, and proper factors proving that each focal prime
is the first prime after its anchor. It also checks the consistency of
the reference counts, offsets, and half-integer midpoints.

#### Formula and panel conventions

`large_scale_formula.py` computes the same paired formula as the original
evaluator, with the larger prime-power corrections included:

$$
F_K(x)=\sum_{m=1}^{M}\frac{\mu(m)}{m}J_K(x^{1/m}).
$$

For each window, $M=\lfloor\log_2(p+200)\rfloor$ is fixed while both $x$
and $K$ vary. The table above gives the four cutoffs. The reconstruction
receives the chosen center, offsets, zero heights, and zero-pair counts;
it does not receive the prime list or the exact prime-count baseline.

Let $A=\pi(p^-)+1/2$. The upper panel plots $F_K(p+h)-A$ and
$\pi(p+h)-A$. Both subtract exactly the same baseline, so the
reconstruction's actual vertical error remains visible. Its symmetric-log
axis is linear within 20 counts of zero and logarithmic beyond that
range; the axis limits stay fixed over all stages of each GIF.

The lower panel plots $F_K(p+h)-F_K(p)$ against $\pi(p+h)-A$. It is
explicitly labeled as a shape comparison with vertical error removed.
Its reconstruction passes through zero by construction. The exact
midpoint marker at $(0,0)$ represents the infinite formula's value at
the focal prime; the right-continuous staircase jumps from $-1/2$ to
$+1/2$ there. The actual midpoint error $F_K(p)-A$ is displayed throughout.

The local cycle scale of the fastest retained zero is approximately
$2\pi p/\gamma_K$. At $K=10000$, the four scales are about 636,
636,093, 636,092,687, and 636,092,686,716 numbers. This is a local
oscillation calculation, not a rigorous information limit. The last
three are much wider than the entire plotted window, explaining why
their local curves are almost straight. At $K=0$, there is no retained
zero frequency; only the smooth and analytic correction terms remain.
The error at a chosen prime can improve or worsen as $K$ increases.

#### Numerical evaluation, input precision, and truncation

The evaluator separates an absolute center value from the small local
change. It forms the center using high-precision smooth exponential
integrals, direct mpmath evaluation of low-argument complex terms, and
a 20-term asymptotic expansion in extended precision above modulus 128.
Only the real part of each paired exponential integral is needed.
Centers are returned as decimal strings, and the exact midpoint is
subtracted with decimal arithmetic before conversion to plotting floats.

Local increments use `log1p(h/p)` and an integrated degree-64 Taylor
series for the analytic derivative of the finite formula. They are
computed directly, avoiding subtraction of two large totals. This matters
near $10^{15}$, where ordinary floating-point spacing in the horizontal
coordinate is already 0.125. Plotting integer-relative offsets also
keeps the locations of individual prime steps unambiguous.

Each rebuild checks representative complex Ei values against mpmath,
compares the first ten pairs against a direct high-precision sum,
compares centers against SciPy evaluation, compares Taylor degrees 48
and 64, and independently integrates the full retained derivative with
Gauss–Legendre quadrature at the window endpoints. These are numerical
cross-checks on the finite calculation, not certified global bounds.
The report records the discrepancies and numerical precision in use.

For the supplied rounded zero table, the final midpoint errors are
approximately −0.702893, −14.837824, −1,001.157591, and +1,872.175060
primes. Those digits describe the implemented finite sum. They do not
remove the source table's stated uncertainty of $3\times10^{-9}$ in
each zero height. Its conservative propagated bounds on the absolute
center values at 10,000 pairs are, rounded upward:

| Scale | Bound from zero-height uncertainty alone |
|---|---:|
| 1 million | 0.0000264 primes |
| 1 billion | 0.000818 primes |
| 1 trillion | 0.0258 primes |
| 1,000 trillion | 0.815 primes |

The local increments have much smaller propagated uncertainty because
the two nearby values share the same zero heights. Both bounds are
recorded per zero-pair count in `large_prime_validation.json`, together
with the fixed cutoffs, midpoint errors, cycle scales, and numerical
checks. They assume the source's stated height accuracy. Keep three
effects separate: **numerical evaluation error**, **uncertainty in the
input zero heights**, and **truncation error from omitting later zeros**.
An aligned lower panel removes a center offset for display; it does not
reduce any of those errors in the absolute reconstruction.

## Lean companion

The article also includes short Lean examples and links to a separate
[Lean project](lean/README.md). Its files prove the prime-definition
equivalence, a genuine sieve's soundness and completeness, exact counting
and modular-arithmetic facts, and primality of all four large focal
integers. Further examples use Mathlib's proved analytic results and
state precisely which explicit-formula and error-bound claims have not
been formalized by this companion.

The Lean project is independent of the Python runtime. With Lean's
toolchain manager installed, run from the repository root:

```bash
cd riemann/lean
lake exe cache get
lake build
python verify.py
```

The project pins Lean 4.19.0 and an exact Mathlib revision. Its verifier
builds every module, audits theorem dependencies for unfinished proofs or
extra axioms, and compiles every Lean box extracted from `Riemann.md`.
It also enforces the article's ten-line limit for each Lean block.
Results and source hashes appear in [lean/validation.json](lean/validation.json).
This formal companion does not certify the floating-point animations or
import the separate formal proof of RH.

## Sources

- [Riemann's 1859 paper, English translation](https://www.maths.tcd.ie/pub/HistMath/People/Riemann/Zeta/EZeta.pdf).
- [John Baez, Riemann's explicit formulas](https://math.ucr.edu/home/baez/mathematical/riemann_explicit_formula/explicit_formulas.html).
- [Odlyzko's zero tables](https://www-users.cse.umn.edu/~odlyzko/zeta_tables/), with local provenance in [data/SOURCE.md](data/SOURCE.md).
- [Tomás Oliveira e Silva's tables of prime counts](https://sweet.ua.pt/tos/primes.html), with the four anchor counts and local primality certificates in [data/large_prime_windows.json](data/large_prime_windows.json).
- [SciPy `expi`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.expi.html) and [SciPy `exp1`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.exp1.html).
- [FINUFFT documentation](https://finufft.readthedocs.io/).
