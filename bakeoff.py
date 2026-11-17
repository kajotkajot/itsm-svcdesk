# ai-generated: 100% - GitHub Copilot implemented CI-SPEC.md P-14 to P-24 and checked the practice set
"""Build a per-tool confusion matrix from SARIF findings and labelled defects."""

from __future__ import annotations

import argparse
import json
import re
import sys
from urllib.parse import unquote


CLASSES_BY_CWE = {
    "secret": {259, 260, 321, 798},
    "injection": {74, 77, 78, 79, 80, 88, 89, 90, 91, 94, 95, 96, 611, 776, 917, 943, 1336},
    "deserialization": {502},
    "weak-crypto": {261, 326, 327, 328, 330, 331, 338, 759, 760, 916},
    "insecure-transport": {295, 297, 319, 322, 757},
    "path-traversal": {22, 23, 35, 36, 73},
    "ssrf": {918},
    "vulnerable-dependency": {937, 1035, 1104, 1395},
    "misconfiguration": {16, 215, 250, 489, 668, 732, 1188},
    "access-control": {284, 285, 639, 862, 863},
}
VALID_CLASSES = set(CLASSES_BY_CWE)
CWE_PATTERN = re.compile(r"(?<![A-Za-z0-9])CWE-([0-9]+)", re.IGNORECASE)
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9._-]+")
PACKAGE_SEPARATORS = re.compile(r"[-_.]+")


