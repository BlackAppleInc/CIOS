import inspect

from core.intelligence.drafter import ExecutiveDrafter
from core.intelligence.negotiator import NegotiationStrategist
from core.intelligence.scorer import OpportunityScorer
from core.intelligence.strategist import InterviewStrategist

classes = [ExecutiveDrafter, NegotiationStrategist, OpportunityScorer, InterviewStrategist]

print("--- TIER 1 AUDIT: STRICT INJECTION VERIFICATION ---")
for cls in classes:
    params = inspect.signature(cls.__init__).parameters
    print(f"Class {cls.__name__}.__init__ params: {list(params.keys())}")
    try:
        assert 'llm_provider' in params, f"'{cls.__name__}' failed strict 'llm_provider' check"
        print(f"  [PASS] {cls.__name__}")
    except AssertionError as e:
        print(f"  [FAIL] {e}")
