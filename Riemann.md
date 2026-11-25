# Riemann, from scratch: rebuilding the primes

A **prime number** is a whole number greater than 1 whose only positive divisors are 1 and itself. The first few are

$$
2,\ 3,\ 5,\ 7,\ 11,\ 13,\ 17,\ 19,\ 23,\ 29,\ldots
$$

Seven is prime because it cannot be divided evenly by any whole number between 2 and 6. Twelve is composite because, for example, $12=3\times4$. One is neither prime nor composite.

That definition seems far removed from complex numbers, waves, or a famous mathematical hypothesis. I wanted to understand how the pieces connect well enough to build something: a program that reconstructs the distribution of primes using the zeros of the Riemann zeta function.

The inspiration is a sentence Richard Feynman left on his blackboard:

> “What I cannot create, I do not understand.”[^feynman]

Here, “from scratch” means making the chain of ideas visible. We will write a small prime finder, explain why primes are useful, derive the bridge to the zeta function, and watch the prime-counting staircase emerge as we add more zero pairs. The numerical work uses established libraries for special functions; rebuilding all of numerical analysis would be a different project.

> **A note on the date — November 24, 2026.** This essay uses the traditional name *Riemann hypothesis*. On November 20, Levent Alpöge released a formal proof in Lean. The Lean FRO and Mathlib Initiative subsequently certified the RH statement and proof, and Andrew Sutherland's MIT verification record documents independent builds and proof checks. The verified statements also cover GRH for Dirichlet $L$-functions. Work to explain and simplify the argument continues. This essay develops the statement and a numerical experiment; it does not reproduce or independently audit that formal proof.[^lean][^verification][^announcement]

## 1. The building blocks of multiplication

Every integer greater than 1 can be written as a product of primes. Apart from rearranging the factors, that representation is unique. For example,

$$
60=2\times2\times3\times5=2^2\cdot3\cdot5.
$$

We can group those factors into $6\times10$ or $4\times15$, but breaking the groups down again leads to the same primes. This is the fundamental theorem of arithmetic.

Excluding 1 from the primes keeps this statement clean. Otherwise we could keep inserting factors of 1 without changing the number. Two is the only even prime: every larger even number has 2 as an additional divisor.

There are infinitely many primes. Suppose we had a complete finite list $p_1,\ldots,p_k$. Form

$$
N=p_1p_2\cdots p_k+1.
$$

Dividing $N$ by any prime on the list leaves remainder 1. Therefore $N$ has a prime divisor missing from the list. The number $N$ itself need not be prime; the contradiction only requires a new prime factor.

This is already a useful example of proof. We did not check a very long list and decide the pattern would probably continue. We gave an argument that defeats every proposed finite list.

### A first prime test

To test an integer $n$, we can try dividing it by smaller integers. We only need to reach $\sqrt n$. If $n=ab$ and both $a$ and $b$ were greater than $\sqrt n$, their product would exceed $n$.

~~~python
from math import isqrt

def is_prime(n):
    if n < 2:
        return False
    for divisor in range(2, isqrt(n) + 1):
        if n % divisor == 0:
            return False
    return True

print([n for n in range(2, 30) if is_prime(n)])
# [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
~~~

Every line has a mathematical reason. The first condition handles numbers outside the definition. The loop implements the square-root argument. Finding one divisor is enough to reject a candidate.

Running the test for each integer from 0 through 100 gives a list of primes. We can then keep a running count, written $\pi(x)$: the number of primes less than or equal to $x$.

![A staircase showing the number of primes less than or equal to each number x from 0 to 100. The count starts at 0 and reaches 25 at x equals 100.](riemann/assets/prime_count_0_to_100.png)

*The horizontal axis runs from 0 to 100. The vertical axis is the number of primes found so far, $\pi(x)$. The count rises by one at each prime and stays flat between primes. For example, $\pi(10)=4$ and $\pi(100)=25$.*

## 2. How we find primes today

“Find primes” hides several different tasks:

| Task | Question | Example |
|---|---|---|
| Test | Is this particular integer prime? | Is 97 prime? |
| Generate | Produce a prime satisfying some requirements. | Find a random prime with a specified bit length. |
| Enumerate or count | Which primes, or how many primes, lie below a cutoff? | List the primes up to 100. |
| Factor | Which primes multiply to a given composite number? | Recover 7 and 13 from 91. |

