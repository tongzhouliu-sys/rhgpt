"""Prompt Builder (`src/builder.py`) — A3, implements [修正-3].

Whitelist substitution, NO blanket cleanup. Only variables that actually exist
in the current Context are substituted:

    {{user_question}}      -> context["user_question"]
    {{<step_key>}}         -> context["outputs"][<step_key>]   (already produced)

Any other `{{...}}` is left **verbatim**, so legitimate double-braces in model
outputs (Jinja / Vue / Handlebars / LaTeX examples) are never destroyed when a
later step references that output via {{key}}.

Hardening over the reference skeleton: substitution is a SINGLE regex pass with
a lookup callback, not sequential str.replace(). This guarantees that a value
injected for one variable can never itself be re-scanned and partially
substituted (i.e. no accidental re-injection from model output content).
"""

from __future__ import annotations

import os
import re

# A variable placeholder is a *bare identifier* in double braces with no
# internal whitespace: {{user_question}}, {{generate}}. This is exactly the
# reference semantics (exact "{{name}}" match). Anything with spaces, dots,
# pipes, operators, etc. — e.g. {{ vue_var }}, {{ user.name }}, {{ a | b }} —
# is NOT a variable reference and passes through untouched.
PLACEHOLDER_RE = re.compile(r"\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}")


class PromptBuilder:
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir

    def build(self, prompt_name: str, context: dict) -> str:
        """Render prompts/{prompt_name}.md against `context`.

        `context` shape: {"user_question": str, "outputs": {step_key: str, ...}}.
        Unknown placeholders are preserved as-is (an explicit, visible failure
        signal in the persisted *_prompt.md rather than a silent deletion).
        """
        prompt_path = os.path.join(self.prompts_dir, f"{prompt_name}.md")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

        variables = {"user_question": context.get("user_question", "")}
        variables.update(context.get("outputs", {}))

        def _sub(match: "re.Match[str]") -> str:
            name = match.group(1)
            if name in variables:
                return str(variables[name])
            return match.group(0)  # unknown -> keep verbatim

        return PLACEHOLDER_RE.sub(_sub, template)


__all__ = ["PromptBuilder", "PLACEHOLDER_RE"]
