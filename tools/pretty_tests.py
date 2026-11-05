"""Print a pytest JUnit report the way Jest or Mocha print test results.

Tests are grouped by module, each one marked with a tick or a cross and
its duration, and a summary closes the run.  Colours are only used when
writing to a terminal and ``NO_COLOR`` is unset.

Usage: ``python3 tools/pretty_tests.py build/test-report.xml``
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from typing import Final

USE_COLOR: Final = sys.stdout.isatty() and "NO_COLOR" not in os.environ


def paint(text: str, code: str) -> str:
    """Wrap ``text`` in an ANSI colour code when colours are enabled."""
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def first_line(case: ET.Element) -> str:
    """Return the first line of a failed test's message."""
    problem = case.find("failure")
    if problem is None:
        problem = case.find("error")
    if problem is None:
        return ""
    message = problem.get("message") or problem.text or ""
    return message.strip().splitlines()[0] if message.strip() else ""


def main(argv: list[str]) -> int:
    """Print the report named in ``argv``; return 1 if anything failed."""
    if len(argv) != 2:
        print("usage: pretty_tests.py REPORT.xml", file=sys.stderr)
        return 2
    try:
        root = ET.parse(argv[1]).getroot()
    except (OSError, ET.ParseError) as error:
        print(f"cannot read the test report: {error}", file=sys.stderr)
        return 2
    suite = root.find("testsuite") if root.tag == "testsuites" else root
    if suite is None:
        print("the test report has no test suite", file=sys.stderr)
        return 2

    groups: dict[str, list[ET.Element]] = {}
    for case in suite.iter("testcase"):
        groups.setdefault(case.get("classname", "?"), []).append(case)

    passed = failed = skipped = 0
    for module, cases in groups.items():
        print("\n" + paint(module, "1"))
        for case in cases:
            name = case.get("name", "?")
            took = paint(f"({float(case.get('time', 0)) * 1000:.0f} ms)", "2")
            if case.find("failure") is not None \
                    or case.find("error") is not None:
                failed += 1
                print(f"  {paint('✗ ' + name, '31')} {took}")
                reason = first_line(case)
                if reason:
                    print(f"      {paint(reason, '31')}")
            elif case.find("skipped") is not None:
                skipped += 1
                print(paint(f"  ○ {name} (skipped)", "2"))
            else:
                passed += 1
                print(f"  {paint('✓', '32')} {name} {took}")

    total = passed + failed + skipped
    print()
    print(f"{paint('Test Suites:', '1')} {len(groups)} modules")
    print(f"{paint('Tests:', '1')}       "
          f"{paint(f'{passed} passed', '32')}, "
          f"{paint(f'{failed} failed', '31' if failed else '2')}, "
          f"{skipped} skipped, {total} total")
    print(f"{paint('Time:', '1')}        "
          f"{float(suite.get('time', 0)):.2f} s")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
