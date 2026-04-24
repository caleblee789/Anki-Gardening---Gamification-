# Critical Journey E2E Display Assertions

This suite locks down KPI display behavior for the highest-risk user journeys using deterministic seeded state.

## Top journeys covered

1. **Home load → dashboard KPI display**
   - Equivalent to the requested "login → dashboard" style journey for this local-first add-on.
   - Verifies exact displayed values for cards reviewed, garden health, growth, weather, and weekly event.
2. **Review session → progress/reward update → refresh**
   - Simulates post-review state changes (growth, streak, weather/event context).
   - Verifies updated KPI values and confirms they persist across refreshes.
3. **Navigation across home contexts (Deck Browser ↔ Overview)**
   - Verifies KPI values remain accurate when the widget is injected in different primary home contexts.
   - Ensures no duplicate widget insertion (idempotent navigation behavior).

## Deterministic test data strategy

- Uses a seeded `GardenState` with fixed plants, streak, weather, and growth values.
- Uses a fake Anki collection DB scalar return for cards reviewed today.
- Uses fixed engine outputs for health index and weekly event summary.
- Avoids non-deterministic data sources (system time drift, live Anki DB, external services).

## Assertion policy

- Assertions are strict string checks against the rendered HTML values (not mere element existence).
- Examples:
  - `Cards Today: 27`
  - `Garden Health: 86%`
  - `Growth today: 36/240`
  - `width:15%` for growth bar percentage

## CI execution policy

The workflow `.github/workflows/e2e-display-assertions.yml` runs these tests:

- on **every pull request**,
- on push to `main`,
- **nightly** via cron (`0 7 * * *` UTC),
- and manually via `workflow_dispatch`.
