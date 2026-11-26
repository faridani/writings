import Mathlib.NumberTheory.ArithmeticFunction
import Mathlib.Data.Complex.Basic
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.NormNum.Prime
import Mathlib.Data.Nat.Log
import Mathlib.Tactic.Ring

/-!
# Exact finite calculations and reconstruction bookkeeping

This file proves finite identities used to explain the article. It does
not implement complex Ei or prove the analytic explicit formula. In
particular, the function `term` in `zeroPairSum` is an explicit parameter;
there is no assumption that it is a certified numerical zeta-zero term.
-/

namespace RiemannEssay

open scoped BigOperators

/-! ## Section 9: weighted prime powers and Möbius inversion -/

/-- Count prime powers with weight `1 / k`, using exact rational arithmetic.
The exponent and base search bounds are both `n`. This is deliberately
a simple educational finite computation, not a fast prime-count algorithm. -/
def weightedPrimePowers (n : ℕ) : ℚ :=
  ∑ p ∈ Finset.range (n + 1), ∑ k ∈ Finset.range (n + 1),
    if p.Prime ∧ 0 < k ∧ p ^ k ≤ n then (1 : ℚ) / k else 0

/-- The finite search bounds do not omit any prime power below the cutoff. -/
theorem prime_power_indices_bounded {p k n : ℕ} (hp : p.Prime)
    (hk : 0 < k) (hpow : p ^ k ≤ n) : p ≤ n ∧ k ≤ n := by
  exact ⟨(Nat.le_pow hk).trans hpow,
    (Nat.le_of_lt (Nat.lt_pow_self hp.one_lt)).trans hpow⟩

theorem weightedPrimePowers_ten : weightedPrimePowers 10 = 16 / 3 := by
  norm_num [weightedPrimePowers, Finset.sum_range_succ]

/-- The same concrete prime-power correction shown in the essay at x = 10. -/
theorem remove_prime_powers_at_ten :
    weightedPrimePowers 10 - (1 / 2 : ℚ) * weightedPrimePowers 3
      - (1 / 3 : ℚ) * weightedPrimePowers 2 = 4 := by
  norm_num [weightedPrimePowers, Finset.sum_range_succ]

theorem moebius_two : ArithmeticFunction.moebius 2 = -1 := by
  exact ArithmeticFunction.moebius_apply_prime Nat.prime_two

theorem moebius_four : ArithmeticFunction.moebius 4 = 0 := by
  decide

theorem moebius_six : ArithmeticFunction.moebius 6 = 1 := by
  have h := ArithmeticFunction.isMultiplicative_moebius.map_mul_of_coprime
    (by decide : Nat.Coprime 2 3)
  simpa [ArithmeticFunction.moebius_apply_prime Nat.prime_two,
    ArithmeticFunction.moebius_apply_prime Nat.prime_three] using h

/-- Actual divisor-sum Möbius inversion from Mathlib. Relating this to the
analytic prime-count formula needs further arguments not supplied here. -/
theorem divisor_moebius_inversion (f g : ℕ → ℚ)
    (h : ∀ n > 0, ∑ d ∈ n.divisors, f d = g n) :
    ∀ n > 0, ∑ a ∈ n.divisorsAntidiagonal,
      (ArithmeticFunction.moebius a.1 : ℚ) * g a.2 = f n := by
  exact ArithmeticFunction.sum_eq_iff_sum_mul_moebius_eq.mp h

/-! ## Section 10: adding one more conjugate-pair contribution -/

/-- The real contribution of the first `K` pairs, indexed from zero.
The caller supplies the complex term, including whatever weights it needs. -/
noncomputable def zeroPairSum (term : ℕ → ℂ) (K : ℕ) : ℝ :=
  ∑ n ∈ Finset.range K, 2 * (term n).re

theorem zeroPairSum_zero (term : ℕ → ℂ) : zeroPairSum term 0 = 0 := by
  simp [zeroPairSum]

theorem zeroPairSum_succ (term : ℕ → ℂ) (K : ℕ) :
    zeroPairSum term (K + 1) = zeroPairSum term K + 2 * (term K).re := by
  exact Finset.sum_range_succ _ K

/-! ## Section 11: midpoint convention, alignment, and finite checks -/

def jumpMidpoint (left right : ℚ) : ℚ := (left + right) / 2

theorem midpoint_at_twenty_nine : jumpMidpoint 9 10 = 19 / 2 := by
  norm_num [jumpMidpoint]

theorem subtracting_same_reference_preserves_error (f exact reference : ℝ) :
    (f - reference) - (exact - reference) = f - exact := by ring

/-- This explains what the deliberately aligned lower panels remove. -/
theorem center_removes_offset (fx fp reference : ℝ) :
    (fx - reference) - (fp - reference) = fx - fp := by ring

theorem centered_value_is_zero (f : ℝ → ℝ) (p : ℝ) : f p - f p = 0 := by ring

/-- Exact integer checks of the four fixed Möbius cutoffs used by the GIFs.
These verify the cutoff arithmetic, not the floating-point curves. -/
theorem large_window_cutoffs :
    (Nat.log2 (1000003 + 200), Nat.log2 (1000000007 + 200),
      Nat.log2 (1000000000039 + 200), Nat.log2 (1000000000000037 + 200)) =
    (19, 29, 39, 49) := by
  simp only [Nat.log2_eq_log_two, Prod.mk.injEq]
  refine ⟨?_, ?_, ?_, ?_⟩ <;>
    apply Nat.log_eq_of_pow_le_of_lt_pow <;> norm_num

/-- A logical counterexample: checking through any finite cutoff does not
by itself establish a statement for every natural number. This example
does not assert anything about the uncomputed zeros of zeta. -/
theorem finite_checks_do_not_force_everywhere (B : ℕ) :
    (∀ n ≤ B, n ≠ B + 1) ∧ ¬ (∀ n : ℕ, n ≠ B + 1) := by
  constructor
  · intro n hn
    exact ne_of_lt (Nat.lt_succ_of_le hn)
  · intro h
    exact h (B + 1) rfl

end RiemannEssay
