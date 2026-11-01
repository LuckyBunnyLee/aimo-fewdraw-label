# Few-draw robustness labels: code and records

This is the code and record release for the report *Our few-draw robustness label mostly measures solving noise, not edit sensitivity* (AIMO Interpretability Challenge, NeurIPS 2026 competition workshop).
The report tests a strict "fragile under rewriting" label on maths problems (Qwen3.5-4B, problems from DeepMathGAP). Its main experiment compares real rewrites against byte-identical copies of the original problem.
The folder also holds a constant-robust baseline implementation, the frozen local Small-track bundle described under "Competition bundle". It is not evidence for the report.

## Layout

- `repro/`: three short scripts that check the report against the released files (below).
- `repo/`: exact copies of the original files, under their original repository paths, which are the paths the report's Appendix A cites. These archived scripts contain absolute paths from the machine they ran on (`E:\work\research-cycle\...`). Only the three `repro/` wrappers below are portable.
- `submission/`: the competition bundle and its sha256.
- `DATA-MANIFEST.md`: every input of the report build, with sha256, size and availability. If a file is withheld, the manifest says why.
- `DATA-NOTICE.md`: licence and attribution for the records derived from DeepMathGAP.
- `MANIFEST.sha256`: a hash for every published file except itself. Check it with `sha256sum -c MANIFEST.sha256`.

## What this release reproduces

The release recomputes Section 4/Table 1 from released draw records and redraws Figure 1. It verifies 419 stored report values, including 173 checks against released upstream results; it does not independently rerun every reported analysis.

Appendix J is not reproduced in this release because the request/answer-key inputs are withheld. The archived make_*.py and generation scripts retain historical paths and are not made portable by the three repro wrappers. Request-level parsing/correctness and original request-to-draw binding cannot be re-audited from the released correctness-only draws.

## Setup

Use Python 3.12 and run `pip install -r requirements.txt`. The pinned requirements cover the three CPU checks below. They are not a complete environment for the archived generation programs, which need vLLM, Transformers, PyTorch and a GPU. Once the requirements are installed, the checks run on CPU in seconds with no model, GPU or network.

## The three CPU checks

Run these from this folder. The `Expected` lines are what we got on 30 Oct 2026 with the pinned versions. The full output is in `repro/EXPECTED-OUTPUT.txt`.

**1. Section 4 and Table 1 (prospective identical-text control): recomputed.** This runs the frozen scorer's `analyse()` on the 76,800 released draw records. It then compares every value, including all 320 per-problem rows, with the scorer's original `RESULT.json`.

    python -B repro/reproduce_prospective.py

Expected:

    PRIMARY solve loss, rewrites vs identical copies: 0.052 [0.040, 0.065]
    CAL1 original minus copies: 0.0013 [-0.0049, 0.0072]
    CAL2 share |z|>1.96: 0.0456 of 767 tests (pass)
    T1 eligible: 207 problems (64.7%)
    T1 fragile rate, copies: 0.183 [0.150, 0.218];  real rewrites: 0.235 [0.197, 0.273]
    compared with the scorer output RESULT.json: ALL MATCH

**2. Figure 1: redrawn.** This runs the exact figure script with only its paths redirected, and writes `repro/out/fig1_tag_null_sham_v4b.png`.

    python -B repro/fig1.py

Expected: the PNG has sha256 `781974c38833a8086213c4faa9b6e3c400ce4aef568ced52670d7ce95f3a508a`, byte-identical to the report figure (`repro/expected/`). Panel (b) has 207 problems, with mean fragile rate 0.183 for the copies and 0.235 for the real rewrites. The PNG bytes can differ with another matplotlib version or other fonts.

**3. The other report values: verified against stored values, not recomputed.** This checks all 419 measured values against the numbers files the report was built from, using each file's pinned sha256 and JSON pointer. Where the value is a direct field of a released upstream result file, it checks that file too.

    python -B repro/check_numbers.py

Expected: `419 stored ok`, `173 upstream ok`, `FAILURES: 0`. For the other 246 values, the source is one of these:
- an expression (a difference, count or percent);
- a post hoc rebuild;
- a constructed number;
- a file that is not released.

