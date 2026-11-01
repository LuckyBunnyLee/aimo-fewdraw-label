# SHAM Phase 1 v1.1: fix check and CL admission (W9b, 25 Oct 2026)

**Request.** Confirm that V23's fixes 1–5 (`explore/V23/SHAM1-VERDICT.md`) are implemented as logged, and that nothing else changed. Nothing has run on a GPU. W9b launches nothing.

**Freeze:** `SHAM1-FREEZE-v1.1.sha256` in this folder; its sha is in the turn note and in `../LAUNCH-NOTES.md`. Verify it from this folder with `sha256sum -c`. The v1.0 freeze `../SHAM1-FREEZE.sha256` (`83618489…`) still verifies and is listed inside the v1.1 freeze.

**Read:** `SHAM-PHASE1-v1.1-ADDENDUM.md`, then the diffs: `diff ../wave_core.py wave_core.py`, `diff ../wave_runner.py wave_runner.py`, `diff ../score_phase1.py score_phase1.py`.

## CPU checks (seconds each; temp folders are kept, nothing is deleted)
1. `python -I test_wave_core.py` must print `ALL PASS`. It runs 12 cases, including the kill, cap and load cases.
2. `python -I contrast_v10.py` runs the same cap scenarios on the frozen v1.0 core. Expect 6.539 h on a 4.0 h cap and 31,300 tokens on a 30,000 cap.
3. `python -I test_admission.py` must print `ALL PASS`.
4. `python -I score_phase1.py selftest` and `python -I score_phase1.py dryrun` must both print `ok`.
5. Data: the four build outputs in the v1.1 freeze are the v1.0 hashes. `python -I ../build_phase1.py`, run in an empty folder as for v1.0, still reproduces them.

## For CL at admission (not part of the freeze)
1. **Copy** into a new run folder:
   - from this folder: `wave_runner.py`, `wave_core.py` and `SHAM1-FREEZE-v1.1.sha256`;
   - from `..`: `request_core.py`, `MANIFEST.json`, `REQUESTS.json` and `TRUTHS.json`.
2. **Write `ADMISSION.json`** with:
   - `generation_authorized: true`;
   - `base_manifest_sha256` (`3885f9da…`);
   - `freeze_sha256` = sha of `SHAM1-FREEZE-v1.1.sha256`;
   - `code_sha256` for exactly `wave_runner.py`, `wave_core.py` and `request_core.py`;
   - `model_path` = `/root/.cache/huggingface/hub/models--Qwen--Qwen3.5-4B/snapshots/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`;
   - `max_model_len: 8192`, `capture_sizes: [1, 2, 4, 8, 16, 32]`;
   - `cache_root` and `absolute_deadline`.
3. **CPU admit check** in WSL, which hashes the model files and launches nothing: `python wave_core.py admit-check <RUN> <freeze sha from the verifier's PASS>`. Then run CL's usual GPU preflight.
4. **Launch** `wave_runner.py` in the vLLM environment, as for READY63.
5. **Operator controls.**
   - **Pause for CVPR:** `touch PAUSE`. The run stops at the next wave boundary, which can take up to one wave (an estimate of about 80 min).
   - **Urgent:** `touch STOP_NOW`. The current wave is abandoned and a make-up wave replaces it.
   - **Resume:** clear the file and relaunch.
   - **Killed process:** `python wave_core.py seal <RUN>/block-<id>`, promptly, because dead time is charged. Then relaunch.
   - **Status:** `python wave_core.py status <RUN>`.
6. **After the final EXIT,** W9b scores once: `python -I score_phase1.py run <RUN>`, from this folder.
