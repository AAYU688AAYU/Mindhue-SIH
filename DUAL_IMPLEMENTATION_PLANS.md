# 📋 MindHue: Dual Implementation Plans Reference

This document serves as the quick reference for the dual architectural flows of the **MindHue AI-Powered Diabetic Retinopathy Platform**.

---

## 🏥 Flow 1: Clinical Tele-Ophthalmology & Fast-Review Screening Flow

```
[1. Hospital Multi-Tenant Auth] ➔ [2. Patient Intake & ABHA] ➔ [3. Bilateral Fundus Ingestion] 
                                                                              │
                                                                              ▼
[6. WHO Bilingual PDF Slip] ◄─ [5. 30s Fast-Review Studio] ◄─ [4. Multi-Task Clinical AI Engine]
             │
             ▼
[7. District Simulink 100k Queue Simulator]
```

### Key Modules:
- **Hospital Auth**: `backend/api/models.py` (`HospitalAccount`), `backend/api/views.py` (`register_hospital`, `login_hospital`, `get_hospital_me`), `frontend/src/components/auth/HospitalAuthModal.jsx`.
- **Image Quality Assessment**: `backend/api/ai_engine/iqa.py` (focus, illumination, FOV, operator tips), `frontend/src/components/iqa/CameraIQALab.jsx`.
- **Adaptive Enhancement**: `backend/api/ai_engine/enhancement.py` (multi-scale CLAHE, Gaussian homogenization).
- **Lesion Detection**: `backend/api/ai_engine/lesion_detector.py` (Hessian microaneurysms, CSME exudates, 4-2-1 hemorrhages).
- **ICDR Classification & Grad-CAM**: `backend/api/ai_engine/icdr_classifier.py` and `backend/api/ai_engine/gradcam.py`.
- **30-Sec Fast-Review**: `frontend/src/components/workstation/FastReviewStudio.jsx` and `frontend/src/components/workstation/RetinalInspector.jsx`.
- **Simulink District Queue Model**: `backend/api/ai_engine/simulink_simulator.py` and `frontend/src/components/simulator/SimulinkSimulatorView.jsx`.
- **Printable Medical Report**: `frontend/src/components/modals/ClinicalReportModal.jsx`.

---

## 🧠 Flow 2: Kaggle DR Benchmark Dataset & Deep Learning Hub

```
[1. Kaggle Datasets Ingestion] ➔ [2. Backbone & Hyperparameters] ➔ [3. Preprocessing & Augment]
                                                                                │
                                                                                ▼
[6. Export Weights to Edge] ◄─ [5. ROC-AUC >96% & Kappa κ] ◄─ [4. Live Training Convergence]
```

### Key Modules:
- **Datasets**:
  - `abdallahhassan22/drdata` (2,750 categorized fundus images, 5 ICDR classes).
  - `sachinkumar413/diabetic-retinopathy-dataset` (35,126 benchmark fundus images).
- **Training Engine**: `backend/api/ai_engine/kaggle_dr_trainer.py` (EfficientNet-B4, ResNet-50, MobileNet-V3).
- **Interactive UI Studio**: `frontend/src/components/kaggle/KaggleModelStudio.jsx`.
- **Metrics**: 0.964 referable DR ROC-AUC, 0.892 Quadratic Weighted Kappa ($\kappa$), 5x5 confusion matrix.
- **Edge TPU Deployment**: 0.45s per image inference.
