#!/usr/bin/env python3
import os
import sys
import django
from django.test.utils import get_runner
from django.conf import settings

def run_tests():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_root = os.path.join(project_root, 'backend')
    
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    django.setup()

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False)
    
    # Run tests in testing/backend as well as api.tests
    test_labels = [
        'testing.backend.test_api_endpoints',
        'testing.backend.test_ai_pipeline',
        'testing.backend.test_model_inference',
        'api.tests'
    ]
    
    failures = test_runner.run_tests(test_labels)
    sys.exit(bool(failures))

if __name__ == '__main__':
    run_tests()
