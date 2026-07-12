import unittest
from datetime import datetime
from domain.opportunity import OpportunityCase, OpportunityStatus
from domain.lifecycle import LifecycleException

class TestOpportunityCase(unittest.TestCase):
    def setUp(self):
        self.now = datetime.utcnow()
        self.opportunity = OpportunityCase(
            id="123",
            title="Software Engineer",
            company="Acme Corp",
            status=OpportunityStatus.Detected,
            confidence_score=1.0,
            raw_ingestion_data={},
            created_at=self.now,
            updated_at=self.now
        )

    def test_post_init_validates_title_and_company(self):
        with self.assertRaises(ValueError):
            OpportunityCase("1", "", "Acme Corp", OpportunityStatus.Detected, 1.0, {}, self.now, self.now)
            
        with self.assertRaises(ValueError):
            OpportunityCase("1", "Title", "  ", OpportunityStatus.Detected, 1.0, {}, self.now, self.now)

    def test_advance_status_linear_progression(self):
        self.opportunity.transition_to(OpportunityStatus.Evaluating)
        self.assertEqual(self.opportunity.status, OpportunityStatus.Evaluating)
        
        self.opportunity.transition_to(OpportunityStatus.Preparing)
        self.assertEqual(self.opportunity.status, OpportunityStatus.Preparing)

    def test_advance_status_backwards_transition_raises_error(self):
        self.opportunity.transition_to(OpportunityStatus.Evaluating)
        self.opportunity.transition_to(OpportunityStatus.Preparing)
        
        with self.assertRaises(LifecycleException):
            self.opportunity.transition_to(OpportunityStatus.Evaluating)

    def test_advance_status_to_closed_from_any_state(self):
        self.opportunity.transition_to(OpportunityStatus.Closed)
        self.assertEqual(self.opportunity.status, OpportunityStatus.Closed)
        
        opp2 = OpportunityCase("2", "Title", "Company", OpportunityStatus.Interview, 1.0, {}, self.now, self.now)
        opp2.transition_to(OpportunityStatus.Closed)
        self.assertEqual(opp2.status, OpportunityStatus.Closed)

if __name__ == '__main__':
    unittest.main()
