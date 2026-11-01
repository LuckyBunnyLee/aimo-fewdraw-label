# SHAM Phase 1: ready for a fresh verifier (W9b, 25 Oct 2026)

**Request.** Verify the frozen amendment and its code before CL admits Phase 1 to the 5070. Nothing has run on a GPU; W9b launches nothing.

**Freeze:** `SHAM1-FREEZE.sha256`, sha `836184893a15bbe8ef0c124f29538e9e3ab72aed0a44571dd25dcf4932a9a45b`, 15 files. Verify it first.

**Read:** `SHAM-PHASE1-AMENDMENT-20261025.md`, then the code. The original frozen design is `../decomp/SHAM-SPEC-20261025.md` (Phase 1 section, `019827a0…`).

## What to check (CPU; each takes seconds to minutes)
1. **Pool and cohort.**
   - Rebuild: copy `build_phase1.py` to an empty folder and run it with `python -I`. The four output shas must match the freeze.
   - The rebuild re-checks that the 2,474 reached originals are the first 2,474 of the roster's hash order, and that `COHORT.json` was chosen without reading tags.
2. **Requests.**
   - 15 waves × 320 × 5 × 4 = 96,000 requests.
   - The sham texts are byte-identical to the base text.
   - Seeds follow the fresh6h rule, and there is no overlap with fresh6h identities.
   - The endpoint settings and template sha are fresh6h's.
3. **Run control.**
   - `python -I test_wave_core.py` must print `ALL PASS` (7 cases).
   - Read `wave_core.run_block` and `boundary`. Check that the pause, abandonment and make-up rules are outcome-blind, and that no identity can be issued twice.
4. **Runner.**
   - `wave_runner.py` should match CL's runner (`explore/CL-5070-recovery-20261020-1740/ready63-reliability/run_overnight.py`, `e8360555…`) in environment, resource guard, model binding, template check and `LLM(...)` arguments.
   - It cannot be exercised here (vLLM, WSL, GPU). Flag any difference that would change the endpoint.
5. **Scorer.**
   - `python -I score_phase1.py selftest` and `python -I score_phase1.py dryrun` must both print `ok`.
   - Check that the primary, the calibration rule and the reading match amendment section 3, and that `run` refuses a second scoring.
6. **Power [C].** `power_phase1.py` reproduces `POWER-PHASE1.json`. Write the output to a fresh folder, since the script exclusive-creates its JSON.
7. **Judgement calls to rule on:**
   - the reached set as the pool, not the roster;
   - Δ_solve against the sham copies as the primary;
   - ≥ 3 waves for tag eligibility;
   - three make-up waves;
   - pause latency of up to one wave.

## For CL at admission (not part of the freeze)
- Copy these files into a new run folder: `MANIFEST.json`, `REQUESTS.json`, `TRUTHS.json`, `wave_runner.py`, `wave_core.py` and `request_core.py`.
- Write `ADMISSION.json` with:
  - `generation_authorized: true`;
  - `base_manifest_sha256` = sha of `MANIFEST.json`;
  - `code_sha256` for the three .py files;
  - `model_path`, `max_model_len` 8192, `capture_sizes` [1, 2, 4, 8, 16, 32], `cache_root`;
  - `absolute_deadline`.
- Launch `wave_runner.py` in the vLLM environment, as for READY63.
- **Pause for CVPR:** `touch PAUSE` (up to one wave, about 80 min). **Urgent:** `touch STOP_NOW`. **Resume:** remove the file and relaunch. **Status:** `python wave_core.py status <RUN>`.
- **After the final EXIT,** W9b scores once: `python -I score_phase1.py run <RUN>`.
