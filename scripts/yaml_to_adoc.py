#!/usr/bin/env python3
"""
Convert data-table.yaml into AsciiDoc (.adoc) with row-spanned cells
that reflect the hierarchical Domain > Function > Description > Tests structure.

Usage:
    python3 yaml_to_adoc.py [input.yaml] [output.adoc]
"""
import yaml
import sys
import re

GH_REPO = "NVIDIA/ISV-NCP-Validation-Suite"


def count_tests(node, level):
    """Recursively count leaf tests below a tree node."""
    if level == "domain":
        return sum(count_tests(f, "function") for f in node.get("functions", []))
    if level == "function":
        return sum(count_tests(d, "description") for d in node.get("descriptions", []))
    return len(node.get("tests", []))


def esc(val):
    """Escape a value for use inside an AsciiDoc table cell."""
    if val is None:
        return ""
    s = str(val)
    s = s.replace("|", "\\|")
    return s


def fmt_bool(val):
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    return str(val) if val is not None else ""


def span_cell(span, content):
    """Return an AsciiDoc cell with .N+ row-span prefix when N > 1."""
    if span > 1:
        return f".{span}+| {content}"
    return f"| {content}"


def fmt_gh_issues(entries):
    """Format github_issues list into AsciiDoc with hyperlinks and TODO markers."""
    if not entries:
        return ""
    parts = []
    for entry in entries:
        m = re.match(r"#(\d+)\s*\((\w+)\)(.*)", entry)
        if m:
            num, state, rest = m.group(1), m.group(2), m.group(3).strip()
            link = f"https://github.com/{GH_REPO}/issues/{num}"
            icon = "icon:check-circle[role=green]" if state == "closed" else "icon:exclamation-circle[role=red]"
            label = f"{icon} {link}[#{num}]"
            if "TODO" in rest:
                todo_text = rest.lstrip("# ").strip()
                label += f" [small]#({todo_text})#"
            parts.append(label)
        else:
            parts.append(esc(entry))
    return " +\n".join(parts)


def main():
    infile = sys.argv[1] if len(sys.argv) > 1 else "docs/test-plan.yaml"
    outfile = sys.argv[2] if len(sys.argv) > 2 else "docs/test-plan.adoc"

    with open(infile, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    lines = [
        "= NCP Validation Test Suite",
        ":toc:",
        ":icons: font",
        ":max-width: none",
        "",
        "[cols=\"2,2,5,2,1,1,1,3,1,1,1,6\",options=\"header\"]",
        "|===",
        "| Test Domain | Function | Description | Example | Min Req | Notes | Priority | Issues | Dependency | Milestone | Release | Test Cases",
        "",
    ]

    for domain in data.get("domains", []):
        d_span = count_tests(domain, "domain")
        if d_span == 0:
            continue
        first_d = True

        for func in domain.get("functions", []):
            f_span = count_tests(func, "function")
            if f_span == 0:
                continue
            first_f = True

            for desc in func.get("descriptions", []):
                tests = desc.get("tests", [])
                desc_span = len(tests)
                if desc_span == 0:
                    continue
                first_desc = True

                for test in tests:
                    parts = []

                    if first_d:
                        parts.append(span_cell(d_span, esc(domain["name"])))
                        first_d = False

                    if first_f:
                        parts.append(span_cell(f_span, esc(func["name"])))
                        first_f = False

                    if first_desc:
                        parts.append(span_cell(desc_span, esc(desc.get("text", ""))))
                        parts.append(span_cell(desc_span, esc(desc.get("example", ""))))
                        first_desc = False

                    parts.append(f"| {fmt_bool(test.get('min_req', ''))}")
                    parts.append(f"| {esc(test.get('notes', ''))}")
                    parts.append(f"| {esc(test.get('priority', ''))}")
                    parts.append(f"a| {fmt_gh_issues(test.get('github_issues', []))}")
                    parts.append(f"| {esc(test.get('dependency', ''))}")
                    parts.append(f"| {esc(test.get('milestone', ''))}")
                    parts.append(f"| {esc(test.get('release', ''))}")
                    parts.append(f"| {esc(test.get('summary', ''))}")

                    lines.append("\n".join(parts))
                    lines.append("")

    lines.append("|===")

    with open(outfile, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")

    print(f"Wrote {outfile}")


if __name__ == "__main__":
    main()
