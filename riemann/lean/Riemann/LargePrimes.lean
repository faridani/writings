import Mathlib.NumberTheory.LucasPrimality
import Mathlib.Data.List.Prime
import Mathlib.Tactic.NormNum.Prime

/-!
# Kernel-checked certificates for the four large focal primes

Witnesses and complete factorizations come from the bundled
`data/large_prime_windows.json`. Lean checks every factorization, every
modular power, and the application of Mathlib's Lucas-primality theorem.

The explicit binary digits are also checked against their exponents.
Structural recursion on these short lists avoids trial division and
recursion through an exponent near one quadrillion. Ordinary `decide`
builds proof terms checked by Lean's kernel; no native oracle is used.
-/

namespace RiemannEssay

/-- Little-endian binary digits, with the empty list representing zero. -/
private def bitsValue : List Bool → ℕ
  | [] => 0
  | b :: bs => (if b then 1 else 0) + 2 * bitsValue bs

/-- Repeated squaring with structural recursion on a finite digit list. -/
private def bitsPower {M : Type*} [Monoid M] (a : M) : List Bool → M
  | [] => 1
  | b :: bs =>
    if b then a * bitsPower (a * a) bs else bitsPower (a * a) bs

private theorem bitsPower_eq {M : Type*} [Monoid M] (a : M) (bs : List Bool) :
    bitsPower a bs = a ^ bitsValue bs := by
  induction bs generalizing a with
  | nil => simp [bitsPower, bitsValue]
  | cons b bs ih =>
    cases b <;> simp [bitsPower, bitsValue, ih, pow_add, pow_mul, pow_two]

private theorem powerCertificate (p a e : ℕ) (bs : List Bool)
    (hvalue : bitsValue bs = e) (hpower : bitsPower (a : ZMod p) bs = 1) :
    (a : ZMod p) ^ e = 1 := by
  simpa only [bitsPower_eq, hvalue] using hpower

private theorem nonOneCertificate (p a e : ℕ) (bs : List Bool)
    (hvalue : bitsValue bs = e) (hpower : bitsPower (a : ZMod p) bs ≠ 1) :
    (a : ZMod p) ^ e ≠ 1 := by
  simpa only [bitsPower_eq, hvalue] using hpower

/-- Every prime divisor of the complete product occurs in its prime-factor list. -/
private theorem lucas_from_list (p a : ℕ) (factors : List ℕ)
    (hproduct : factors.prod = p - 1)
    (hprimes : ∀ q ∈ factors, Nat.Prime q)
    (hpower : (a : ZMod p) ^ (p - 1) = 1)
    (hpowers : ∀ q ∈ factors, (a : ZMod p) ^ ((p - 1) / q) ≠ 1) :
    Nat.Prime p := by
  apply lucas_primality p (a : ZMod p) hpower
  intro q hq hqd
  have hmem : q ∈ factors := mem_list_primes_of_dvd_prod hq.prime
    (fun r hr => (hprimes r hr).prime) (by simpa only [hproduct] using hqd)
  exact hpowers q hmem

set_option maxRecDepth 10000
set_option maxHeartbeats 2000000

private theorem certified_2 : Nat.Prime 2 := Nat.prime_two