They are checked against the stored numbers file only.

**Optional self-tests of the frozen code** (synthetic data):

    cd repo/explore/W9b/sham1/v1.1 && python -I -B score_phase1.py selftest

Expected: `selftest ok`. You can also run `cd repo/explore/W9b/decomp && python -I -B decomp.py selftest`; expect `selftest ok`.

## Competition bundle

We include the frozen local constant-robust Small-track bundle (SHA256 b50844ed…7b16). Its relationship to Codabench entry 1013613 and any second-track record must be verified against the submission record before the final report describes it as the exact uploaded artifact.

| Item | Value |
|---|---|
| File | `submission/W16-C-constant-robust.zip` (contains `solution.py`, `artifact.json`, `small.txt`; `small.txt` marks a Small-track bundle) |
| sha256 | `b50844ed6c1358c08f6726471a6b422db0110386c2871c521419284f8c807b16`, equal to the hash recorded when the bundle was frozen (20 Oct 2026) |
| Predictor | constant: `are_robust(model_id, reasoning_effort, problems)` returns `True` for every problem |
| Training, data, model | none |
| Runtime dependencies | Python standard library |

    sha256sum -c submission/W16-C-constant-robust.zip.sha256
    python -B -c "import sys; sys.path.insert(0, 'submission/W16-C-constant-robust.zip'); import solution; print(solution.are_robust('m', 'low', ['a', 'b']))"

Expected: `OK` and `[True, True]`. These commands check the predictor's outputs. They do not regenerate the private leaderboard score.

## What the scripts in `repo/` are

- **Prospective control.**
  - The design, amendment and freeze are in `repo/explore/W9b/sham1/` and `v1.1/`. The external design review is `repo/explore/V23/SHAM1-VERDICT.md`.
  - The generation code (`wave_core.py`, `wave_runner.py` and `request_core.py`) needs vLLM and a GPU.
  - The frozen scorer is `v1.1/score_phase1.py`. Its one scoring run is recorded in `repo/from-box/research/W9d/sham1-score/`: `RESULT.json`, `DRAWS.jsonl` and the run receipt.
- **Numbers files.** `repo/pair/aimo/report/numbers/` and `repo/pair/aimo/paper/numbers/` hold the numbers files and the `make_*.py` scripts that wrote them. These scripts were not rerun for this release. The build manifest that maps each report value to its source is `repo/pair/aimo/report/REPORT-DRAFT-v1.4e.build.json`.
- **Other analyses.** Their scorers and result summaries are archived but not rerun:
  - under `repo/explore/W9b/`: decomposition, fresh test, repeat cohort, thinking-on repeat, causal-length test and why-fragility;
  - the random cohort, in `repo/from-box/research/W9d/random100-freeze-r5/pack/`, whose specification is withheld;
  - the leaderboard simulation, `repo/explore/AM1-aimo/board_noise.py`.

## Withheld, and why

- **Problem text, requests, answer keys and raw responses.** This covers the prospective run's 96,000 requests and answer keys (106 MB), all raw response text, and the other experiments' draw records. They are large and contain problem text. The problems are from DeepMathGAP (see `DATA-NOTICE.md`). `build_phase1.py` shows how the prospective requests were built. The prospective run's correctness-only draw records are included.
- **Files derived from organiser-released challenge data or third-party sets** (for example GSM-Plus), and our internal competition-entry work. Their redistribution terms have not been confirmed.
- **Internal drafting files and specifications:** the report's Markdown source, its LaTeX converter and three internal analysis specifications. The report is published separately.
- **Third-party material:** the model weights (Qwen3.5-4B, revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a) and the NeurIPS style file.

`DATA-MANIFEST.md` lists each withheld file by path, sha256 and size.

## Licence

- **Code:** the new analysis code is under the MIT licence (`LICENSE`).
- **Records:** the released records derived from DeepMathGAP stay under CC BY 4.0, with the attribution and the list of changes in `DATA-NOTICE.md`.
- **Dependencies:** external Python packages keep their own licences.
