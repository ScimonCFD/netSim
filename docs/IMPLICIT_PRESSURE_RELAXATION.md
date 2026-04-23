**Implicit Pressure Relaxation**
`netSim` solves a pressure-correction equation of the form:

```text
A p' = b
```

For the implicit relaxation mode, we define the relaxed correction through:

```text
p' = p'^* + alpha (p'_(new) - p'^*)
```

where:
- `p'` is the unrelaxed pressure correction,
- `p'^*` is a predictor for the pressure correction,
- `p'_(new)` is the new relaxed correction,
- `alpha` is the pressure-relaxation factor.

Expanding and regrouping:

```text
p' = alpha p'_(new) + (1 - alpha) p'^*
```

Substituting into the original linear system:

```text
A [alpha p'_(new) + (1 - alpha) p'^*] = b
```

Distributing `A`:

```text
alpha A p'_(new) + (1 - alpha) A p'^* = b
```

Moving the predictor term to the right-hand side:

```text
alpha A p'_(new) = b - (1 - alpha) A p'^*
```

Dividing by `alpha`:

```text
A p'_(new) = b/alpha - ((1 - alpha)/alpha) A p'^*
```

This is the form implemented in the implicit relaxation option:
- the matrix `A` is kept unchanged,
- the right-hand side is modified consistently using the predictor `p'^*`.

For the current implementation, `p'^*` is taken as the pressure-correction vector from the previous outer iteration of the same solve stage.
