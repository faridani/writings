import Mathlib.Algebra.Field.ZMod
import Mathlib.Tactic.NormNum.Prime

/-!
# Prime arithmetic in applications

These are exact arithmetic proofs for the essay's deliberately tiny RSA
example and its modulo-seven clock. They prove the displayed identities,
not cryptographic security or correctness of a production implementation.
-/

namespace RiemannEssay

theorem toy_rsa_primes : Nat.Prime 61 ∧ Nat.Prime 53 := by norm_num

theorem toy_rsa_modulus : (61 : ℕ) * 53 = 3233 := by norm_num

theorem toy_rsa_exponents : (17 : ℕ) * 2753 % 3120 = 1 := by norm_num

theorem toy_rsa_encrypt : (65 : ℕ) ^ 17 % 3233 = 2790 := by decide

set_option maxRecDepth 10000 in
set_option exponentiation.threshold 3000 in
theorem toy_rsa_decrypt : (2790 : ℕ) ^ 2753 % 3233 = 65 := by decide

theorem clock_addition : (5 : ZMod 7) + 4 = 2 := by decide

theorem clock_multiplication : (3 : ZMod 7) * 5 = 1 := by decide

/-- Modulo 256 has zero divisors, so it is not the 256-element field. -/
theorem two_nonzero_mod_256 : (2 : ZMod 256) ≠ 0 := by decide

theorem one_twenty_eight_nonzero_mod_256 : (128 : ZMod 256) ≠ 0 := by decide

theorem zero_divisors_mod_256 : (2 : ZMod 256) * 128 = 0 := by decide

/-- With a prime modulus, Mathlib constructs a field. -/
example (p : ℕ) [Fact p.Prime] : Field (ZMod p) := inferInstance

/-- Every nonzero residue has an inverse, for every prime modulus. -/
theorem inverse_at_prime_modulus (p : ℕ) [Fact p.Prime]
    (a : ZMod p) (ha : a ≠ 0) : a * a⁻¹ = 1 := by
  exact mul_inv_cancel₀ ha

end RiemannEssay
