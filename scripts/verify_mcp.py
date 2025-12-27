#!/usr/bin/env python3
"""Verification script for MCP tools and resources.

This script verifies that all 64 tools and 6 resources are properly
registered in the MCP server.

Usage:
    uv run python scripts/verify_mcp.py
"""

import re
import sys
from pathlib import Path

# Expected counts
EXPECTED_TOOLS = 71  # 64 original + 7 ergonomics tools
EXPECTED_RESOURCES = 6

# Tool categories with expected counts
EXPECTED_TOOL_CATEGORIES = {
    "Orchestration": 23,
    "Topology": 6,
    "Session": 12,
    "Hooks": 8,
    "Semantic Memory": 6,
    "Command": 9,
    "Ergonomics": 7,  # squad, list_aliases, detect_intent, detect_all_intents, list_shortcuts, run_shortcut, detect_project
}


def extract_tools_from_server(server_path: Path) -> list[str]:
    """Extract tool names from server.py."""
    content = server_path.read_text()

    # Find all @mcp.tool() decorated functions
    # Pattern: @mcp.tool() followed by def function_name
    pattern = r'@mcp\.tool\(\)\s+@?(?:observe\([^)]*\)\s+)?def\s+(\w+)'
    tools = re.findall(pattern, content)

    return tools


def extract_resources_from_server(server_path: Path) -> list[str]:
    """Extract resource URIs from server.py."""
    content = server_path.read_text()

    # Find all @mcp.resource() decorated functions
    pattern = r'@mcp\.resource\("([^"]+)"\)'
    resources = re.findall(pattern, content)

    return resources


def extract_observe_decorators(server_path: Path) -> list[str]:
    """Extract @observe decorated functions from server.py."""
    content = server_path.read_text()

    # Pattern: @observe(name="function_name")
    pattern = r'@observe\(name="(\w+)"\)'
    observed = re.findall(pattern, content)

    return observed


def verify_tools(tools: list[str]) -> tuple[bool, list[str]]:
    """Verify tools are correctly registered."""
    issues = []

    if len(tools) != EXPECTED_TOOLS:
        issues.append(f"Expected {EXPECTED_TOOLS} tools, found {len(tools)}")

    # Check for duplicates
    duplicates = [t for t in tools if tools.count(t) > 1]
    if duplicates:
        issues.append(f"Duplicate tools: {set(duplicates)}")

    return len(issues) == 0, issues


def verify_resources(resources: list[str]) -> tuple[bool, list[str]]:
    """Verify resources are correctly registered."""
    issues = []

    if len(resources) != EXPECTED_RESOURCES:
        issues.append(f"Expected {EXPECTED_RESOURCES} resources, found {len(resources)}")

    # Expected resource patterns (using actual parameter names from server.py)
    expected_patterns = [
        "squad://agents",
        "squad://agents/{agent_name}",
        "squad://skills",
        "squad://skills/{skill_name}",
        "squad://commands",
        "squad://commands/{category}/{command_name}",
    ]

    for pattern in expected_patterns:
        if pattern not in resources:
            issues.append(f"Missing resource: {pattern}")

    return len(issues) == 0, issues


def verify_observe_coverage(tools: list[str], observed: list[str]) -> tuple[bool, list[str]]:
    """Verify all tools have @observe decorators."""
    issues = []

    if len(tools) != len(observed):
        issues.append(f"Tools ({len(tools)}) != Observed ({len(observed)})")

    missing = set(tools) - set(observed)
    if missing:
        issues.append(f"Missing @observe: {missing}")

    extra = set(observed) - set(tools)
    if extra:
        issues.append(f"Extra @observe: {extra}")

    return len(issues) == 0, issues


def print_summary(
    tools: list[str],
    resources: list[str],
    observed: list[str],
    tools_ok: bool,
    resources_ok: bool,
    observe_ok: bool,
) -> None:
    """Print verification summary."""
    print("=" * 60)
    print("MCP Server Verification Report")
    print("=" * 60)
    print()

    # Tools summary
    status = "\u2713" if tools_ok else "\u2717"
    print(f"{status} Tools: {len(tools)}/{EXPECTED_TOOLS}")

    # Resources summary
    status = "\u2713" if resources_ok else "\u2717"
    print(f"{status} Resources: {len(resources)}/{EXPECTED_RESOURCES}")

    # Observe coverage
    status = "\u2713" if observe_ok else "\u2717"
    print(f"{status} Langfuse @observe coverage: {len(observed)}/{len(tools)}")

    print()
    print("-" * 60)
    print("Tool List:")
    print("-" * 60)
    for i, tool in enumerate(sorted(tools), 1):
        has_observe = "\u2713" if tool in observed else "\u2717"
        print(f"  {i:2}. {tool} {has_observe}")

    print()
    print("-" * 60)
    print("Resource List:")
    print("-" * 60)
    for i, resource in enumerate(resources, 1):
        print(f"  {i}. {resource}")

    print()


def main() -> int:
    """Run verification."""
    # Find server.py
    project_root = Path(__file__).parent.parent
    server_path = project_root / "orchestrator" / "server.py"

    if not server_path.exists():
        print(f"Error: {server_path} not found")
        return 1

    # Extract data
    tools = extract_tools_from_server(server_path)
    resources = extract_resources_from_server(server_path)
    observed = extract_observe_decorators(server_path)

    # Verify
    tools_ok, tools_issues = verify_tools(tools)
    resources_ok, resources_issues = verify_resources(resources)
    observe_ok, observe_issues = verify_observe_coverage(tools, observed)

    # Print summary
    print_summary(tools, resources, observed, tools_ok, resources_ok, observe_ok)

    # Print issues
    all_issues = tools_issues + resources_issues + observe_issues
    if all_issues:
        print("Issues Found:")
        print("-" * 60)
        for issue in all_issues:
            print(f"  - {issue}")
        print()

    # Overall result
    all_ok = tools_ok and resources_ok and observe_ok
    print("=" * 60)
    if all_ok:
        print("PASS: All verifications passed")
        return 0
    else:
        print("FAIL: Some verifications failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
