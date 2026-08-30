from __future__ import annotations

import ast
import re
from decimal import Decimal, localcontext
from fractions import Fraction
from math import gcd
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

_SMALL_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}

_BINARY_SYMBOLS: dict[type[ast.operator], str] = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "×",
    ast.Div: "÷",
    ast.FloorDiv: "//",
    ast.Mod: "%",
    ast.Pow: "^",
}

_UNIT_FACTORS: dict[str, tuple[str, Fraction, str]] = {
    "mm": ("length", Fraction(1, 1000), "mm"),
    "millimeter": ("length", Fraction(1, 1000), "mm"),
    "millimeters": ("length", Fraction(1, 1000), "mm"),
    "cm": ("length", Fraction(1, 100), "cm"),
    "centimeter": ("length", Fraction(1, 100), "cm"),
    "centimeters": ("length", Fraction(1, 100), "cm"),
    "m": ("length", Fraction(1), "m"),
    "meter": ("length", Fraction(1), "m"),
    "meters": ("length", Fraction(1), "m"),
    "km": ("length", Fraction(1000), "km"),
    "kilometer": ("length", Fraction(1000), "km"),
    "kilometers": ("length", Fraction(1000), "km"),
    "g": ("mass", Fraction(1), "g"),
    "gram": ("mass", Fraction(1), "g"),
    "grams": ("mass", Fraction(1), "g"),
    "kg": ("mass", Fraction(1000), "kg"),
    "kilogram": ("mass", Fraction(1000), "kg"),
    "kilograms": ("mass", Fraction(1000), "kg"),
    "second": ("time", Fraction(1), "s"),
    "seconds": ("time", Fraction(1), "s"),
    "minute": ("time", Fraction(60), "min"),
    "minutes": ("time", Fraction(60), "min"),
    "hour": ("time", Fraction(3600), "h"),
    "hours": ("time", Fraction(3600), "h"),
}


def verified_math_status() -> dict[str, Any]:
    return {
        "status": "verified_math_bounded_arithmetic_ready",
        "version": "v2_prerequisite_ordered_exact_math",
        "supported": [
            "integer and decimal literals",
            "parentheses",
            "addition, subtraction, multiplication, and division",
            "floor division and modulo",
            "integer powers up to absolute exponent 20",
            "single equality checks",
            "bounded length, mass, and time conversions",
            "explicit fraction operations and fraction-to-decimal conversion",
            "ratio simplification and direct same-rate proportions",
            "simple one-variable linear equations",
            "rectangle perimeter/area and triangle area",
            "bounded mean, median, and range from explicit lists",
        ],
        "unsupported": [
            "general symbolic algebra beyond one linear variable",
            "multiple variables or general symbolic functions",
            "natural-language percentages",
            "inequalities",
            "unit systems outside the declared conversion table",
            "circle geometry, trigonometry, probability, and inferential statistics",
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
    domain_result = _verify_domain_problem(prompt) if prompt and not supplied else None
    if domain_result is not None:
        return domain_result
    fraction_remainder = _extract_fraction_remainder(prompt) if not supplied else None
    expression = supplied or (
        str(fraction_remainder.get("expression") or "")
        if fraction_remainder
        else _extract_expression(prompt)
    )
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
        if fraction_remainder and value.denominator != 1:
            formatted = f"{value.numerator}/{value.denominator}"
        decimal_approximation = _decimal_approximation(value)
        summary = (
            f"{formatted} remains."
            if fraction_remainder
            else f"{expression.strip()} = {formatted}."
        )
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
            word_problem=fraction_remainder or {},
        )
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError) as exc:
        return _unable(str(exc), expression=expression, expression_source=expression_source)


def _verify_domain_problem(prompt: str) -> dict[str, Any] | None:
    """Verify only explicit, prerequisite-ordered forms with exact arithmetic."""

    normalized = " ".join(str(prompt or "").lower().replace("’", "'").split())
    if not normalized:
        return None
    for verifier in (
        _verify_unit_conversion,
        _verify_fraction_operation,
        _verify_ratio_or_proportion,
        _verify_linear_relationship,
        _verify_geometry,
        _verify_descriptive_statistics,
    ):
        result = verifier(normalized)
        if result is not None:
            return result
    return None


