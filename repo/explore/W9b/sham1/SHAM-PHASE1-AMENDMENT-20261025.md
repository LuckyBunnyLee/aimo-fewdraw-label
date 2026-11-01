# SHAM Phase 1 amendment: pool, endpoints, eligibility and wave checkpoints (W9b, 25 Oct 2026)

**Status:**
- EXPLORATORY. CPU only up to admission.
- Frozen with `SHAM1-FREEZE.sha256` before any Phase 1 request exists on a GPU.
- It amends Phase 1 of `explore/W9b/decomp/SHAM-SPEC-20261025.md` (sha `019827a0…`, frozen 25 Oct 02:30 PT). Phase 0 and its result are unchanged.
- The lead chose this item on 25 Oct; CL admits it on a fresh verifier's PASS. W9b launches nothing.

**What changes from the frozen Phase 1, and why:**
- **Pool:** "the 2,657 reached" is replaced by **the 2,474 reached** (section 1). The spec's figure was the roster.
- **Primary endpoint:** the all-answer solve change against identical-text copies (section 3). The spec's tag contrast P1 becomes a secondary. The report's conclusion recommends this measure, and it needs no eligibility rule, so it covers every sampled problem.
- **Eligibility rule** for the tag secondaries is frozen: ≥ 3 waves. The spec's ≥ 1 rule is kept as a named sensitivity.
- **Within-wave order** is a seeded random permutation, stronger than "the same order positions".
- **Run control:** checkpoints at every wave boundary, so CL can pause for the CVPR jobs (C2H, P4 Stage 1) and resume. Interrupted waves are abandoned, and three make-up waves are pre-built (section 4).

Everything else stands as frozen: endpoint, design, per-wave content, caps (20 GPU-h, 90M tokens), ≥ 8 whole waves or "not measured", and the independence check.

## 1. Pool: the 2,474 reached originals
**[D]** The fresh6h roster is 2,657 originals in SHA256(seed|id) order (`ROSTER.json`, seed 202610210935). Requests were queued in roster order, verified in `build_phase1.py`. The compute block ended after the first 2,474 originals, so **the unreached 183 are exactly the last 183 in hash order**.

Either set is therefore an outcome-blind, hash-random sample, but the reached set is the better pool:
1. It is the population the report's fresh test describes, with its 1,255 binary problems. Phase 1 results then attach to the same population.
2. Every pool member has a fresh6h primary tag, so the S1 stratification (UNUSABLE vs binary) is defined for all 320.
3. Nothing is lost on randomness: a prefix of a hash order is as random as the whole.

The roster would add only 183 problems with no fresh6h tag.

**Selection:**
- The first 320 of the 2,474 by SHA256("20261025|" + problem_id).
- Fresh6h tags are not read by this rule. They are copied into `COHORT.json` afterwards, for S1 only.
- Resulting mix (descriptive): UNUSABLE 153, R 124, NR 41, FLOOR 2. The pool has 49% UNUSABLE, the cohort 48%.

## 2. Requests (`build_phase1.py`, deterministic)
- **Inputs:** fresh6h `REQUESTS.json` (`daccdc4f…`), `TRUTHS.json` (`b06a6f45…`), `ROSTER.json` (`b75af74a…`) and `MANIFEST.json` (`67d42df9…`), and W9b `fresh6h/out/PER-ORIGINAL.jsonl` (`0e6a6657…`), all read-only and sha-checked. Texts, system prompt and settings come from each original's fresh6h replicate-0 requests.
- **Versions:** five, with four draws each per wave.
  - `base` is the original text.
  - `surface_gs` and `surface_dlm` are the two renames.
  - `sham_a` and `sham_b` are **byte-identical copies of the base text** (asserted). They have their own family and variant ids, so their identities and seeds differ.
- **Identity and seed:**
  - Protocol `W9b-sham-phase1-20261025`; replicate = 4·wave + r.
  - seed = first 16 hex digits of the identity sha, masked to 63 bits (the fresh6h rule).
  - No identity overlaps fresh6h.