These tasks are related, but a fast solution to one does not automatically solve the others.

### Many small primes: the sieve

If we want every prime up to a moderate limit, we can cross out composites together. Start with the integers from 2 to the limit. Keep 2 and cross out its larger multiples. Keep the next remaining number, 3, and cross out its multiples. Continue.

This is the sieve of Eratosthenes. When processing a prime $p$, we can begin at $p^2$: smaller multiples already have a smaller prime factor and have been crossed out.

~~~python
from math import isqrt

def primes_up_to(limit):
    if limit < 2:
        return []
    keep = [True] * (limit + 1)
    keep[0] = keep[1] = False
    for p in range(2, isqrt(limit) + 1):
        if keep[p]:
            for multiple in range(p * p, limit + 1, p):
                keep[multiple] = False
    return [n for n, prime in enumerate(keep) if prime]

print(len(primes_up_to(100)))  # 25
~~~

The exact black staircase in our later graphs comes from a separate implementation of this idea.

### One very large prime: generate candidates and test

A cryptographic library does not normally list every smaller prime before producing a large one. It generates a candidate of the required size, rejects easy failures, and performs stronger primality tests. If the candidate fails, it tries again.

OpenSSL documents small-prime trial division followed by Miller–Rabin testing. Miller–Rabin exploits modular arithmetic to expose composites without trial-dividing by every possible factor. With appropriately chosen random tests, a composite's chance of passing can be made extremely small. A passing candidate is called a *probable prime*.[^openssl]

There are also methods that establish primality conclusively. NIST's Digital Signature Standard distinguishes probable-prime and provable-prime generation. The AKS result establishes that primality can be decided deterministically in polynomial time, without assuming RH. Here the input size is the number of bits needed to write the integer. That theoretical guarantee is separate from which method is fastest in a particular implementation.[^nist][^aks]

Thus a prime can be easy to recognize without making the factorization of a large composite easy.

## 3. Where primes do useful work

### RSA: a public product with secret factors

In the familiar two-prime form of RSA, choose distinct large secret primes $p$ and $q$ and publish their product

$$
N=pq
$$

as part of a public key. The private-key construction uses information available from the factors. One such quantity is Euler's totient $\varphi(N)$, the number of integers from 1 through $N$ that share no prime factor with $N$:

$$
\varphi(N)=(p-1)(q-1).
$$

As a tiny illustration, $61\times53=3233$, and $\varphi(3233)=60\times52=3120$. Real keys use much larger numbers and a complete cryptographic scheme.

Multiplying known factors is straightforward. Recovering the factors from a large product is a different problem. Knowing $p$ and $q$ allows recovery of the RSA private key. The original RSA paper explicitly connects its security, in part, to the difficulty of factoring.[^rsa]

This is why efficient prime generation is compatible with RSA: the legitimate user chooses the factors first. An attacker is given their product. Factoring the modulus is sufficient to break RSA. Whether every efficient way to reverse RSA's public operation would also give an efficient factoring method is a separate question.[^rsa-problem]

### A prime can also define the arithmetic

Working *modulo* $p$ means keeping remainders after division by $p$. Modulo 7, for example,

$$
5+4\equiv2,\qquad 3\cdot5\equiv1.
$$

The second equation says that 5 behaves as the multiplicative inverse of 3. When the modulus is prime, every nonzero remainder has an inverse. The result is a finite field: an arithmetic system in which addition, subtraction, multiplication, and division by nonzero elements behave consistently.

X25519, an elliptic-curve method for agreeing on a shared secret, uses the public prime $2^{255}-19$. Its secret values participate in curve operations; the prime itself is published in the specification. This is a different use of primes from hiding RSA's factors.[^x25519]

### Data lookup and recovering damaged messages

Some universal hash families use arithmetic modulo a prime to spread integer keys among hash-table buckets. Choosing a function randomly from a suitable family gives a bound on collisions between different keys. The prime helps establish the guarantee; it does not mean every hash table needs a prime number of buckets.[^hashing]

Finite-field algebra also supports error-correcting codes. NASA's Galileo mission used Reed–Solomon codes over a field with $256=2^8$ elements to help recover transmitted data. The underlying prime is 2. A field of 256 elements uses a construction based on polynomials over the two-element field; it is not ordinary integer arithmetic modulo 256.[^galileo]

