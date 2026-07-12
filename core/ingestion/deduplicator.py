import re
import math
import uuid
from datetime import datetime
from collections import Counter

from core.ports.repository import IRepository
from domain.opportunity import OpportunityCase, Interaction, InteractionType, OpportunityStatus

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _shingles(text: str, n: int = 3) -> set[str]:
    tokens = _tokenize(text)
    if len(tokens) < n:
        return set(tokens)
    return {" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def jaccard_similarity(a: str, b: str, n: int = 3) -> float:
    sa, sb = _shingles(a, n), _shingles(b, n)
    if not sa or not sb:
        return 1.0 if a.strip().lower() == b.strip().lower() else 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


def _cosine_tf(counter_a: Counter, counter_b: Counter) -> float:
    common = set(counter_a) & set(counter_b)
    dot = sum(counter_a[t] * counter_b[t] for t in common)
    norm_a = math.sqrt(sum(v * v for v in counter_a.values()))
    norm_b = math.sqrt(sum(v * v for v in counter_b.values()))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def description_similarity(text_a: str, text_b: str) -> float:
    if not text_a or not text_b:
        return 0.0
    return _cosine_tf(Counter(_tokenize(text_a)), Counter(_tokenize(text_b)))


def _extract_raw_text(opportunity: OpportunityCase) -> str:
    raw = opportunity.raw_ingestion_data
    return str(raw.get("original_raw_text") or "") if isinstance(raw, dict) else ""


class DuplicateDetector:
    TITLE_THRESHOLD = 0.55   # Jaccard on 3-gram title shingles
    DESC_THRESHOLD = 0.80    # TF cosine on full ingested text

    def __init__(self, repository: IRepository[OpportunityCase]):
        self.repository = repository

    def check_for_duplicates(self, opportunity: OpportunityCase) -> None:
        all_opportunities = self.repository.get_all()
        opp_company = opportunity.company.strip().lower()
        opp_title = opportunity.title.strip().lower()
        opp_text = _extract_raw_text(opportunity)

        for existing_opp in all_opportunities:
            if existing_opp.id == opportunity.id:
                continue
            if opp_company != existing_opp.company.strip().lower():
                continue

            title_sim = jaccard_similarity(opp_title, existing_opp.title.strip().lower())
            desc_sim = 0.0
            if opp_text:
                existing_text = _extract_raw_text(existing_opp)
                if existing_text:
                    desc_sim = description_similarity(opp_text, existing_text)

            if title_sim >= self.TITLE_THRESHOLD or desc_sim >= self.DESC_THRESHOLD:
                score = max(title_sim, desc_sim)
                warning_interaction = Interaction(
                    id=str(uuid.uuid4()),
                    interaction_type=InteractionType.Other,
                    interaction_date=datetime.utcnow(),
                    notes=(
                        f"[WARNING]: Potential duplicate of Opportunity ID {existing_opp.id} "
                        f"(title_sim={title_sim:.2f}, desc_sim={desc_sim:.2f}, score={score:.2f})"
                    ),
                )
                opportunity.interactions.append(warning_interaction)
                opportunity.status = OpportunityStatus.Detected
                return