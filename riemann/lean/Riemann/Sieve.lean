import Lean.Elab.Tactic.Omega
import Mathlib.Data.Finset.Sort
import Mathlib.Data.Nat.Prime.Defs
import Mathlib.Order.Interval.Finset.Nat
import Mathlib.Tactic.SplitIfs

/-!
# An Eratosthenes sieve, with soundness and completeness

Begin with the integers from 2 through `limit`. At stage `k`, inspect
`p = k + 2`. If `p` is still present, retain `p` itself and cross out its
proper multiples. If it has already been crossed out, skip that stage.

The algorithm never calls a primality test. The proofs below establish
that a surviving candidate is prime when its turn arrives, that every
prime survives, and that the final result contains precisely the primes
at most `limit`.

This deliberately simple finite-set implementation processes candidates
through `limit`. The square-root stopping rule and the array-based Python
implementation in the article are separate optimizations; no equivalence
to that particular Python program is claimed here.
-/

namespace RiemannEssay

/-- State after `k` candidates (2 through `k + 1`) have been considered. -/
def sieveState (limit : ℕ) : ℕ → Finset ℕ
  | 0 => Finset.Icc 2 limit
  | k + 1 =>
      let candidates := sieveState limit k
      let p := k + 2
      if p ∈ candidates then
        candidates.filter (fun n => n = p ∨ ¬p ∣ n)
      else candidates

/-- The sieve is defined by removing multiples, not by filtering `Nat.Prime`. -/
def sieve (limit : ℕ) : Finset ℕ :=
  sieveState limit (limit - 1)

/-- A sieve stage can remove candidates but cannot introduce new ones. -/
theorem sieveState_succ_subset (limit k : ℕ) :
    sieveState limit (k + 1) ⊆ sieveState limit k := by
  simp only [sieveState]
  split_ifs
  · exact Finset.filter_subset _ _
  · intro n hn
    exact hn

/-- Anything surviving a later stage also survived every earlier stage. -/
theorem sieveState_subset_of_le (limit : ℕ) {i j : ℕ} (hij : i ≤ j) :
    sieveState limit j ⊆ sieveState limit i := by
  induction hij with
  | refl =>
      intro n hn
      exact hn
  | @step j _ ih =>
      intro n hn
      exact ih (sieveState_succ_subset limit j hn)

/-- All candidates stay inside the original interval. -/
theorem sieveState_bounds {limit k n : ℕ} (hn : n ∈ sieveState limit k) :
    2 ≤ n ∧ n ≤ limit := by
  have hstart := sieveState_subset_of_le limit (Nat.zero_le k) hn
  simpa only [sieveState, Finset.mem_Icc] using hstart

/-- Completeness invariant: no stage ever removes a prime in the interval. -/
theorem prime_mem_sieveState {limit p : ℕ} (hp : Nat.Prime p)
    (hlimit : p ≤ limit) (k : ℕ) : p ∈ sieveState limit k := by
  induction k with
  | zero =>
      simpa only [sieveState, Finset.mem_Icc] using And.intro hp.two_le hlimit
  | succ k ih =>
      simp only [sieveState]
      split_ifs
      · apply Finset.mem_filter.mpr
        refine ⟨ih, ?_⟩
        by_cases heq : p = k + 2
        · exact Or.inl heq
        · right
          intro hdvd
          have := (Nat.dvd_prime hp).mp hdvd
          omega
      · exact ih

/-- After a prime's own stage, no proper multiple of it remains. -/
theorem sieveState_after_prime {limit k n : ℕ}
    (hp : Nat.Prime (k + 2)) (hlimit : k + 2 ≤ limit)
    (hn : n ∈ sieveState limit (k + 1)) :
    n = k + 2 ∨ ¬(k + 2) ∣ n := by
  have hpresent := prime_mem_sieveState hp hlimit k
  simp only [sieveState, hpresent, if_true, Finset.mem_filter] at hn
  exact hn.2

/-- Soundness invariant: all survivors through the next candidate are prime.

Any composite in this range would have a smaller prime divisor. That
prime survived to its own stage and removed the composite then.
-/
theorem sieveState_prime_of_le {limit k n : ℕ}
    (hn : n ∈ sieveState limit k) (hprocessed : n ≤ k + 2) : Nat.Prime n := by
  obtain ⟨hn2, hnlimit⟩ := sieveState_bounds hn
  obtain ⟨q, hq, hqdvd⟩ := Nat.exists_prime_and_dvd (by omega : n ≠ 1)
  have hqle : q ≤ n := Nat.le_of_dvd (by omega) hqdvd
  by_cases heq : n = q
  · simpa only [heq] using hq
  · have hq2 := hq.two_le
    have hindex : q - 2 + 2 = q := by omega
    have hstage : q - 2 + 1 ≤ k := by omega
    have hsurvived := sieveState_subset_of_le limit hstage hn
    have hqprime : Nat.Prime (q - 2 + 2) := by simpa only [hindex] using hq
    have hqbound : q - 2 + 2 ≤ limit := by omega
    have hnotmultiple := sieveState_after_prime hqprime hqbound hsurvived
    rw [hindex] at hnotmultiple
    exact False.elim (hnotmultiple.elim heq (fun h => h hqdvd))

/-- The algorithm's conditional branch really does select a prime. -/
theorem next_candidate_prime {limit k : ℕ}
    (h : k + 2 ∈ sieveState limit k) : Nat.Prime (k + 2) :=
  sieveState_prime_of_le h (Nat.le_refl _)

/-- Complete correctness for every bound, including 0 and 1. -/
theorem mem_sieve {limit n : ℕ} :
    n ∈ sieve limit ↔ Nat.Prime n ∧ n ≤ limit := by
  constructor
  · intro hn
    have hbounds := sieveState_bounds hn
    exact ⟨sieveState_prime_of_le hn (by omega), hbounds.2⟩
  · rintro ⟨hp, hlimit⟩
    exact prime_mem_sieveState hp hlimit (limit - 1)

theorem sieve_sound {limit n : ℕ} (hn : n ∈ sieve limit) : Nat.Prime n :=
  (mem_sieve.mp hn).1

theorem sieve_complete {limit n : ℕ} (hp : Nat.Prime n) (hn : n ≤ limit) :
    n ∈ sieve limit :=
  mem_sieve.mpr ⟨hp, hn⟩

example : sieve 0 = ∅ := by decide
example : sieve 1 = ∅ := by decide

-- Evaluation displays the exact output of the defined algorithm.
#eval (sieve 100).sort (· ≤ ·)
#eval (sieve 100).card -- 25

end RiemannEssay