These examples connect prime-based mathematics to private communication, efficient computation, and reliable transmission. They use algebraic properties of particular primes or finite fields. To understand Riemann's question, we now turn to the distribution of *all* primes.

## 4. Turning a list into a staircase

Define

```math
\pi(x)=\operatorname{card}\left\lbrace p\le x : p\text{ is prime}\right\rbrace.
```

Here $\operatorname{card}$ means the number of elements in the set. The symbol $\pi(x)$ means “prime count,” not the circle constant. For example, $\pi(10)=4$ because the primes up to 10 are 2, 3, 5, and 7. Also, $\pi(100)=25$.

Plotting $\pi(x)$ gives a staircase. It jumps by one at every prime and stays flat between primes. The individual steps are irregular, but the broad trend is remarkably regular.

The prime number theorem says

$$
\pi(x)\sim\frac{x}{\log x}.
$$

The symbol $\sim$ means that the ratio tends to 1 as $x$ grows. Throughout this essay, $\log$ is the natural logarithm. A more accurate smooth guide at large scales is the logarithmic integral, defined here using the standard principal-value convention:

$$
\operatorname{li}(x)=\operatorname{PV}\int_0^x\frac{dt}{\log t}
=\operatorname{Ei}(\log x).
$$

The principal value, written PV, balances the two sides of the singularity at $t=1$. The name $\operatorname{Ei}$ denotes the exponential integral used by our numerical library. The derivative of $\operatorname{li}(x)$ is $1/\log x$, so the integral accumulates a predicted density. This motivates the heuristic that primes near a large number $x$ have average density about $1/\log x$. It does not treat primality as a sequence of independent coin flips.[^pnt][^li]

![The exact prime-counting staircase and its smooth logarithmic-integral approximation from 2 to 100.](riemann/assets/prime_count_and_logarithmic_integral.png)

*The horizontal axis is the numerical cutoff $x$. The vertical axis counts primes up to that cutoff. The smooth curve describes an average trend; it does not reproduce each step.*

The next question is more demanding than identifying that trend: **how large can the discrepancy between the staircase and its smooth approximation become?**

## 5. A sum over integers becomes a product over primes

Begin with a function that seems to involve all positive integers equally:

$$
\zeta(s)=\sum_{n=1}^{\infty}\frac{1}{n^s}.
$$

This series converges when the real part of $s$ is greater than 1. For a concrete real input,

$$
\zeta(2)=1+\frac{1}{2^2}+\frac{1}{3^2}+\frac{1}{4^2}+\cdots.
$$

Now take one prime, say 2. The geometric-series identity gives

$$
\frac{1}{1-2^{-s}}=1+2^{-s}+2^{-2s}+2^{-3s}+\cdots.
$$

Do the same for 3, 5, 7, and every other prime, and multiply the expressions. Selecting one term from each factor amounts to selecting a power of each prime. For instance, selecting $2^{-2s}$, $3^{-s}$, and $5^{-s}$ produces

$$
(2^2\cdot3\cdot5)^{-s}=60^{-s}.
$$

Unique factorization tells us exactly why every positive integer appears once. With the convergence condition $\operatorname{Re}(s)>1$ in place, this gives Euler's product:

$$
\boxed{\displaystyle
\zeta(s)=\prod_{p\ \mathrm{prime}}\frac{1}{1-p^{-s}}.
}
$$

The same function can be assembled from all integers or from just the primes. This identity is the bridge we need.[^zeta]

There is another useful detail hidden in the product. For real $s>1$, expanding its logarithm gives

$$
\log\zeta(s)=
\sum_p\sum_{k=1}^{\infty}\frac{p^{-ks}}{k},
\qquad s>1.
$$

Primes appear together with their squares, cubes, and higher powers, weighted by $1/k$. Those weights will return when we reconstruct the prime count.

## 6. Why complex numbers enter

Write a complex input as

$$
s=\sigma+it,\qquad i^2=-1.
$$

The real number $\sigma$ is its horizontal coordinate in the complex plane, and $t$ is its vertical coordinate. For a positive integer $n$,

$$
n^{-s}=e^{-s\log n}
=n^{-\sigma}\bigl(\cos(t\log n)-i\sin(t\log n)\bigr).
$$

