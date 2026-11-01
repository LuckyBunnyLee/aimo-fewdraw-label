# 170 — Frozen state readout across existing protocols

**Exploratory cross-protocol transfer; historically exposed labels, not fresh validation.** [Prespec](continuous0910/170/SPEC-BEFORE-SCORES.json), [disjointness](continuous0910/170/DISJOINTNESS.json), [metrics](continuous0910/170/METRICS.json).

Apply the six frozen original-only report-168 models without fitting or calibration. Exclude all training UIDs, ancestry groups, normalized text hashes and base feature keys before scoring. This retains 281 rows, separated by source/protocol. Primary is MATH; no pooled AUC is reported.

|protocol|model|originals|NR|AUC|gain_frozen_length|gain_ci95|
|---|---|---|---|---|---|---|
|CL-long6h-v1-aime-checked-cap4096|length|1|0|None|None|None|
|CL-long6h-v1-aime-checked-cap4096|PRIMARY_originalPCA16|1|0|None|None|None|
|CL-long6h-v1-gsm-P1P2-cap4096|length|12|2|0.5|0|[0, 0]|
|CL-long6h-v1-gsm-P1P2-cap4096|PRIMARY_originalPCA16|12|2|0.3|-0.2|[-0.5458, 0.2]|
|CL-long6h-v1-gsm-symbolic100-cap4096|length|37|3|0.7941|0|[0, 0]|
|CL-long6h-v1-gsm-symbolic100-cap4096|PRIMARY_originalPCA16|37|3|0.8922|0.09804|[-0.1667, 0.3056]|
|CL-long6h-v1-gsmplus-extra-families100-cap4096|length|81|46|0.7786|0|[0, 0]|
|CL-long6h-v1-gsmplus-extra-families100-cap4096|PRIMARY_originalPCA16|81|46|0.8193|0.04068|[-0.06759, 0.1523]|
|CL-long6h-v1-gsmplus-remaining819-cap4096|length|38|14|0.3988|0|[0, 0]|
|CL-long6h-v1-gsmplus-remaining819-cap4096|PRIMARY_originalPCA16|38|14|0.494|0.09524|[-0.09862, 0.2917]|
|CL-long6h-v1-math-hard-cap4096|length|97|28|0.6755|0|[0, 0]|
|CL-long6h-v1-math-hard-cap4096|PRIMARY_originalPCA16|97|28|0.6599|-0.01553|[-0.1627, 0.1224]|
|CL-long6h-v1-own-checked85-cap4096|length|15|2|0.3077|0|[0, 0]|
|CL-long6h-v1-own-checked85-cap4096|PRIMARY_originalPCA16|15|2|0.3077|0|[-0.2308, 0.3333]|

On MATH, 97 originals/28 NR, frozen state AUC 0.660 versus frozen length 0.675 gives -0.016 [-0.163,0.122]. Both cross-protocol screen references are 1. The state candidate does not establish a MATH increment. Extra-family GSM-Plus gives +0.041 [-0.068,0.152]; symbolic has only three NR. No favourable source or secondary model replaces the primary.

Use 2,000 ancestry-group paired bootstraps and 1,200 fixed-score six-model shuffles per reference mode, with within-protocol and cross-protocol maxima. Cross-protocol maximum eligibility requires at least 40 originals and ten cases of each class. Tiny or unary sources remain descriptive. Retargeted extra-family/symbolic protocols can change answer keys or meaning, so these are protocol transfer tests rather than certified answer-preserving nuisance robustness. Remaining-GSM rows are selected exclusions from the original binary cohort. No hard-pack labels or sealed TEST was scored.
