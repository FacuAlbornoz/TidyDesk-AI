import json
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from app.config import RULES_FILE
from app.schemas.rules import CustomRule, CustomRuleCreate

def load_rules() -> List[CustomRule]:
    """Carga todas las reglas personalizadas almacenadas."""
    if not RULES_FILE.exists():
        return []
    try:
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [CustomRule(**item) for item in data] if isinstance(data, list) else []
    except Exception:
        return []

def save_rules(rules: List[CustomRule]) -> None:
    """Persiste las reglas en rules.json."""
    data = [r.model_dump() for r in rules]
    with open(RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def create_rule(rule_data: CustomRuleCreate) -> CustomRule:
    """Crea y almacena una nueva regla personalizada."""
    rules = load_rules()
    new_rule = CustomRule(
        id=f"rule_{uuid.uuid4().hex[:8]}",
        name=rule_data.name.strip(),
        pattern_type=rule_data.pattern_type,
        patterns=[p.strip().lower() for p in rule_data.patterns if p.strip()],
        destination_path=rule_data.destination_path.strip(),
        enabled=rule_data.enabled,
    )
    rules.append(new_rule)
    save_rules(rules)
    return new_rule

def delete_rule(rule_id: str) -> bool:
    """Elimina una regla por su ID."""
    rules = load_rules()
    initial_count = len(rules)
    rules = [r for r in rules if r.id != rule_id]
    if len(rules) < initial_count:
        save_rules(rules)
        return True
    return False

def toggle_rule(rule_id: str) -> Optional[CustomRule]:
    """Alterna el estado activado/desactivado de una regla."""
    rules = load_rules()
    target_rule = None
    for r in rules:
        if r.id == rule_id:
            r.enabled = not r.enabled
            target_rule = r
            break
    if target_rule:
        save_rules(rules)
    return target_rule

def import_rules_batch(incoming_items: List[dict]) -> List[CustomRule]:
    """Importa un lote de reglas desde un archivo JSON evitando duplicar nombres exactos."""
    existing = load_rules()
    existing_names = {r.name.lower().strip() for r in existing}
    for item in incoming_items:
        name = str(item.get("name", "")).strip()
        if not name or name.lower() in existing_names:
            continue
        existing.append(
            CustomRule(
                id=f"rule_{uuid.uuid4().hex[:8]}",
                name=name,
                pattern_type=item.get("pattern_type", "extension"),
                patterns=[str(p).strip().lower() for p in item.get("patterns", []) if str(p).strip()],
                destination_path=str(item.get("destination_path", "")).strip(),
                enabled=bool(item.get("enabled", True)),
            )
        )
        existing_names.add(name.lower())
    save_rules(existing)
    return existing

def match_custom_rule(file_name: str, file_ext: str) -> Optional[Tuple[str, str]]:
    """Evalúa si un archivo coincide con alguna regla personalizada activa.
    Retorna (destination_path, reason) o None si no hay coincidencia.
    """
    rules = load_rules()
    name_lower = file_name.lower()
    ext_lower = file_ext.lower()

    for rule in rules:
        if not rule.enabled:
            continue

        if rule.pattern_type == "extension":
            for pat in rule.patterns:
                clean_pat = pat if pat.startswith(".") else f".{pat}"
                if ext_lower == clean_pat:
                    return rule.destination_path, f"⭐ Regla Personalizada: {rule.name}"

        elif rule.pattern_type == "keyword":
            for pat in rule.patterns:
                if pat in name_lower:
                    return rule.destination_path, f"⭐ Regla Personalizada: {rule.name}"

    return None