The size of this term is $n^{-\sigma}$, while its direction rotates as $t$ changes. Complex inputs allow cancellation among terms pointing in different directions.

But the original series only converges for $\sigma>1$. We cannot simply substitute $\sigma=1/2$ into that series and assume it still defines the function.

The extension is called *analytic continuation*. A familiar analogy is

$$
1+z+z^2+\cdots=\frac{1}{1-z},\qquad |z|<1.
$$

The series fails at $z=2$, but the function on the right still makes sense there. Evaluating the continued function at 2 does not make the divergent series an ordinary convergent sum.

For zeta, we can see part of the continuation concretely through the alternating series

$$
\eta(s)=1-\frac{1}{2^s}+\frac{1}{3^s}-\frac{1}{4^s}+\cdots.
$$

Where the original series converges, separating the even terms gives

$$
\eta(s)=(1-2^{1-s})\zeta(s).
$$

The alternating series converges in the larger region $\operatorname{Re}(s)>0$. Consequently,

$$
\zeta(s)=\frac{\eta(s)}{1-2^{1-s}}
$$

provides a continuation throughout the strip $0<\operatorname{Re}(s)<1$, where the denominator is nonzero. More generally, zeta continues across the complex plane with a single pole at $s=1$.[^zeta]

This is a crucial step in the story. The continuation lets us investigate a region that the original infinite sum could not reach.

## 7. What a zeta zero is

A zero is a complex input $\rho$ satisfying

$$
\zeta(\rho)=0.
$$

Zeta has *trivial zeros* at the negative even integers:

$$
-2,-4,-6,\ldots.
$$

Its other zeros lie in the *critical strip*

$$
0<\operatorname{Re}(\rho)<1.
$$

The Riemann hypothesis is the statement that every one of these nontrivial zeros has real part exactly $1/2$. This vertical line is called the *critical line*.[^zeros]

The first few positive imaginary parts are approximately

| Pair index | Positive height $\gamma_n$ |
|---:|---:|
| 1 | 14.134725142 |
| 2 | 21.022039639 |
| 3 | 25.010857580 |

For each listed zero $\rho_n=1/2+i\gamma_n$, its complex conjugate $1/2-i\gamma_n$ is also a zero. In our graphs, **one zero pair** means these two zeros. Ten thousand pairs therefore means 20,000 nontrivial zeros, represented by 10,000 positive heights.[^odlyzko]

![The first zeta zero pairs in the complex plane, with the critical strip and the line of real part one half marked.](riemann/assets/zeta_zeros.png)

*Here the horizontal coordinate is the real part of a complex input. In the prime-counting graphs it is the real-number cutoff $x$. These are different plots with different meanings for their axes.*

A symmetric arrangement by itself would not establish RH: points can be symmetric about a line while lying on either side of it. The assertion is that every nontrivial zero is actually on the line.

## 8. How a zero becomes a wave

The connection becomes easier to see by expanding a term that occurs in explicit formulas. If $\rho=\beta+i\gamma$ and $x>1$, then

$$
x^\rho=x^\beta e^{i\gamma\log x}
=x^\beta\bigl(\cos(\gamma\log x)+i\sin(\gamma\log x)\bigr).
$$

The two coordinates of a zero play different roles:

- Its real part $\beta$ controls the factor $x^\beta$.
- Its imaginary part $\gamma$ sets an oscillation frequency in $\log x$.

On the critical line, the first factor is $\sqrt{x}$. Adding a conjugate pair produces a real oscillation, which is why pairs are convenient for reconstructing a real-valued prime count.

There is a useful analogy with synthesizing a signal from frequencies. Lower zeros supply broad variations. Higher zeros supply finer variations. Near a fixed value of $x$, the phase $\gamma\log x$ changes by approximately $\gamma\,\Delta x/x$, so a full oscillation has local scale

$$
\Delta x\approx\frac{2\pi x}{\gamma}.
$$

This also explains a limitation: the same finite set of zeros gives coarser spatial resolution as we move farther out along the number line.

The analogy needs one qualification. The exact prime-counting reconstruction contains exponential-integral terms and prime-power corrections, not just a freely chosen sum of sine waves. The frequencies and weights come from the mathematics.