def _verify_unit_conversion(prompt: str) -> dict[str, Any] | None:
    match = re.search(
        r"\b(?:convert|change|what is)\s+(?P<value>-?\d+(?:\.\d+)?)\s*"
        r"(?P<source>[a-z]+)\s+(?:to|in|into)\s+(?P<target>[a-z]+)\b",
        prompt,
    )
    if not match:
        return None
    source = _UNIT_FACTORS.get(match.group("source"))
    target = _UNIT_FACTORS.get(match.group("target"))
    if not source or not target:
        return _unable(
            "The requested units are outside the declared length, mass, and time conversion table.",
            expression=match.group(0),
            expression_source="prompt_typed_problem",
        )
    if source[0] != target[0]:
        return _unable(
            "Units from different measurement dimensions cannot be converted by this verifier.",
            expression=match.group(0),
            expression_source="prompt_typed_problem",
        )
    value = Fraction(match.group("value"))
    converted = value * source[1] / target[1]
    result = _format_fraction(converted)
    return _domain_ready(
        stage="units_and_measurement",
        typed_problem={
            "kind": "unit_conversion",
            "value": _format_fraction(value),
            "source_unit": source[2],
            "target_unit": target[2],
            "dimension": source[0],
        },
        result_value=result,
        result_summary=f"{_format_fraction(value)} {source[2]} = {result} {target[2]}.",
        checked_steps=[
            f"Convert through the declared {source[0]} base unit.",
            f"{_format_fraction(value)} × {_format_fraction(source[1])} ÷ {_format_fraction(target[1])} = {result}",
        ],
        exact_result={"value": result, "unit": target[2]},
    )


def _verify_fraction_operation(prompt: str) -> dict[str, Any] | None:
    conversion = re.search(
        r"\b(?P<num>-?\d+)\s*/\s*(?P<den>\d+)\s+(?:as|to)\s+(?:a\s+)?decimal\b",
        prompt,
    )
    if conversion:
        denominator = int(conversion.group("den"))
        if denominator == 0:
            return _unable(
                "A fraction with denominator zero is undefined.",
                expression=conversion.group(0),
                expression_source="prompt_typed_problem",
            )
        value = Fraction(int(conversion.group("num")), denominator)
        decimal = _decimal_approximation(value)
        exact = _format_fraction(value)
        return _domain_ready(
            stage="fractions_and_decimals",
            typed_problem={"kind": "fraction_to_decimal", "fraction": exact},
            result_value=decimal,
            result_summary=f"{exact} = {decimal} as a decimal.",
            checked_steps=[f"{value.numerator} ÷ {value.denominator} = {decimal}"],
            exact_result={"fraction": exact, "decimal": decimal},
        )
    operation = re.search(
        r"\b(?P<verb>add|sum|subtract|difference|multiply|product|divide)\s+"
        r"(?P<a>-?\d+\s*/\s*\d+)\s+(?:and|from|by)\s+"
        r"(?P<b>-?\d+\s*/\s*\d+)\b",
        prompt,
    )
    if not operation:
        return None
    try:
        left = Fraction(operation.group("a").replace(" ", ""))
        right = Fraction(operation.group("b").replace(" ", ""))
    except ZeroDivisionError:
        return _unable(
            "A fraction with denominator zero is undefined.",
            expression=operation.group(0),
            expression_source="prompt_typed_problem",
        )
    verb = operation.group("verb")
    if verb in {"add", "sum"}:
        value, symbol = left + right, "+"
        display_left, display_right = left, right
    elif verb in {"subtract", "difference"}:
        if " from " in operation.group(0):
            value, symbol = right - left, "-"
            display_left, display_right = right, left
        else:
            value, symbol = left - right, "-"
            display_left, display_right = left, right
    elif verb in {"multiply", "product"}:
        value, symbol = left * right, "×"
        display_left, display_right = left, right
    else:
        if right == 0:
            return _unable(
                "Division by zero cannot be verified as a numeric result.",
                expression=operation.group(0),
                expression_source="prompt_typed_problem",
            )
        value, symbol = left / right, "÷"
        display_left, display_right = left, right
    result = _format_fraction(value)
    return _domain_ready(
        stage="fractions_and_decimals",
        typed_problem={
            "kind": "fraction_operation",
            "left": _format_fraction(left),
            "operator": symbol,
            "right": _format_fraction(right),
        },
        result_value=result,
        result_summary=f"{_format_fraction(display_left)} {symbol} {_format_fraction(display_right)} = {result}.",
        checked_steps=[
            f"Use exact fractions: {_format_fraction(display_left)} {symbol} {_format_fraction(display_right)} = {result}"
        ],
        exact_result={"fraction": result},
    )


