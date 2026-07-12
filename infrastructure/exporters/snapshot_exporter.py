import os
from datetime import datetime
from pathlib import Path
from domain.opportunity import OpportunityCase

class SnapshotExporter:
    """
    Exports aggregate opportunity information and AI-generated strategic 
    guidance into a clean, local markdown file strictly adhering to template.
    """
    def __init__(self, export_dir: str = "data/exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
    def export(self, opportunity: OpportunityCase, strategy: dict) -> str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        safe_date_str = datetime.utcnow().strftime("%Y%m%d")
        safe_company = "".join(c for c in opportunity.company if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        filename = f"Snapshot_{safe_company}_{safe_date_str}.md"
        dest_path = self.export_dir / filename
        
        score_percentage = int(opportunity.confidence_score * 100) if opportunity.confidence_score is not None else 0
        
        selling_points = "\n".join(f"- {point}" for point in strategy.get("key_selling_points", []))
        objections = "\n".join(f"- {obj}" for obj in strategy.get("potential_objections", []))
        risks = "\n".join(f"- {risk}" for risk in strategy.get("company_risks", []))
        questions = "\n".join(f"- {q}" for q in strategy.get("strategic_questions", []))
        mitigation = strategy.get("mitigation_strategy", "")
        
        content = f"""# 🎯 {opportunity.title} @ {opportunity.company}
**Generated:** {date_str} | **Status:** {opportunity.status.value} | **Confidence:** {score_percentage}%

## 1. Executive Summary
This snapshot provides a strategic assessment of the opportunity for {opportunity.title} at {opportunity.company}.

### Core Information
- **ID:** {opportunity.id}
- **Company:** {opportunity.company}
- **Title:** {opportunity.title}
- **Current Status:** {opportunity.status.value}

### Interaction History
"""
        if opportunity.interactions:
            for i in opportunity.interactions:
                content += f"- **{i.interaction_date.strftime('%Y-%m-%d')} ({i.interaction_type.value}):** {i.notes or 'No notes'}\n"
        else:
            content += "*No interactions recorded.*\n"
            
        content += "\n### Attached Supporting Documents\n"
        if opportunity.documents:
            for d in opportunity.documents:
                content += f"- **{d.document_type}:** {d.name} (Stored: `{d.file_path}`)\n"
        else:
            content += "*No documents attached.*\n"
            
        content += f"""
## 2. Value Proposition
### Key Selling Points
{selling_points if selling_points else "*None generated*"}

## 3. Risk Assessment & Objections
### Company / Opportunity Risks
{risks if risks else "*None generated*"}

### Potential Objections
{objections if objections else "*None generated*"}

### Mitigation Strategy
{mitigation if mitigation else "*None generated*"}

## 4. Strategic Questions
### Questions to Ask the Company
{questions if questions else "*None generated*"}
"""
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return str(dest_path.resolve())
