import os
import cv2
import numpy as np
import uuid
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from .models import DistrictCenter, Patient, ScreeningSession, RetinalImage, AIAnalysis
from .ai_engine.pipeline import run_retinal_pipeline

def generate_synthetic_fundus(
    icdr_grade=0,
    blur_level=0,
    illumination_level=1.0,
    add_glaucoma=False,
    width=600,
    height=600
):
    """
    Generates a high-fidelity synthetic retinal fundus image representing specific
    clinical pathology, image quality defects, and anatomical landmarks.
    """
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # 1. Base circular fundus background
    center_x, center_y = width // 2, height // 2
    fundus_radius = int(min(width, height) * 0.44)
    
    # Create radial gradient for retinal pigmentation (warm orange-reddish glow)
    y_coords, x_coords = np.ogrid[:height, :width]
    dist_from_center = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
    
    # Retina base colors: deeper reddish-orange in center, darker at periphery
    mask = dist_from_center <= fundus_radius
    norm_dist = np.clip(dist_from_center / fundus_radius, 0, 1)
    
    red_chan = (210 - 75 * norm_dist**1.5).astype(np.uint8)
    green_chan = (85 - 45 * norm_dist**1.5).astype(np.uint8)
    blue_chan = (35 - 20 * norm_dist**1.5).astype(np.uint8)
    
    img[mask, 0] = red_chan[mask]
    img[mask, 1] = green_chan[mask]
    img[mask, 2] = blue_chan[mask]

    # 2. Optic Disc (OD) on the nasal side (e.g. right side for OD eye)
    od_x = int(center_x + fundus_radius * 0.52)
    od_y = center_y
    od_radius = int(fundus_radius * 0.22)
    
    # Draw glowing optic disc
    cv2.circle(img, (od_x, od_y), od_radius, (255, 220, 160), -1)
    
    # Physiological cup
    cup_radius = int(od_radius * 0.70 if add_glaucoma else od_radius * 0.38)
    cv2.circle(img, (od_x, od_y), cup_radius, (255, 245, 210), -1)

    # 3. Fovea & Macula on the temporal side (left of OD)
    fovea_x = int(center_x - fundus_radius * 0.25)
    fovea_y = center_y + int(fundus_radius * 0.05)
    
    # Darker avascular zone for fovea
    for r in range(int(od_radius * 1.4), 0, -2):
        darken_factor = 0.98
        sub_mask = (x_coords - fovea_x)**2 + (y_coords - fovea_y)**2 <= r**2
        img[sub_mask & mask] = (img[sub_mask & mask] * darken_factor).astype(np.uint8)

    # 4. Vascular Tree (Arcades emerging from Optic Disc)
    # Superior and Inferior temporal vascular arches
    vessel_color = (130, 20, 10)  # Deep dark red
    
    def draw_arcade(start_x, start_y, control_x, control_y, end_x, end_y, thickness=4):
        pts = []
        for t in np.linspace(0, 1, 60):
            # Quadratic Bezier
            bx = (1 - t)**2 * start_x + 2 * (1 - t) * t * control_x + t**2 * end_x
            by = (1 - t)**2 * start_y + 2 * (1 - t) * t * control_y + t**2 * end_y
            pts.append([int(bx), int(by)])
        pts = np.array(pts, np.int32).reshape((-1, 1, 2))
        cv2.polylines(img, [pts], isClosed=False, color=vessel_color, thickness=thickness)
        
        # Add small branching vessels
        for i in range(10, 50, 8):
            px, py = pts[i][0]
            dx = (px - fovea_x) * 0.3
            dy = (py - fovea_y) * 0.3
            cv2.line(img, (px, py), (int(px - dx), int(py - dy)), vessel_color, max(1, thickness - 2))

    # Superior temporal arcade
    draw_arcade(od_x, od_y, center_x, center_y - int(fundus_radius * 0.75), fovea_x - 60, fovea_y - 120, thickness=5)
    # Inferior temporal arcade
    draw_arcade(od_x, od_y, center_x, center_y + int(fundus_radius * 0.75), fovea_x - 60, fovea_y + 120, thickness=5)
    # Nasal vessels
    draw_arcade(od_x, od_y, od_x + 60, od_y - 60, od_x + 100, od_y - 90, thickness=3)
    draw_arcade(od_x, od_y, od_x + 60, od_y + 60, od_x + 100, od_y + 90, thickness=3)

    # 5. Add Diabetic Retinopathy Pathologies based on ICDR Grade
    np.random.seed(42 + icdr_grade)

    if icdr_grade >= 1:
        # Microaneurysms (small dark red circular dots)
        num_mas = 4 if icdr_grade == 1 else (14 if icdr_grade == 2 else 32)
        for _ in range(num_mas):
            rx = int(np.random.normal(fovea_x, fundus_radius * 0.45))
            ry = int(np.random.normal(fovea_y, fundus_radius * 0.45))
            if (rx - center_x)**2 + (ry - center_y)**2 < (fundus_radius * 0.8)**2:
                cv2.circle(img, (rx, ry), np.random.randint(2, 4), (100, 10, 5), -1)

    if icdr_grade >= 2:
        # Hard Exudates (bright yellowish waxy deposits near macula)
        num_exudates = 8 if icdr_grade == 2 else 24
        for _ in range(num_exudates):
            rx = int(np.random.normal(fovea_x + 35, 45))
            ry = int(np.random.normal(fovea_y - 25, 45))
            if (rx - center_x)**2 + (ry - center_y)**2 < (fundus_radius * 0.8)**2:
                cv2.circle(img, (rx, ry), np.random.randint(3, 7), (250, 245, 140), -1)

    if icdr_grade >= 3:
        # Extensive Intraretinal Hemorrhages across quadrants (Blot & Flame HMs)
        num_hms = 18 if icdr_grade == 3 else 35
        for _ in range(num_hms):
            rx = int(np.random.uniform(center_x - fundus_radius * 0.7, center_x + fundus_radius * 0.7))
            ry = int(np.random.uniform(center_y - fundus_radius * 0.7, center_y + fundus_radius * 0.7))
            if (rx - center_x)**2 + (ry - center_y)**2 < (fundus_radius * 0.8)**2:
                # Blot hemorrhage
                axes = (np.random.randint(6, 15), np.random.randint(4, 10))
                angle = np.random.randint(0, 180)
                cv2.ellipse(img, (rx, ry), axes, angle, 0, 360, (110, 12, 6), -1)

    if icdr_grade == 4:
        # Proliferative Neovascularization: Tortuous fine vessel tangle on disc
        for _ in range(12):
            nx1 = od_x + np.random.randint(-15, 15)
            ny1 = od_y + np.random.randint(-15, 15)
            nx2 = nx1 + np.random.randint(-25, 25)
            ny2 = ny1 + np.random.randint(-25, 25)
            cv2.line(img, (nx1, ny1), (nx2, ny2), (160, 25, 15), 2)
        # Large preretinal boat-shaped hemorrhage
        cv2.ellipse(img, (fovea_x + 50, fovea_y + 80), (35, 16), 15, 0, 180, (95, 8, 4), -1)

    # 6. Apply Image Quality Defect Modifiers
    if illumination_level != 1.0:
        img = np.clip(img * illumination_level, 0, 255).astype(np.uint8)

    if blur_level > 0:
        ksize = blur_level * 2 + 1
        img = cv2.GaussianBlur(img, (ksize, ksize), blur_level * 2)

    return img


