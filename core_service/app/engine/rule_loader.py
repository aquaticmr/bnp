import json
import logging
from pathlib import Path
from typing import List, Optional
from app.core.config import settings
from app.schemas.rules import RuleCatalog, RuleDefinition

logger = logging.getLogger(__name__)


class RuleLoader:
    def __init__(self, rules_file_path: Optional[Path] = None):
        self.rules_file_path = rules_file_path or settings.RULES_PATH
        self._cached_rules: List[RuleDefinition] = []

    def load_rules(self, force_reload: bool = False) -> List[RuleDefinition]:
        if self._cached_rules and not force_reload:
            return self._cached_rules

        if not self.rules_file_path.exists():
            logger.warning("Rules file not found at: %s", self.rules_file_path)
            return []

        try:
            with open(self.rules_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_rules = data.get("rules", []) if isinstance(data, dict) else data
            parsed_rules: List[RuleDefinition] = []

            for item in raw_rules:
                try:
                    rule = RuleDefinition(**item)
                    parsed_rules.append(rule)
                except Exception as err:
                    logger.error("Failed to parse rule definition %s: %s", item.get("rule_id"), err)

            self._cached_rules = parsed_rules
            logger.info("Successfully loaded %d regulatory rules from %s", len(parsed_rules), self.rules_file_path)
            return self._cached_rules

        except Exception as exc:
            logger.error("Error reading regulatory rules JSON: %s", exc)
            return []

    def get_catalog(self) -> RuleCatalog:
        rules = self.load_rules()
        regulators = sorted(list({r.regulator for r in rules}))
        return RuleCatalog(
            version="1.0.0",
            regulators=regulators,
            total_rules=len(rules),
            rules=rules,
        )


default_rule_loader = RuleLoader()
