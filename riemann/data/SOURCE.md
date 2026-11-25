# Zeta-zero data

`odlyzko_zeros_10000.txt` contains the first 10,000 positive imaginary parts
of the nontrivial Riemann zeta zeros, taken from Andrew Odlyzko's public
table of the first 100,000 zeros. The decimal values are preserved; only
the first 10,000 entries are included.

- Author: Andrew Odlyzko.
- Table index: <https://www-users.cse.umn.edu/~odlyzko/zeta_tables/>.
- Original text: <https://www-users.cse.umn.edu/~odlyzko/zeta_tables/zeros1>.
- Compressed original: <https://www-users.cse.umn.edu/~odlyzko/zeta_tables/zeros1.gz>.
- Source-stated absolute accuracy: within $3\times10^{-9}$ per height.
- First entry: `14.134725142`.
- Entry 10,000: `9877.782654004`.

Each value $\gamma_n$ specifies the conjugate pair
$\tfrac12+i\gamma_n$ and $\tfrac12-i\gamma_n$. Thus 10,000 rows supply
10,000 zero pairs, or 20,000 nontrivial zeros in the explicit formula.

The generator checks the file's length, positivity and ordering, then
records its SHA-256 hash in `../validation.json`. Those checks concern file
integrity and numerical reproducibility; they are not a new certification
of the zero locations or a proof of the Riemann hypothesis.
