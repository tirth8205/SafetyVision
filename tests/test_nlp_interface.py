"""
Test suite for NLP Interface
"""

import pytest
import asyncio
from safetyvision.communication.nlp_interface import NLPInterface

class TestNLPInterface:
    """Test cases for Natural Language Interface"""
    
    @pytest.fixture
    def nlp_interface(self):
        """Create NLP interface instance for testing"""
        return NLPInterface()
    
    @pytest.mark.asyncio
    async def test_radiation_query(self, nlp_interface):
        """Test radiation-related queries"""
        result = await nlp_interface.process_command(
            "What are the current radiation levels?"
        )
        
        assert result['intent'] == 'radiation'
        assert 'radiation' in result['response'].lower()
        assert result['confidence'] > 0.5
    
    @pytest.mark.asyncio
    async def test_emergency_query(self, nlp_interface):
        """Test emergency-related queries"""
        result = await nlp_interface.process_command(
            "Emergency evacuation required!"
        )
        
        assert result['intent'] == 'evacuation'
        assert 'emergency' in result['response'].lower()
    
    @pytest.mark.asyncio
    async def test_maintenance_query(self, nlp_interface):
        """Test maintenance-related queries"""
        result = await nlp_interface.process_command(
            "Is it safe to perform maintenance in Zone A?"
        )
        
        assert result['intent'] == 'maintenance'
        assert 'maintenance' in result['response'].lower()
    
    def test_intent_classification(self, nlp_interface):
        """Test intent classification accuracy"""
        test_cases = [
            ("Check radiation levels", "radiation"),
            ("Temperature too high", "temperature"),
            ("Emergency stop needed", "evacuation"),
            ("Schedule maintenance", "maintenance"),
            ("How are things going?", "general_query")
        ]
        
        for query, expected_intent in test_cases:
            intent = nlp_interface._classify_intent(query)
            assert intent == expected_intent
    
    def test_decision_explanation(self, nlp_interface):
        """Test decision explanation functionality"""
        explanation = nlp_interface.explain_decision(
            "Robot stopped operation",
            "Why did the robot stop?"
        )
        
        assert len(explanation) > 50
        assert isinstance(explanation, str)