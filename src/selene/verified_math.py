from __future__ import annotations

import ast
import re
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

from .registry import truncate


VERIFIED_MATH_BOUNDARY = (
    "verified_math_exact_bounded_arithmetic_only_"
    "no_eval_symbolic_guessing_provider_memory_or_authority_change"
)

MAX_EXPRESSION_LENGTH = 240
MAX_AST_NODES = 80
MAX_POWER = 20
MAX_RESULT_DIGITS = 240

_BINARY_SYMBOLS: dict[type[ast.operator], str] = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "×",
    ast.Div: "÷",
    ast.FloorDiv: "//",
    ast.Mod: "%",
    ast.Pow: "^",
}


def verified_math_status() -> dict[str, Any]:
    return {
        "status": "verified_math_bounded_arithmetic_ready",
        "version": "v1_exact_fraction_evaluator",
        "supported": [
            "integer and decimal literals",
            "parentheses",
            "addition, subtraction, multiplication, and division",
            "floor division and modulo",
            "integer powers up to absolute exponent 20",
            "single equality checks",
        ],
        "unsupported": [
            "symbolic algebra",
            "variables or functions",
            "units and conversions",
            "natural-language percentages",
            "inequalities",
            "external-provider calculation",
        ],
        "deterministic": True,
        "uses_python_eval": False,
        "writes_records": False,
        "visible_verification_steps_only": True,
        "hidden_chain_of_thought_exposed": False,
        "review_status": "status_only",
        "provenance_boundary": VERIFIED_MATH_BOUNDARY,
    }


def verify_bounded_math(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    supplied = str(payload.get("expression") or "").strip()
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 1000).strip()
    if len(supplied) > MAX_EXPRESSION_LENGTH:
        return _unable(
            f"The expression exceeds the {MAX_EXPRESSION_LENGTH}-character verification limit.",
            expression=supplied,
            expression_source="explicit_expression",
        )
    expression = supplied or _extract_expression(prompt)
    expression_source = "explicit_expression" if supplied else "prompt_extracted"
    if not expression:
        return _unable(
            "No bounded arithmetic expression could be identified. Supply an explicit expression.",
            expression="",
            expression_source=expression_source,
        )
    if len(expression) > MAX_EXPRESSION_LENGTH:
        return _unable(
            f"The expression exceeds the {MAX_EXPRESSION_LENGTH}-character verification limit.",
            expression=expression,
            expression_source=expression_source,
        )

    try:
        parts = expression.split("=")
        if len(parts) > 2 or any(not part.strip() for part in parts):
            raise ValueError("Only one complete equality may be checked at a time.")
        if len(parts) == 2:
            left = _evaluate_expression(parts[0])
            right = _evaluate_expression(parts[1])
            correct = left["value"] == right["value"]
            checked_steps = [*left["steps"], *right["steps"]]
            checked_steps.append(
                f"{_format_fraction(left['value'])} {'=' if correct else '≠'} {_format_fraction(right['value'])}"
            )
            summary = f"{expression.strip()} is {'correct' if correct else 'not correct'}."
            return _ready(
                expression=expression,
                normalized_expression=f"{left['normalized']} = {right['normalized']}",
                verification_kind="equality_check",
                result_value=str(correct).lower(),
                exact_result={
                    "left": _format_fraction(left["value"]),
                    "right": _format_fraction(right["value"]),
                    "equal": correct,
                },
                decimal_approximation="",
                checked_steps=checked_steps,
                result_summary=summary,
                expression_source=expression_source,
            )

        evaluated = _evaluate_expression(expression)
        value = evaluated["value"]
        formatted = _format_fraction(value)
        decimal_approximation = _decimal_approximation(value)
        summary = f"{expression.strip()} = {formatted}."
        return _ready(
            expression=expression,
            normalized_expression=evaluated["normalized"],
            verification_kind="exact_arithmetic",
            result_value=formatted,
            exact_result={"fraction": formatted},
            decimal_approximation=decimal_approximation,
            checked_steps=evaluated["steps"],
            result_summary=summary,
            expression_source=expression_source,
        )
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError) as exc:
        return _unable(str(exc), expression=expression, expression_source=expression_source)


