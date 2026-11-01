# SHAM Phase 1, v1.1 addendum (W9b, 25 Oct 2026, written 12:45 PT, before any Phase 1 output exists)

**What this is.** V23 gave the frozen v1.0 design PASS-WITH-FIXES (`explore/V23/SHAM1-VERDICT.md`). Selection, pairing and the primary passed. GPU admission waits on fixes 1–3. This addendum implements fixes 1–5 and changes nothing else.

**Unchanged.** The v1.0 amendment (`../SHAM-PHASE1-AMENDMENT-20261025.md`, `1ec2e89d…`) still governs. That covers the pool, the cohort, the requests, the endpoint, the primary, the calibration rule, the secondaries, the 8-wave floor and the caps (20 GPU-h, 90M tokens). The build outputs are the v1.0 files, byte for byte: COHORT `a626ed85`, REQUESTS `68129da3`, TRUTHS `a17a313b`, MANIFEST `3885f9da`. No request was rebuilt.

**v1.0 is kept.** `../SHAM1-FREEZE.sha256` (`83618489…`) still verifies. The v1.1 code lives in this folder, and the new freeze is `SHAM1-FREEZE-v1.1.sha256`. Where this addendum and the amendment differ, this addendum wins.

## Fix 1: the 20 GPU-h cap is real (`wave_core.py`, `wave_runner.py`)
- **When the clock starts.** The runner records T0 at its first line. It then opens the block (`open_block`, which writes `START.json` with `started = T0`) before the tokenizer, model or engine load.
  - Model load, weight hashing and every load failure are therefore charged.
  - A failed load closes the block with reason `load_error` and its elapsed time.
- **Hard limit inside a wave.** The block stops, abandoning the wave, once used hours plus a 60 s shutdown margin reach the cap (`gpu_hour_cap_in_wave`).
  - Overshoot is bounded by one engine step. That is under a second on vLLM and well inside the margin.
- **Boundary projections are unchanged:** 1.25 × the largest wave so far.
- **CPU replay (`test_wave_core.py`, case "GPU-hour cap with load time and a slow wave").**
  - Setup: 0.5 h of load, then a wave far slower than the projection, on a 4.0 h cap.
  - v1.1 stops inside the wave, charging 3.9–4.0 h.
  - The same scenario on the frozen v1.0 core (`contrast_v10.py`) records 6.539 h on the 4.0 h cap. v1.0 also omits the load time.

## Fix 2: killed-block and token accounting are conservative (`wave_core.py`)
- **Submission ledger.** Before any request is submitted, its key is appended to the block's `ADMITTED.jsonl` and fsynced.
  - A torn final line was never fsynced, so its requests were never submitted.
  - Any other malformed line refuses resume.
- **What the operator seal charges.** The seal (`wave_core.py seal <block>`) charges a bound, not a count:
  - **tokens:** tokens in terminal records, plus `max_new_tokens` (4,096) for each admitted request without a record;
  - **hours:** process start to the seal time.
  - The seal refuses while the run lock (`OWNED.lock`) is held, which proves the process is dead.
  - Dead time before the seal is charged, so CL should seal promptly.
- **Exits.** Every `EXIT.json` carries `charged_tokens` and `charged_seconds`.
  - A clean stop charges the counted tokens.
  - An engine error, a load error or an interrupt charges the ledger bound.
  - `scan()` sums the charged values. It refuses to resume if any block lacks a ledger, an exit or a seal, or charged fields.
- **Hard token cap.** A request is submitted only if used tokens plus 4,096 for every active request (itself included) stay at or under 90M. No sequence of steps can then cross the cap.
  - If the cap blocks a needed submission, the block stops at once with `token_cap_in_wave`, and the wave is abandoned.
  - The reserve is at most 32 × 4,096 = 131,072 tokens, 0.15% of the cap.
- **Abandoned work.** Its records and identities are kept, never scored and never reissued, as in v1.0.
- **CPU replays.**
  - A child process killed mid-wave with `os._exit` refuses resume until sealed, and its seal charges exactly the bound.
  - Three kills with prompt seals, then a resume under a 240,000-token cap, keep the total charged at or under the cap.
  - An oversized wave stops inside the cap.
  - v1.0 on the same oversized-wave case records 31,300 tokens on a 30,000 cap (`contrast_v10.py`).

