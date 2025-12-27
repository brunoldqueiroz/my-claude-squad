"""Intent-based routing for natural language task descriptions.

Provides semantic understanding of user intent beyond keyword matching.
Maps natural phrases to specific agents and actions.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from orchestrator.tracing import observe


class IntentCategory(Enum):
    """Categories of user intent."""

    CREATE = "create"  # Building something new
    FIX = "fix"  # Debugging, troubleshooting
    REVIEW = "review"  # Code review, analysis
    OPTIMIZE = "optimize"  # Performance improvement
    EXPLAIN = "explain"  # Documentation, understanding
    TRANSFORM = "transform"  # ETL, data processing
    DEPLOY = "deploy"  # Infrastructure, CI/CD
    RESEARCH = "research"  # Looking up information
    COORDINATE = "coordinate"  # Multi-step orchestration


@dataclass
class Intent:
    """Detected intent from user input."""

    category: IntentCategory
    agent: str  # Recommended agent name
    confidence: float  # 0.0 to 1.0
    action: str  # Specific action to take
    keywords: list[str] = field(default_factory=list)  # Matched keywords
    context: dict[str, Any] = field(default_factory=dict)  # Extracted context


# Intent patterns - ordered by specificity (most specific first)
INTENT_PATTERNS: list[tuple[str, IntentCategory, str, str, float]] = [
    # (pattern, category, agent, action, base_confidence)

    # === Code Review ===
    (r"review\s+(this|my|the)?\s*(code|pr|pull\s*request|changes?)", IntentCategory.REVIEW, "squad-orchestrator", "code_review", 0.9),
    (r"check\s+(this|my|the)?\s*(code|implementation)", IntentCategory.REVIEW, "squad-orchestrator", "code_review", 0.85),
    (r"look\s+at\s+(this|my|the)?", IntentCategory.REVIEW, "squad-orchestrator", "code_review", 0.7),

    # === Debugging/Fixing ===
    (r"(fix|debug|troubleshoot|solve)\s+(this|the|my)?\s*(bug|issue|error|problem)", IntentCategory.FIX, "python-developer", "debug", 0.9),
    (r"(why\s+is|what\'s\s+wrong\s+with)", IntentCategory.FIX, "python-developer", "diagnose", 0.85),
    (r"(doesn\'t|does\s*not|isn\'t|won\'t)\s+work", IntentCategory.FIX, "python-developer", "debug", 0.8),
    (r"(failing|broken|error|exception|crash)", IntentCategory.FIX, "python-developer", "debug", 0.75),

    # === SQL Help ===
    (r"(help|assist)\s+(me\s+)?(with\s+)?(my\s+)?sql", IntentCategory.CREATE, "sql-specialist", "sql_help", 0.9),
    (r"(write|create|build)\s+(a\s+)?sql\s+(query|statement)", IntentCategory.CREATE, "sql-specialist", "write_sql", 0.9),
    (r"(optimize|improve|speed\s*up)\s+(this|my|the)?\s*query", IntentCategory.OPTIMIZE, "sql-specialist", "optimize_query", 0.9),

    # === Data Pipeline ===
    (r"(create|build|set\s*up)\s+(a\s+)?(data\s+)?pipeline", IntentCategory.CREATE, "python-developer", "create_pipeline", 0.9),
    (r"(etl|elt)\s+(pipeline|process|job)", IntentCategory.CREATE, "python-developer", "create_pipeline", 0.9),
    (r"(move|transfer|migrate)\s+data\s+(from|to)", IntentCategory.TRANSFORM, "python-developer", "data_migration", 0.85),

    # === Explanation/Documentation ===
    (r"(explain|describe|walk\s+me\s+through)\s+(this|the|how)", IntentCategory.EXPLAIN, "documenter", "explain", 0.85),
    (r"(document|write\s+docs\s+for)", IntentCategory.EXPLAIN, "documenter", "document", 0.9),
    (r"(what\s+does|how\s+does)\s+(this|it)\s+(do|work)", IntentCategory.EXPLAIN, "documenter", "explain", 0.8),

    # === Optimization ===
    (r"(optimize|improve|speed\s*up|make\s+.*faster)", IntentCategory.OPTIMIZE, "python-developer", "optimize", 0.85),
    (r"(performance|slow|bottleneck)", IntentCategory.OPTIMIZE, "python-developer", "optimize", 0.75),

    # === Infrastructure/Deployment ===
    (r"(deploy|ship|release)\s+(this|to)", IntentCategory.DEPLOY, "kubernetes-specialist", "deploy", 0.85),
    (r"(create|set\s*up)\s+(a\s+)?(docker|container)", IntentCategory.DEPLOY, "container-specialist", "containerize", 0.9),
    (r"(kubernetes|k8s|helm)", IntentCategory.DEPLOY, "kubernetes-specialist", "k8s_deploy", 0.9),

    # === Research ===
    (r"(find|search\s+for|look\s+up)\s+(docs?|documentation|examples?)", IntentCategory.RESEARCH, "squad-orchestrator", "lookup_docs", 0.85),
    (r"(how\s+do\s+i|how\s+to|show\s+me\s+how)", IntentCategory.RESEARCH, "squad-orchestrator", "research", 0.8),

    # === Creation ===
    (r"(create|build|make|write|implement|add)\s+(a\s+)?new", IntentCategory.CREATE, "python-developer", "create", 0.8),
    (r"(scaffold|bootstrap|generate|init)", IntentCategory.CREATE, "python-developer", "scaffold", 0.85),

    # === Orchestration ===
    (r"(coordinate|orchestrate|manage)\s+(multiple|several|many)", IntentCategory.COORDINATE, "squad-orchestrator", "orchestrate", 0.9),
    (r"(end\s*-?\s*to\s*-?\s*end|full|complete)\s+(pipeline|workflow|process)", IntentCategory.COORDINATE, "squad-orchestrator", "orchestrate", 0.85),
    (r"(complex|multi-?\s*step|multi-?\s*agent)", IntentCategory.COORDINATE, "squad-orchestrator", "decompose", 0.85),
]

# Action to tool mapping
ACTION_TO_TOOL: dict[str, str] = {
    "code_review": "spawn_agent",
    "debug": "spawn_agent",
    "diagnose": "spawn_agent",
    "sql_help": "spawn_agent",
    "write_sql": "spawn_agent",
    "optimize_query": "analyze_query",
    "create_pipeline": "create_pipeline",
    "data_migration": "spawn_agent",
    "explain": "spawn_agent",
    "document": "spawn_agent",
    "optimize": "spawn_agent",
    "deploy": "spawn_agent",
    "containerize": "create_dockerfile",
    "k8s_deploy": "create_k8s_manifest",
    "lookup_docs": "lookup_docs",
    "research": "route_task",
    "create": "spawn_agent",
    "scaffold": "spawn_agent",
    "orchestrate": "decompose_task",
    "decompose": "decompose_task",
}


class IntentDetector:
    """Detects user intent from natural language input."""

    def __init__(self):
        """Initialize the intent detector."""
        self._compiled_patterns: list[tuple[re.Pattern, IntentCategory, str, str, float]] = [
            (re.compile(pattern, re.IGNORECASE), category, agent, action, confidence)
            for pattern, category, agent, action, confidence in INTENT_PATTERNS
        ]

    @observe(name="detect_intent")
    def detect(self, text: str) -> Intent | None:
        """Detect intent from natural language text.

        Args:
            text: User input text

        Returns:
            Detected intent or None if no match
        """
        text_lower = text.lower().strip()
        best_match: Intent | None = None
        best_confidence = 0.0

        for pattern, category, agent, action, base_confidence in self._compiled_patterns:
            match = pattern.search(text_lower)
            if match:
                # Boost confidence based on match coverage
                match_coverage = len(match.group()) / len(text_lower)
                confidence = min(1.0, base_confidence + (match_coverage * 0.1))

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = Intent(
                        category=category,
                        agent=agent,
                        confidence=confidence,
                        action=action,
                        keywords=[match.group()],
                        context=self._extract_context(text, match),
                    )

        return best_match

    def _extract_context(self, text: str, match: re.Match) -> dict[str, Any]:
        """Extract additional context from the matched text.

        Args:
            text: Full input text
            match: Regex match object

        Returns:
            Extracted context dictionary
        """
        context: dict[str, Any] = {
            "matched_text": match.group(),
            "position": match.span(),
        }

        # Extract file paths
        file_pattern = r'[\w/.-]+\.(py|sql|ts|js|yaml|yml|json|md)'
        files = re.findall(file_pattern, text)
        if files:
            context["files"] = files

        # Extract numbers (potential IDs, PR numbers, etc.)
        numbers = re.findall(r'\b\d+\b', text)
        if numbers:
            context["numbers"] = numbers

        # Extract quoted strings
        quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', text)
        if quoted:
            context["quoted"] = [q[0] or q[1] for q in quoted]

        return context

    @observe(name="detect_multiple_intents")
    def detect_all(self, text: str, threshold: float = 0.5) -> list[Intent]:
        """Detect all matching intents above a confidence threshold.

        Args:
            text: User input text
            threshold: Minimum confidence threshold

        Returns:
            List of detected intents, sorted by confidence
        """
        text_lower = text.lower().strip()
        intents: list[Intent] = []
        seen_agents: set[str] = set()

        for pattern, category, agent, action, base_confidence in self._compiled_patterns:
            match = pattern.search(text_lower)
            if match:
                match_coverage = len(match.group()) / len(text_lower)
                confidence = min(1.0, base_confidence + (match_coverage * 0.1))

                if confidence >= threshold and agent not in seen_agents:
                    seen_agents.add(agent)
                    intents.append(Intent(
                        category=category,
                        agent=agent,
                        confidence=confidence,
                        action=action,
                        keywords=[match.group()],
                        context=self._extract_context(text, match),
                    ))

        return sorted(intents, key=lambda x: x.confidence, reverse=True)

    def get_suggested_tool(self, intent: Intent) -> str | None:
        """Get the suggested tool for an intent.

        Args:
            intent: Detected intent

        Returns:
            Suggested tool name or None
        """
        return ACTION_TO_TOOL.get(intent.action)

    def explain_intent(self, intent: Intent) -> str:
        """Generate a human-readable explanation of the detected intent.

        Args:
            intent: Detected intent

        Returns:
            Explanation string
        """
        explanations = {
            IntentCategory.CREATE: "You want to create or build something new",
            IntentCategory.FIX: "You need help debugging or fixing an issue",
            IntentCategory.REVIEW: "You want code or implementation reviewed",
            IntentCategory.OPTIMIZE: "You want to improve performance",
            IntentCategory.EXPLAIN: "You want something explained or documented",
            IntentCategory.TRANSFORM: "You want to transform or process data",
            IntentCategory.DEPLOY: "You want to deploy or set up infrastructure",
            IntentCategory.RESEARCH: "You're looking for information or examples",
            IntentCategory.COORDINATE: "You need multi-step coordination",
        }

        base = explanations.get(intent.category, "Intent detected")
        return f"{base}. Recommended agent: {intent.agent} ({intent.confidence:.0%} confidence)"


# Singleton instance
_detector: IntentDetector | None = None


def get_intent_detector() -> IntentDetector:
    """Get the global intent detector instance."""
    global _detector
    if _detector is None:
        _detector = IntentDetector()
    return _detector