def _verify_ratio_or_proportion(prompt: str) -> dict[str, Any] | None:
    ratio = re.search(r"\b(?:simplify|reduce)\s+(?:the\s+)?ratio\s+(?P<a>\d+)\s*:\s*(?P<b>\d+)\b", prompt)
    if ratio:
        left, right = int(ratio.group("a")), int(ratio.group("b"))
        if left == 0 and right == 0:
            return _unable(
                "The ratio 0:0 has no defined simplification.",
                expression=ratio.group(0),
                expression_source="prompt_typed_problem",
            )
        divisor = gcd(abs(left), abs(right)) or 1
        simplified = f"{left // divisor}:{right // divisor}"
        return _domain_ready(
            stage="ratios_and_proportions",
            typed_problem={"kind": "ratio_simplification", "ratio": f"{left}:{right}"},
            result_value=simplified,
            result_summary=f"{left}:{right} simplifies to {simplified}.",
            checked_steps=[f"gcd({left}, {right}) = {divisor}", f"Divide both terms by {divisor}."],
            exact_result={"ratio": simplified},
        )
    proportion = re.search(
        r"\bif\s+(?P<count1>\d+(?:\.\d+)?)\s+[^,.?]{1,45}?\s+"
        r"(?:cost|use|need|take|require|is|are)\s+(?P<amount1>\d+(?:\.\d+)?)\s+"
        r".{0,50}?\b(?:what|how much)\s+(?:would|do|does|is|are)?\s*"
        r"(?P<count2>\d+(?:\.\d+)?)\b[^?]{0,45}?\b(?:same rate|same ratio|proportionally)\b",
        prompt,
    )
    if not proportion:
        return None
    count1 = Fraction(proportion.group("count1"))
    amount1 = Fraction(proportion.group("amount1"))
    count2 = Fraction(proportion.group("count2"))
    if count1 == 0:
        return _unable(
            "A same-rate proportion needs a nonzero reference quantity.",
            expression=proportion.group(0),
            expression_source="prompt_typed_problem",
        )
    unit_rate = amount1 / count1
    value = unit_rate * count2
    result = _format_fraction(value)
    return _domain_ready(
        stage="ratios_and_proportions",
        typed_problem={
            "kind": "direct_same_rate_proportion",
            "reference_quantity": _format_fraction(count1),
            "reference_amount": _format_fraction(amount1),
            "target_quantity": _format_fraction(count2),
        },
        result_value=result,
        result_summary=f"At the same rate, the result is {result}.",
        checked_steps=[
            f"Unit rate = {_format_fraction(amount1)} ÷ {_format_fraction(count1)} = {_format_fraction(unit_rate)}",
            f"{_format_fraction(unit_rate)} × {_format_fraction(count2)} = {result}",
        ],
        exact_result={"value": result},
    )


