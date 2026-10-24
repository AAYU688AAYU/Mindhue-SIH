import numpy as np
from django.test import TestCase
from api.ai_engine.enhancement import enhance_fundus_image
from api.ai_engine.iqa import assess_image_quality
from api.ai_engine.left_right import detect_eye_laterality
from api.ai_engine.anatomical_detection import assess_fundus_landmarks
from api.ai_engine.lesion_detector import detect_retinal_lesions
from api.seed_helper import generate_synthetic_fundus

class RetinalAIPipelineUnitTestCase(TestCase):
    def setUp(self):
        # Generate baseline synthetic clinical fundus images
        self.clear_normal_od = generate_synthetic_fundus(icdr_grade=0, blur_level=0, illumination_level=1.0)
        self.severe_npdr_od = generate_synthetic_fundus(icdr_grade=3, blur_level=0, illumination_level=1.0)
        self.blurry_fundus = generate_synthetic_fundus(icdr_grade=0, blur_level=6, illumination_level=1.0)

    def test_fundus_enhancement(self):
        """Test adaptive illumination normalization and multi-scale CLAHE enhancement."""
        enhanced = enhance_fundus_image(self.clear_normal_od)
        self.assertIsNotNone(enhanced)
        self.assertEqual(enhanced.shape, self.clear_normal_od.shape)
        self.assertEqual(enhanced.dtype, np.uint8)

        # Edge case: Empty / None image
        self.assertIsNone(enhance_fundus_image(None))

    def test_image_quality_assessment_scoring(self):
        """Test IQA focus, illumination, and gradeability scoring."""
        # 1. High-quality clear fundus image
        iqa_clear = assess_image_quality(self.clear_normal_od)
        self.assertTrue(iqa_clear['gradeable'])
        self.assertGreaterEqual(iqa_clear['overall_score'], 70.0)
        self.assertGreaterEqual(iqa_clear['focus_score'], 60.0)

        # 2. Defocused / blurry fundus image
        iqa_blurry = assess_image_quality(self.blurry_fundus)
        self.assertLess(iqa_blurry['focus_score'], 55.0)

    def test_eye_laterality_detection(self):
        """Test OD (Right Eye) vs OS (Left Eye) determination."""
        res = detect_eye_laterality(self.clear_normal_od)
        self.assertIn(res['eye_code'], ['OD', 'OS'])
        self.assertGreaterEqual(res['confidence'], 0.50)
        self.assertIsNotNone(res['retina_center'])

    def test_anatomical_landmark_detection(self):
        """Test identification of Optic Disc, Macula, and vascular tree."""
        landmarks = assess_fundus_landmarks(self.clear_normal_od)
        self.assertIn('decision', landmarks)
        self.assertIn('details', landmarks)
        details = landmarks['details']
        self.assertIn('vessels', details)
        self.assertIn('optic_disc', details)
        self.assertIn('macula', details)

    def test_lesion_detection_and_end_to_end_analysis(self):
        """Test full clinical AI pipeline analysis on severe NPDR fundus image."""
        from api.ai_engine.pipeline import analyze_retinal_image
        res = analyze_retinal_image(self.severe_npdr_od)
        self.assertIn('quality', res)
        self.assertIn('classification', res)
        self.assertIn('lesions', res)
        self.assertIn('optic_disc', res)
        self.assertIn('vessels', res)

        lesions = res['lesions']
        self.assertIn('microaneurysms_count', lesions)
        self.assertIn('hard_exudates_count', lesions)
        self.assertIn('hemorrhages_count', lesions)
        self.assertIn('quadrant_counts', lesions)
        self.assertIn('csme_risk', lesions)
