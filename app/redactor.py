import re
from typing import Dict, List, Tuple

PATTERNS = {
    "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "IBAN": r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",
    "PHONE": r"(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}",
    "PPSN_OR_TAX_ID": r"\b\d{7}[A-Z]{1,2}\b",
}


class PIIRedactor:
    def redact(self, text: str) -> Tuple[str, Dict[str, str], List[str]]:
        mapping: Dict[str, str] = {}
        detected_types: List[str] = []
        redacted_text = text

        for label, pattern in PATTERNS.items():
            matches = list(re.finditer(pattern, redacted_text))
            for idx, match in enumerate(matches, start=1):
                original_value = match.group(0)
                placeholder = f"[{label}_{idx}]"
                if original_value not in mapping.values():
                    mapping[placeholder] = original_value
                    redacted_text = redacted_text.replace(original_value, placeholder)
                    if label not in detected_types:
                        detected_types.append(label)

        return redacted_text, mapping, detected_types

    def restore(self, text: str, mapping: Dict[str, str]) -> str:
        restored_text = text
        for placeholder, original_value in mapping.items():
            restored_text = restored_text.replace(placeholder, original_value)
        return restored_text