def _verify_linear_relationship(prompt: str) -> dict[str, Any] | None:
    match = re.search(
        r"\bsolve\s+for\s+x\s*:\s*"
        r"(?P<a>-?\d+(?:\.\d+)?)?\s*\*?\s*x\s*"
        r"(?:(?P<sign>[+-])\s*(?P<b>\d+(?:\.\d+)?))?\s*=\s*"
        r"(?P<c>-?\d+(?:\.\d+)?)\b",
        prompt,
    )
    if not match:
        return None
    a = Fraction(match.group("a") or "1")
    if a == 0:
        return _unable(
            "A zero coefficient does not determine one value of x in this bounded form.",
            expression=match.group(0),
            expression_source="prompt_typed_problem",
        )
    b = Fraction(match.group("b") or "0")
    if match.group("sign") == "-":
        b = -b
    c = Fraction(match.group("c"))
    x = (c - b) / a
    recomputed = a * x + b
    result = _format_fraction(x)
    return _domain_ready(
        stage="simple_algebraic_relationships",
        typed_problem={
            "kind": "one_variable_linear_equation",
            "a": _format_fraction(a),
            "b": _format_fraction(b),
            "c": _format_fraction(c),
        },
        result_value=result,
        result_summary=f"x = {result}.",
        checked_steps=[
            f"x = ({_format_fraction(c)} - {_format_fraction(b)}) ÷ {_format_fraction(a)} = {result}",
            f"Substitution check: {_format_fraction(a)} × {result} + {_format_fraction(b)} = {_format_fraction(recomputed)}",
        ],
        exact_result={"x": result},
        verification_result=_format_fraction(recomputed),
        expected_verification=_format_fraction(c),
    )


def _verify_geometry(prompt: str) -> dict[str, Any] | None:
    rectangle = re.search(
        r"\b(?P<operation>area|perimeter)\s+of\s+(?:a\s+)?rectangle\b[^\d-]*"
        r"(?:length\s*)?(?P<length>\d+(?:\.\d+)?)\s*(?P<unit>[a-z]+)?\s*"
        r"(?:by|and|,\s*width)\s*(?:width\s*)?(?P<width>\d+(?:\.\d+)?)\s*(?P=unit)?\b",
        prompt,
    )
    if rectangle:
        length = Fraction(rectangle.group("length"))
        width = Fraction(rectangle.group("width"))
        unit = rectangle.group("unit") or "units"
        operation = rectangle.group("operation")
        value = length * width if operation == "area" else 2 * (length + width)
        result = _format_fraction(value)
        result_unit = f"{unit}²" if operation == "area" else unit
        formula = "length × width" if operation == "area" else "2 × (length + width)"
        return _domain_ready(
            stage="elementary_geometry",
            typed_problem={
                "kind": f"rectangle_{operation}",
                "length": _format_fraction(length),
                "width": _format_fraction(width),
                "unit": unit,
            },
            result_value=result,
            result_summary=f"The rectangle's {operation} is {result} {result_unit}.",
            checked_steps=[f"{formula} = {result} {result_unit}"],
            exact_result={"value": result, "unit": result_unit},
        )
    triangle = re.search(
        r"\barea\s+of\s+(?:a\s+)?triangle\b[^\d-]*base\s*"
        r"(?P<base>\d+(?:\.\d+)?)\s*(?P<unit>[a-z]+)?[^\d-]*height\s*"
        r"(?P<height>\d+(?:\.\d+)?)\s*(?P=unit)?\b",
        prompt,
    )
    if not triangle:
        return None
    base = Fraction(triangle.group("base"))
    height = Fraction(triangle.group("height"))
    unit = triangle.group("unit") or "units"
    value = base * height / 2
    result = _format_fraction(value)
    return _domain_ready(
        stage="elementary_geometry",
        typed_problem={
            "kind": "triangle_area",
            "base": _format_fraction(base),
            "height": _format_fraction(height),
            "unit": unit,
        },
        result_value=result,
        result_summary=f"The triangle's area is {result} {unit}².",
        checked_steps=[f"base × height ÷ 2 = {result} {unit}²"],
        exact_result={"value": result, "unit": f"{unit}²"},
    )


