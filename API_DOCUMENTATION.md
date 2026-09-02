# 📡 MindHue: REST API Reference Manual

Base URL: `http://127.0.0.1:8000/api/`

---

## 🔐 1. Hospital Multi-Tenant Authentication

### Register Hospital
- **Endpoint**: `POST /api/auth/register/`
- **Request Body**:
  ```json
  {
    "hospital_id": "DH-MH-KRD-01",
    "name": "District Hospital Karad",
    "email": "dh.karad@nhm.gov.in",
    "contact_number": "+91 9822019482",
    "district": "Satara",
    "state": "Maharashtra",
    "hospital_type": "DH",
    "password": "securepassword123"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "status": "success",
    "token": "hosp_tk_9f8a2b1c4e6d3f7a8c9e0b1d",
    "hospital": { "hospital_id": "DH-MH-KRD-01", "name": "District Hospital Karad", ... }
  }
  ```

### Login Hospital
- **Endpoint**: `POST /api/auth/login/`
- **Request Body**:
  ```json
  {
    "hospital_id": "HOSP-AIIMS-01",
    "password": "password123"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "token": "hosp_tk_8f9a2b1c4e6d3f7a",
    "hospital": { "hospital_id": "HOSP-AIIMS-01", "name": "AIIMS Tele-Retina Apex Hub", ... }
  }
  ```

### Get Active Hospital Profile
- **Endpoint**: `GET /api/auth/me/`
- **Headers**: `Authorization: Bearer <token>`

---

## 📊 2. Kaggle DR Datasets & Deep Learning Engine

### Get Dataset Summary
- **Endpoint**: `GET /api/kaggle/summary/`
- **Response (200 OK)**:
  ```json
  {
    "total_images": 37876,
    "datasets": {
      "abdallahhassan22_drdata": { "total_images": 2750, ... },
      "sachinkumar413_diabetic_retinopathy": { "total_images": 35126, ... }
    },
    "class_distribution": [
      { "grade": 0, "name": "Grade 0: Normal", "count": 26860, "percentage": 70.92 },
      ...
    ]
  }
  ```

### Train Deep Learning Model
- **Endpoint**: `POST /api/kaggle/train/`
- **Request Body**:
  ```json
  {
    "backbone": "EfficientNet-B4",
    "dataset": "sachinkumar413_diabetic_retinopathy",
    "epochs": 5,
    "learning_rate": 0.0003,
    "batch_size": 32,
    "use_clahe": true,
    "use_mixup": true
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "status": "COMPLETED",
    "final_validation_acc": 90.6,
    "final_quadratic_kappa": 0.892,
    "final_referable_auc": 0.964,
    "history": [ ... ],
    "confusion_matrix": [ ... ]
  }
  ```

---

## 🏥 3. Clinical Patients & Screening Sessions

### List Screenings Queue
- **Endpoint**: `GET /api/screenings/`

### Get Screening Detail
- **Endpoint**: `GET /api/screenings/{id}/`

### Upload Retinal Fundus & Run AI Pipeline
- **Endpoint**: `POST /api/screenings/{id}/upload_image/`
- **Body (Multipart Form)**:
  - `image`: File (JPEG/PNG)
  - `eye`: `OD` or `OS`

### 1-Click Clinical Validation
- **Endpoint**: `POST /api/screenings/{id}/validate_session/`
- **Request Body**:
  ```json
  {
    "ophthalmologist_name": "Dr. Ananya Sharma, MD (Retina)",
    "confirmed_icdr_grade": 2,
    "clinical_notes": "Hard exudates near fovea. Refer for OCT.",
    "treatment_plan": "Referral to district retina clinic within 30 days.",
    "validation_duration_seconds": 18.2
  }
  ```

---

## 📈 4. Tele-Simulation & Epidemiology Analytics

### Run Simulink 100k District Queue Simulation
- **Endpoint**: `POST /api/simulation/run/`
- **Request Body**:
  ```json
  {
    "annual_target": 100000,
    "active_phcs": 40,
    "ophthalmologist_count": 3,
    "doctor_hours_per_day": 4.0,
    "avg_bandwidth_kbps": 2048,
    "use_edge_ai": true,
    "enable_30s_fast_review": true
  }
  ```

### Get Epidemiological Overview
- **Endpoint**: `GET /api/analytics/overview/`