## 9. The explicit formula: rebuilding the staircase

The most natural intermediate function counts prime powers with the weights we saw in $\log\zeta(s)$:

$$
J(x)=\sum_{p^k\le x}\frac1k
=\pi(x)+\frac12\pi(\sqrt{x})
+\frac13\pi(x^{1/3})+\cdots.
$$

A prime contributes 1. Its square contributes another $1/2$, its cube another $1/3$, and so on.

For example, below 10 there are four primes, two prime squares (4 and 9), and one prime cube (8). Therefore

$$
J(10)=4+\frac12\cdot2+\frac13\cdot1=\frac{16}{3}.
$$

Riemann's explicit formula expresses this function using the zeros. A convenient paired form is

$$
\begin{aligned}
J_0(x)={}&\operatorname{Ei}(\log x)
-2\lim_{T\to\infty}\operatorname{Re}
\sum_{0<\operatorname{Im}\rho\le T}
\operatorname{Ei}(\rho\log x)\\
&-\log2+
\int_x^\infty\frac{dt}{t(t^2-1)\log t}.
\end{aligned}
$$

The subscript 0 specifies a midpoint convention: at a jump, use the average of the left and right limits. Away from prime powers, $J_0(x)=J(x)$. Zeros are counted with multiplicity and ordered by increasing height, with conjugates combined before taking the limit.[^explicit]

Read the formula as three ingredients: a smooth logarithmic-integral term, oscillatory corrections supplied by nontrivial zeros, and the remaining constant and trivial-zero correction. The formula is a theorem connecting zeros and prime powers; its validity does not depend on assuming that the zeros lie on the critical line.

### Removing the prime powers

We still want ordinary primes, so we must undo the extra counting. Möbius inversion does exactly that:

$$
\pi_0(x)=\sum_{m\ge1}\frac{\mu(m)}{m}J_0(x^{1/m}).
$$

The Möbius function $\mu(m)$ is zero if a squared prime divides $m$. Otherwise it is $(-1)^r$, where $r$ is the number of distinct prime factors. In particular,

$$
\mu(1)=1,\quad
\mu(2)=\mu(3)=\mu(5)=-1,\quad
\mu(4)=0,\quad
\mu(6)=1.
$$

This is an inclusion-and-exclusion correction: subtract the square and cube contributions, then restore contributions subtracted too often. For $2\le x\le100$, only $m\le6$ can contribute in the exact formula, so

$$
\boxed{\displaystyle
\pi_0(x)=J_0(x)
-\frac12J_0(\sqrt{x})
-\frac13J_0(x^{1/3})
-\frac15J_0(x^{1/5})
+\frac16J_0(x^{1/6}).
}
$$

For example, at $x=10$ the correction gives $16/3-1-1/3=4$. For $m\ge7$, even $100^{1/m}<2$, below the first prime, so the remaining exact terms vanish.

At an ordinary nonprime point, $\pi_0(x)=\pi(x)$. At a prime $p$, the midpoint convention gives

$$
\pi_0(p)=\pi(p)-\frac12.
$$

This half-step matters when we inspect the graphs closely.

## 10. Add 10, then 50, then 10,000 zero pairs

For computation, replace the infinite zero sum by its first $K$ pairs. Call the resulting weighted count $\widehat J_K(x)$, and apply the same prime-power correction to obtain $\widehat\pi_K(x)$. The hats mark finite approximations: $\widehat J_0$ means the smooth calculation with no zero pairs, whereas $J_0$ in the exact formula means the midpoint convention.

The experiment has two independent inputs:

1. A sieve supplies the exact reference staircase.
2. A table of zeta-zero heights supplies the reconstruction.

**The list of primes is never passed to the reconstruction function.** The two outputs are compared only after they have been computed.

The zero heights come from Andrew Odlyzko's published table. We use the first 10,000 positive heights, ending near $\gamma_{10000}=9877.782654004$. The source states an absolute accuracy of $3\times10^{-9}$ for the table.[^odlyzko]

![Six comparisons of the exact prime count with reconstructions using 0, 10, 50, 200, 1000, and 10000 zero pairs.](riemann/assets/zero_pair_progression.png)

*Each panel uses the same close-up interval and vertical scale. The black staircase is the independent prime count. The colored curve uses the indicated number of zero pairs. The zero-pair-free curve includes the smooth and trivial-zero corrections; it is not simply the logarithmic integral.*