- **Order:** waves are contiguous blocks of 6,400 requests. Within wave w, originals are in a seeded shuffle (`sham1-order-20261025|wave{w}`), and each original's five four-draw blocks are in a seeded random permutation. Real and sham versions therefore share the wave, the time and, in expectation, the position.
- **Size:** 15 waves are built, 96,000 requests: 12 planned plus 3 make-up waves, issued only to replace abandoned waves. The planned run is still 12 × 6,400 = 76,800 requests.
- **Endpoint:** unchanged from the report. Qwen3.5-4B rev `851bf6e8…`, no-think, T 1, top-p 0.95, top-k 40, cap 4,096, template sha `12de9034…`, max 32 active, vLLM continuous batching, prefix caching on. The sham prompts share the base prefix cache; caching changes compute, not the per-request seeded sampling.

## 3. Analysis (`score_phase1.py`, frozen; scored once)
**Data:** the first 12 complete waves in index order (fewer if the run ends early). With fewer than 8 complete waves the reading is "not measured". Per version, p is the **all-answer** solve rate over 4·W draws: any non-correct answer, numeric or not, counts as unsolved.

**Primary:**
- Δ_solve = mean_i [ (p_sham_a + p_sham_b)/2 − (p_gs + p_dlm)/2 ] over all 320 originals.
- 95% original-bootstrap CI: 2,000 resamples, seed 20261025.
- The base cancels, so the comparison is between rewrites and identical-text copies drawn in the same waves under their own request ids.

**Calibration, required before the primary is read as an edit effect:**
- **CAL1:** mean_i [ p_base − (p_sham_a + p_sham_b)/2 ], whose 95% CI must contain 0.
- **CAL2:** per-original z for base vs sham_a, base vs sham_b and sham_a vs sham_b. The share with |z| > 1.96 must be ≤ 0.10; independent draws give about 0.05. This is the spec's P3 sham-contrast rule.

**Reading:**
- If either calibration fails: "calibration failed: not read as an edit effect". The primary is still reported.
- Otherwise:
  - CI lower bound > 0: "edit loss in solve probability";
  - CI upper bound < 0: "edit gain";
  - else: "not resolved".

**Secondaries:**
- **S, the report's metric:** δ = mean_i [ p_base − (p_gs + p_dlm)/2 ], with CI, and τ by method of moments as in DECOMP D1.
- **Tags:** per wave, real = tag(base, gs, dlm) and sham = tag(base, sham_a, sham_b), with the same base draws and the same wave, using the frozen `fresh81_pure.tag`.
  - **T1 (joint eligibility):** originals with ≥ 3 waves binary for both tags. NR rates over those waves; real, sham, difference and ratio, each with a CI.
  - **T2 (own eligibility):** originals with ≥ 3 binary waves for each tag, each tag over its own waves.
  - **T3:** T2 with the spec's ≥ 1 rule.
  - **T4:** mean(NR_sham − N0(p̂_b)) over T2 originals, with p̂_b the base accuracy among numeric answers over the scored waves; ±0.03 rule.
- **Selection displays (descriptive):** the share of originals eligible under T1, and Δ_solve for T1-eligible vs ineligible originals.
- **S1:** Δ_solve for originals whose fresh6h tag was UNUSABLE vs the rest.

**Why ≥ 3:** the threshold is set now, before any Phase 1 record exists. At 12 waves, the report's ≥ 5 would drop many problems (fresh6h was 49% UNUSABLE). A single binary wave gives a 0-or-1 rate, so ≥ 1 stays as a sensitivity (T3).

**Outputs:** `out/RESULT.json`, `out/DRAWS.jsonl` and `out/SCORE-ONCE-STARTED.json` (exclusive create). Every record is bound to its frozen request (identity, seed, request sha, record sha in WAVE-COMPLETE).

**Checks:**
- `selftest` plants a null, a 0.06 edit loss with 40% partly unusable problems, and a 0.08 sham shift; it must read "not resolved", "edit loss" and "calibration failed".
- `dryrun` runs 10 originals end to end through `wave_core` with a fake engine, including one STOP_NOW. Wave 3 was abandoned, make-up wave 12 replaced it, 12 waves were scored, and the binding passed.

## 4. Run control: checkpoint at every wave boundary
`wave_runner.py` is CL's READY63/fresh6h runner environment (resource guard, cgroup, model binding, vLLM settings) around `wave_core.run_block()`. One process is one block.

