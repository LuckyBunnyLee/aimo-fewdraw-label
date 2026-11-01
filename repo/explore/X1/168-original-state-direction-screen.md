# 168 — Original prompt-state directions carry an exploratory signal

**Exploratory cached white-box screen; no inference or validation claim.** [Prespec](continuous0910/168/SPEC-BEFORE-SCORES.json), [metrics](continuous0910/168/METRICS.json), [freeze](continuous0910/168/FREEZE.json).

Read existing prompt-last states from 3,264 cached texts. Exclude the embedding layer, normalize each of 32 layer vectors to unit norm, average each consecutive eight-layer quartile, and apply the same fixed 64-dimensional Rademacher projection (seed 1945). Original-state PCA is fitted only inside the training folds. Primary is length plus the first 16 original-state PCs in fixed C=1 logistic regression. Compare original norm, input confidence, edit-state differences and independent base-answer behaviour. There are 696 nuisance GSM-Plus originals, including 161 NR in independent wave B. No harder-pack or independent-validation labels enter fitting.

|model|AUC|gain_length|pipeline_gain_length_ci95|screenP_length_fold|screenP_length_fold_lengthband|
|---|---|---|---|---|---|
|length|0.5733|0|[0, 0]|1|1|
|old_input|0.6027|0.02939|[-0.02875, 0.1001]|0.746|0.1207|
|norm4|0.6068|0.0335|[-0.02721, 0.08856]|0.7019|0.08576|
|PRIMARY_originalPCA16|0.6769|0.1035|[0.02392, 0.1844]|0.1207|0.0008326|
|originalPCA32|0.6664|0.09303|[-0.003273, 0.1742]|0.1765|0.0008326|
|input_originalPCA16|0.6663|0.09301|[0.003873, 0.1809]|0.1765|0.0008326|
|meanDeltaPCA16|0.5809|0.00761|[-0.07124, 0.07061]|0.9351|0.5371|
|concatDeltaPCA16|0.5904|0.01703|[-0.05253, 0.09617]|0.8609|0.2981|
|original_concatPCA16|0.6823|0.1089|[0.02913, 0.1943]|0.09409|0.0008326|
|scalar_drift|0.5794|0.006078|[-0.05962, 0.0708]|0.9409|0.5845|
|behaviour|0.6671|0.0938|[0.03225, 0.17]|0.1715|0.0008326|
|behaviour_originalPCA16|0.6841|0.1107|[0.02242, 0.1942]|0.0841|0.0008326|

Primary AUC 0.677 versus length 0.573 gives +0.104: conditional interval [0.048,0.159], complete-pipeline interval [0.024,0.184]. It adds 0.074 over input confidence but only 0.010 [-0.042,0.061] over base-answer behaviour. Scalar drift and edit-state differences are weaker. Original state direction is more promising than a scalar edit-distance probe on this development cohort.

The 12-readout maximum null gives P=0.121 for fold-wide shuffles and 0.000833 for length-band shuffles. These reference hypotheses disagree; this is a candidate, not a selection-adjusted confirmed win. There are 1,200 complete-screen refits per null mode, 2,000 original conditional bootstraps and 500 pipeline bootstraps including PCA, scaling and model fitting. All full models are frozen without selecting a different primary. Projection SHA is recorded with the exact matrix; raw state-file hashes are retained.

Extraction used read-only remote CPU NumPy, no model weights or GPU. The initial default Python lacked NumPy; the existing relay environment was used, documented before fitting. White-box prompt states require an auxiliary Qwen forward in deployment and are not a cheap text-only feature. Old formal validation failures remain unchanged. Cross-source and job-confounding diagnostics follow separately; cached state numerical fidelity is not established by the likelihood audit.

Label scope: NR is the sampled accuracy-drop endpoint under supplied benchmark keys and variant protocols. These analyses inherit the source/key/meaning limitations audited in reports 70/71; they do not certify per-original semantic robustness.

The matched 696-original cohort is the existing complete-case independent-wave screen, not every GSM source original. Model pretraining overlap is unknown. Original-state direction has not been established as a reading/recall mechanism.
