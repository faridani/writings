# Lean companion to “Riemann, from scratch”

This project supplies definitions, computations, and proofs alongside the
[article](../../Riemann.md). Short examples stay in the article; the complete
proofs are here. Every article Lean block is limited to **ten lines**, and
the verification script compiles those blocks as well as the source files.

The project uses **Lean 4.19.0** and **Mathlib v4.19.0**, pinned to commit
`c44e0c8ee63ca166450922a373c7409c5d26b00b`. The exact dependency revisions
are recorded in [lake-manifest.json](lake-manifest.json).

## Build and check

Install Lean's toolchain manager following the [official Lean community
instructions](https://leanprover-community.github.io/get_started.html).
From the repository root:

```bash
cd riemann/lean
lake exe cache get
lake build
python verify.py
```

The first command inside the project downloads precompiled Mathlib
dependencies, avoiding a full source rebuild. Lake reads `lean-toolchain`
to select the compiler and the manifest to select dependencies. Subsequent
builds can run offline once those dependencies are present.

`python verify.py` checks three separate things:

1. All companion modules build with the pinned compiler and libraries.
2. [Audit.lean](Audit.lean) follows the dependencies of every theorem
   exported in our `RiemannEssay` namespace and accepts only the standard
   foundational axioms `propext`, `Quot.sound`, and `Classical.choice`.
   It rejects unfinished proofs and additional computation axioms.
3. Every Lean block extracted from the article compiles, every numbered
   section has an example, and no block exceeds ten lines.

The generated [validation report](validation.json) records the compiler
version, Mathlib revision, source hashes, block lengths, and axiom audit.
It checks this project; it does not certify the Python plots or the
separate formal proof of RH referenced in the article.

To inspect a single file in the Lean editor, open this directory as a
project. To check it from a terminal, for example:

```bash
lake env lean Riemann/Sieve.lean
```

The first article box loads `Riemann` and opens the companion namespace
and notation. Later article boxes assume that opening setup. Each complete
source file contains its own required imports.

## Guide by article section

| Article section | Complete Lean file | What is established |
|---|---|---|
| Introduction: what a prime is | [Primes.lean](Riemann/Primes.lean) | The readable divisor definition is equivalent to `Nat.Prime`. |
| 1. Building blocks; first prime test | [Primes.lean](Riemann/Primes.lean) | Small prime/composite facts; factorization existence and uniqueness; unbounded primes; the square-root criterion. |
| 2. Finding primes; the sieve | [Sieve.lean](Riemann/Sieve.lean) | A genuine elimination algorithm returns exactly all primes within every natural bound. |
| 3. Applications | [Applications.lean](Riemann/Applications.lean) | Toy RSA arithmetic, modular examples, fields and inverses at prime moduli, and zero divisors modulo 256. |
| 4. The prime staircase | [Counting.lean](Riemann/Counting.lean) | A finite-set count agrees with Mathlib's prime counter; the general successor-step law and small exact counts. |
| 5. Euler product | [Analysis.lean](Riemann/Analysis.lean) | Mathlib's actual infinite Euler product and Dirichlet series identities, with convergence hypotheses. |
| 6. Complex numbers and continuation | [Analysis.lean](Riemann/Analysis.lean) | Complex-coordinate facts, the geometric example, and differentiability of continued zeta away from 1. |
| 7. Zeta zeros and RH | [Analysis.lean](Riemann/Analysis.lean) | All negative-even trivial zeros; an RH proposition definitionally equivalent to Mathlib's statement. |
| 8. Zeros as waves | [Analysis.lean](Riemann/Analysis.lean) | Conjugate pairs have zero imaginary part; a logarithmic complex wave gives a real cosine pair. |
| 9. Prime powers and Möbius inversion | [Reconstruction.lean](Riemann/Reconstruction.lean) | Exact rational prime-power counts, completeness of finite enumeration, the example at 10, and divisor-sum Möbius inversion. |
| 10. Increasing zero pairs | [Reconstruction.lean](Riemann/Reconstruction.lean) | The finite paired-sum recurrence for a supplied term function. |
| 11. Midpoints and finite checks | [Reconstruction.lean](Riemann/Reconstruction.lean) | Exact midpoint arithmetic and a logical example showing that a finite check alone does not imply an unrestricted statement. |
| 11. Large-prime experiments | [LargePrimes.lean](Riemann/LargePrimes.lean), [Reconstruction.lean](Riemann/Reconstruction.lean) | Primality of the four focal integers; the fixed cutoff arithmetic; algebra explaining the two panel alignments. |
| 12. Error bounds | [Analysis.lean](Riemann/Analysis.lean) | Definition of an asymptotic error scale and the interval consequence of an assumed pointwise bound. |
| 13. Human uses of a proof | [Analysis.lean](Riemann/Analysis.lean) | How a supplied RH proof discharges an explicitly conditional theorem. |
| 14. Reproduction | [Audit.lean](Audit.lean), [verify.py](verify.py) | Build, proof-dependency audit, and compilation of the exact article snippets. |

## What the sieve proof says

The executable definitions are `sieveState` and `sieve`. The initial set is
the interval from 2 through the chosen limit. Each stage examines the next
candidate. If that candidate remains in the set, the stage retains it and
removes its proper multiples; otherwise the stage leaves the set alone.
Neither definition calls a primality predicate.

The proof establishes the following invariants:

- A later state is a subset of every earlier state.
- Every prime within the original bound survives every stage.
- After a prime's stage, its proper multiples are absent.
- After `k` passes, every remaining number at most `k + 2` is prime.

The last statement follows because a composite survivor would have a
smaller prime divisor. That divisor survives to its own earlier stage,
which would remove the composite. The same invariant proves that each
candidate selected for a pass is prime.

The exported conclusion is:

```lean
example {N n : ℕ} :
    n ∈ RiemannEssay.sieve N ↔ Nat.Prime n ∧ n ≤ N :=
  RiemannEssay.mem_sieve
```

Both directions are proved for arbitrary bounds, including 0 and 1.
Evaluation at 100 displays the 25 primes from 2 through 97.

This finite-set algorithm processes all candidates through the limit. It
is a deliberately direct explanation of Eratosthenes' elimination idea.
The Python program's array representation, square-root stopping point,
and exact correspondence to Python execution are not formalized here.
The separate trial-division theorem proves the mathematical square-root
criterion.

## The four large-prime certificates

[LargePrimes.lean](Riemann/LargePrimes.lean) proves:

| Theorem | Proved prime |
|---|---:|
| `prime_near_million` | 1,000,003 |
| `prime_near_billion` | 1,000,000,007 |
| `prime_near_trillion` | 1,000,000,000,039 |
| `prime_near_quadrillion` | 1,000,000,000,000,037 |

It uses the 27 recursive Lucas certificate nodes underlying the existing
[reference data](../data/large_prime_windows.json). Each certificate supplies
a complete prime factorization of `n - 1` and a witness whose modular
powers satisfy Mathlib's Lucas primality criterion. The source embeds
the needed constants; no external certificate file is trusted at compile
time.

For efficient checking, the code computes powers from explicit binary
digit lists. An induction proves this computation equals ordinary
exponentiation. Lean then checks the integer factorizations, encoded
exponents, and modular identities. These proofs use ordinary `decide`
and proof-producing arithmetic, without `native_decide` or an added axiom
asserting the result of external computation.

These statements prove primality of the four integers. They do not prove
that they are the first primes after the power-of-ten anchors, recompute
the global prime counts, or certify the zeta-zero input data. The article's
separate Python reference verifier checks the local intervals and records
the provenance of the global counts.

## Definitions, computations, and proofs

These distinctions matter when reading short Lean examples:

| Lean construct | Meaning here |
|---|---|
| `def ... : Prop := ...` | Defines a proposition; does not prove that proposition. |
| `theorem` or `example` with a proof | Supplies a term whose type is the claimed proposition, checked by Lean. |
| `#check name` | Displays a declaration's type; does not prove a new theorem. |
| `#eval expression` | Executes a computation; does not by itself create a theorem. |
| `#print axioms theoremName` | Reports the axioms used by the theorem and its dependencies. |
| A parameter such as `rh : RiemannHypothesis` | Assumes a proof is supplied by the caller; does not construct it. |

For example, the definition `RHStatement` and its equivalence to
`RiemannHypothesis` check that two statements express the same proposition.
They do not prove RH. The trivial-zero theorem, by contrast, proves an
actual fact about every negative even integer. The Euler-product and
continuation examples reuse actual proved Mathlib results with their
hypotheses visible.

The finite sum `zeroPairSum term K` accepts its term function as an explicit
input. Its recurrence is proved for every such function. Certifying the
specific complex Ei terms and rounded zero heights used in the Python
animations would require further formalization. Similarly, the exact
weighted prime-power example and arithmetic Möbius inversion do not alone
prove the analytic explicit formula.

`HasRHScaleError` describes an asymptotic bound for supplied count and
estimate functions. The file does not prove its equivalence to RH. The
interval theorem proves what follows once an absolute error bound is
available. These limits are stated beside the article snippets so that
their shortness does not conceal missing mathematical work.

## Primary references

- [Lean project setup](https://leanprover-community.github.io/install/project.html).
- [Lean reference: axioms](https://lean-lang.org/doc/reference/latest/Axioms/).
- [Pinned natural prime definitions](https://github.com/leanprover-community/mathlib4/blob/v4.19.0/Mathlib/Data/Nat/Prime/Defs.lean).
- [Pinned Lucas primality theorem](https://github.com/leanprover-community/mathlib4/blob/v4.19.0/Mathlib/NumberTheory/LucasPrimality.lean).
- [Pinned Euler product](https://github.com/leanprover-community/mathlib4/blob/v4.19.0/Mathlib/NumberTheory/EulerProduct/DirichletLSeries.lean).
- [Pinned zeta definitions and results](https://github.com/leanprover-community/mathlib4/blob/v4.19.0/Mathlib/NumberTheory/LSeries/RiemannZeta.lean).
- [Pinned arithmetic Möbius inversion](https://github.com/leanprover-community/mathlib4/blob/v4.19.0/Mathlib/NumberTheory/ArithmeticFunction.lean).