With few zeros, the broad trend is visible but individual steps are blurred. Additional zeros sharpen the transitions. By 10,000 pairs, the reconstructed curve almost lies on the staircase at this scale.

We can measure the improvement instead of relying only on the picture. The following values are errors at the 98 half-integers $2.5,3.5,\ldots,99.5$, chosen to stay away from the prime jumps:

| Zero pairs | Mean absolute error in prime count | Largest absolute error on these points |
|---:|---:|---:|
| 0 | 0.325460 | 0.976994 |
| 10 | 0.187564 | 0.615364 |
| 50 | 0.090096 | 0.359967 |
| 200 | 0.033206 | 0.134489 |
| 1,000 | 0.009428 | 0.032872 |
| 10,000 | 0.001497 | 0.006710 |

These are measurements for this interval and these sample points. They are not universal error bounds, and increasing $K$ need not improve the approximation at every individual location. The [reproduction notes](riemann/REPRODUCE.md) explain the calculation and numerical checks.

## 11. What remains visible at 10,000 pairs

Here are just the exact curve and the reconstruction using 10,000 pairs:

![Exact prime count versus its 10000-pair reconstruction, including a tight close-up of the jump at 29.](riemann/assets/primes_exact_vs_10000_zero_pairs.png)

*The overview nearly hides the difference. The tight detail at 29 reveals a smooth transition and small oscillations around the jump.*

Immediately below 29 there are nine primes; at 29 and immediately above it there are ten. At $x=29$, our finite reconstruction is approximately $9.49995$, close to the midpoint value $9.5$ specified by the infinite formula.

The overshoot and undershoot near that jump are a form of Gibbs ringing. A finite collection of smooth oscillatory terms is approximating a discontinuity. Increasing the number of terms compresses the transition and the surrounding ripples. It does not turn a finite sum into a discontinuous staircase.

This is why the picture must be interpreted at a stated scale. A plot that looks exact when shown across 100 integers can reveal structure when magnified to a width of a few hundredths.

The graph also illustrates a distinction worth preserving even after a proof of RH: a finite computation shows what happens for the inputs and zero data it uses. A theorem supplies a reason that covers infinitely many cases. Our Python experiment does not inspect every zero or verify the new formal proof.

## 12. What RH says about the error

Return to the discrepancy

$$
E(x)=\pi(x)-\operatorname{li}(x).
$$

A standard equivalent formulation of RH is

$$
\pi(x)=\operatorname{li}(x)+O(\sqrt{x}\log x).
$$

The $O$ notation says that, beyond some cutoff, the absolute error is bounded by a constant times $\sqrt{x}\log x$. It is a bound on the accumulated prime count, not an exact prediction of the next prime.[^bombieri]

The explicit formula explains why the real part $1/2$ is significant. A zero with real part $\beta$ contributes terms involving $x^\beta$. Locating the nontrivial zeros on the critical line constrains the scale of the fluctuations. Turning this observation into the stated error estimate requires control of the whole zero sum, not merely bounding one oscillation.

There is also a precise classical bound: RH is equivalent to

$$
\left|\pi(x)-\operatorname{li}(x)\right|
<\frac{\sqrt{x}\log x}{8\pi},
\qquad x\ge2657.
$$

Here the $\pi$ in $8\pi$ is the circle constant.[^pnt]

An illustrative calculation makes the scale concrete. At $x=10^{12}$, the right-hand side is about $1.10$ million. The smooth estimate $\operatorname{li}(10^{12})$ is about $3.76\times10^{10}$, so this bound is small relative to the estimated total count. It is still an allowed error of more than a million: a rigorous estimate and an exact answer serve different purposes.

The same global statement cannot be established by our very accurate small graph. The graph helps us see the mechanism; the theorem controls it beyond the plotted range.

## 13. How does this help us as humans?

The immediate mathematical value is a stronger guarantee about prime distribution. A proof turns results established under RH into unconditional theorems, provided RH was the assumption they actually required. That is useful in reasoning about prime counts, error terms, and the intervals in which primes must occur.

One concrete historical example is the computation of $\pi(10^{24})$. An early analytic computation used RH, and David Platt later verified that count unconditionally. This is the kind of practical distinction that an assumption makes: not necessarily a different numerical answer, but a different justification for trusting it.[^primecount][^platt]

