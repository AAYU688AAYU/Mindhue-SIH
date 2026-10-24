import numpy as np
from PIL import Image
from django.test import TestCase
from api.ai_engine.model_inference import DRModelInference, CLASS_NAMES
from api.seed_helper import generate_synthetic_fundus

class RetinalModelInferenceTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = DRModelInference.get_instance()
        cls.synthetic_fundus = generate_synthetic_fundus(icdr_grade=1, blur_level=0, illumination_level=1.0)
        cls.pil_fundus = Image.fromarray(cls.synthetic_fundus)

    def test_singleton_engine_initialization(self):
        """Verify DRModelInference instantiates properly as a thread-safe singleton."""
        engine2 = DRModelInference.get_instance()
        self.assertIs(self.engine, engine2)
        self.assertIsNotNone(self.engine.model)

    def test_single_forward_pass_prediction(self):
        """Verify single-image prediction schema and probability distribution."""
        result = self.engine.predict(self.synthetic_fundus, use_tta=False)
        
        self.assertIn('icdr_grade', result)
        self.assertIn(result['icdr_grade'], [0, 1, 2, 3, 4])
        self.assertIn('icdr_grade_name', result)
        self.assertIn(result['icdr_grade_name'], CLASS_NAMES)

        # Probabilities validation
        grade_probs = result['grade_probabilities']
        self.assertEqual(len(grade_probs), 5)
        prob_sum = sum(grade_probs.values())
        self.assertAlmostEqual(prob_sum, 1.0, places=2)
        self.assertGreaterEqual(result['confidence'], 0.0)
        self.assertLessEqual(result['confidence'], 1.0)

        # Clinical referable DR consistency
        is_ref = bool(result['referable_probability'] >= 0.5 or result['icdr_grade'] >= 2)
        self.assertEqual(result['referable_dr'], is_ref)

    def test_test_time_augmentation_5view_parity(self):
        """Verify 5-view Test-Time Augmentation (TTA) executes properly and stabilizes predictions."""
        result_tta = self.engine.predict(self.synthetic_fundus, use_tta=True)
        self.assertEqual(result_tta['inference_mode'], '5-view TTA')
        grade_probs = result_tta['grade_probabilities']
        self.assertEqual(len(grade_probs), 5)
        self.assertAlmostEqual(sum(grade_probs.values()), 1.0, places=2)

    def test_multi_format_input_support(self):
        """Verify engine accepts NumPy arrays, PIL Images, and handles type conversion seamlessly."""
        # 1. PIL Image input
        res_pil = self.engine.predict(self.pil_fundus)
        self.assertIn(res_pil['icdr_grade'], [0, 1, 2, 3, 4])

        # 2. Preprocessing shape check
        tensor = self.engine.preprocess_image(self.pil_fundus)
        self.assertEqual(tensor.ndim, 4)
        self.assertEqual(tensor.shape[0], 1)
        self.assertEqual(tensor.shape[1], 3)