from .models import HospitalAccount, DistrictCenter, Patient, ScreeningSession, RetinalImage, AIAnalysis
from .ai_engine.pipeline import run_retinal_pipeline

def seed_clinical_cases():
    """Generates and seeds diverse, medical-grade clinical benchmark cases and Hospital accounts."""
    # Ensure standard Hospital Accounts exist
    hosp_aiims, _ = HospitalAccount.objects.get_or_create(
        hospital_id='HOSP-AIIMS-01',
        defaults={
            'name': 'AIIMS Tele-Retina Apex Hub, New Delhi',
            'email': 'tele.retina@aiims.edu.in',
            'contact_number': '+91 11 26588500',
            'district': 'New Delhi',
            'state': 'Delhi',
            'hospital_type': 'APEX_TELE'
        }
    )
    hosp_aiims.set_password('password123')
    hosp_aiims.generate_token()

    hosp_pune, _ = HospitalAccount.objects.get_or_create(
        hospital_id='PHC-MH-PN-01',
        defaults={
            'name': 'Primary Health Centre Shirur, Pune',
            'email': 'phc.shirur.pune@nhm.gov.in',
            'contact_number': '+91 9822019482',
            'district': 'Pune',
            'state': 'Maharashtra',
            'hospital_type': 'PHC'
        }
    )
    hosp_pune.set_password('password123')
    hosp_pune.generate_token()

    hosp_varanasi, _ = HospitalAccount.objects.get_or_create(
        hospital_id='PHC-UP-VN-04',
        defaults={
            'name': 'Pindra Primary Health Center, Varanasi',
            'email': 'phc.pindra.up@nhm.gov.in',
            'contact_number': '+91 9415028391',
            'district': 'Varanasi',
            'state': 'Uttar Pradesh',
            'hospital_type': 'PHC'
        }
    )
    hosp_varanasi.set_password('password123')
    hosp_varanasi.generate_token()

    # Ensure standard District Centers exist and link to hospitals
    phc_pune, _ = DistrictCenter.objects.get_or_create(
        code='PHC-MH-PN-01',
        defaults={
            'name': 'Primary Health Centre Shirur',
            'district': 'Pune',
            'state': 'Maharashtra',
            'level': 'PHC',
            'catchment_population': 65000,
            'bandwidth_kbps': 2048,
            'camera_model': 'Forus 3nethra Classic HD',
            'operator_name': 'Savita G. (Community Health Officer)',
            'hospital_account': hosp_pune
        }
    )
    
    phc_varanasi, _ = DistrictCenter.objects.get_or_create(
        code='PHC-UP-VN-04',
        defaults={
            'name': 'Pindra Primary Health Center',
            'district': 'Varanasi',
            'state': 'Uttar Pradesh',
            'level': 'PHC',
            'catchment_population': 82000,
            'bandwidth_kbps': 1024,
            'camera_model': 'Remidio Non-Mydriatic Fundus on Phone (FOP)',
            'operator_name': 'Rakesh Patel (Senior Optometrist)',
            'hospital_account': hosp_varanasi
        }
    )


    cases_meta = [
        {
            'first': 'Ramesh', 'last': 'Patil', 'age': 54, 'gender': 'M',
            'mrn': 'MRN-2026-001', 'abha': '91-4829-1029-4821',
            'diabetes_type': 'TYPE2', 'duration': 4.5, 'hba1c': 6.8, 'bp_s': 122, 'bp_d': 78,
            'center': phc_pune, 'grade': 0, 'blur': 0, 'illum': 1.0, 'glaucoma': False,
            'notes': 'Normal screening. Glycemic control well-maintained.'
        },
        {
            'first': 'Sunita', 'last': 'Deshmukh', 'age': 49, 'gender': 'F',
            'mrn': 'MRN-2026-002', 'abha': '91-3829-5519-7712',
            'diabetes_type': 'TYPE2', 'duration': 7.0, 'hba1c': 7.6, 'bp_s': 136, 'bp_d': 86,
            'center': phc_pune, 'grade': 1, 'blur': 0, 'illum': 1.0, 'glaucoma': False,
            'notes': 'Mild NPDR with isolated microaneurysms in paramacular arcade.'
        },
        {
            'first': 'Mohammad', 'last': 'Ansari', 'age': 62, 'gender': 'M',
            'mrn': 'MRN-2026-003', 'abha': '91-7712-4491-0021',
            'diabetes_type': 'TYPE2', 'duration': 12.0, 'hba1c': 9.2, 'bp_s': 148, 'bp_d': 94,
            'center': phc_varanasi, 'grade': 2, 'blur': 0, 'illum': 1.0, 'glaucoma': False,
            'notes': 'Moderate NPDR with hard exudates encroaching 1DD from fovea.'
        },
        {
            'first': 'Lakshmi', 'last': 'Devi', 'age': 58, 'gender': 'F',
            'mrn': 'MRN-2026-004', 'abha': '91-1182-9930-4567',
            'diabetes_type': 'TYPE2', 'duration': 14.5, 'hba1c': 10.4, 'bp_s': 158, 'bp_d': 98,
            'center': phc_varanasi, 'grade': 3, 'blur': 0, 'illum': 1.0, 'glaucoma': False,
            'notes': 'Severe NPDR meeting 4-2-1 criteria. Immediate referral for FFA/anti-VEGF.'
        },
        {
            'first': 'Gurpreet', 'last': 'Singh', 'age': 65, 'gender': 'M',
            'mrn': 'MRN-2026-005', 'abha': '91-9921-3341-8891',
            'diabetes_type': 'TYPE1', 'duration': 22.0, 'hba1c': 11.2, 'bp_s': 162, 'bp_d': 102,
            'center': phc_pune, 'grade': 4, 'blur': 0, 'illum': 1.0, 'glaucoma': False,
            'notes': 'High-risk Proliferative Diabetic Retinopathy (NVD + preretinal bleed).'
        },
        {
            'first': 'Anil', 'last': 'Kulkarni', 'age': 61, 'gender': 'M',
            'mrn': 'MRN-2026-006', 'abha': '91-5521-7719-3321',
            'diabetes_type': 'TYPE2', 'duration': 8.0, 'hba1c': 8.1, 'bp_s': 142, 'bp_d': 90,
            'center': phc_pune, 'grade': 1, 'blur': 0, 'illum': 1.0, 'glaucoma': True,
            'notes': 'Concomitant Glaucoma Suspect (CDR 0.70) with Mild NPDR.'
        },
        {
            'first': 'Kavita', 'last': 'Yadav', 'age': 46, 'gender': 'F',
            'mrn': 'MRN-2026-007', 'abha': '91-2291-8831-7744',
            'diabetes_type': 'TYPE2', 'duration': 3.0, 'hba1c': 7.1, 'bp_s': 125, 'bp_d': 80,
            'center': phc_varanasi, 'grade': 0, 'blur': 4, 'illum': 1.0, 'glaucoma': False,
            'notes': 'Borderline focus blur test case.'
        },
        {
            'first': 'Bhanu', 'last': 'Prasad', 'age': 52, 'gender': 'M',
            'mrn': 'MRN-2026-008', 'abha': '91-6671-3382-9901',
            'diabetes_type': 'TYPE2', 'duration': 6.0, 'hba1c': 8.5, 'bp_s': 138, 'bp_d': 88,
            'center': phc_varanasi, 'grade': 0, 'blur': 0, 'illum': 0.28, 'glaucoma': False,
            'notes': 'Ungradeable underexposed capture test case.'
        }
    ]

    seeded_count = 0
    for meta in cases_meta:
        patient, _ = Patient.objects.get_or_create(
            mrn=meta['mrn'],
            defaults={
                'abha_id': meta['abha'],
                'first_name': meta['first'],
                'last_name': meta['last'],
                'age': meta['age'],
                'gender': meta['gender'],
                'village_or_city': f"Sector {meta['age'] % 9 + 1}, {meta['center'].district}",
                'district_center': meta['center'],
                'diabetes_type': meta['diabetes_type'],
                'diabetes_duration_years': meta['duration'],
                'hba1c_level': meta['hba1c'],
                'systolic_bp': meta['bp_s'],
                'diastolic_bp': meta['bp_d'],
                'contact_number': f"+91 98{np.random.randint(10000000, 99999999)}"
            }
        )

        session, _ = ScreeningSession.objects.get_or_create(
            session_code=f"SESS-{meta['mrn']}",
            defaults={
                'patient': patient,
                'district_center': meta['center'],
                'screener_name': meta['center'].operator_name,
                'status': 'PENDING_AI'
            }
        )

        # Generate synthetic image
        img_np = generate_synthetic_fundus(
            icdr_grade=meta['grade'],
            blur_level=meta['blur'],
            illumination_level=meta['illum'],
            add_glaucoma=meta['glaucoma']
        )

        pil_img = Image.fromarray(img_np)
        import io
        buf = io.BytesIO()
        pil_img.save(buf, format='JPEG', quality=95)
        content_file = ContentFile(buf.getvalue())
        retinal_img, created = RetinalImage.objects.get_or_create(
            session=session,
            eye='OD'
        )
        retinal_img.raw_image.save(f"raw_{meta['mrn']}_OD.jpg", content_file, save=True)

        # Execute AI analysis
        run_retinal_pipeline(retinal_img)
        seeded_count += 1

    return seeded_count