private theorem certified_3 : Nat.Prime 3 := by
  apply lucas_from_list 3 2 [2]
  · norm_num
  · simp [certified_2]
  · exact powerCertificate 3 2 (3 - 1)
      [false, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl
    exact nonOneCertificate 3 2 ((3 - 1) / 2)
        [true] (by decide) (by decide)

private theorem certified_5 : Nat.Prime 5 := by
  apply lucas_from_list 5 2 [2, 2]
  · norm_num
  · simp [certified_2]
  · exact powerCertificate 5 2 (5 - 1)
      [false, false, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl
    exact nonOneCertificate 5 2 ((5 - 1) / 2)
        [false, true] (by decide) (by decide)

private theorem certified_7 : Nat.Prime 7 := by
  apply lucas_from_list 7 3 [2, 3]
  · norm_num
  · simp [certified_2, certified_3]
  · exact powerCertificate 7 3 (7 - 1)
      [false, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl
    · exact nonOneCertificate 7 3 ((7 - 1) / 2)
        [true, true] (by decide) (by decide)
    · exact nonOneCertificate 7 3 ((7 - 1) / 3)
        [false, true] (by decide) (by decide)

private theorem certified_11 : Nat.Prime 11 := by
  apply lucas_from_list 11 2 [2, 5]
  · norm_num
  · simp [certified_2, certified_5]
  · exact powerCertificate 11 2 (11 - 1)
      [false, true, false, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl
    · exact nonOneCertificate 11 2 ((11 - 1) / 2)
        [true, false, true] (by decide) (by decide)
    · exact nonOneCertificate 11 2 ((11 - 1) / 5)
        [false, true] (by decide) (by decide)

private theorem certified_13 : Nat.Prime 13 := by
  apply lucas_from_list 13 2 [2, 2, 3]
  · norm_num
  · simp [certified_2, certified_3]
  · exact powerCertificate 13 2 (13 - 1)
      [false, false, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl
    · exact nonOneCertificate 13 2 ((13 - 1) / 2)
        [false, true, true] (by decide) (by decide)
    · exact nonOneCertificate 13 2 ((13 - 1) / 3)
        [false, false, true] (by decide) (by decide)

private theorem certified_17 : Nat.Prime 17 := by
  apply lucas_from_list 17 3 [2, 2, 2, 2]
  · norm_num
  · simp [certified_2]
  · exact powerCertificate 17 3 (17 - 1)
      [false, false, false, false, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl
    exact nonOneCertificate 17 3 ((17 - 1) / 2)
        [false, false, false, true] (by decide) (by decide)

private theorem certified_29 : Nat.Prime 29 := by
  apply lucas_from_list 29 2 [2, 2, 7]
  · norm_num
  · simp [certified_2, certified_7]
  · exact powerCertificate 29 2 (29 - 1)
      [false, false, true, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl
    · exact nonOneCertificate 29 2 ((29 - 1) / 2)
        [false, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 29 2 ((29 - 1) / 7)
        [false, false, true] (by decide) (by decide)

private theorem certified_31 : Nat.Prime 31 := by
  apply lucas_from_list 31 3 [2, 3, 5]
  · norm_num
  · simp [certified_2, certified_3, certified_5]
  · exact powerCertificate 31 3 (31 - 1)
      [false, true, true, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl | rfl
    · exact nonOneCertificate 31 3 ((31 - 1) / 2)
        [true, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 31 3 ((31 - 1) / 3)
        [false, true, false, true] (by decide) (by decide)
    · exact nonOneCertificate 31 3 ((31 - 1) / 5)
        [false, true, true] (by decide) (by decide)

private theorem certified_37 : Nat.Prime 37 := by
  apply lucas_from_list 37 2 [2, 2, 3, 3]
  · norm_num
  · simp [certified_2, certified_3]
  · exact powerCertificate 37 2 (37 - 1)
      [false, false, true, false, false, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl
    · exact nonOneCertificate 37 2 ((37 - 1) / 2)
        [false, true, false, false, true] (by decide) (by decide)
    · exact nonOneCertificate 37 2 ((37 - 1) / 3)
        [false, false, true, true] (by decide) (by decide)

private theorem certified_41 : Nat.Prime 41 := by
  apply lucas_from_list 41 6 [2, 2, 2, 5]
  · norm_num
  · simp [certified_2, certified_5]
  · exact powerCertificate 41 6 (41 - 1)
      [false, false, false, true, false, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl
    · exact nonOneCertificate 41 6 ((41 - 1) / 2)
        [false, false, true, false, true] (by decide) (by decide)
    · exact nonOneCertificate 41 6 ((41 - 1) / 5)
        [false, false, false, true] (by decide) (by decide)

private theorem certified_83 : Nat.Prime 83 := by
  apply lucas_from_list 83 2 [2, 41]
  · norm_num
  · simp [certified_2, certified_41]
  · exact powerCertificate 83 2 (83 - 1)
      [false, true, false, false, true, false, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl
    · exact nonOneCertificate 83 2 ((83 - 1) / 2)
        [true, false, false, true, false, true] (by decide) (by decide)
    · exact nonOneCertificate 83 2 ((83 - 1) / 41)
        [false, true] (by decide) (by decide)

private theorem certified_101 : Nat.Prime 101 := by
  apply lucas_from_list 101 2 [2, 2, 5, 5]
  · norm_num
  · simp [certified_2, certified_5]
  · exact powerCertificate 101 2 (101 - 1)
      [false, false, true, false, false, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl
    · exact nonOneCertificate 101 2 ((101 - 1) / 2)
        [false, true, false, false, true, true] (by decide) (by decide)
    · exact nonOneCertificate 101 2 ((101 - 1) / 5)
        [false, false, true, false, true] (by decide) (by decide)

private theorem certified_167 : Nat.Prime 167 := by
  apply lucas_from_list 167 5 [2, 83]
  · norm_num
  · simp [certified_2, certified_83]
  · exact powerCertificate 167 5 (167 - 1)
      [false, true, true, false, false, true, false, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl
    · exact nonOneCertificate 167 5 ((167 - 1) / 2)
        [true, true, false, false, true, false, true] (by decide) (by decide)
    · exact nonOneCertificate 167 5 ((167 - 1) / 83)
        [false, true] (by decide) (by decide)

private theorem certified_499 : Nat.Prime 499 := by
  apply lucas_from_list 499 7 [2, 3, 83]
  · norm_num
  · simp [certified_2, certified_3, certified_83]
  · exact powerCertificate 499 7 (499 - 1)
      [false, true, false, false, true, true, true, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl | rfl
    · exact nonOneCertificate 499 7 ((499 - 1) / 2)
        [true, false, false, true, true, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 499 7 ((499 - 1) / 3)
        [false, true, true, false, false, true, false, true] (by decide) (by decide)
    · exact nonOneCertificate 499 7 ((499 - 1) / 83)
        [false, true, true] (by decide) (by decide)

private theorem certified_3907 : Nat.Prime 3907 := by
  apply lucas_from_list 3907 2 [2, 3, 3, 7, 31]
  · norm_num
  · simp [certified_2, certified_3, certified_7, certified_31]
  · exact powerCertificate 3907 2 (3907 - 1)
      [false, true, false, false, false, false, true, false, true, true, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl | rfl | rfl
    · exact nonOneCertificate 3907 2 ((3907 - 1) / 2)
        [true, false, false, false, false, true, false, true, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 3907 2 ((3907 - 1) / 3)
        [false, true, true, false, true, false, false, false, true, false, true] (by decide) (by decide)
    · exact nonOneCertificate 3907 2 ((3907 - 1) / 7)
        [false, true, true, true, false, true, false, false, false, true] (by decide) (by decide)
    · exact nonOneCertificate 3907 2 ((3907 - 1) / 31)
        [false, true, true, true, true, true, true] (by decide) (by decide)

private theorem certified_9901 : Nat.Prime 9901 := by
  apply lucas_from_list 9901 2 [2, 2, 3, 3, 5, 5, 11]
  · norm_num
  · simp [certified_2, certified_3, certified_5, certified_11]
  · exact powerCertificate 9901 2 (9901 - 1)
      [false, false, true, true, false, true, false, true, false, true, true, false, false, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl | rfl | rfl
    · exact nonOneCertificate 9901 2 ((9901 - 1) / 2)
        [false, true, true, false, true, false, true, false, true, true, false, false, true] (by decide) (by decide)
    · exact nonOneCertificate 9901 2 ((9901 - 1) / 3)
        [false, false, true, false, false, true, true, true, false, false, true, true] (by decide) (by decide)
    · exact nonOneCertificate 9901 2 ((9901 - 1) / 5)
        [false, false, true, true, true, true, false, true, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 9901 2 ((9901 - 1) / 11)
        [false, false, true, false, false, false, false, true, true, true] (by decide) (by decide)

private theorem certified_148721 : Nat.Prime 148721 := by
  apply lucas_from_list 148721 6 [2, 2, 2, 2, 5, 11, 13, 13]
  · norm_num
  · simp [certified_2, certified_5, certified_11, certified_13]
  · exact powerCertificate 148721 6 (148721 - 1)
      [false, false, false, false, true, true, true, true, false, false, true, false, false, false, true, false, false, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl | rfl | rfl
    · exact nonOneCertificate 148721 6 ((148721 - 1) / 2)
        [false, false, false, true, true, true, true, false, false, true, false, false, false, true, false, false, true] (by decide) (by decide)
    · exact nonOneCertificate 148721 6 ((148721 - 1) / 5)
        [false, false, false, false, true, true, false, false, false, false, true, false, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 148721 6 ((148721 - 1) / 11)
        [false, false, false, false, true, false, true, true, false, false, true, false, true, true] (by decide) (by decide)
    · exact nonOneCertificate 148721 6 ((148721 - 1) / 13)
        [false, false, false, false, true, true, false, true, false, false, true, true, false, true] (by decide) (by decide)

private theorem certified_166667 : Nat.Prime 166667 := by
  apply lucas_from_list 166667 2 [2, 167, 499]
  · norm_num
  · simp [certified_2, certified_167, certified_499]
  · exact powerCertificate 166667 2 (166667 - 1)
      [false, true, false, true, false, false, false, false, true, true, false, true, false, false, false, true, false, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl | rfl
    · exact nonOneCertificate 166667 2 ((166667 - 1) / 2)
        [true, false, true, false, false, false, false, true, true, false, true, false, false, false, true, false, true] (by decide) (by decide)
    · exact nonOneCertificate 166667 2 ((166667 - 1) / 167)
        [false, true, true, false, false, true, true, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 166667 2 ((166667 - 1) / 499)
        [false, true, true, true, false, false, true, false, true] (by decide) (by decide)

private theorem certified_250049 : Nat.Prime 250049 := by
  apply lucas_from_list 250049 3 [2, 2, 2, 2, 2, 2, 3907]
  · norm_num
  · simp [certified_2, certified_3907]
  · exact powerCertificate 250049 3 (250049 - 1)
      [false, false, false, false, false, false, true, true, false, false, false, false, true, false, true, true, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl
    · exact nonOneCertificate 250049 3 ((250049 - 1) / 2)
        [false, false, false, false, false, true, true, false, false, false, false, true, false, true, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 250049 3 ((250049 - 1) / 3907)
        [false, false, false, false, false, false, true] (by decide) (by decide)

private theorem certified_1000003 : Nat.Prime 1000003 := by
  apply lucas_from_list 1000003 2 [2, 3, 166667]
  · norm_num
  · simp [certified_2, certified_3, certified_166667]
  · exact powerCertificate 1000003 2 (1000003 - 1)
      [false, true, false, false, false, false, true, false, false, true, false, false, false, false, true, false, true, true, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl | rfl
    · exact nonOneCertificate 1000003 2 ((1000003 - 1) / 2)
        [true, false, false, false, false, true, false, false, true, false, false, false, false, true, false, true, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 1000003 2 ((1000003 - 1) / 3)
        [false, true, true, false, true, false, false, false, false, true, true, false, true, false, false, false, true, false, true] (by decide) (by decide)
    · exact nonOneCertificate 1000003 2 ((1000003 - 1) / 166667)
        [false, true, true] (by decide) (by decide)

private theorem certified_26005097 : Nat.Prime 26005097 := by
  apply lucas_from_list 26005097 5 [2, 2, 2, 13, 250049]
  · norm_num
  · simp [certified_2, certified_13, certified_250049]
  · exact powerCertificate 26005097 5 (26005097 - 1)
      [false, false, false, true, false, true, true, false, false, true, true, true, false, false, true, true, false, false, true, true, false, false, false, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl | rfl
    · exact nonOneCertificate 26005097 5 ((26005097 - 1) / 2)
        [false, false, true, false, true, true, false, false, true, true, true, false, false, true, true, false, false, true, true, false, false, false, true, true] (by decide) (by decide)
    · exact nonOneCertificate 26005097 5 ((26005097 - 1) / 13)
        [false, false, false, true, false, false, false, false, false, true, true, false, false, false, false, true, false, true, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 26005097 5 ((26005097 - 1) / 250049)
        [false, false, false, true, false, true, true] (by decide) (by decide)

private theorem certified_500000003 : Nat.Prime 500000003 := by
  apply lucas_from_list 500000003 2 [2, 41, 41, 148721]
  · norm_num
  · simp [certified_2, certified_41, certified_148721]
  · exact powerCertificate 500000003 2 (500000003 - 1)
      [false, true, false, false, false, false, false, false, true, false, true, false, false, true, true, false, true, false, true, true, false, false, true, true, true, false, true, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl | rfl
    · exact nonOneCertificate 500000003 2 ((500000003 - 1) / 2)
        [true, false, false, false, false, false, false, true, false, true, false, false, true, true, false, true, false, true, true, false, false, true, true, true, false, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 500000003 2 ((500000003 - 1) / 41)
        [false, true, false, false, true, true, false, false, true, false, true, false, true, false, false, false, false, true, false, true, true, true, false, true] (by decide) (by decide)
    · exact nonOneCertificate 500000003 2 ((500000003 - 1) / 148721)
        [false, true, false, false, false, true, false, false, true, false, true, true] (by decide) (by decide)

private theorem certified_1000000007 : Nat.Prime 1000000007 := by
  apply lucas_from_list 1000000007 5 [2, 500000003]
  · norm_num
  · simp [certified_2, certified_500000003]
  · exact powerCertificate 1000000007 5 (1000000007 - 1)
      [false, true, true, false, false, false, false, false, false, true, false, true, false, false, true, true, false, true, false, true, true, false, false, true, true, true, false, true, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl
    · exact nonOneCertificate 1000000007 5 ((1000000007 - 1) / 2)
        [true, true, false, false, false, false, false, false, true, false, true, false, false, true, true, false, true, false, true, true, false, false, true, true, true, false, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 1000000007 5 ((1000000007 - 1) / 500000003)
        [false, true] (by decide) (by decide)

private theorem certified_965250965251 : Nat.Prime 965250965251 := by
  apply lucas_from_list 965250965251 2 [2, 3, 3, 3, 5, 5, 5, 11, 13, 101, 9901]
  · norm_num
  · simp [certified_2, certified_3, certified_5, certified_11, certified_13, certified_101, certified_9901]
  · exact powerCertificate 965250965251 2 (965250965251 - 1)
      [false, true, false, false, false, false, false, false, true, true, true, true, true, false, true, true, false, false, false, false, true, true, true, false, true, false, true, true, true, true, false, true, false, false, false, false, false, true, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl | rfl | rfl | rfl | rfl | rfl
    · exact nonOneCertificate 965250965251 2 ((965250965251 - 1) / 2)
        [true, false, false, false, false, false, false, true, true, true, true, true, false, true, true, false, false, false, false, true, true, true, false, true, false, true, true, true, true, false, true, false, false, false, false, false, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 965250965251 2 ((965250965251 - 1) / 3)
        [false, true, true, false, true, false, true, false, false, true, false, true, false, false, true, false, false, false, false, false, true, false, true, true, true, false, false, true, false, true, true, true, false, true, false, true, false, false, true] (by decide) (by decide)
    · exact nonOneCertificate 965250965251 2 ((965250965251 - 1) / 5)
        [false, true, false, true, true, false, false, true, false, false, true, true, false, true, false, false, false, false, false, false, true, true, false, true, false, true, false, false, true, true, true, true, false, false, true, true, false, true] (by decide) (by decide)
    · exact nonOneCertificate 965250965251 2 ((965250965251 - 1) / 11)
        [false, true, true, false, false, false, true, false, false, false, true, false, true, false, false, false, false, false, false, false, true, false, true, false, false, true, true, true, false, true, true, false, false, false, true, false, true] (by decide) (by decide)
    · exact nonOneCertificate 965250965251 2 ((965250965251 - 1) / 13)
        [false, true, false, true, false, false, false, true, false, false, false, true, true, true, false, false, false, true, true, false, false, true, false, true, true, false, false, true, false, false, true, false, true, false, false, false, true] (by decide) (by decide)
    · exact nonOneCertificate 965250965251 2 ((965250965251 - 1) / 101)
        [false, true, false, true, true, false, true, true, true, false, true, false, true, false, true, false, true, true, false, false, false, true, false, true, true, false, false, true, true, true, false, false, false, true] (by decide) (by decide)
    · exact nonOneCertificate 965250965251 2 ((965250965251 - 1) / 9901)
        [false, true, false, true, false, false, true, false, true, false, true, false, true, false, false, true, true, true, true, true, false, false, true, true, true, false, true] (by decide) (by decide)

private theorem certified_1000000000039 : Nat.Prime 1000000000039 := by
  apply lucas_from_list 1000000000039 3 [2, 3, 13, 17, 29, 26005097]
  · norm_num
  · simp [certified_2, certified_3, certified_13, certified_17, certified_29, certified_26005097]
  · exact powerCertificate 1000000000039 3 (1000000000039 - 1)
      [false, true, true, false, false, true, false, false, false, false, false, false, true, false, false, false, true, false, true, false, false, true, false, true, false, false, true, false, true, false, true, true, false, false, false, true, false, true, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl | rfl | rfl | rfl | rfl
    · exact nonOneCertificate 1000000000039 3 ((1000000000039 - 1) / 2)
        [true, true, false, false, true, false, false, false, false, false, false, true, false, false, false, true, false, true, false, false, true, false, true, false, false, true, false, true, false, true, true, false, false, false, true, false, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 1000000000039 3 ((1000000000039 - 1) / 3)
        [false, true, false, false, false, true, true, false, true, false, true, false, false, false, false, false, true, true, true, false, true, true, false, false, false, false, true, true, true, false, false, true, true, false, true, true, false, false, true] (by decide) (by decide)
    · exact nonOneCertificate 1000000000039 3 ((1000000000039 - 1) / 13)
        [false, true, true, true, true, true, false, false, true, false, false, false, false, false, false, false, true, false, false, true, true, true, true, true, false, false, false, true, false, true, true, true, true, false, false, false, true] (by decide) (by decide)
    · exact nonOneCertificate 1000000000039 3 ((1000000000039 - 1) / 17)
        [false, true, true, false, false, false, true, true, true, true, false, false, true, false, true, true, true, true, true, false, false, true, false, false, false, true, false, false, true, true, false, true, true, false, true, true] (by decide) (by decide)
    · exact nonOneCertificate 1000000000039 3 ((1000000000039 - 1) / 29)
        [false, true, true, true, true, false, true, true, true, true, false, false, false, true, false, false, true, false, true, false, true, false, true, false, true, true, true, false, false, false, false, false, false, false, false, true] (by decide) (by decide)
    · exact nonOneCertificate 1000000000039 3 ((1000000000039 - 1) / 26005097)
        [false, true, true, false, true, true, false, false, false, true, true, false, true, false, false, true] (by decide) (by decide)

private theorem certified_1000000000000037 : Nat.Prime 1000000000000037 := by
  apply lucas_from_list 1000000000000037 2 [2, 2, 7, 37, 965250965251]
  · norm_num
  · simp [certified_2, certified_7, certified_37, certified_965250965251]
  · exact powerCertificate 1000000000000037 2 (1000000000000037 - 1)
      [false, false, true, false, false, true, false, false, false, false, false, false, false, false, false, true, false, true, true, false, false, false, true, true, false, false, true, false, false, true, false, true, false, true, true, true, true, true, true, false, true, false, true, true, false, false, false, true, true, true] (by decide) (by decide)
  · intro q hq
    simp only [List.mem_cons, List.not_mem_nil, or_false, or_self, or_self_left] at hq
    rcases hq with rfl | rfl | rfl | rfl
    · exact nonOneCertificate 1000000000000037 2 ((1000000000000037 - 1) / 2)
        [false, true, false, false, true, false, false, false, false, false, false, false, false, false, true, false, true, true, false, false, false, true, true, false, false, true, false, false, true, false, true, false, true, true, true, true, true, true, false, true, false, true, true, false, false, false, true, true, true] (by decide) (by decide)
    · exact nonOneCertificate 1000000000000037 2 ((1000000000000037 - 1) / 7)
        [false, false, true, true, true, true, false, true, true, false, true, true, false, true, true, true, false, false, false, false, false, false, true, false, true, false, true, false, false, false, false, true, true, false, true, true, false, true, true, true, true, false, false, false, false, false, false, true] (by decide) (by decide)
    · exact nonOneCertificate 1000000000000037 2 ((1000000000000037 - 1) / 37)
        [false, false, true, false, true, false, true, false, false, false, true, false, false, true, true, false, false, false, false, true, true, false, true, false, false, false, false, true, true, true, false, true, false, false, true, false, true, false, false, true, false, false, false, true, true] (by decide) (by decide)
    · exact nonOneCertificate 1000000000000037 2 ((1000000000000037 - 1) / 965250965251)
        [false, false, true, true, false, false, false, false, false, false, true] (by decide) (by decide)

theorem prime_near_million : Nat.Prime 1000003 := certified_1000003

theorem prime_near_billion : Nat.Prime 1000000007 := certified_1000000007

theorem prime_near_trillion : Nat.Prime 1000000000039 := certified_1000000000039

theorem prime_near_quadrillion : Nat.Prime 1000000000000037 := certified_1000000000000037

end RiemannEssay
