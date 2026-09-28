"""find every definition module under casedefs/definitions."""

from __future__ import annotations

import importlib
import pkgutil
from functools import lru_cache

from . import definitions
from .definition import Composite, Definition


@lru_cache(maxsize=1)
def all_definitions() -> dict[str, Definition | Composite]:
    found: dict[str, Definition | Composite] = {}
    for mod in pkgutil.walk_packages(definitions.__path__, definitions.__name__ + "."):
        module = importlib.import_module(mod.name)
        defn = getattr(module, "DEFINITION", None)
        if isinstance(defn, (Definition, Composite)):
            if defn.id in found:
                raise RuntimeError(f"two definitions share the id {defn.id!r}")
            found[defn.id] = defn
    return dict(sorted(found.items()))


def get_definition(definition_id: str) -> Definition | Composite:
    defs = all_definitions()
    if definition_id not in defs:
        known = ", ".join(defs) or "(none)"
        raise KeyError(f"unknown definition {definition_id!r}. available: {known}")
    return defs[definition_id]