For an existing algorithm, removing an unproved assumption may strengthen its guarantee without changing a single instruction or making it run faster. New speedups would require additional algorithmic ideas. A useful proof might supply those ideas, but that is work to identify and demonstrate.

The distinction between RH and its generalizations also matters. Ordinary RH concerns the single function $\zeta(s)$. Dirichlet $L$-functions describe finer questions such as the distribution of primes among arithmetic progressions. Other families of zeta and $L$-functions lead to further generalizations.

The November 2026 verification record explicitly covers RH and GRH for Dirichlet $L$-functions. It does not claim every extension to general Dedekind zeta, Hecke, or automorphic $L$-functions. When applying the result to an older conditional theorem, we must match its assumption to the family actually covered.[^verification]

For everyday technology, the consequences should be stated carefully. RSA, elliptic-curve key agreement, hash tables, and error-correcting codes already had functioning constructions and proofs of their relevant algebraic properties. A prime-distribution theorem does not by itself supply an efficient method to factor a specific RSA modulus. Nor does it automatically accelerate every program that uses primes.

There is a wider human value in making previously separate ideas explain one another. We began with whole-number division and reached a relationship between a discrete staircase and complex oscillations. Learning to move between such descriptions can suggest methods beyond the question that first motivated them.

The recent proof also sharpens the Feynman theme. Establishing that an argument is logically valid and understanding its organizing ideas are related achievements with different demands. Alpöge's announcement explicitly describes the work of understanding, simplifying, and communicating the argument that remains after the formalization.[^announcement]

For this essay, the goal is smaller and concrete: rebuild enough of the connection that the sentence “the zeros encode the primes” has an operational meaning. We can supply zero heights to a program, add the corresponding contributions, remove the prime-power terms, and watch the prime-counting steps appear.

That leaves us with a useful habit: when a remarkable result appears, ask what we can construct from it, what we can verify, and what we can explain.

## 14. Reproduce the experiment

The figures, zero data, and Python implementation are included in the [riemann directory](riemann/REPRODUCE.md).

From the repository root, with Python and a suitable environment:

~~~bash
python -m pip install -r riemann/requirements.txt
python riemann/generate_figures.py
~~~

The code keeps the sieve separate from the zero-based reconstruction and records numerical validation. It includes a direct implementation of the finite formula and an accelerated evaluation for drawing the dense 10,000-pair curve.

Three implementation choices deserve explanation:

1. **Evaluate the complex exponential integral directly.** The code uses $\operatorname{Ei}(\rho\log x)$. Computing a complex power first and then taking its principal logarithm can wrap the phase and evaluate the wrong expression.
2. **Use the same prime-power cutoff throughout this experiment.** For $2\le x\le100$, the Möbius sum uses $m\le6$ everywhere. The exact $J(y)$ vanishes below 2, but its finite approximation need not. Changing the cutoff as $x$ moves can therefore introduce artificial jumps.
3. **Distinguish numerical error from truncation error.** Agreement between two implementations of the same finite formula checks the numerical evaluation. Agreement with the prime staircase measures what is lost by retaining finitely many zeros. Neither check is a proof about every zero.

Useful next experiments are to move the close-up from $20$–$40$ to $60$–$80$ while keeping the same zero count, compare behavior at primes and prime powers, and test how smoothing the zero cutoff changes the ringing. Extending the computation beyond 100 also requires revisiting the prime-power cutoff and the accelerated evaluator's numerical settings. Each experiment asks a precise question that the code can help answer.

## Sources and further reading

