import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from api.models import (
    HospitalAccount,
    DistrictCenter,
    Patient,
    ScreeningSession,
    ClinicalValidation
)

class APIEndpointsIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Seed hospital account
        self.hospital = HospitalAccount.objects.create(
            hospital_id='HOSP-AIIMS-TEST',
            name='AIIMS Tele-Retina Regional Node',
            email='test-tele-retina@aiims.edu',
            contact_number='+91 9876543210',
            district='New Delhi',
            state='Delhi',
            hospital_type='APEX_TELE'
        )
        self.hospital.set_password('MedicalAI2026!')
        self.hospital_token = self.hospital.generate_token()

        # Seed district center
        self.center = DistrictCenter.objects.create(
            hospital_account=self.hospital,
            name='Rural Health Centre Najafgarh',
            code='PHC-DL-NJ-01',
            district='South West Delhi',
            state='Delhi',
            level='PHC',
            catchment_population=60000,
            bandwidth_kbps=2048
        )

        # Seed patient
        self.patient = Patient.objects.create(
            mrn='MRN-TEST-API-001',
            first_name='Sunita',
            last_name='Devi',
            age=49,
            gender='F',
            district_center=self.center,
            hospital_account=self.hospital,
            hba1c_level=8.1,
            systolic_bp=130,
            diastolic_bp=85
        )

    def test_district_centers_api(self):
        """Test listing and filtering of district health centers."""
        response = self.client.get('/api/centers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['code'], 'PHC-DL-NJ-01')

    def test_patient_registration_and_search(self):
        """Test creating a new patient intake and quick search functionality."""
        new_mrn = f"MRN-API-{uuid.uuid4().hex[:6]}"
        payload = {
            'mrn': new_mrn,
            'first_name': 'Kavita',
            'last_name': 'Singh',
            'age': 55,
            'gender': 'F',
            'district_center': str(self.center.id),
            'diabetes_type': 'TYPE2',
            'diabetes_duration_years': 7.0,
            'hba1c_level': 7.9,
            'systolic_bp': 128,
            'diastolic_bp': 82
        }
        res = self.client.post('/api/patients/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['mrn'], new_mrn)

        # Search for patient
        search_res = self.client.get('/api/patients/quick_search/?q=Kavita')
        self.assertEqual(search_res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(search_res.data), 1)

    def test_screening_session_lifecycle(self):
        """Test creating a screening session and retrieving its clinical details."""
        session_code = f"SESS-{uuid.uuid4().hex[:8]}"
        res = self.client.post('/api/screenings/', {
            'session_code': session_code,
            'patient': str(self.patient.id),
            'district_center': str(self.center.id),
            'hospital_account': str(self.hospital.id)
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        session_id = res.data['id']

        # Retrieve detail
        detail_res = self.client.get(f'/api/screenings/{session_id}/')
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data['session_code'], session_code)

    def test_doctor_session_validation(self):
        """Test clinical verification sign-off by ophthalmologist."""
        session = ScreeningSession.objects.create(
            session_code=f"SESS-VAL-{uuid.uuid4().hex[:6]}",
            patient=self.patient,
            district_center=self.center,
            hospital_account=self.hospital,
            status='AI_GRADED'
        )

        validation_payload = {
            'confirmed_icdr_grade': 2,
            'ophthalmologist_name': 'Dr. Rajan, MD (Retina)',
            'clinical_notes': 'Confirmed Moderate NPDR with macular ring exudates.',
            'treatment_plan': 'Refer to district tertiary centre for optical coherence tomography (OCT).',
            'validation_duration_seconds': 28.5
        }

        res = self.client.post(
            f'/api/screenings/{session.id}/validate_session/',
            validation_payload,
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        session.refresh_from_db()
        self.assertEqual(session.status, 'VERIFIED')
        self.assertEqual(session.referral_recommendation, 'PRIORITY_3MO')

    def test_hospital_authentication_flow(self):
        """Test hospital node login and identity retrieval."""
        # 1. Successful Login
        login_res = self.client.post('/api/auth/login/', {
            'hospital_id': 'HOSP-AIIMS-TEST',
            'password': 'MedicalAI2026!'
        }, format='json')
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertIn('token', login_res.data)
        token = login_res.data['token']

        # 2. Authenticated me endpoint
        me_res = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(me_res.status_code, status.HTTP_200_OK)
        self.assertTrue(me_res.data['authenticated'])
        self.assertEqual(me_res.data['hospital']['hospital_id'], 'HOSP-AIIMS-TEST')

        # 3. Invalid credentials rejection
        bad_login = self.client.post('/api/auth/login/', {
            'hospital_id': 'HOSP-AIIMS-TEST',
            'password': 'WrongPassword123'
        }, format='json')
        self.assertEqual(bad_login.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_analytics_and_simulation_apis(self):
        """Test clinical analytics aggregation and district discrete event simulation."""
        # Analytics overview
        analytics_res = self.client.get('/api/analytics/overview/')
        self.assertEqual(analytics_res.status_code, status.HTTP_200_OK)
        self.assertIn('summary', analytics_res.data)
        self.assertIn('icdr_distribution', analytics_res.data)

        # Simulink simulation
        sim_res = self.client.post('/api/simulation/run/', {
            'annual_target': 80000,
            'active_phcs': 35,
            'ophthalmologist_count': 3,
            'doctor_hours_per_day': 5.0,
            'avg_bandwidth_kbps': 2048,
            'use_edge_ai': True,
            'enable_30s_fast_review': True
        }, format='json')
        self.assertEqual(sim_res.status_code, status.HTTP_200_OK)
        self.assertIn('throughput_metrics', sim_res.data)
        self.assertIn('economic_impact', sim_res.data)