**Rules (`wave_core.py`, tested in `test_wave_core.py`):**
- **Wave records:** waves run whole and in index order. A wave opens with `WAVE-STARTED-w.json`. It closes with `WAVE-COMPLETE-w.json`, which lists every record sha and is written only when all 6,400 requests have terminal records in that block. `CHECKPOINT-w.json` follows.
- **Boundary checks,** in frozen order: planned waves done → stop "complete"; no unstarted wave → "wave_pool_exhausted"; `PAUSE` → "paused_at_wave_boundary"; `STOP_NOW`; token cap; GPU-hour cap; deadline.
- **Projections:** the token, GPU-hour and deadline checks project one more wave at 1.25 × the largest wave so far (first wave: 6.4M tokens, 2 h), so caps stop at a boundary, not inside a wave.
- **Stops inside a wave:** `STOP_NOW`, an engine error, the deadline, a hard token cap or CL's resource reserve end the block at once. That wave is **abandoned**: started, never complete, records kept, never scored, identities never reissued. The next block starts the next unstarted wave, so make-up waves 12–14 replace up to three abandoned waves.
- **Killed blocks:** a block that died without `EXIT.json` blocks every resume until CL runs `python wave_core.py seal R/block-<id>`. The seal only records what is on disk.
- **Outcome-blind:** pausing, abandonment and make-up depend only on operator files, time and token counts, never on outcomes. Real and sham versions share every wave, so a pause gap between waves affects both equally.

**Operator use for the CVPR jobs:**
- **To pause:** `touch R/PAUSE`. Latency is up to one wave, about 80 min at the measured rate. The process exits and the GPU is free.
- **Urgent:** `touch R/STOP_NOW`. Exit is within seconds, at a cost of up to one wave (about 1.3 GPU-h) and one make-up wave.
- **To resume:** remove the file and relaunch `wave_runner.py` unchanged.
- **Status:** `python wave_core.py status R`.

PAUSE is preferred: three urgent stops use up the make-up pool.

**Caps and cost:**
- 20 GPU-h and 90M tokens, summed over blocks. GPU-h counts block wall-clock, including model load, and not paused time.
- Estimate: 15.5 GPU-h on the 5070 (12–19 h), from READY63's measured 1,375 tokens/s and about 1,000 tokens per fresh request.
- Each resume adds a model load of a few minutes.

**Test (`test_wave_core.py`, CPU, fake engine), all PASS:**
- a clean 12-wave run;
- pause at a boundary, then resume;
- STOP_NOW abandons a wave and a make-up wave replaces it;
- an engine error abandons the wave and raises;
- a killed block refuses resume until it is sealed;
- the token cap stops at a boundary;
- the make-up pool can be exhausted.

No identity is ever issued twice. The test writes only temporary folders and removes them.

## 5. Power [C] (`power_phase1.py` → `POWER-PHASE1.json`)
**Simulation:**
- 320 originals resampled from the 34 READY63 all-answer rates, with sham = base.
- True mean effect 0.044. At 12 waves, P(CI lower bound > 0) = 1.00 and the mean CI half-width is 0.013, so the approximate MDE is 0.018 (80%, two-sided 5%).
- At 8 waves, the power is 1.00 and the half-width 0.013.
- Under the null, either-direction resolution happens 0.053 of the time at 12 waves and 0.048 at 8.

**Caveat:** the fresh pool's effects are unknown. The half-width is mostly between-problem spread, taken here from READY63.

## 6. Freeze, admission, score-once
- **`SHAM1-FREEZE.sha256` lists:** this amendment, `build_phase1.py`, `COHORT.json`, `REQUESTS.json`, `TRUTHS.json`, `MANIFEST.json`, `wave_core.py`, `wave_runner.py`, `request_core.py` (CL's, unchanged, `49d2049a…`), `score_phase1.py`, `test_wave_core.py`, `power_phase1.py`, `POWER-PHASE1.json`, and the scorer's imports `fresh81_pure.py` and `decomp.py`.
- **CL stages:** CL copies the run files into its own run folder and writes `ADMISSION.json`. It holds `generation_authorized`, `base_manifest_sha256` (= `MANIFEST.json` sha), `code_sha256` for `wave_runner.py`, `wave_core.py` and `request_core.py`, `model_path`, `max_model_len` 8192, `capture_sizes`, `cache_root` and `absolute_deadline`. The runner refuses on any mismatch.
- **After the final EXIT,** once only: `python -I score_phase1.py run <RUN>`. An independent replay, written after this freeze and before any output, is welcome from the verifier.
- **Deviations:** any change after the freeze is logged in `LAUNCH-NOTES.md` as a numbered deviation before the affected run, and never after outcomes are read.