[^feynman]: Caltech Magazine, [“Biology through the Eyes of a Physicist”](https://magazine.caltech.edu/post/biology-through-the-eyes-of-a-physicist), July 2021. Records the quotation found on Feynman's blackboard.
[^lean]: Lean FRO and Mathlib Initiative, [“Lean verification of the Riemann Hypothesis”](https://leanprover-community.github.io/blog/posts/riemann-hypothesis/), November 21, 2026.
[^verification]: Andrew Sutherland, MIT, [“Verification files for the Lean proof of the Riemann Hypothesis”](https://math.mit.edu/~drew/grh/), record consulted November 24, 2026. Includes the precise scope of the five verified statements.
[^announcement]: Levent Alpöge, [announcement of the formal proof](https://alpo.ge/remark.pdf), November 20, 2026. The [community repository](https://github.com/leanprover-community/riemann-hypothesis) maintains the formalization.
[^openssl]: OpenSSL 3.5 documentation, [BN_generate_prime](https://docs.openssl.org/3.5/man3/BN_generate_prime/).
[^nist]: NIST, [FIPS 186-5: Digital Signature Standard](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.186-5.pdf), especially the prime-generation and primality-testing appendices.
[^aks]: Manindra Agrawal, Neeraj Kayal, and Nitin Saxena, [“PRIMES is in P”](https://annals.math.princeton.edu/2004/160-2/p12), *Annals of Mathematics* 160 (2004), 781–793.
[^rsa]: Ronald Rivest, Adi Shamir, and Leonard Adleman, [“A Method for Obtaining Digital Signatures and Public-Key Cryptosystems”](https://people.csail.mit.edu/rivest/Rsapaper.pdf), 1978.
[^rsa-problem]: Ronald Rivest and Burt Kaliski, [“RSA Problem”](https://people.csail.mit.edu/rivest/pubs/RK03.prepub.pdf), 2003.
[^x25519]: A. Langley, M. Hamburg, and S. Turner, [RFC 7748: Elliptic Curves for Security](https://www.rfc-editor.org/rfc/rfc7748.html), 2016, especially Sections 4.1 and 6.1.
[^hashing]: MIT 6.006, [Recitation 4: Hashing](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/bd220fb629aefdf30f416b5abf45d38d_MIT6_006S20_r04.pdf), Spring 2020.
[^galileo]: K.-M. Cheung, M. Belongie, and K. Tong, [“End-to-End System Consideration of the Galileo Image Compression System”](https://ipnpr.jpl.nasa.gov/progress_report/42-126/126E.pdf), JPL TDA Progress Report 42-126, 1996.
[^pnt]: NIST Digital Library of Mathematical Functions, [Section 27.12: Asymptotic Formulas—Primes](https://dlmf.nist.gov/27.12), especially Equation 27.12.7 for the explicit RH-equivalent error bound.
[^li]: NIST Digital Library of Mathematical Functions, [Section 6.2: Exponential and Logarithmic Integrals](https://dlmf.nist.gov/6.2), especially Equation 6.2.8.
[^zeta]: NIST Digital Library of Mathematical Functions, [Section 25.2: Definition and Expansions](https://dlmf.nist.gov/25.2), for the Dirichlet series, continuation, alternating representation, and Euler product.
[^zeros]: NIST Digital Library of Mathematical Functions, [Section 25.10: Zeros](https://dlmf.nist.gov/25.10).
[^odlyzko]: Andrew Odlyzko, [Tables of zeros of the Riemann zeta function](https://www-users.cse.umn.edu/~odlyzko/zeta_tables/), specifically the [first 100,000 zero heights](https://www-users.cse.umn.edu/~odlyzko/zeta_tables/zeros1), of which this experiment uses the first 10,000.
[^explicit]: Bernhard Riemann, [“On the Number of Prime Numbers less than a Given Quantity”](https://www.maths.tcd.ie/pub/HistMath/People/Riemann/Zeta/EZeta.pdf), 1859, English translation by David R. Wilkins. For a modern statement of the formula with the constant, integral correction, and Möbius inversion, see [“Riemann's explicit formula, one zero at a time”](https://math.ucr.edu/home/baez/mathematical/riemann_explicit_formula/riemann_explicit_formula.html), hosted by John Baez at UC Riverside.
[^bombieri]: Enrico Bombieri, “The Riemann Hypothesis,” in the Clay Mathematics Institute's [*The Millennium Prize Problems*](https://www.claymath.org/wp-content/uploads/2022/02/MPPc.pdf), for the equivalent prime-counting error formulation and mathematical context.
[^primecount]: Jan Büthe, [Analytic computation of the prime-counting function](https://www.math.uni-bonn.de/people/jbuethe/topics/AnalyticPiX.html).
[^platt]: David J. Platt, [“Computing $\pi(x)$ Analytically”](https://arxiv.org/abs/1203.5712), describing the unconditional verification of $\pi(10^{24})$.
