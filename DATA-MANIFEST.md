# Data manifest

Every input file of the report build (the 241 files pinned in `repo/pair/aimo/report/REPORT-DRAFT-v1.4e.build.json`), plus the
prospective run's request and answer-key files and four withheld text files. Paths are relative to the original repository root;
files marked `included` are in this release under `repo/<path>` with the same bytes. 69 of 243 are included.
Licence and attribution for the released DeepMathGAP-derived records: `DATA-NOTICE.md`.

## External sources (not redistributed here)

| What | Where | Version | Licence |
|---|---|---|---|
| DeepMathGAP problems (all problems in the report) | https://huggingface.co/datasets/amz25/DeepMathGAP | revision 2c6ca2e9 | CC BY 4.0 (DeepMath-103K content MIT) |
| Model Qwen3.5-4B | https://huggingface.co/Qwen/Qwen3.5-4B | revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a | see the model card |
| NeurIPS 2026 LaTeX style (report PDF only) | NeurIPS 2026 call for papers | `neurips_2026.sty` | organisers' terms; not needed for any number |

## Why a file is not included

- **A**: raw or intermediate research records (model draws with problem text and model outputs, logs, run folders). Not needed for the
  released checks; large; withheld in v1. Their summaries that the report uses are included where listed.
- **B**: derived from organiser-released challenge data or third-party sets (for example GSM-Plus), or internal competition-entry
  work. Redistribution terms not confirmed, so withheld.
- **C**: internal operations records (GPU job receipts other than the two included).
- **D**: the prospective run's 96,000 requests and answer keys. They contain DeepMathGAP problem text and our rewrites (CC BY 4.0
  allows redistribution with attribution) but are 106 MB. `repo/explore/W9b/sham1/build_phase1.py` built them from the fresh-test
  request files listed in `repo/explore/W9b/sham1/MANIFEST.json` (also withheld). Withheld in v1 for size; can be added.
- **E**: internal drafting files: the report's Markdown source, its LaTeX converter and three internal analysis specifications. The
  report itself is published separately; the specifications' frozen rules are restated in the report's appendices.

Categories A to C were assigned by folder, not file by file.

## Files

