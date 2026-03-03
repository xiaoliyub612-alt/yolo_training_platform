# Anomalib Plugin Backend Integration Design

**Date:** 2026-03-03
**Project:** yolo_training_platform
**Scope:** Integrate Anomalib (PatchCore first) into platform via plugin backend architecture.

## 1. Goals

- Add Anomalib support without breaking current YOLO workflows.
- Use plugin backend architecture for long-term extensibility.
- Support end-to-end flow: train -> predict -> review -> relabel queue.
- Keep YOLO dataset/training path unchanged.
- Add Anomalib data adapter (existing-dir -> folder format) plus standard folder mode.

## 2. Non-Goals

- No full rewrite of all UI pages in one step.
- No forced unification of YOLO dataset format into Anomalib format.
- No multi-model benchmarking framework in first phase.

## 3. Confirmed Decisions

- Architecture: Option 3 (pluginized model backend).
- Data intake: dual mode for Anomalib (`adapter` + `standard`).
- OK/NG decision: dual mode (`score` and `area`) with switch; default = `score`.
- YOLO path remains native and backward compatible.

## 4. High-Level Architecture

### 4.1 Backend Layer

Create `business/model_backends/`:

- `base.py`
  - Defines unified backend interface:
    - `healthcheck()`
    - `train(config, emit)`
    - `predict(config, emit)`
    - `export(config, emit)` (optional for Anomalib phase-1)
- `yolo_backend.py`
  - Wrap current YOLO train/predict flow behind interface.
- `anomalib_backend.py`
  - Implements PatchCore training and inference.
  - Produces score, heatmap/overlay, and manifest entries.

### 4.2 Router Layer

Create `business/backend_router.py`:

- Resolve backend by task config (`backend=yolo|anomalib`).
- Validate required fields before dispatch.
- Normalize error handling via `BackendError`.

### 4.3 Worker Layer

Create `tools/backend_worker.py`:

- Unified worker entrypoint for backend execution.
- Emit JSON event stream compatible with current UI threading model.
- Ensure batch terminal status on normal/failed/stopped exits.

### 4.4 UI Layer

- Add `ui/anomaly_widget.py` (or equivalent backend switch pane).
- Add backend selector and dynamic config panel.
- Keep existing `train_widget` and `predict_widget` usable during migration.
- Add entry tab in `ui/main_window.py` for anomaly flow.

## 5. Data & I/O Design

### 5.1 YOLO Data

- Keep current dataset maker and yaml training mechanism unchanged.

### 5.2 Anomalib Data

- `adapter` mode:
  - Parse existing directory style.
  - Build temporary folder-compliant structure for Anomalib `Folder` datamodule.
  - Return explicit diagnostics for missing requirements.
- `standard` mode:
  - Use user-provided canonical structure directly:
    - `train/good`
    - `test/good`
    - `test/<defect_name>`
    - optional `ground_truth`

### 5.3 Unified Output Layout

- Train outputs: `runs/<backend>/train/<timestamp>/`
- Predict outputs: `runs/<backend>/predict/<timestamp>/`
- Review archive: `runs/<backend>/predict/<timestamp>/review/OK|NG/...`

### 5.4 Unified Manifest Schema

Per image fields:

- `image_path`
- `backend`
- `label` (`OK` or `NG`)
- `score`
- `threshold_mode` (`score` or `area`)
- `threshold_value`
- `heatmap_path` (nullable)
- `overlay_path` (nullable)
- `raw_meta` (backend-specific extras)

Batch fields:

- `model_info`
- `data_info`
- `time_cost`
- `errors`

## 6. OK/NG Decision Rules

- Score mode (default):
  - `anomaly_score >= score_threshold => NG`, else `OK`.
- Area mode:
  - heatmap binarization -> anomaly area ratio
  - `area_ratio >= area_threshold => NG`, else `OK`.
- Both metrics are stored in `raw_meta` for auditability.

## 7. Error Handling Strategy

Create unified exception model:

- `BackendError(code, message, detail=None)`

Proposed error codes:

- `DATA_INVALID`
- `ENV_MISSING`
- `TRAIN_FAILED`
- `PREDICT_FAILED`
- `MANIFEST_BROKEN`

Behavior:

- UI shows concise `message`.
- Worker log persists full `detail` and traceback.
- Batch metadata always records terminal status (`success|failed|stopped`).

## 8. Testing Strategy

### 8.1 Unit

- Router dispatch correctness.
- Anomalib result parser and threshold logic (`score` / `area`).
- Manifest read/write compatibility checks.

### 8.2 Integration

- Minimal Anomalib sample run: train -> predict -> review list visibility.
- YOLO regression checks through plugin wrapper.

### 8.3 UI Smoke

- Backend switch behavior.
- Parameter persistence.
- Stop/abort and recovery states.

## 9. Migration Plan (Risk-Controlled)

1. Introduce backend abstraction + router with YOLO adapter only (no behavior change).
2. Add Anomalib backend (PatchCore phase-1).
3. Integrate unified manifest into review/relabel flow.
4. Switch UI calls to router, keep rollback switch for one release cycle.

## 10. Risks & Mitigations

- Risk: environment conflicts (torch/anomalib/vision).
  - Mitigation: backend-specific healthcheck and explicit startup diagnostics.
- Risk: user data format inconsistency.
  - Mitigation: adapter diagnostics and standard-mode fallback.
- Risk: review page incompatibility.
  - Mitigation: manifest contract tests and backward parser compatibility.

## 11. Acceptance Criteria

- User can select Anomalib PatchCore and complete train+predict in UI.
- Prediction outputs include score + heatmap/overlay + unified manifest.
- Review and relabel queue ingest Anomalib runs.
- Existing YOLO features still run without configuration changes.
