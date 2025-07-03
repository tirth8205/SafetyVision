"""
Pytest configuration and shared fixtures
"""

import pytest
import numpy as np
from datetime import datetime

@pytest.fixture(scope="session")
def test_image():
    """Shared test image fixture"""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

@pytest.fixture(scope="session") 
def test_config():
    """Test configuration settings"""
    return {
        "vlm_model": "test-model",
        "temperature": 0.1,
        "max_tokens": 100,
        "confidence_threshold": 0.8
    }