## Fix 3: admission binds the endpoint and the reviewed code (`wave_core.check_admission`, `wave_core.bind_model`, `wave_runner.py`)
- **Code.**
  - The runner hard-codes the sha256 of `wave_core.py` and `request_core.py` and checks both before importing either.
  - `ADMISSION.json` must name `freeze_sha256` (the sha of `SHAM1-FREEZE-v1.1.sha256`, copied into the run folder).
  - `wave_runner.py`, `wave_core.py`, `request_core.py`, `MANIFEST.json`, `REQUESTS.json` and `TRUTHS.json` in the run folder must match that freeze.
  - `code_sha256` must name exactly those three code files with the freeze's hashes; an empty or partial map is refused.
  - CL checks the freeze against the sha in the verifier's PASS with `python wave_core.py admit-check <RUN> <reviewed-freeze-sha256>`. This is CPU only and launches nothing.
- **Model.** `model_path` must be exactly `/root/.cache/huggingface/hub/models--Qwen--Qwen3.5-4B/snapshots/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, the path in the earlier ENGINE-CONFIG files.
  - The pinned hashes for config.json (`ddc63e1c…`), tokenizer_config.json (`316230d6…`) and tokenizer.json (`5f9e4d49…`) come from all 120 earlier CL MODEL-BINDING files for this snapshot (READY63, fresh6h).
  - Every `*.safetensors` file is hashed and must equal the name of its content-addressed blob in the Hugging Face cache. The shard index must list exactly the shards present.
  - **Disclosed limit:** no earlier record pins the weight hashes. The first block records them, and every later block must match them.
- **Engine.**
  - `max_model_len` must be 8192 and `capture_sizes` must be [1, 2, 4, 8, 16, 32].
  - After load, the vLLM config repr must contain the model path, `max_model_len=8192` and `dtype=torch.bfloat16`.
  - `MODEL-BINDING.json` and `ENGINE-CONFIG.json` are written to each block, as in the reference runner.
- **Before launch.** CL's GPU preflight still applies. W9b launches nothing.
- **CPU test (`test_admission.py`).** It accepts a correct admission and refuses each of the following:
  - an unreviewed freeze;
  - an empty or altered code map;
  - a wrong model path;
  - wrong engine arguments;
  - an edited `wave_core.py`;
  - a wrong snapshot revision, an altered tokenizer or an altered weight blob (fake snapshot with test-only pins).

## Fix 4: every outcome has a defined reading (`score_phase1.py`)
- **Ratio with zero real NR.** If the set's mean real NR is zero, the sham/real ratio is `null`, read as "undefined: no real-rewrite NR in this set (zero denominator)", with no CI. Otherwise any resamples with a zero denominator are left out and counted.
- **No eligible originals:** `n = 0`, read as "not estimable: no eligible originals".
- **CAL2 with zero variance.** If every sham contrast has zero variance, CAL2 is "not estimable". The primary is then read as "calibration not estimable: not read as an edit effect". In v1.0 this case failed calibration.
- **T4 empty:** `T4_calibrated_within_0_03 = null`, read as "not estimable … (not evidence against calibration)". This is distinct from "not shown within 0.03".
- **Serialisation.** The result is serialised with `allow_nan=False` before any output file is opened, so a NaN is an error and never a value.
- **Edge-case checks.** `selftest` adds three cases: all-perfect draws, no eligible originals, and zero real NR with nonzero sham NR. Each reading must hold, and the output must have no NaN. All secondaries remain descriptive.

## Fix 5: wording and provenance (no GPU)
- **Power [C]** (amendment section 5) is conditional on READY63 rates in a normal-CI simulation.
  - "Power 1.00, half-width 0.013, MDE ≈ 0.018" is the power of the CI to resolve an effect of 0.044.
  - It is not the power of the full calibrated rule, which also needs CAL1 and CAL2 to pass, and it does not use the scorer's bootstrap.
- **Roster order (amendment section 1).**
  - `build_phase1.py` verifies that the reached set is a prefix of the roster order. It does not verify that the roster is in SHA256(202610210935|id) order.
  - V23 checked the hash order separately and confirmed it.
- **Pause and pre-emption.** The PAUSE latency of about 80 min is an estimate, not a guarantee, and STOP_NOW is the urgent CVPR route. Abandonment is operational, but token and time censoring can correlate with difficulty, so it is not called independent of outcomes.
- **Sealed TEST.** The source is the pinned existing fresh6h roster. No Phase 1 code opens a sealed TEST split. Historical disjointness from sealed TEST rests on the fresh6h roster's approved provenance and is not re-proved here.
- **Deleting nothing.**
  - The v1.1 tests keep their temp folders and clear operator files by renaming them.
  - The only removal is the hard-linked staging name inside `put()`, whose content stays under the final name (as in v1.0).

## Not changed, and not run
- No GPU, no model and no Claude call was used.
- `wave_runner.py` still cannot be exercised on CPU (vLLM, WSL, GPU). Its new lines are the binding checks and the block open/close calls shown above.
