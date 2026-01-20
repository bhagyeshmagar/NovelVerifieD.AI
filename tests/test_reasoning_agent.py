"""Tests for the reasoning agent."""

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.reasoning_agent import (
    synthesize_verdict,
    exponential_backoff_delay,
    CONTRADICTION_THRESHOLD,
    STRONG_SUPPORT_THRESHOLD,
    WEAK_CONTRADICTION_THRESHOLD
)
from agents.constraint_types import Verdict, ConstraintType, SubClaim


class TestExponentialBackoff:
    """Tests for the exponential_backoff_delay function."""
    
    @pytest.mark.unit
    def test_first_attempt_returns_base_delay(self):
        """First attempt should return around base delay."""
        delay = exponential_backoff_delay(0)
        # Should be BASE_DELAY (1.0) +/- 25% jitter
        assert 0.75 <= delay <= 1.25
    
    @pytest.mark.unit
    def test_delay_increases_exponentially(self):
        """Delay should increase with each attempt."""
        # Test multiple times to account for jitter
        delays = []
        for attempt in range(3):
            delays.append(exponential_backoff_delay(attempt))
        
        # Later attempts should generally have larger delays (allowing for jitter)
        # The base delay doubles each time, so delay2 should be > delay0
        assert delays[2] > delays[0]
    
    @pytest.mark.unit
    def test_delay_capped_at_max(self):
        """Delay should be capped at MAX_DELAY."""
        # At attempt 10, delay would be 2^10 = 1024 without cap
        delay = exponential_backoff_delay(10)
        # MAX_DELAY is 60.0, +/- 25% jitter
        assert delay <= 75.0


class TestSynthesizeVerdict:
    """Tests for the synthesize_verdict function."""
    
    @pytest.mark.unit
    def test_strong_contradiction_wins(self):
        """Strong contradiction should result in CONTRADICTED verdict."""
        sub_claims = []
        verdict, conf, reason = synthesize_verdict(
            support_conf=0.8,  # High support
            support_reason="Evidence supports",
            contradict_conf=0.5,  # Above CONTRADICTION_THRESHOLD (0.4)
            contradict_reason="Timeline violation found",
            violation_type="temporal",
            sub_claims=sub_claims
        )
        
        assert verdict == Verdict.CONTRADICTED
        assert conf > 0.5
        assert "temporal" in reason.lower() or "violation" in reason.lower()
    
    @pytest.mark.unit
    def test_high_support_with_low_contradiction(self):
        """High support with low contradiction should result in SUPPORTED."""
        sub_claims = []
        verdict, conf, reason = synthesize_verdict(
            support_conf=0.8,  # Above STRONG_SUPPORT_THRESHOLD (0.7)
            support_reason="Clear evidence found",
            contradict_conf=0.1,  # Below WEAK_CONTRADICTION_THRESHOLD (0.25)
            contradict_reason="No contradictions",
            violation_type="none",
            sub_claims=sub_claims
        )
        
        assert verdict == Verdict.SUPPORTED
        assert conf > 0.6
    
    @pytest.mark.unit
    def test_ambiguous_becomes_undetermined(self):
        """Ambiguous evidence should result in UNDETERMINED."""
        sub_claims = []
        # Moderate support and moderate contradiction
        verdict, conf, reason = synthesize_verdict(
            support_conf=0.5,
            support_reason="Some evidence",
            contradict_conf=0.35,  # Below threshold but not negligible
            contradict_reason="Possible issues",
            violation_type="none",
            sub_claims=sub_claims
        )
        
        assert verdict == Verdict.UNDETERMINED
    
    @pytest.mark.unit
    def test_weak_support_is_undetermined(self):
        """Weak support should be UNDETERMINED even with no contradiction."""
        sub_claims = []
        verdict, conf, reason = synthesize_verdict(
            support_conf=0.6,  # Below STRONG_SUPPORT_THRESHOLD (0.7)
            support_reason="Weak evidence",
            contradict_conf=0.1,
            contradict_reason="None found",
            violation_type="none",
            sub_claims=sub_claims
        )
        
        assert verdict == Verdict.UNDETERMINED
    
    @pytest.mark.unit
    def test_moderate_contradiction_blocks_support(self):
        """Moderate contradiction should prevent SUPPORTED verdict."""
        sub_claims = []
        verdict, conf, reason = synthesize_verdict(
            support_conf=0.8,  # High support
            contradict_conf=0.3,  # Above WEAK_CONTRADICTION_THRESHOLD (0.25)
            support_reason="Good evidence",
            contradict_reason="Some issues",
            violation_type="none",
            sub_claims=sub_claims
        )
        
        # Should NOT be supported because contradiction is too high
        assert verdict != Verdict.SUPPORTED


class TestAntibiasThresholds:
    """Tests for the anti-bias threshold configuration."""
    
    @pytest.mark.unit
    def test_thresholds_are_reasonable(self):
        """Anti-bias thresholds should be set to reasonable values."""
        # Contradiction threshold should be low enough to catch issues
        assert CONTRADICTION_THRESHOLD <= 0.5
        
        # Support threshold should be high enough to require strong evidence
        assert STRONG_SUPPORT_THRESHOLD >= 0.6
        
        # Weak contradiction threshold should be lower than main threshold
        assert WEAK_CONTRADICTION_THRESHOLD < CONTRADICTION_THRESHOLD
    
    @pytest.mark.unit
    def test_thresholds_prevent_bias(self):
        """Thresholds should be designed to prevent 'supported' bias."""
        # The sum of support threshold and weak contradiction threshold
        # should help ensure we don't trivially reach 'supported'
        assert STRONG_SUPPORT_THRESHOLD + WEAK_CONTRADICTION_THRESHOLD > 0.5
