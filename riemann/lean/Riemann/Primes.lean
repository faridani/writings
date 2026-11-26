import Mathlib.Data.Nat.Factors
import Mathlib.Data.Nat.Prime.Infinite
import Mathlib.Tactic.NormNum.Prime

/-!
# Prime numbers, factorization, and trial division

This file uses the pinned Mathlib definitions. The readable divisor
definition is proved equivalent to `Nat.Prime`; it is not a competing
unconnected definition. The general factorization, infinitude, and
square-root results below reuse already-proved Mathlib theorems.
-/

namespace RiemannEssay

/-- A whole number at least two with no divisors except one and itself. -/
def PrimeByDivisors (p : ℕ) : Prop :=
  2 ≤ p ∧ ∀ d : ℕ, d ∣ p → d = 1 ∨ d = p

theorem primeByDivisors_iff (p : ℕ) : PrimeByDivisors p ↔ Nat.Prime p :=
  Nat.prime_def.symm

theorem seven_is_prime : Nat.Prime 7 := by norm_num

theorem twelve_is_not_prime : ¬ Nat.Prime 12 := by norm_num

theorem one_is_not_prime : ¬ Nat.Prime 1 := Nat.not_prime_one

/-- Existence: the list of prime factors multiplies back to a nonzero number. -/
theorem factors_multiply_back (n : ℕ) (hn : n ≠ 0) :
    n.primeFactorsList.prod = n :=
  Nat.prod_primeFactorsList hn

/-- Uniqueness is up to permutation, so the order of the factors is irrelevant. -/
theorem factorization_unique {n : ℕ} {factors : List ℕ}
    (hproduct : factors.prod = n)
    (hprimes : ∀ p ∈ factors, Nat.Prime p) :
    factors.Perm n.primeFactorsList :=
  Nat.primeFactorsList_unique hproduct hprimes

theorem factors_of_sixty :
    ([2, 2, 3, 5] : List ℕ).Perm (60 : ℕ).primeFactorsList := by
  apply factorization_unique
  · norm_num
  · intro p hp
    simp only [List.mem_cons, List.not_mem_nil, or_false] at hp
    rcases hp with rfl | rfl | rfl | rfl <;> norm_num

/-- For every bound there is a prime at least that large. -/
theorem primes_are_unbounded (bound : ℕ) :
    ∃ p : ℕ, bound ≤ p ∧ Nat.Prime p :=
  Nat.exists_infinite_primes bound

/-- `Nat.sqrt` is the integer square root, matching Python's `isqrt`. -/
theorem trial_division_criterion (n : ℕ) :
    Nat.Prime n ↔
      2 ≤ n ∧ ∀ d : ℕ, 2 ≤ d → d ≤ Nat.sqrt n → ¬ d ∣ n :=
  Nat.prime_def_le_sqrt

theorem ninety_seven_is_prime : Nat.Prime 97 := by norm_num

theorem ninety_one_is_composite : ¬ Nat.Prime 91 := by norm_num

end RiemannEssay
