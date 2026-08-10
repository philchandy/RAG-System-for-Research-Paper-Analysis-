# The Primes Contain Arbitrarily Long Arithmetic Progressions

## problem
- It was a long-standing, "classical"/folklore conjecture, dating back to at least Lagrange and Waring's investigations around 1770 (as recorded in Dickson's *History*) and formalized as a special case of Hardy and Littlewood's 1923 conjecture, that the primes contain arbitrarily long arithmetic progressions.
- Prior to this paper, the only proven case was k = 3 (three-term progressions), shown by van der Corput in 1939 using Vinogradov's method of prime number sums; the existence of longer progressions (even k = 4) remained completely open except for upper bounds.
- Partial results were known for *almost* primes — e.g. Heath-Brown's four-term progressions consisting of three primes plus a number that is prime or a product of two primes — which motivated the strategy of working with a larger, better-behaved set than the primes themselves.

## method
- The proof rests on three main ingredients: (1) Szemerédi's theorem, which states that any subset of the integers with positive density contains arithmetic progressions of arbitrary length; (2) a novel "transference principle" — the paper's main new contribution — which extends Szemerédi's theorem to any subset of positive relative density within a sufficiently pseudorandom set or measure; and (3) a result of Goldston and Yıldırım (reproduced here) used to place a positive-relative-density subset of the primes inside a pseudorandom set of "almost primes."
- Pseudorandomness of a measure ν on Z_N is defined by two explicit conditions: the *linear forms condition* and the *correlation condition*. The central theorem (Theorem 3.5) says that, for the purposes of Szemerédi's theorem and up to o(1) errors, a k-pseudorandom measure is indistinguishable from the constant measure.
- The argument works in the finitary setting of Z_N (integers mod a prime N) rather than the classical infinite ergodic-theory framework, borrowing the language and many tools of ergodic theory while incurring o(1) error terms instead of taking weak limits (and thereby avoiding the axiom of choice).
- The proof of Theorem 3.5 decomposes f into a Gowers-uniform part plus a bounded Gowers anti-uniform part plus negligible error: the uniform part contributes nothing by a generalised von Neumann theorem, and the anti-uniform part is handled by ordinary Szemerédi. The decomposition is built by a Furstenberg-tower-style iteration that terminates in boundedly many steps because each step gives a quantitative L² energy increment.
- The majorant ν is built from Goldston–Yıldırım truncated divisor sums Λ_R rather than from the von Mangoldt function directly, since verifying pseudorandomness for Λ itself would be as hard as the Hardy–Littlewood prime tuples conjecture.
- A "W-trick" removes the arithmetic obstructions to pseudorandomness caused by small prime divisors: the primes are restricted to the residue class n ≡ 1 (mod W), where W is the product of all primes below a slowly growing w(N). (This is a variant of an older device, described in §2, of passing to a subprogression of common difference 2 × 3 × 5 × ⋯ × w(N), which raises the primes' effective density from about 1/log N to about log log N / log N. That density gain is what one would need if attacking Theorem 1.1 through improved Szemerédi bounds; the §9 W-trick is used instead for pseudorandomness, not density.)

## dataset
- This is a pure mathematics proof paper with no experimental dataset. It cites known numerical examples of long prime arithmetic progressions as context, including the longest known at the time of writing — a length-23 progression found in 2004 by Markus Frind, Paul Underwood, and Paul Jobling (56211383760397 + 44546738095860k for k = 0,…,22) — and an earlier length-22 progression found by Moran, Pritchard, and Thyssen (11410337850553 + 4609098694200k for k = 0,…,21).

## results
- Theorem 1.1: the prime numbers contain infinitely many arithmetic progressions of length k, for every k.
- Theorem 1.2 ("Szemerédi's theorem in the primes"): any subset of the primes with positive relative upper density contains infinitely many arithmetic progressions of length k, for every k.
- Theorem 3.5 (Szemerédi's theorem relative to a pseudorandom measure): the general transference statement from which 1.1 and 1.2 follow, and the result the authors identify as the paper's main new contribution.
- As a byproduct, the argument yields a quantitative lower bound of (γ(k) + o(1))N²/log^k(N) for the number of k-term prime arithmetic progressions up to N, for some unspecified, very small γ(k) > 0 — weaker than the precise asymptotic constant C_k conjectured by Hardy and Littlewood, which the paper does not establish. Standard sieve arguments give a matching upper bound O_k(N²/log^k N), so the lower bound is off only by a constant depending on k.
- §11 notes that w(N) need not actually grow with N but can be taken to be a fixed (very large) constant depending only on k, so the loss incurred by the W-trick is bounded uniformly in N.
- Applying Theorem 1.2 to the primes p ≡ 1 (mod 4) yields the previously unknown result that there are arbitrarily long arithmetic progressions of numbers expressible as a sum of two squares.

## limitations
- The proof explicitly relies on Szemerédi's theorem as a "large" external ingredient rather than proving it from scratch; the paper describes itself as self-contained modulo this one caveat, plus (per footnote 2) standard analytic number theory: the prime number theorem, Dirichlet's theorem on primes in arithmetic progressions, and the classical zero-free region for the Riemann ζ-function.
- The paper does not make progress on the famous open problem of finding the correct quantitative dependence of N₀(δ, k) (the threshold size in Szemerédi's theorem) on δ and k; the transference argument works regardless of which bound for N₀(δ, k) is used, but consequently does not improve or resolve it.
- The paper only establishes a lower bound on the count of k-term prime progressions with a small, unspecified constant γ(k), not the precise asymptotic count with the explicit constant C_k conjectured by Hardy and Littlewood. The bound on γ(k) is described as extremely poor, partly because of the growth of constants in the best known Szemerédi bounds and partly because the o(1) decay rates were not optimised.
- The methods yield no progress on the Hardy–Littlewood prime tuples conjecture; verifying pseudorandomness for the von Mangoldt function directly is described as strictly harder than the paper's main theorem.
- Suggested extensions — a Bergelson–Leibman-type polynomial result for primes, constellations in the Gaussian primes, affine subspaces among monic irreducibles over a finite field — are conjectured rather than proved, and would require non-trivial modifications (notably because characteristic factors for those generalizations are much less well understood). Footnotes added in press record that the first two were subsequently obtained elsewhere.

## follow_up_questions

Answerable from the paper:
- Q: What is the main theorem proved in this paper?
  A: That the prime numbers contain infinitely many arithmetic progressions of length k, for every k (Theorem 1.1).
- Q: What are the three main ingredients of the proof?
  A: Szemerédi's theorem, a new transference principle (the paper's main new contribution), and a result of Goldston and Yıldırım used to embed the primes in a pseudorandom set of "almost primes."
- Q: Who first proved the existence of infinitely many three-term (k = 3) arithmetic progressions of primes, and when?
  A: Van der Corput, in 1939, using Vinogradov's method of prime number sums.
- Q: What was the longest known arithmetic progression of primes at the time the paper was written?
  A: A progression of length 23, found in 2004 by Markus Frind, Paul Underwood, and Paul Jobling.
- Q: What generalized theorem, analogous to Szemerédi's theorem but for the primes, does the paper prove?
  A: Theorem 1.2: any subset of the primes with positive relative upper density contains infinitely many arithmetic progressions of length k for all k.

Not answered in the paper:
- Q: What is the exact numerical value of the constant γ(k)?
  A: Not given — only "some very small γ(k) > 0," with the paper noting the bound it could extract would be extremely poor and that no attempt was made to optimise it.
- Q: Does the paper resolve the quantitative dependence of N₀(δ, k) in Szemerédi's theorem?
  A: No — the paper explicitly states this remains a famous open problem, and notes that its own proof needs no quantitative estimate on N₀(δ, k) at all.
- Q: Does the paper give an explicit algorithm or bound for locating a k-term progression of primes below some N?
  A: No — the result is an infinitude/counting statement; no effective search bound is derived.