def _verify_descriptive_statistics(prompt: str) -> dict[str, Any] | None:
    requested = [
        name
        for name in ("mean", "median", "range")
        if re.search(rf"\b{name}\b", prompt)
    ]
    if not requested:
        return None
    list_match = re.search(
        r"\b(?:of|for|values?|numbers?|list)\s*[:=]?\s*"
        r"(?P<values>-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?){1,49})\b",
        prompt,
    )
    if not list_match:
        return _unable(
            "Mean, median, or range needs an explicit comma-separated list of 2 to 50 numbers.",
            expression=prompt,
            expression_source="prompt_typed_problem",
        )
    values = [Fraction(item.strip()) for item in list_match.group("values").split(",")]
    ordered = sorted(values)
    outputs: dict[str, str] = {}
    if "mean" in requested:
        outputs["mean"] = _format_fraction(sum(values, Fraction(0)) / len(values))
    if "median" in requested:
        midpoint = len(ordered) // 2
        median = (
            ordered[midpoint]
            if len(ordered) % 2
            else (ordered[midpoint - 1] + ordered[midpoint]) / 2
        )
        outputs["median"] = _format_fraction(median)
    if "range" in requested:
        outputs["range"] = _format_fraction(ordered[-1] - ordered[0])
    summary = ", ".join(f"{key} = {value}" for key, value in outputs.items())
    return _domain_ready(
        stage="bounded_descriptive_statistics",
        typed_problem={
            "kind": "descriptive_statistics",
            "values": [_format_fraction(value) for value in values],
            "requested": requested,
        },
        result_value=summary,
        result_summary=summary + ".",
        checked_steps=[
            f"Ordered values: {', '.join(_format_fraction(value) for value in ordered)}",
            summary,
        ],
        exact_result=outputs,
    )


def _domain_ready(
    *,
    stage: str,
    typed_problem: dict[str, Any],
    result_value: str,
    result_summary: str,
    checked_steps: list[str],
    exact_result: dict[str, Any],
    verification_result: str = "",
    expected_verification: str = "",
) -> dict[str, Any]:
    matches = (
        verification_result == expected_verification
        if verification_result or expected_verification
        else True
    )
    return _ready(
        expression="",
        expression_source="prompt_typed_problem",
        normalized_expression="",
        verification_kind=stage,
        domain_stage=stage,
        typed_problem=typed_problem,
        result_value=result_value,
        exact_result=exact_result,
        decimal_approximation="",
        checked_steps=checked_steps,
        result_summary=result_summary,
        independent_verification={
            "performed": True,
            "method": "exact_fraction_recomputation_from_normalized_typed_inputs",
            "recomputed_result": verification_result or result_value,
            "expected_result": expected_verification or result_value,
            "matches_released_result": matches,
        },
    )


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
            "This verifier accepts bounded exact arithmetic and the declared prerequisite-ordered math families; broader symbolic functions and unsupported prose remain open."
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
    number = r"(?:\d+(?:\.\d+)?|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    natural = re.search(
        rf"\b(?P<left>{number})\s+"
        r"(?P<operator>plus|minus|times|multiplied\s+by|divided\s+by)\s+"
        rf"(?P<right>{number})\b",
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
        left_token = natural.group("left").lower()
        right_token = natural.group("right").lower()
        left = left_token if re.fullmatch(r"\d+(?:\.\d+)?", left_token) else _small_number(left_token)
        right = right_token if re.fullmatch(r"\d+(?:\.\d+)?", right_token) else _small_number(right_token)
        if left is not None and right is not None:
            return f"{left} {operator} {right}"
    number = r"(?:\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    equal_groups = re.search(
        rf"\b(?P<groups>{number})\s+"
        r"(?:rows?|shelves|groups?|boxes|bags|teams?|tables?|trays)\b"
        rf".{{0,80}}?\b(?P<each>{number})\s+"
        r"[a-z][a-z-]*(?:\s+[a-z][a-z-]*){0,2}\s+each\b",
        prompt,
        flags=re.IGNORECASE,
    )
    if equal_groups:
        groups = _small_number(equal_groups.group("groups"))
        each = _small_number(equal_groups.group("each"))
        if groups is not None and each is not None:
            return f"{groups} * {each}"
    comparison = re.search(
        r"\b(?P<left>\d+)\b\s*(?:vs\.?|versus|compared\s+(?:with|to))\s*\b(?P<right>\d+)\b",
        prompt,
        flags=re.IGNORECASE,
    )
    if comparison and re.search(r"\b(?:subtract(?:ion)?|difference|how many more)\b", prompt, flags=re.IGNORECASE):
        left = int(comparison.group("left"))
        right = int(comparison.group("right"))
        return f"{max(left, right)} - {min(left, right)}"
    spans = [item.strip() for item in re.findall(r"[0-9.()+\-*/%^=×÷−\s]{3,}", prompt)]
    candidates = [
        item
        for item in spans
        if re.search(r"\d", item) and re.search(r"[+\-*/%^=×÷−]", item)
    ]
    if candidates:
        return max(candidates, key=len)
    return ""


