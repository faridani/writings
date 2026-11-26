import Mathlib.NumberTheory.EulerProduct.DirichletLSeries
import Mathlib.Analysis.Asymptotics.Defs
import Mathlib.Analysis.SpecialFunctions.Sqrt
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

/-!
# Analytic ideas accompanying the Riemann essay

The Euler-product, analytic-continuation, and trivial-zero results below
reuse actual Mathlib theorems. `RHStatement` and `HasRHScaleError` are
definitions of propositions, not proofs that those propositions hold.
This small educational project does not import the separate RH proof,
prove the analytic explicit formula, or certify the numerical GIFs.

The file is checked against the project's pinned Lean/Mathlib release.
-/

namespace RiemannEssay

open scoped BigOperators ComplexConjugate

/-! ## Section 5: an infinite product really equals zeta -/

/-- An existing Mathlib theorem, with its convergence hypothesis visible. -/
theorem euler_product (s : ℂ) (hs : 1 < s.re) :
    (∏' p : Nat.Primes, (1 - (p : ℂ) ^ (-s))⁻¹) = riemannZeta s := by
  exact riemannZeta_eulerProduct_tprod hs

/-- The continued zeta agrees with its series in the convergence region. -/
theorem zeta_as_series (s : ℂ) (hs : 1 < s.re) :
    riemannZeta s = ∑' n : ℕ, 1 / (n + 1 : ℂ) ^ s := by
  exact zeta_eq_tsum_one_div_nat_add_one_cpow hs

/-! ## Section 6: complex coordinates and analytic continuation -/

/-- This is a complex number with real coordinate `σ` and imaginary coordinate `t`. -/
def complexPoint (σ t : ℝ) : ℂ := ⟨σ, t⟩

theorem complexPoint_re (σ t : ℝ) : (complexPoint σ t).re = σ := rfl

theorem complexPoint_im (σ t : ℝ) : (complexPoint σ t).im = t := rfl

theorem imaginary_unit_squared : Complex.I * Complex.I = -1 := by simp

/-- A genuine convergence theorem for the geometric-series illustration. -/
theorem geometric_half : HasSum (fun n : ℕ => (1 / 2 : ℝ) ^ n) 2 := by
  convert hasSum_geometric_of_norm_lt_one (by norm_num : ‖(1 / 2 : ℝ)‖ < 1) using 1
  norm_num

/-- The continued expression can be evaluated at 2; this is not a sum of the divergent series. -/
theorem geometric_expression_at_two : (1 - (2 : ℝ))⁻¹ = -1 := by norm_num

/-- Differentiability away from the pole uses the continued function. -/
theorem zeta_differentiable_away_from_one (s : ℂ) (hs : s ≠ 1) :
    DifferentiableAt ℂ riemannZeta s := by
  exact differentiableAt_riemannZeta hs

/-! ## Section 7: zeros, trivial zeros, and the precise RH statement -/

def IsZetaZero (s : ℂ) : Prop := riemannZeta s = 0

/-- This is a proof for every negative even integer, not a decimal zero test. -/
theorem trivial_zeta_zero (n : ℕ) : IsZetaZero (-2 * (n + 1)) := by
  exact riemannZeta_neg_two_mul_nat_add_one n

/-- A local spelling of Mathlib's RH proposition; it does not prove RH. -/
def RHStatement : Prop :=
  ∀ s : ℂ, riemannZeta s = 0 →
    (¬ ∃ n : ℕ, s = -2 * (n + 1)) → s ≠ 1 → s.re = 1 / 2

theorem rhStatement_iff_mathlib : RHStatement ↔ RiemannHypothesis := Iff.rfl

/-! ## Section 8: conjugate pairs and a logarithmic oscillation -/

/-- Pairing any complex value with its conjugate cancels its imaginary part. -/
theorem conjugate_pair_is_real (z : ℂ) : (z + conj z).im = 0 := by simp

theorem conjugate_pair_re (z : ℂ) : (z + conj z).re = 2 * z.re := by
  simp [two_mul]

/-- A unit-amplitude building block, not the complete explicit-formula term. -/
noncomputable def logWave (γ x : ℝ) : ℂ :=
  Complex.exp (((γ * Real.log x : ℝ) : ℂ) * Complex.I)

theorem logWave_pair_re (γ x : ℝ) :
    (logWave γ x + conj (logWave γ x)).re = 2 * Real.cos (γ * Real.log x) := by
  rw [conjugate_pair_re, logWave, Complex.exp_ofReal_mul_I_re]

theorem logWave_pair_im (γ x : ℝ) :
    (logWave γ x + conj (logWave γ x)).im = 0 := by simp

/-! ## Section 12: stating an error scale versus proving it -/

/-- The shape of the asymptotic bound for supplied count and estimate functions.
To state the article's claim, these must be instantiated with the actual
prime-count function and principal-value logarithmic integral. Neither that
identification nor its equivalence to RH is proved by this definition. -/
def HasRHScaleError (count estimate : ℝ → ℝ) : Prop :=
  Asymptotics.IsBigO Filter.atTop (fun x => count x - estimate x)
    (fun x => Real.sqrt x * Real.log x)

/-- A proved consequence of a supplied pointwise error bound. -/
theorem interval_from_error_bound (count estimate bound : ℝ)
    (h : |count - estimate| ≤ bound) :
    estimate - bound ≤ count ∧ count ≤ estimate + bound := by
  obtain ⟨hlo, hhi⟩ := abs_le.mp h
  constructor <;> linarith

/-! ## Section 13: what removing a theorem's assumption means -/

/-- This application requires an RH proof as an explicit input.
It illustrates discharging a dependency; it does not supply that proof. -/
theorem use_proved_RH (rh : RiemannHypothesis) (claim : Prop)
    (conditional : RiemannHypothesis → claim) : claim :=
  conditional rh

end RiemannEssay