def _evaluate_expression(expression: str) -> dict[str, Any]:
    normalized = (
        expression.strip()
        .replace("×", "*")
        .replace("÷", "/")
        .replace("−", "-")
        .replace("^", "**")
    )
    if not normalized:
        raise ValueError("The arithmetic expression is empty.")
    if not re.fullmatch(r"[0-9.()+\-*/%\s]+", normalized):
        raise ValueError(
            "This verifier accepts only bounded numeric arithmetic; variables, functions, units, and prose remain unsupported."
        )
    tree = ast.parse(normalized, mode="eval")
    if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
        raise ValueError("The expression is too structurally large for this bounded verifier.")
    steps: list[str] = []
    value = _evaluate_node(tree.body, normalized, steps)
    _check_result_size(value)
    return {"value": value, "normalized": normalized, "steps": steps}


def _evaluate_node(node: ast.AST, source: str, steps: list[str]) -> Fraction:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        literal = ast.get_source_segment(source, node) or str(node.value)
        try:
            return Fraction(literal)
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError(f"Unsupported numeric literal: {literal}") from exc
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate_node(node.operand, source, steps)
        result = value if isinstance(node.op, ast.UAdd) else -value
        _check_result_size(result)
        return result
    if not isinstance(node, ast.BinOp) or type(node.op) not in _BINARY_SYMBOLS:
        raise ValueError("Only the documented bounded arithmetic operators are supported.")

    left = _evaluate_node(node.left, source, steps)
    right = _evaluate_node(node.right, source, steps)
    if isinstance(node.op, ast.Add):
        result = left + right
    elif isinstance(node.op, ast.Sub):
        result = left - right
    elif isinstance(node.op, ast.Mult):
        result = left * right
    elif isinstance(node.op, ast.Div):
        if right == 0:
            raise ZeroDivisionError("Division by zero cannot be verified as a numeric result.")
        result = left / right
    elif isinstance(node.op, ast.FloorDiv):
        if right == 0:
            raise ZeroDivisionError("Floor division by zero cannot be verified as a numeric result.")
        result = Fraction(left // right, 1)
    elif isinstance(node.op, ast.Mod):
        if right == 0:
            raise ZeroDivisionError("Modulo by zero cannot be verified as a numeric result.")
        result = left % right
    else:
        if right.denominator != 1:
            raise ValueError("Fractional powers remain outside this exact arithmetic verifier.")
        exponent = right.numerator
        if abs(exponent) > MAX_POWER:
            raise ValueError(f"Powers are limited to absolute exponent {MAX_POWER}.")
        if left == 0 and exponent < 0:
            raise ZeroDivisionError("Zero cannot be raised to a negative power.")
        result = left**exponent
    _check_result_size(result)
    steps.append(
        f"{_format_fraction(left)} {_BINARY_SYMBOLS[type(node.op)]} "
        f"{_format_fraction(right)} = {_format_fraction(result)}"
    )
    return result


def _check_result_size(value: Fraction) -> None:
    if len(str(abs(value.numerator))) > MAX_RESULT_DIGITS or len(str(value.denominator)) > MAX_RESULT_DIGITS:
        raise OverflowError("The exact result exceeds this verifier's bounded result size.")


def _format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    if _has_terminating_decimal(value.denominator):
        with localcontext() as context:
            context.prec = MAX_RESULT_DIGITS + 10
            decimal_value = Decimal(value.numerator) / Decimal(value.denominator)
        return format(decimal_value, "f").rstrip("0").rstrip(".") or "0"
    return f"{value.numerator}/{value.denominator}"


def _decimal_approximation(value: Fraction) -> str:
    if value.denominator == 1 or _has_terminating_decimal(value.denominator):
        return _format_fraction(value)
    with localcontext() as context:
        context.prec = 20
        decimal_value = Decimal(value.numerator) / Decimal(value.denominator)
    return format(decimal_value, "f")


def _has_terminating_decimal(denominator: int) -> bool:
    remainder = denominator
    for factor in (2, 5):
        while remainder % factor == 0:
            remainder //= factor
    return remainder == 1


def _extract_expression(prompt: str) -> str:
    if not prompt:
        return ""
    stripped = prompt.strip().rstrip("?.").strip()
    stripped = re.sub(
        r"^(?:please\s+)?(?:what\s+is|calculate|compute|evaluate|verify|check\s+whether|is)\s+",
        "",
        stripped,
        flags=re.IGNORECASE,
    )
    if re.fullmatch(r"[0-9.()+\-*/%^=×÷−\s]+", stripped):
        return stripped.strip()
    # Ordinary conversation may wrap an otherwise explicit expression in a
    # polite request. Extract only a contiguous numeric expression and never
    # reinterpret symbolic algebra as arithmetic.
    if re.search(r"\bsolve\s+for\b", prompt, flags=re.IGNORECASE):
        return ""
    if re.search(r"[A-Za-z]\s*[+\-*/^=×÷]|[+\-*/^=×÷]\s*[A-Za-z]", prompt):
        return ""
    natural = re.search(
        r"\b(?P<left>\d+(?:\.\d+)?)\s+"
        r"(?P<operator>plus|minus|times|multiplied\s+by|divided\s+by)\s+"
        r"(?P<right>\d+(?:\.\d+)?)\b",
        prompt,
        flags=re.IGNORECASE,
    )
    if natural:
        operator = {
            "plus": "+",
            "minus": "-",
            "times": "*",
            "multiplied by": "*",
            "divided by": "/",
        }[" ".join(natural.group("operator").lower().split())]
        return f"{natural.group('left')} {operator} {natural.group('right')}"
    spans = [item.strip() for item in re.findall(r"[0-9.()+\-*/%^=×÷−\s]{3,}", prompt)]
    candidates = [
        item
        for item in spans
        if re.search(r"\d", item) and re.search(r"[+\-*/%^=×÷−]", item)
    ]
    if candidates:
        return max(candidates, key=len)
    return ""


def _ready(**payload: Any) -> dict[str, Any]:
    return {
        "status": "verified_math_result_ready",
        **payload,
        "verified": True,
        "deterministic": True,
        "uses_python_eval": False,
        "writes_records": False,
        "evidence_confidence": "deterministic_exact_arithmetic",
        "answer_confidence": "verified_exact",
        "assumptions": ["standard arithmetic precedence", "base-10 decimal literals are exact"],
        "limitations": verified_math_status()["unsupported"],
        "source_refs": ["verified_math:exact_fraction_evaluator_v1"],
        "visible_verification_steps_only": True,
        "hidden_chain_of_thought_exposed": False,
        "review_status": "status_only",
        "provenance_boundary": VERIFIED_MATH_BOUNDARY,
    }


def _unable(reason: str, *, expression: str, expression_source: str) -> dict[str, Any]:
    return {
        "status": "verified_math_unable_to_verify",
        "expression": truncate(expression, MAX_EXPRESSION_LENGTH),
        "expression_source": expression_source,
        "verified": False,
        "result_summary": "",
        "checked_steps": [],
        "no_answer_reason": truncate(reason or "The expression is outside this bounded verifier.", 800),
        "deterministic": True,
        "uses_python_eval": False,
        "writes_records": False,
        "evidence_confidence": "no_verified_result",
        "answer_confidence": "unable_to_verify",
        "assumptions": ["unsupported math must remain explicitly open"],
        "limitations": verified_math_status()["unsupported"],
        "source_refs": ["verified_math:exact_fraction_evaluator_v1"],
        "visible_verification_steps_only": True,
        "hidden_chain_of_thought_exposed": False,
        "review_status": "status_only",
        "provenance_boundary": VERIFIED_MATH_BOUNDARY,
    }