def _object(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _array(value: object) -> list:
    return value if isinstance(value, list) else []


def _tool_id(run: dict) -> str:
    tool = _object(run.get("tool"))
    driver = _object(tool.get("driver"))
    name = driver.get("name")
    if not isinstance(name, str):
        return "unknown"
    normalized = name.strip().lower()
    if not normalized:
        return "unknown"
    if normalized in {"trivy", "grype", "osv-scanner", "gitleaks"}:
        return normalized
    if normalized in {
        "semgrep", "semgrep oss", "semgrep ce", "semgrep community edition", "semgrep pro"
    }:
        return "semgrep"
    result = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return result or "unknown"


def _empty_suppressions(value: object) -> bool:
    if value is None or value is False or value == "" or value == [] or value == {}:
        return True
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value == 0


def _path_in_set(uri: str, set_root: str) -> str | None:
    path = unquote(uri)
    if path[:7].casefold() == "file://":
        path = path[7:]
    if path.startswith("./"):
        path = path[2:]
    components = path.split("/")
    matches = [index for index, part in enumerate(components) if part == set_root]
    if not matches:
        return None
    return "/".join(components[matches[-1] :])


def _result_location(result: dict, set_root: str) -> tuple[str, int | None, int | None] | None:
    locations = _array(result.get("locations"))
    if not locations:
        return None
    physical = _object(_object(locations[0]).get("physicalLocation"))
    artifact = _object(physical.get("artifactLocation"))
    uri = artifact.get("uri")
    if not isinstance(uri, str) or not uri:
        return None
    file = _path_in_set(uri, set_root)
    if file is None:
        return None

    region = _object(physical.get("region"))
    start = region.get("startLine")
    if not isinstance(start, int) or isinstance(start, bool) or start < 1:
        return file, None, None
    end = region.get("endLine")
    if not isinstance(end, int) or isinstance(end, bool) or end < start:
        end = start
    return file, start, end


def _tags(value: object) -> list[str]:
    properties = _object(value)
    return [tag for tag in _array(properties.get("tags")) if isinstance(tag, str)]


def _rule_for(run: dict, result: dict) -> dict:
    rule_id = result.get("ruleId")
    if rule_id is None:
        return {}
    for candidate in _array(_object(_object(run.get("tool")).get("driver")).get("rules")):
        if isinstance(candidate, dict) and candidate.get("id") is not None and candidate.get("id") == rule_id:
            return candidate
    return {}


def _result_classes(tool: str, result: dict, rule: dict) -> set[str]:
    result_properties = _object(result.get("properties"))
    declared = result_properties.get("class")
    if isinstance(declared, str) and declared in VALID_CLASSES:
        return {declared}

    if tool == "gitleaks":
        return {"secret"}
    if tool in {"grype", "osv-scanner"}:
        return {"vulnerable-dependency"}
    if tool == "trivy":
        tag_classes = {
            "vulnerability": "vulnerable-dependency",
            "secret": "secret",
            "misconfiguration": "misconfiguration",
        }
        mapped = {
            tag_classes[tag.casefold()]
            for tag in _tags(_object(rule.get("properties")))
            if tag.casefold() in tag_classes
        }
        if mapped:
            return mapped

    cwe_numbers = {
        match.group(1).lstrip("0") or "0"
        for tag in _tags(result_properties) + _tags(_object(rule.get("properties")))
        for match in CWE_PATTERN.finditer(tag)
    }
    matched = {
        class_name
        for class_name, numbers in CLASSES_BY_CWE.items()
        if cwe_numbers.intersection(str(number) for number in numbers)
    }
    return matched or {"other"}


def _package_token(value: str) -> str:
    return PACKAGE_SEPARATORS.sub("-", value.lower())


def _message_names_package(result: dict, package: object) -> bool:
    if not isinstance(package, str):
        return False
    message = _object(result.get("message")).get("text")
    if not isinstance(message, str):
        return False
    expected = _package_token(package)
    if not expected:
        return False
    for token in TOKEN_PATTERN.findall(message):
        normalized = _package_token(token.strip("._-"))
        if normalized and normalized == expected:
            return True
    return False


def _matches(result: dict, location: tuple[str, int | None, int | None], classes: set[str], defect: dict) -> bool:
    if location[0] != defect.get("file") or defect.get("class") not in classes:
        return False
    if defect.get("class") == "vulnerable-dependency":
        return _message_names_package(result, defect.get("package"))
    start, end = location[1], location[2]
    if start is None or end is None:
        return False
    defect_start, defect_end = defect.get("start_line"), defect.get("end_line")
    return isinstance(defect_start, int) and isinstance(defect_end, int) and start <= defect_end and defect_start <= end


def _finding_key(result: dict, location: tuple[str, int | None, int | None]) -> tuple:
    rule_id = result.get("ruleId")
    if not isinstance(rule_id, str):
        rule_id = None
    return rule_id, location[0], location[1], location[2]


def confusion_matrix(labels: dict, sarif_documents: list[dict]) -> dict:
    """Return the P-21/P-22 matrix for parsed SARIF documents and labels."""
    defects = labels["defects"]
    set_root = labels["set"]
    tools: dict[str, dict] = {}

    for document in sarif_documents:
        for run in _array(_object(document).get("runs")):
            if not isinstance(run, dict):
                continue
            tool = _tool_id(run)
            state = tools.setdefault(tool, {"matched": set(), "false_positives": set()})
            for result in _array(run.get("results")):
                if not isinstance(result, dict):
                    continue
                kind = result.get("kind")
                if kind is not None and kind != "fail":
                    continue
                if not _empty_suppressions(result.get("suppressions")):
                    continue
                location = _result_location(result, set_root)
                if location is None:
                    continue
                rule = _rule_for(run, result)
                classes = _result_classes(tool, result, rule)
                matches = {
                    index
                    for index, defect in enumerate(defects)
                    if _matches(result, location, classes, defect)
                }
                if matches:
                    state["matched"].update(matches)
                else:
                    state["false_positives"].add(_finding_key(result, location))

    total_defects = len(defects)
    output_tools = {}
    for tool in sorted(tools):
        matched = tools[tool]["matched"]
        tp = len(matched)
        fp = len(tools[tool]["false_positives"])
        fn = total_defects - tp
        precision_denominator = tp + fp
        recall_denominator = tp + fn
        f1_denominator = 2 * tp + fp + fn
        output_tools[tool] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(tp / precision_denominator, 4) if precision_denominator else None,
            "recall": round(tp / recall_denominator, 4) if recall_denominator else None,
            "f1": round(2 * tp / f1_denominator, 4) if f1_denominator else None,
        }

    return {"set": set_root, "defects": total_defects, "tools": output_tools}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="per-tool confusion matrix of SARIF against labels (CI-SPEC.md P-23)")
    parser.add_argument("--labels", required=True, help="the labels file (P-14)")
    parser.add_argument("sarif", nargs="+", help="SARIF 2.1.0 files")
    args = parser.parse_args(argv)
    with open(args.labels, encoding="utf-8") as fh:
        labels = json.load(fh)
    documents = []
    for path in args.sarif:
        with open(path, encoding="utf-8") as fh:
            documents.append(json.load(fh))
    json.dump(confusion_matrix(labels, documents), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())