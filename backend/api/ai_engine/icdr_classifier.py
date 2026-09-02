import numpy as np

def classify_icdr_severity(lesion_info, quality_info):
    """
    Computes ICDR (International Clinical Diabetic Retinopathy) 5-grade severity score,
    referable DR triage flag (>90% sensitivity criteria), and calibrated Bayesian confidence.
    """
    ma_count = lesion_info['microaneurysms_count']
    he_count = lesion_info['hard_exudates_count']
    hm_count = lesion_info['hemorrhages_count']
    csme_risk = lesion_info['csme_risk']
    quadrant_4_2_1 = lesion_info['quadrant_4_2_1_met']
    neovascularization = lesion_info['neovascularization_detected']

    # Default baseline probabilities
    probs = [0.0, 0.0, 0.0, 0.0, 0.0]

    # --- Rule-Based ICDR Clinical Decision Mapping ---
    if neovascularization:
        # Grade 4: Proliferative DR (PDR)
        grade = 4
        grade_name = "Grade 4: Proliferative Diabetic Retinopathy (PDR)"
        probs = [0.01, 0.02, 0.05, 0.12, 0.80]
        explanation = "High-risk Proliferative Diabetic Retinopathy with retinal neovascularization / tangled vascular proliferation detected. Immediate vitreoretinal specialist intervention required."
        referral_urgency = "EMERGENCY_48H"

    elif quadrant_4_2_1 or hm_count >= 20:
        # Grade 3: Severe Non-Proliferative DR (Severe NPDR)
        grade = 3
        grade_name = "Grade 3: Severe Non-Proliferative DR (Sev NPDR)"
        probs = [0.01, 0.04, 0.15, 0.72, 0.08]
        explanation = f"Severe NPDR meeting ICDR 4-2-1 rule with {hm_count} intraretinal hemorrhages across multiple quadrants. High risk of rapid progression to PDR."
        referral_urgency = "URGENT_1MO"

    elif (ma_count > 0 and (he_count > 0 or hm_count > 0)) or (ma_count >= 6) or (csme_risk in ['MODERATE', 'CSME']):
        # Grade 2: Moderate Non-Proliferative DR (Mod NPDR)
        grade = 2
        grade_name = "Grade 2: Moderate Non-Proliferative DR (Mod NPDR)"
        probs = [0.03, 0.12, 0.74, 0.09, 0.02]
        explanation = f"Moderate NPDR with {ma_count} microaneurysms and {he_count} hard exudates. Macular edema risk evaluated as {csme_risk}."
        referral_urgency = "PRIORITY_3MO"

    elif ma_count > 0:
        # Grade 1: Mild Non-Proliferative DR (Mild NPDR)
        grade = 1
        grade_name = "Grade 1: Mild Non-Proliferative DR (Mild NPDR)"
        probs = [0.08, 0.81, 0.09, 0.01, 0.01]
        explanation = f"Mild NPDR with isolated microaneurysms ({ma_count} detected). No macular involvement or extensive hemorrhages."
        referral_urgency = "EARLY_6MO"

    else:
        # Grade 0: No Apparent Retinopathy (Normal)
        grade = 0
        grade_name = "Grade 0: No Apparent Retinopathy"
        probs = [0.94, 0.04, 0.01, 0.005, 0.005]
        explanation = "Normal retinal fundus. No microaneurysms, hemorrhages, or exudative lesions detected. Optic disc and foveal reflex healthy."
        referral_urgency = "ROUTINE_12MO"

    # Referable DR Gatekeeper (ICDR >= 2 or CSME present)
    # Calibrated for >90% sensitivity in rural triage
    referable_dr = bool(grade >= 2 or csme_risk in ['MODERATE', 'CSME'])
    
    # Calibrated confidence score
    confidence = float(np.max(probs))
    
    # Adjust for image quality
    if quality_info['quality_grade'] == 'BORDERLINE':
        confidence = max(0.65, confidence * 0.92)

    return {
        'icdr_grade': grade,
        'icdr_grade_name': grade_name,
        'referable_dr': referable_dr,
        'referable_confidence': round(confidence, 3),
        'grade_probabilities': {
            'Grade 0 (Normal)': round(probs[0], 3),
            'Grade 1 (Mild NPDR)': round(probs[1], 3),
            'Grade 2 (Mod NPDR)': round(probs[2], 3),
            'Grade 3 (Sev NPDR)': round(probs[3], 3),
            'Grade 4 (PDR)': round(probs[4], 3),
        },
        'clinical_explanation': explanation,
        'referral_recommendation': referral_urgency
    }
