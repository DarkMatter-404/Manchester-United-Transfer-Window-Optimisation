# Toy inputs

Eight invented players used only to test the formulation. No number here describes a real player.

- `players.csv`: one row per player. `status` is `E` (existing), `C` (candidate) or `K` (fixed arrival). `fee` applies to candidates and `receipt` to existing players, both in GBP million. `wage` is in GBP million per year. `homegrown` and `senior_reg` are 0/1 flags. `availability` is between 0 and 1. `development` is in score points.
- `roles.csv`: one row per eligible player-role pair with its quality score (0-100).

The registration flags do not affect the two basic checks, where the limits of 25 and 17 cannot bind with three players. They are used by the registration checks in `src/toy_model.py`, which also adds one fixed arrival and one versatile player in code.
