import Mathlib.NumberTheory.PrimeCounting

/-!
# The exact prime-counting staircase

The finite set definition below is a specification, not an implementation
of the sieve. Its membership test asks whether each candidate is prime.
`Sieve.lean` separately proves a genuine elimination algorithm correct.
-/

namespace RiemannEssay

/-- All primes at most `n`; `range (n+1)` includes `n`. -/
def primesThrough (n : ℕ) : Finset ℕ :=
  (Finset.range (n + 1)).filter Nat.Prime

/-- The number of primes less than or equal to a natural cutoff. -/
def primeCount (n : ℕ) : ℕ := (primesThrough n).card

theorem mem_primesThrough (n p : ℕ) :
    p ∈ primesThrough n ↔ p ≤ n ∧ Nat.Prime p := by
  simp [primesThrough, Nat.lt_succ_iff]

/-- This finite set count agrees with Mathlib's standard prime counter. -/
theorem primeCount_eq_mathlib (n : ℕ) : primeCount n = Nat.primeCounting n := by
  exact (Nat.count_eq_card_filter_range Nat.Prime (n + 1)).symm

/-- The count increases by one exactly when the next integer is prime. -/
theorem primeCount_step (n : ℕ) :
    primeCount (n + 1) = primeCount n + if Nat.Prime (n + 1) then 1 else 0 := by
  unfold primeCount primesThrough
  rw [Finset.range_succ, Finset.filter_insert]
  split_ifs with hp
  · rw [Finset.card_insert_of_not_mem (by simp)]
  · simp

theorem primeCount_zero : primeCount 0 = 0 := by decide

theorem primeCount_ten : primeCount 10 = 4 := by decide

set_option maxRecDepth 10000 in
set_option maxHeartbeats 2000000 in
theorem primeCount_hundred : primeCount 100 = 25 := by decide

-- This is an executable display, not an additional theorem.
#eval primeCount 100

end RiemannEssay