| Path | Bytes | sha256 | Status |
|---|---:|---|---|
| `aimo/factory/domain_gen/runs/ext_ids_label.txt` | 1214 | `93ae54b076fcab54d1796bb33924565ccd55e21e28642564e5d8713de3b2e26c` | B |
| `aimo/factory/domain_gen/runs/ext_ids_pilot.txt` | 29 | `ddb203f2ca7b38719246587d0164e29c4b5c704645ff111d70d807edb330c3bc` | B |
| `aimo/factory/domain_gen/runs/ext_ids_scale.txt` | 333 | `69c32abf9c9b90408c8d143109dba4f6646bef8d2b0b8f59ff3588ad1bc855fa` | B |
| `aimo/factory/domain_gen/runs/label_export_explore_v1.jsonl` | 1789598 | `2f21ce0a7fb5efc1135ee7d53bea737a24a06e07fd7cd18efa083523d23687a3` | B |
| `aimo/factory/domain_gen/runs/label_export_explore_v1.manifest.json` | 35411 | `3372154eedbefc2f676a81cb0544d5cac66c626b85d46d838875e46ce7d791bd` | B |
| `aimo/factory/domain_gen/runs/label_export_explore_v1_distract.manifest.json` | 6481 | `de4855d5fe980156bd1624d80882539599548723245e9541c908055a3154354b` | B |
| `aimo/factory/domain_gen/runs/label_export_explore_v1_originals.jsonl` | 47055 | `3635881469d2f8a1e77f7e50646ee9243c1d65ecb5a9e1f952286e546397036b` | B |
| `aimo/factory/domain_gen/runs/pilot_pool_status_v2.json` | 28980 | `b4435f5acd5f60ad8805e3bea304c4c8fdbba06e60d994a8474e6edcbe399cb8` | B |
| `aimo/factory/domain_gen/runs/pilot_pool_status_v4.json` | 55588 | `fb7675a49ee729ae50177efd04b5da61beea6eca9e6d36e68c09dc89149ad03c` | B |
| `aimo/factory/domain_gen/runs/pilot_pool_status_v6.json` | 100222 | `813c04136f8922258dd7988838b5a2b8860dfaee0bbcb20db359dfa7ec007fda` | B |
| `aimo/factory/domain_gen/runs/pilot_pool_status_v7.json` | 128172 | `65a590adb24b598c908ec221ba2601567f93dfabd5b14df4a84c2c9d10e9e426` | B |
| `aimo/factory/domain_gen/runs/pool_status_DB1.json` | 10362 | `1782040964bce082ffc35254639284fda7590c119b28aa90b1f93674efcdddcc` | B |
| `aimo/factory/domain_gen/runs/pool_v6_summary.json` | 19435 | `eaafdac14e8c4e399b5acfc7a631045e19b64e1193bf0b7e0e8a05214d4c04e8` | B |
| `aimo/factory/domain_gen/runs/pool_v7_summary.json` | 19536 | `672a15c8515e5041202add0b3086f3069062cb51be5d958b73b0b51ffc93d9a5` | B |
| `aimo/factory/domain_gen/runs/semantic_flags_manual.jsonl` | 19767 | `b560f3b8d3a3635132291181d7590fe1f9dd04780a5712099e4ed7d7cd3fb083` | B |
| `aimo/factory/domain_gen/runs/semantic_flags_wholenumber_triage.jsonl` | 35977 | `a724faf9d3be544ee0189143a1d50a44d663b6c9b4db1d6b139db99be2114806` | B |
| `aimo/factory/domain_gen/runs/w16_d025_audit_I.jsonl` | 56240 | `2d703473f13c33fc12457010757b187455fa9d6febda348789da359701bce6fa` | B |
| `aimo/factory/domain_gen/runs/w16_flag_tiers_GH.jsonl` | 177427 | `ed15fd533a4542f3f4eec8cca1442377fb3ff57ce826932ab34518d27fe54add` | B |
| `explore/AM1-aimo/out/board_noise.json` | 1471 | `b699940ceddf7ed8800f30d98467621e3e24ee4760b0296d9adb37cc6f4a176a` | included |
| `explore/CL-gsmplus-20261019/REQUESTS.json` | 3884954 | `b8b582f5c68f621e3dbd622f51bf42d4963dfa2ed7ba41e626b804fa2f5c7731` | B |
| `explore/CL-gsmplus-20261019/SCORED-5070-LIVE-003.json` | 357668 | `a221768ca5b618118cf0ae6c6e1ca2b5279c691ae66dba2a629f21af465c7f22` | B |
| `explore/CL-gsmplus-20261019/THROUGHPUT-5070-LIVE-003.json` | 1892 | `5145a543d8d95144340b6bd9d3d25f3084309c851dfb3393fa0a7bb5b1d1304e` | B |
| `explore/CL-labels-20261019/MANIFEST.json` | 2638 | `00f588b6d0419847e4755b9e49a176d9a5085b25a10a1f2cc4e04f42f5ba20d9` | B |
| `explore/CL-labels-20261019/REQUESTS.json` | 1009378 | `9a94bffd27f0abc0a832151ad76be17249e2f44e76772903939bf765b1c8bffc` | B |
| `explore/CL-volume-features-20261019/FIRST-OUTPUT-VERIFICATION.json` | 1707 | `75d476ee2b3ee353ed26b96160d76a3b751095765e5713560ba4a8a585d70169` | B |
| `explore/M1b/NOISE-CEILING-RESULT-20261021.json` | 14189 | `2b773b9c8316e77826b9c531c7f6f761a2323bdef293e86ed05b9a5c57bb8777` | included |
| `explore/M1d/WHY-FRESH6H-ADDON-20261021.json` | 1122 | `7daadbe175f54a33a2fc39e68b1bf80d93848d84cbba755ec215c3e2363a1d19` | A |
| `explore/M1d/WHY-FRESH6H-RESULT-20261021.json` | 5325 | `c493e21af0680ab2b9a291da036b860a29e566faaa7451876c5d680e6e4a249c` | A |
| `explore/R6/NUMBER-CHECKS.json` | 5039 | `2906e8812d6551679fb8e5d403461f11a5fb08fbbc6ff40e432b0425b95a0cf1` | included |
| `explore/R7/NUMBER-CHECKS.json` | 9883 | `42f40cb14fa6a10b046ea3b8f660c7802f9944d1735718d0454997d3c9df7b20` | included |
| `explore/R8/NUMBER-CHECKS.json` | 8785 | `bc4a8cde77a86769c9aceeccb1b4175c5a5a2dfdd7ef84a808fc099675ec1673` | included |
| `explore/RA/an08-rf-20261024/RESULT-AN-08-RF.json` | 37729 | `ad1a2f7efe899bccfb47960109cf9bb2d666dc159d34d60fd40459caa970ccef` | A |
| `explore/W16-round-20261020-1530/125-repeat-assay-forecast-ceilings/125-RESULT.md` | 810 | `3202d30d3965716d5623df6887968d0febf5d041c06b879618b24b825f6ae97c` | A |
| `explore/W16-sprint-20261020/78-oracle-objective-tradeoff/78-RESULT.md` | 2618 | `e2fd981cf9d135058aab12b6a179886d5351a51435ed9e0f3416f6e7acf1da0f` | included |
| `explore/W16-sprint-20261020/80-feature-conditional-nonidentification/80-RESULT.md` | 2813 | `872b432171802db267aae76b656f5de60dfc890328c810f3f6667ac009edb106` | A |
| `explore/W16-sprint-20261020/82-retention-conditioned-correctness/82-RESULT.md` | 3902 | `0c2bea2162b30ba9e4282fd40b811556355735c2fbd157a6bfdb02e3851a63e8` | A |
| `explore/W16-sprint-20261020/86-calibration-only-controls/86-RESULT.md` | 3172 | `4aa010f2ac33d2fc5df2b4b4514e439e7aec3e05465ad8dd0cbfbdb80098044f` | A |
| `explore/W16-sprint-20261020/88-threshold-library-selection/88-RESULT.md` | 3330 | `199ef4dd801c4b8076ea0bbf91f9dcf4ab6049bd2503959e1c042787475197b4` | A |
| `explore/W16-sprint-20261020/89-detection-floor-prevalence-bounds/89-RESULT.md` | 3906 | `34e4ef41d8d080b79c085ee60cae19dd7963668888877c206325bdb457afc48d` | A |
| `explore/W16-sprint-20261020/92-depth-detection-geometry/92-RESULT.md` | 2850 | `ec203d3082ebcccffe4303705dd57b14d0fe4337153f7dc6a985ab438c39356b` | A |
| `explore/W16-sprint-20261020/94-screen-volume-versus-depth/94-RESULT.md` | 2625 | `cacc52f0917c7694133a715e9f67eb21a1c5102a7b94d5f6e8b47e7e8b65ace2` | A |
| `explore/W9b/154/out/RESULT.json` | 29167 | `d1a7b8ac4ff3cac03931802c675d30e6931381462f455d211860b6820717ca3e` | A |
| `explore/W9b/causal_length/an63/RESULT.json` | 4442 | `01b5d73103e1f0b002bd200b071ff3e50d87e939e584ffc6c5e9398836e7f411` | A |
| `explore/W9b/causal_length/final/AUDIT-SAMPLE.json` | 54045 | `e9c0c1cb30c3a386e4557146f8b198e4a22451efcea7b55f1473aa4f9e1374b3` | A |
| `explore/W9b/causal_length/final/EVAL-FREEZE.json` | 2381 | `123f4d74c055dc2fd9834fa36e748e9b0207df1ed228391474d273273a7610e2` | included |
| `explore/W9b/causal_length/final/audit/AUDIT-RESULTS.json` | 730 | `9ed32797068cf95714a4e9b215f8354103d3260f1cc1641a280d1b2a7a5072ea` | included |
| `explore/W9b/causal_length/final/audit/READER1.json` | 3988 | `b91be30b54300c189eb8c4e5a9eba5d64fc43b6e5a1bd7a89aa4c913d9f05507` | A |
| `explore/W9b/causal_length/final/audit/READER2.json` | 6291 | `abfda8bb84d27e319d099aad22ebf728ac9cb0695ddcdfd2a60c366bef31e59e` | A |
| `explore/W9b/causal_length/replay/COMPARE.json` | 2133 | `e2d4d2821b64eadfa2f8592df8ea7937fdeff601d6d60fa49c55a2af1f76b3b2` | A |
| `explore/W9b/causal_length/score/RESULT.json` | 5375 | `dc5b00b5a96e4854fe4a4823426334015ff2c0b53fdbfb8557cbdc422794441b` | included |
| `explore/W9b/decomp/RESULT.json` | 60398 | `f70423eb7b03d70ac5252fdaee8464705b802cd0a3dc8b3d66127d3bb12ace0f` | included |
| `explore/W9b/decomp/SHAM-JOINT-RESULT.json` | 15807 | `2fe5c50452fd09b53867118dc7e9b023c52da701a79a7c57f441c9549c70f9b3` | included |
| `explore/W9b/decomp/SHAM-PHASE0-RESULT.json` | 13188 | `7cbdc2f0c899ea72ad40e5726c6f8dde1d627f00e4e027572feeece3b92d7b91` | included |
| `explore/W9b/decomp/decomp.py` | 15936 | `a37aebe72f582fd24ff9353ea273ed05abe70cf2ab6f5b1efff0a9bf85bb6929` | included |
| `explore/W9b/fresh6h/PREDICTIONS-BEFORE-RECORDS.json` | 557747 | `d8c8549f45d1e8491594a0c0e658de60f862a53af073f7cdfa474ecc7b3e95d1` | included |
| `explore/W9b/fresh6h/out/PER-ORIGINAL.jsonl` | 770431 | `0e6a6657b948e78a088bd83d6fc5174ee4f4c239b3e6e110dd54358cd52ed49e` | included |
| `explore/W9b/fresh6h/out/RESULT.json` | 11919 | `e30d33c6ec7daccfdd0a12f6e67b249cefda692cbec9bb9ef5c6267a2309ed9c` | included |
| `explore/W9b/ready63rel/out/DRAWS.jsonl` | 9717116 | `e4c66547ecc6ac1aacc9a6921b5611f3e9e183eec7aab6b90e55cf49edaa01b3` | A |
| `explore/W9b/ready63rel/out/RESULT.json` | 55304 | `98ebc88e7d7ce4d5aca91916fe4dfa8fa28d12c6f7a54fb21ae0403c1d31ac25` | included |
| `explore/W9b/sham1/COHORT.json` | 28742 | `a626ed85a93dc4afdad1a096a20f666a5b2a667ef04a03eb5bdcc35dcd5e678b` | included |
| `explore/W9b/sham1/MANIFEST.json` | 1547 | `3885f9da6de0ccfc53717f6e533ac62a90504f6d2f29ed4371249469bada4e57` | included |
| `explore/W9b/sham1/build_phase1.py` | 6350 | `6ec5f85c0463fd1cd813a97903a9d6bd959e28ced8643cf93a6af70d12573fb4` | included |
| `explore/W9b/sham1/launch_shim_d2.py` | 5361 | `57144338d25d9594caf6dfdb389837760193008cf026be203badcb2bfd21f5dc` | included |
| `explore/W9b/sham1/v1.1/SHAM1-FREEZE-v1.1.sha256` | 1725 | `cf704ca303b4791351426d97f9be715e7a475644be557e1498e1f11794a94b5b` | included |
| `explore/W9b/sham1/v1.1/score_phase1.py` | 17790 | `a430019242757aae788ced32795cf944536ef2e4f3c5dd5cedac293c97e5370c` | included |
| `explore/W9b/sham1/v1.1/wave_core.py` | 19410 | `814d851efa858fbf53dbc9e1617ec9744bd154cebe191fda81b0a5b54a4bf203` | included |
| `explore/W9b/sham1/v1.1/wave_runner.py` | 9546 | `46ca0f463b14a82cced1168fb6f30b4cb7d73f1bc12cef2e2abfe82cab4fec3b` | included |
| `explore/W9b/thinkrep/out/INDEPENDENT-REPLAY.json` | 1071 | `06348947c24e1d8e2d852baadc14ba088be872ebe945b9b907baf3f83d72ca16` | A |
| `explore/W9b/thinkrep/out/RESULT.json` | 14682 | `e791c9a09a320a6cfde9836c10b4cd2574be9bd233a34e783b250078b537cc7b` | included |
| `explore/W9b/whyfrag/RESULT.json` | 33454 | `01e52b412554ab20615faed8fbd9487dc8ef4dda94fa23763b9977aa7b3ec9ef` | included |
| `explore/W9b/whyfrag/why_fragility_varies.py` | 14088 | `502a5c067a3935a35757692d22e3cf6f7bdac69c8cd49637f0037b9c3d793389` | included |
| `explore/W9c/thinkrep-blind/BLIND-COMPARE.json` | 1507 | `a7ff9bf082a676736f6d78d536501bbac13c3ddef110b59a3be157963ad832b7` | A |
| `explore/X1/130-second-wave-predictive-evidence-for-edit-structure.md` | 3452 | `dd71d7dd30dc8eb949da0f61e3338f93266c9ad45de25d00ab67c04807d35cfa` | B |
| `explore/X1/132-operational-auc-versus-edit-specificity.md` | 2337 | `27ede55a8c1bb635328e84bdb4832bdc5c6b75a0b2ec63efe6a1a7713c569a27` | B |
| `explore/X1/150-null-hypotheses-versus-pragmatic-gain.md` | 4096 | `003b1706b0a2d03e3ce23c0504740607fc9f4054b4aa0f4a5ac3fcd8551663a4` | B |
| `explore/X1/156-stable-edit-contrasts-second-moments.md` | 2674 | `043c58023f60ad6b78630b2eebc78b90fe18b70bdb070787461cffebb0139657` | B |
| `explore/X1/158-two-draw-independent-seed-harder-transfer.md` | 3952 | `d1708db1e569abda8a448c4e4c49104b7fa7c488e592f79bf9ff0638123e8857` | B |
| `explore/X1/160-answer-disagreement-direction-decomposition.md` | 3645 | `86550eec4ba8bd48e88af2be69ff6bff98481f358edef0dfce2efd383ae5a09e` | B |
| `explore/X1/161-harder-assay-versus-matched-no-edit-control.md` | 3189 | `7b7f4921736b76b5eaad44e82c9d6db0af60ad51055455acd33e438c68c33a2e` | B |
| `explore/X1/163-cost-aware-label-admission-replay.md` | 3119 | `b7c4e84c612e868070aaa90218f24649cdfad8f7cf1ecef5c978fa0f2d32abf3` | B |
| `explore/X1/166-family-matched-drift-screen.md` | 2984 | `c0625a40d4030c6a7046ed2fce5001e3a8d0ddc6adf0278000b2c31ad9410a92` | B |
| `explore/X1/168-original-state-direction-screen.md` | 3730 | `a1f7a463dd45f129a37cda867f9aefacb77658751628dca94ee836f43916d5fd` | included |
| `explore/X1/170-frozen-state-cross-protocol-transfer.md` | 2777 | `1817c6c65a441b63e38206a014a83572da1758c40135e061c88f1ad3a4ffd355` | included |
| `explore/X1/172-state-signal-versus-signed-edit-effects.md` | 2620 | `edc34b44c8ed8cdb004bef4e7137d8bef4f00678f80eda26c1d8302e80a19d34` | B |
| `explore/X1/174-state-directions-versus-flexible-length.md` | 3330 | `60b32be6fc749b65afe3e08fd9ead21c28deb067f542acfb230e50618dff50ab` | B |
| `explore/X1/176-retrospective-frozen-state-gsm-transfer.md` | 4271 | `3380c89945727b167ba7d967980aabfc2622eb268165b3d63a3fdc9390839a44` | B |
| `explore/X1/177-corrected-numerics-fresh-confidence-calibration.md` | 3327 | `c4ae0b3aa3f8376cb4cc6cc181139e0df70066bad5a714d76ec528ffdba8f9ad` | B |
| `explore/X1/178-state-ability-versus-family-count-forecast.md` | 3478 | `b9cf09864531c42cc415cccb26e91fc8d2b45eeed9b2b0fd0509ae19519a25d5` | B |
| `explore/X1/180-finite-response-threshold-indistinguishability.md` | 2238 | `87b018a7eb28ab9b04173a02ea910028eb1ef031ba09a73cea86e9d33605ceeb` | B |
| `explore/X1/182-state-family-intercepts-and-shrinkage.md` | 3444 | `85163ea2092f25e91425cd1448a10feda3ba891b0a90f4fc63e40beff2af8442` | B |
| `explore/X1/183-counterfactual-success-lens.md` | 3136 | `9b6e13c21d2b2f5e57edbcaed9dcd2b118bdb7fbc829bc53ab9c54df0a943db4` | B |
| `explore/X1/187-family-effect-pipeline-uncertainty.md` | 1781 | `019eb8b37a849af7336c82cb9d75e9ddfcee18ea7601258013cfc4d940e0576f` | B |
| `explore/X1/AMENDED-REPORT74-APPLIED-ONCE.json` | 1751 | `cc9bca4e7baeea0d44093da8476b793cbf2cdf0b865d484be062a8dc3c936839` | B |
| `explore/X1/PREFIX113-ONCE-EVALUATION.json` | 631 | `d99513e55c4824f724abb928e082484962042f45a560b335403749df1e46dfdd` | B |
| `explore/X1/amended0055/PLAN-BEFORE-SCORES.json` | 28981 | `32dbdc1e0f55f6dc9a896719fc244df467d419168ffe859cd436fab3183c0cec` | B |
| `explore/X1/amended0055/PRIMARY_no_prior_label-BOOTSTRAPS.csv` | 153918 | `2adefb99232fbe1e401e0f97d963870b61dc65a34da96ae2e6c619af19f2a661` | B |
| `explore/X1/amended0055/PRIMARY_no_prior_label-SCORES.json` | 49498 | `a1ceed3b3a4d32fd942ee32d4a2ba838584950b6961e94e785b863ae3c15420c` | B |
| `explore/X1/amended0055/RESULTS.json` | 1499 | `d2419968a431bfb21819af77dd029fccaa09b1d7b72d3e2b98c9c99428037d44` | B |
| `explore/X1/amended0055/SECONDARY_all_binary-BOOTSTRAPS.csv` | 153786 | `1bf3179b488d56bcb4a22c711182e311d57ce97b779d5a8cb8ea34b3ad81192e` | B |
| `explore/X1/amended0055/SECONDARY_all_binary-SCORES.json` | 56090 | `1321703d010f138698402c361f0b431f801090a2a2a9d467e85d804845a90813` | B |
| `explore/X1/attempts.jsonl` | 630639 | `49e8a6c84e99a930fddcecc812f44f5ab2493dd224fd81c3f1fd2e42394a2877` | B |
| `explore/X1/continuous0910/154/P34-FROZEN-ROSTER.json` | 68792 | `aff344d1b09bcb44b3de25d0becf06144d36a40dfc45fec5a6d5def2e64672b6` | B |
| `explore/X1/continuous0910/173/APPLY-RA-20261024/METRICS.json` | 1521 | `aebcca9bc5ade61739b26f54906b0fdbec1f1d45626a5682448b10f39eea8617` | included |
| `explore/X1/gsm_live/SEMANTIC-FLAGS.json` | 1760 | `79aaa0c6304789c0202d8ca4f76a62645a226d25672fe36f8c9c35f1d7bfd340` | B |
| `explore/X1/hard_band/snapshot-1792406520069398100/terminals.csv` | 4899 | `b24e505d4e52fee9cceaecbf5cbe6e56b716db50f08ec4c9e5088398d451dba2` | B |
| `explore/X1/independent0040/AUDIT.json` | 1802 | `b800d847089a29f2dec07b022813f34504bb84fce51dbfd6b0c1c196cf2303a0` | B |
| `explore/X1/organiser_primary/edit-level-1792409623836107500/results.json` | 58682 | `a3c5def689b7ad5c24358935cb9c51b2a726c2b38cca1fe7f6a0011433c3d9ba` | B |
| `explore/X1/organiser_primary/label-transfer-1792407474936230200/results.json` | 4995 | `d75e27563a4b82c03dd047aa28511d377e8ec0e086633e9a1cf97eef02b65942` | B |
| `explore/X1/prefix113_once/run-1792449357639288400/freeze.json` | 6657 | `44b8be8229e639d06a1b779ac4f94b0359e95beb21c1d4cbb6c008bd99cd0f67` | B |
| `explore/X1/prefix113_once/run-1792449357639288400/problem_predictions.csv` | 17018 | `0ca4c064cbec041b3bfd3a1ec481e2c0740a83db70e56377bb8bbd1659b93aa3` | B |
| `explore/X1/prefix113_once/run-1792449357639288400/results.json` | 4663 | `00762e2fac7b12f04f94552fb54398a8cde7016ee898b2a4bfecc51a7524ea31` | included |
| `explore/X1/primary_target_v2/available-1792414144591790100/results.json` | 73008 | `905e363b099e6a79157548da6409483707d56da9fff6d56a2ea8908741af2176` | B |
| `explore/X1/primary_target_v2/contraction-followup-1792415455403172300/results.json` | 10529 | `4adaa1df561be9792d5a5f20620d7561d23f7e824d2747467cb06d02bd84ddc8` | B |
| `explore/X1/primary_target_v2/length-matched-1792414359475745300/results.json` | 23559 | `cb1b9fe2dfeb4a95f565ff8d860e6c9b018ee112ec0839c10ec8f7a2486123f3` | B |
| `explore/X1/round1530/180/METRICS.json` | 28289 | `afee56721fcd02588438717fefc0ebbdebdf6ee45642ca1a5bb8508e1a5dcb1b` | B |
| `explore/X1/runs/drift_nodomain.json` | 20054 | `ec801be1c7259f755f8d5d2ecb646ffe41240fab83d1c1b9182544a31fa1efd2` | B |
| `explore/X1/runs/drift_official.json` | 19613 | `38411e7bbbdb40802350fb34b2992287fbaa8f240b8ad250b10a0ae382946e9e` | B |
| `explore/X1/runs/historical_null_summary.json` | 148 | `4a62893c75be17dbf0fb83b588aa71f1e016622caa283d2d8d41656b8c97bde6` | B |
| `explore/X1/screen0850-1792424621460828300/cohort_summary.json` | 960 | `03f523c07ffdc8ea1e87b71dc45bf6423f0f3c5f0f8bc5e840649ec7d7143f43` | B |
| `explore/X1/screen0850-1792424621460828300/metrics.csv` | 25162 | `2effb4dd36daf2ac70c55b60ee8f49c7dfdf095c92427e57fae3dd199f83064d` | B |
| `explore/X1/validation_freeze2045/FREEZE.json` | 7748 | `6bdb06b7e69c8467d664fdf141942cf44a6b3b24fa3f06d6cc97c8a03eb686e2` | B |
| `explore/X1/validation_freeze2045/TRAINING-DATA.csv` | 341878 | `4b93e2c86e359bc69b1d76cb21316f3351460680a87f653853b482dca7723803` | B |
| `explore/X1/volume1355/run-1792443480055232400/AUDIT.json` | 1575 | `ba0f0c1f4fa0f72b3c3a43e493710f720719f6b0e10e3ef3cc174a296c31abb1` | B |
| `explore/X1/volume1355/run-1792443480055232400/SCREEN-VALIDATION.json` | 461 | `36ceb1fcb44c0de0576b8e7f1ff5da7a542c1b1c5a8b36b9dd029ec33fd1983a` | B |
| `explore/X1/volume1355/run-1792443480055232400/SCREEN-cohort-best.json` | 4980 | `ff13df7dbdb5dd3e3a2b48f77db3b4155ec8ed54133b973cc918ad9079c4751d` | B |
| `explore/X1/volume1355/run-1792443480055232400/SCREEN-predictions.csv` | 7417076 | `33bed2fc5689988fab70a70d21c8664a365e769179b4498730f9ad150605d28a` | B |
| `explore/X1/volume1355/run-1792443480055232400/SOURCE-ADJUSTED-COMPARISONS.json` | 4595 | `550cef495e9d2dc668c702b10e774d911d8f0a413621fe3a4eee532f6032fb6e` | B |
| `explore/X1/volume1355/run-1792443480055232400/all_group_labels.csv` | 826054 | `31904d91c7759135e07ad60f496cbb63430e5040b75e2612dd23b67a9b55c781` | B |
| `explore/X1/volume1355/run-1792443480055232400/counts_by_source.csv` | 474 | `e344e88bbb4333d3582ba0a5a357f0671a0147f26af762f5f6bfdd9c9a9ea1ff` | B |
| `explore/X1/volume1355/run-1792443480055232400/neural_cache_coverage.csv` | 90373 | `ed802cf2a4d140c7de4e7d58c933ee3a1786c705c96f37295de701f171c1dece` | B |
| `explore/X1/volume1955/run-1792464972961084800/VALIDATION.json` | 658 | `23648e25c68e68f8fe7c7d2f607d92af3d3f502f4736f03eb79dc7e20bfae671` | B |
| `explore/X1/volume1955/run-1792464972961084800/additional_paired_contrasts.json` | 1502 | `3cfd948cc97b4fcb1ccd54ba454315c83ed757a6a94ebb56bcd7be4bc9a30dfb` | B |
| `explore/X1/volume1955/run-1792464972961084800/metrics.csv` | 61287 | `70b4b22f10c05ebc3e26388de66dde3e791121dff827e433dc978ea0999f2594` | B |
| `explore/X1/volume1955/run-1792464972961084800/predictions.csv` | 23705552 | `b740d3be45ca4265689f2315c0277fbd9829d317390346934c6d04021b03d7a9` | B |
| `explore/X3/106-nested-regularization-count-transport-20261020.md` | 3999 | `0a174d08704d23e9ac1e4dfcf1b001f73ef32236a766c468d14fe3bbed519ac8` | A |
| `explore/X3/109-V2-fresh-bootstrap-correction-20261020.md` | 1531 | `7a2e2071f5bed4da1a6bff449ed765647163fbc2860b2c4c594b64ce1c89656c` | A |
| `explore/X3/109-global-family-adjusted-repeatability-20261020.md` | 6215 | `66d65e71822f274ac035640bbed9be7612fc9dc339f55c24eb908a3e579a2912` | A |
| `explore/X3/114-bounded-probe-and-pipeline-stability-20261020.md` | 9050 | `cee90baf453706949266344a7def24433d0397e5637abadbd5faa6dbb27018a9` | A |
| `explore/X3/60-point-label-null-and-certification-design-20261020.md` | 1981 | `ea94e8cf5a4a794838b1c5b617f2ad37e9fb5ee74a09c229b2516d7da8ea8e25` | A |
| `explore/X3/65-completed-count-structure-analysis-20261020.md` | 1972 | `09fed71a81e2677edb3bfd3196edd30f9a1035c864d480fc727a8346541fcce2` | A |
| `explore/X3/71-partial-count-identified-hard-labels-20261020.md` | 1992 | `1e0266bcc8b4dad0dba5bbb9cda21c79df2f4a37d3315e9a6ec3b7fa08ae423b` | A |
| `explore/X3/72-partial-count-coverage-intrinsic-transfer-20261020.md` | 1989 | `e6626ad44b531e5189a37f9b841c98692283905a40b1b9b5b219ef9e5b622913` | A |
| `explore/X3/73-flexible-prior-optimization-audit-20261020.md` | 2226 | `f8806cc4296e27782f52165d8f72a55182978d67dfe2fe4fcf8b1b515124411b` | A |
| `explore/X3/74-censoring-and-repeatability-identification-20261020.md` | 2300 | `4be8b76d682871f573710bfdb034fab2172d692fcecf254518404fe880260fdc` | A |
| `explore/X3/76-full-frame-AUC-identification-20261020.md` | 1602 | `62692b7d8f74778d61cdbf49744afc724f71633827ac23a069bbb531f9861636` | A |
| `explore/X3/77-joint-proper-risk-identification-20261020.md` | 1703 | `afc852bdc504387755dedba74b9cf0120049ad30f08e5d9a428c0c176d803027` | A |
| `explore/X3/81-fresh-transfer-all38-20261020.md` | 1977 | `0075a2776a198d4c6f455cb0471a4bab230864939e8e8d135109db6cb1b68828` | A |
| `explore/X3/81-fresh-transfer-ready63-20261020.md` | 1978 | `e8ebec781a54bff01544e1d49d39b7ad98be8002a48b4779e614895c1ecfcfde` | A |
| `explore/X3/97-V2-fresh-disjoint-paid-assay-20261020.md` | 4475 | `113572158786458e8a427644072a6b53cb702983410c46ffd8b4e4ea26f02b3b` | A |
| `explore/X3/READY63-reviewed-MATH-20261020/MANIFEST.json` | 3687 | `96540a3a0281004d0b1e1795ec0c979da68dd88d5bd13378fea6b141826a3cfd` | included |
| `explore/X3/READY63-reviewed-MATH-20261020/MEMBERS-WITH-PROOFS.json` | 69658 | `1b27513c326e7c084c95f5921123d0c957764865804bc3e926b61e483954756d` | A |
| `explore/X3/YIELD-OWN-BLOCK1.json` | 693 | `115720bcc2d72c3513e5aac7f3f15be6e02fa6d7e83592b5403b185168396977` | A |
| `explore/X3/afternoon-20261020/56/FREEZE.json` | 2093 | `ec02fdaaf217a7ea8f36398cd37bd94cc2fbc8ec4e3e91e2a3bc9a1cdeb11445` | A |
| `explore/X3/afternoon-20261020/56/MODEL-PARAMETERS-FROZEN.json` | 23755 | `7360901b7d38a95c4d0eddc9d134465f476a795613925a30ebbeb85bd1194d7e` | A |
| `explore/X3/evening-20261020/114/RESULT.json` | 12722 | `7e2b4c4c577aa79b8180d2b5254de5d91e752e1bfe892d4ca5684fb0ef0d9e8c` | A |
| `explore/X3/evening-20261020/81-ready63/RESULT.json` | 40140 | `6d1827772332e11a64d836edafc42e6a3ad02df65118d1aa15f8418fe54a3256` | included |
| `explore/X3/evening-20261020/81-ready63/strict_n4-ALL-ORIGINALS.json` | 61806 | `46481896331cfd599180376f57c8153cb92ac32fb5b5be873a934262c42c1507` | A |
| `explore/X3/fresh81_pure.py` | 5050 | `6b9c0e124f4d690c6bd1412aeccfdc8d12b8b20fb2ebe3d0576656c0b59f1e4d` | included |
| `from-box/research/AM1/random100-score/DONE.json` | 4151 | `2cda498d2fb2c941b867bc2ecb0ecfb4d2d0ba92f606be01363d6432b180a136` | A |
| `from-box/research/AM1/random100-score/SCORE-COMPLETION.json` | 262 | `5f52233bbd71fe570d0fcef9ed947af1e04d10442e9e60ea42ed3a712fbdcce0` | A |
| `from-box/research/AM1/random100-score/out/RESULT.json` | 44136 | `bd57198417c227b926f05a513ee62f460443aacf9831d67de7eddec755915292` | included |
| `from-box/research/W9d/random100-freeze-r5/pack/COHORT.json` | 2888 | `7d59ad30d1b64550fd7b97fcc3190171e5c9bba0bef8e558dd22e7c17edf4cf5` | included |
| `from-box/research/W9d/random100-freeze-r5/pack/FREEZE.sha256` | 2176 | `28d7b0cf58c9c6f3c387a472d1ba729b9ec6867f66714ae8a6cd82428a2e8aff` | included |
| `from-box/research/W9d/random100-freeze-r5/pack/SPEC-v2-20261026.md` | 8491 | `c71f9fa379572075a1cbaa4b963a493db8aceb299d45264a4b50103ac14714c9` | E |
| `from-box/research/W9d/sham1-score/tree/explore/W9b/sham1/v1.1/out/DRAWS.jsonl` | 16185736 | `86e0aca09bcca52f737b48cc28961808f92cb14e002fba91afe1033c77e5804e` | included |
| `from-box/research/W9d/sham1-score/tree/explore/W9b/sham1/v1.1/out/RESULT.json` | 218171 | `23db1055b0180e0c3d61864eb22756a0dd38f57de2bfdb03307f9941d4bf8e18` | included |
| `from-box/research/W9d/sham1-score/tree/explore/W9b/sham1/v1.1/out/SCORE-ONCE-STARTED.json` | 157 | `68b76ddb697730244c08f521728bca8306c069e5cdfbd4b989398d7528773c9e` | included |
| `pair/aimo/evidence/deepseek-tokenizer-audit.json` | 14385 | `6899252db56d513ed3f28cb45a8d288b692d360c7beeb8bdbf8d7fac2593d3de` | B |
| `pair/aimo/evidence/native-deepseek-cache/metadata.json` | 4347 | `44ba86891ee9ac00b7b7276823761c0cd0c1cf4daeb0c653cb9e90c7dcd62766` | B |
| `pair/aimo/evidence/native-forward-check.json` | 1521 | `392b0c41a25d4600a976ded149e7807e6744fc8b604374ab1c8c73a293219205` | B |
| `pair/aimo/evidence/native-objective-text-sensitivity.json` | 97336 | `e0b991d585e07704d3d648b7bcd058ebccb60405e223e740558edf621cb6aa0f` | B |
| `pair/aimo/evidence/native-own-mink-rerun.txt` | 1659 | `4171d16ca562352795fba53aed2a41fe4b3c974ede4d45d02c26be2a8ce97499` | B |
| `pair/aimo/evidence/native-replication.json` | 10068 | `02803326338c4dd64c320a2c147dc449b418c34b3901a90d468794fc67044c24` | B |
| `pair/aimo/evidence/optimizer-objective-audit.json` | 264677 | `0ddf460920444034310925b8eebd1be5b2a62b2a93f57c2d71f64a67b169c5d8` | B |
| `pair/aimo/evidence/own-mink-rerun.txt` | 1642 | `7008f28cb6cff9bf38e73b838e05b0cf050b03f913b4b701a06c67b0f89c4aec` | B |
| `pair/aimo/evidence/pilot-semantic-coverage-008.json` | 817118 | `2e2aa5202209ce7a2731ecb29a2a6e7bcd90f281ff9442db798c8e830d7ac1a8` | B |
| `pair/aimo/evidence/pool-independent-rerun.txt` | 1669 | `b8daaf9f89f07a6af68451783f76e640e6bf3f57d4c606248ad6e063ec31145a` | B |
| `pair/aimo/evidence/replication.json` | 18018 | `418c00dc856c05b98b36cc514d72053fb8ba57aea423f27eec69ade1b350a6b7` | B |
| `pair/aimo/evidence/tokenizer-audit.json` | 39845 | `52773c803b10b289a40998cb28410b31e726f98c6229fc788a7dcbd1d58ddea5` | B |
| `pair/aimo/evidence/w16-blind-lb1-t015/comparison.json` | 16680 | `b1723f3120056c618419199b8ed62a3c5badbd216f192f9da30bfaf26cb84f63` | B |
| `pair/aimo/evidence/w16-blind-lb2-t020/comparison.json` | 20479 | `6257479aa2bf541fb80745ca25c31b80fca48f99c5456ec12ef3b73dfe964d5f` | B |
| `pair/aimo/evidence/w16-blind-lb2-t020/semantic-check.json` | 2257 | `f51aff167ccf706b53302dfa1de6f0f1b466b3b4be82818db373b4f58812b96b` | B |
| `pair/aimo/evidence/w16-blind-lb6-t024/COMPLETE-SUMMARY.json` | 15035 | `e6dfc3eb5214f7db24069c2703c6a790edb48a6e6507e22778e3860b520c6640` | B |
| `pair/aimo/evidence/w16-blind-lb6-t024/DISAGREEMENT-INVENTORY.json` | 12023 | `4baaef95d4711bf259fa3f1c25c30bb68ce5e95c87b1e45256bf81d19abd3bca` | B |
| `pair/aimo/evidence/w16-blind-lb7-t027/summary-1792392805848149700.json` | 11039 | `7e95197bb44c539eb3d4f73b58080f2c3549b679e9d5aeeda920a37a3f3957b8` | B |
| `pair/aimo/evidence/w16-blind-lb8-t031/COMPLETE-SUMMARY.json` | 27300 | `7ad804fd25e6b06657c7befe41caeea441420a98fc9d14a9e89a084671108506` | B |
| `pair/aimo/evidence/w16-db1-t017/audit.json` | 454141 | `f29e998e5f00941ec7456d1d5a6c3a40b2841725df08ad225132db90fc066a9e` | B |
| `pair/aimo/evidence/w16-db1-t017/engineering-candidates-3.json` | 384920 | `dd205dae3c31c8e0abb828660e680a07c9f149751f424ca721fdaf3431763c7b` | B |
| `pair/aimo/evidence/w16-engineering-t019/audit.json` | 38095 | `ffb55148bdb60b1e76d0727d668ad25b1098855e1006489dee2678c921280412` | B |
| `pair/aimo/evidence/w16-pool-t021/audit.json` | 1041191 | `cafec1456aca547c689572871d51d93deb3b9a586c831adf08767afbeee03100` | B |
| `pair/aimo/evidence/w16-pool-t024/audit.json` | 1963525 | `d3ff89aba626b59752b895e9cc85b985fd5932143acae3b4ac42833630b599b2` | B |
| `pair/aimo/evidence/w16-pool-t031/V7-VERIFICATION.json` | 5541 | `7585ca072f37baceea9d2960030d70e0a9d8893c217a29f69911db1fa06ae8ce` | B |
| `pair/aimo/evidence/w16-pool-t031/snapshot-20261018-234712.json` | 2672627 | `b965f13cadfd67d0f67797adee8e2d83e9e4e798b875cc9a3950cd510fab313a` | B |
| `pair/aimo/evidence/w9-019/q1-qwen-screen-union.json` | 403 | `271d81138b9bdbd9973f2148226228730889aaa2498590bb37b418fa01a74a67` | B |
| `pair/aimo/evidence/w9-019/q1-qwen-screen.json` | 3172 | `0b79cebd19da7af85a325194b6d0c26a0d8bceedb592c019fe2ede63f5281b00` | B |
| `pair/aimo/evidence/w9-019/q1-resolution.json` | 72982 | `2e16ffad603c6130ab025f627138bad1535eae21fc4f087d162ed5aa72051d0b` | B |
| `pair/aimo/evidence/w9b-030/lb6-adjudication.json` | 22419 | `cf7a5d39caf9b9c42aa8fc5e634f5cd6aeab575980f22371f8b549c4d28bc2b7` | B |
| `pair/aimo/evidence/w9b-031/flag-adjudication.json` | 5432 | `bfc00f67ae30d18ab4461356f142b61356538dde2363e0f45a287b23a1061b17` | B |
| `pair/aimo/evidence/x1-independent-audit.json` | 2852 | `690e9c0de31b4e8259990ec823aa1de0bcf7ccc8ac886567636da9f03b6bcebe` | B |
| `pair/aimo/paper/numbers/codex-native-t007.json` | 1992 | `b79b4598d34fd9a90d05d6933849ff63cbfaa7d24b85f7e3d7b3e3e756cf616f` | A |
| `pair/aimo/paper/numbers/domain-gen-t004.json` | 5397 | `3d05c7b417cd24d0d259dcc723ee07c36cd588783b6d6aa1606bdcf490b8e24f` | A |
| `pair/aimo/paper/numbers/w9-t019.json` | 11624 | `dd4513b2351582ff7335a0f1493a03813b7034391c4be8a21bef5c9d8ddf8e22` | A |
| `pair/aimo/paper/numbers/w9-t019b.json` | 1749 | `9168c07ade5f489ee99e2afcaaee3147415516f35bdd8f4b5e834c8cc854d5ef` | A |
| `pair/aimo/paper/numbers/w9b-t030.json` | 3471 | `a71be8ae3a1909604d812a5700a1805fa6ae7620daa0bc89a3c08d7c6ce794cc` | A |
| `pair/aimo/paper/numbers/w9b-t034.json` | 5584 | `c76c588e59be7682385c149bea5ecc26c7a38c27e3dfc91bc6762078a80d2249` | A |
| `pair/aimo/paper/numbers/w9b-t035.json` | 8143 | `c94c9edc9ca4f9cdc22df6172a55e8050f6c0881b58321f3b29e0d458d01abcd` | A |
| `pair/aimo/paper/numbers/w9b-t036b.json` | 6097 | `37f9f0c2989fbf996f2657ece91acb309f2e10d56cf62a35d6dd02a2f669194d` | included |
| `pair/aimo/paper/numbers/w9b-t037.json` | 773 | `6310da11484f59bf82e86e1ec64fbf2a45b8efd8684a10cfa71e2a5339f03f16` | A |
| `pair/aimo/paper/numbers/w9b-t038.json` | 11334 | `61c6ead4a724c228d73d232e3b314f9f1e9fb398435cb7ea554ee42d52221d7f` | included |
| `pair/aimo/paper/numbers/w9b-t039.json` | 9111 | `c79d4ac49e6d698ff9639fab2e606f4bc7f29eb3f8150c5a5c611beb4cf315c5` | included |
| `pair/aimo/paper/numbers/w9b-t040.json` | 37859 | `12115118fd1efa959e79408d9b51233a8afebb1c21a3393e4c0f57ac944872a8` | included |
| `pair/aimo/paper/numbers/w9b-t041b.json` | 15989 | `afaf0c8a667cd0cc81d3e9da5bcb314537a1d890d67c8039276dc6ef31ac5bb5` | included |
| `pair/aimo/paper/numbers/w9b-t042.json` | 6934 | `70b6da314676049dceeeee68ce00525f94f2f31ac1d6e0393b1113bf32b7e2f6` | included |
| `pair/aimo/paper/numbers/w9b-t043.json` | 4350 | `7e1407384b939a7ad0d3481ac4ea473842fcff97b64d08a3b5c27c357484406b` | included |
| `pair/aimo/paper/numbers/w9b-t044.json` | 9558 | `ee93f12c2b5bf1c1b62a5fa5078cce4454004764fdb49e6bee4ab00c03461700` | included |
| `pair/aimo/report/fig1_tag_null_sham_v4b.png` | 196231 | `781974c38833a8086213c4faa9b6e3c400ce4aef568ced52670d7ce95f3a508a` | included |
| `pair/aimo/report/make_cx2_repro.py` | 4420 | `24150363a06397cfefdcea2fffbd7d204ffba819b0a2bbe22f4dfe4a5793d61e` | included |
| `pair/aimo/report/numbers/ar1-t104.json` | 13531 | `1a0416fbe90923a0bac20beded5135de78cc0f66f8a14177a90fd5d1cca0a6c6` | included |
| `pair/aimo/report/numbers/ar1-t105.json` | 1816 | `d67db42ee1d2db89ad09b1df105b2e0d0c360dd4b104e80e274fe1a1564e7e0f` | included |
| `pair/aimo/report/numbers/ar1-t105b.json` | 609 | `74f60234e9f6f3d4cc43d3b8b1dd8e81b3afd24c1769e1bbe85189aef136176d` | included |
| `pair/aimo/report/numbers/ar2-t106.json` | 7199 | `0e7c730da5afa84ce9b4bb41c19cb65d57a6cd0485014c24f32d6011409ba10d` | included |
| `pair/aimo/report/numbers/ar2-t107.json` | 3823 | `50a2fe48460490097b261664b678e059bd50a5628072d3c7106ee3fa8a768c11` | included |
| `pair/aimo/report/numbers/cx2-repro.json` | 4952 | `ec084365bc5f59e89943932ce897edc0a627e0d6e7bb99c5a2f87051f8d6c0f4` | included |
| `pair/aimo/report/numbers/d14-t004.json` | 12660 | `ce6420b64d54485f44b6f7249b0fdd5ee9bdd52b53b79ba359d71e010fb691f1` | included |
| `pair/aimo/report/numbers/m1g-t001.json` | 2408 | `bf27ac9f8e13b5fdfceb485ae81c3b5106fd6bb1fc2978a73f909e662a7c6b49` | A |
| `pair/aimo/report/numbers/m1h-t002.json` | 5802 | `c92d2b1ab7e4da0cb47cd9e5b42289a125742029fea32d5683034ab8f6c30335` | included |
| `pair/aimo/report/numbers/w9b-t003.json` | 8125 | `856dd96c7eadb5d2c4eb6920a9d3074744a97b63f88d4b798cb8577362fac516` | included |
| `pair/aimo/report/numbers/w9b-t084.json` | 15123 | `1e473d6f24c99beec5fb67bc4686dc92f84815f589ab8e1792084e9babb3aadd` | included |
| `pair/aimo/report/numbers/w9b-t086.json` | 5810 | `e166f2d94631fdb9cdc42f575dc2eb4e5ae2dccf59703b77522fe1c87ff2607a` | included |
| `pair/aimo/report/numbers/w9b-t087.json` | 7654 | `17ea69b658ca1502af0d7c9d9a878cfc2f985020c29c7803d14c6ed0c2cd8957` | included |
| `pair/aimo/report/numbers/w9b-t087b.json` | 822 | `50ca6e6ffc92950cfdc6e692f2617e0ce29f5df6a359d51de66333abc29f4006` | included |
| `pair/aimo/report/numbers/w9b-t090.json` | 703 | `c62aca0382f65f1514f933df946063b58b1a986ea0112ec9c7260aa3ceac2dc5` | included |
| `pair/aimo/report/numbers/w9b-t090b.json` | 601 | `aee577a5cabae5c7cd6818f24ae07fca8e3ca3446991b8cfb795a5f4ad7a21f5` | included |
| `pair/aimo/report/numbers/w9c-t093.json` | 3855 | `77e96c2b38f9c3a6cfe2e7ade254737b448cbe7fb78b7fb7a356134cccf62968` | included |
| `planning/analysis/calibration-volume-hold-20261019.json` | 647 | `7842729ed488eb7a1c56926c7b7b6c5b6cbcc57f370f4f79537ec99b7518d5cb` | C |
| `planning/gpu-ops/RANDOM100-FINAL-FOR-SCORING-CL4-20261027.json` | 1245 | `50827b88984b06301fc5d42f071fd5da60394f065643961ec2c10662c4ef4061` | included |
| `planning/gpu-ops/SHAM-PHASE1-FINAL-CL4-20261026.json` | 907 | `3d1fc4d37fe6397b508e67df7d717e41b2f5264e4632217e984166ba10fb1eaf` | included |
| `explore/W9b/sham1/REQUESTS.json` | 99117540 | `68129da3f8c178b2bea4a8c5b9ef67f9ca5dd8bbf7f62652abd8e31d9ea3f8c2` | D |
| `explore/W9b/sham1/TRUTHS.json` | 6879001 | `a17a313bd39efb0c0f21c4d7a50a6c93e8baf7e34d70349e93556e744b8af835` | D |
| `explore/W9b/decomp/DECOMP-SPEC-20261025.md` | 7567 | `14c232c077f22cd7c0401b0285204abd5df164b804ca9f2a9b665727c567f755` | E |
| `explore/W9b/decomp/SHAM-SPEC-20261025.md` | 5563 | `019827a0670718a78a5eaee262c8212100d917ecc77f7a38eb5bf41f61a670f4` | E |
| `pair/aimo/report/REPORT-DRAFT-v1.4e.source.md` | 59375 | `6d81750f42695e532a6491aca6a39ce1554c924fc4a3c919f24eda4f49b0b6f7` | E |
| `pair/aimo/report/v1.6/md2tex_v16b.py` | 14836 | `107888dc899be9420c3fe52f658e7cd014ea359c6f4ebfdd394a757d01db0268` | E |