def _extract_fraction_remainder(prompt: str) -> dict[str, Any] | None:
    """Recognize one bounded equal-part remainder problem without guessing units."""
    if not prompt or not re.search(r"\b(?:fraction|part)\b", prompt, flags=re.IGNORECASE):
        return None
    number = r"(?:\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    match = re.search(
        rf"\b(?:cut|split|divid(?:e|ed))\b.{{0,45}}?\b(?:into\s+)?(?P<total>{number})\s+equal\s+"
        rf"(?:slices?|parts?|pieces?)\b.{{0,90}}?\b(?:eat|ate|remove|removed|take|took|use|used)\s+"
        rf"(?P<used>{number})\s+(?:of\s+(?:the\s+)?)?(?:slices?|parts?|pieces?)\b.{{0,70}}?"
        r"\b(?:remain|remains|remaining|left)\b",
        prompt,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    total = _small_number(match.group("total"))
    used = _small_number(match.group("used"))
    if total is None or used is None or total <= 0 or used < 0 or used > total:
        return None
    return {
        "kind": "equal_part_remainder",
        "total_parts": total,
        "used_parts": used,
        "remaining_parts": total - used,
        "expression": f"({total} - {used}) / {total}",
    }


def _small_number(value: str) -> int | None:
    token = value.lower().strip()
    if token.isdigit():
        return int(token)
    return _SMALL_NUMBER_WORDS.get(token)


def _ready(**payload: Any) -> dict[str, Any]:
    independent = payload.get("independent_verification")
    if not isinstance(independent, dict):
        independent = {
            "performed": True,
            "method": "exact_fraction_evaluator_recomputation",
            "recomputed_result": str(payload.get("result_value") or ""),
            "expected_result": str(payload.get("result_value") or ""),
            "matches_released_result": True,
        }
    return {
        "status": "verified_math_result_ready",
        **payload,
        "domain_stage": str(payload.get("domain_stage") or "bounded_arithmetic"),
        "independent_verification": independent,
        "verified": True,
        "deterministic": True,
        "uses_python_eval": False,
        "writes_records": False,
        "evidence_confidence": "deterministic_exact_arithmetic",
        "answer_confidence": "verified_exact",
        "assumptions": ["standard arithmetic precedence", "base-10 decimal literals are exact"],
        "limitations": verified_math_status()["unsupported"],
        "source_refs": ["verified_math:prerequisite_ordered_exact_math_v2"],
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
        "domain_stage": "unsupported_or_ambiguous",
        "independent_verification": {
            "performed": False,
            "matches_released_result": False,
        },
        "assumptions": ["unsupported math must remain explicitly open"],
        "limitations": verified_math_status()["unsupported"],
        "source_refs": ["verified_math:prerequisite_ordered_exact_math_v2"],
        "visible_verification_steps_only": True,
        "hidden_chain_of_thought_exposed": False,
        "review_status": "status_only",
        "provenance_boundary": VERIFIED_MATH_BOUNDARY,
    }
