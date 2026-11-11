#!/usr/bin/env python3
"""Offline catalog search, documentation generation, and consistency checks."""

import argparse
import datetime
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "catalog" / "arsenal.json"
SHA = re.compile(r"[0-9a-f]{40}\Z")
CATEGORIES = (
    "AI Engineering", "Agent / Context", "AI Security", "Cyber",
    "Reverse / DFIR", "Engineering", "Cloud / DevOps", "Web / Frontend",
)


def read_catalog(path=DATA):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_catalog(data):
    """Reject malformed JSON before the CLI's consumers access catalog fields."""
    if not isinstance(data, dict):
        return ["Catalog must be an object"]

    errors = []
    if type(data.get("schema_version")) is not int or data["schema_version"] != 2:
        errors.append("Unsupported schema_version")
    try:
        datetime.date.fromisoformat(data["as_of"])
    except (KeyError, TypeError, ValueError):
        errors.append("as_of must be an ISO date")
    if not isinstance(data.get("snapshot"), str) or not data["snapshot"].strip():
        errors.append("snapshot must be a non-empty string")
    for field in ("sources", "skills", "evidence", "tools"):
        if not isinstance(data.get(field), list):
            errors.append(f"{field} must be an array")
            continue
        for index, record in enumerate(data[field]):
            if not isinstance(record, dict):
                errors.append(f"{field}[{index}] must be an object")
    if errors:
        return errors

    text_fields = {
        "sources": ("repo", "url", "commit", "license", "note", "kind"),
        "skills": ("repo", "path", "commit", "blob_sha", "url", "name",
                   "purpose", "requires", "note", "category", "review_level"),
        "evidence": ("repo", "path", "url", "blob_sha"),
        "tools": ("repo", "name", "group", "purpose", "requires", "note",
                  "url", "review_level"),
    }
    for field, required in text_fields.items():
        for index, record in enumerate(data[field]):
            label = f"{field}[{index}]"
            for key in required:
                if not isinstance(record.get(key), str) or not record[key].strip():
                    errors.append(f"{label}.{key} must be a non-empty string")
            if "reviewed_at" in record:
                try:
                    datetime.date.fromisoformat(record["reviewed_at"])
                except (TypeError, ValueError):
                    errors.append(f"{label}.reviewed_at must be an ISO date")
    for index, source in enumerate(data["sources"]):
        for key in ("license_url", "readme_url"):
            value = source.get(key)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                errors.append(f"sources[{index}].{key} must be a non-empty string or null")
        for key in ("license_blob_sha", "readme_blob_sha"):
            value = source.get(key)
            if value is not None and (not isinstance(value, str) or not SHA.fullmatch(value)):
                errors.append(f"sources[{index}].{key} must be a SHA or null")
    for index, entry in enumerate(data["skills"]):
        if type(entry.get("id")) is not int or entry["id"] < 1:
            errors.append(f"Invalid entry ID: skills[{index}].id")
        tags = entry.get("tags")
        if not isinstance(tags, list) or not tags or any(
                not isinstance(tag, str) or not tag.strip() for tag in tags):
            errors.append(f"skills[{index}].tags must be a non-empty array of non-empty strings")
    if errors:
        return errors

    sources = {}
    for source in data.get("sources", []):
        repo = source.get("repo", "")
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
            errors.append(f"Invalid repository: {repo}")
        if repo in sources:
            errors.append(f"Duplicate source: {repo}")
        sources[repo] = source
        if not SHA.fullmatch(source.get("commit", "")):
            errors.append(f"Invalid source commit: {repo}")
        if source.get("url") != f"https://github.com/{repo}":
            errors.append(f"Source URL mismatch: {repo}")
        if not source.get("license"):
            errors.append(f"Missing license note: {repo}")
        if source.get("kind") not in ("skill-collection", "tool"):
            errors.append(f"Invalid source kind: {repo}")
    seen_ids, seen_entries = set(), set()
    for entry in data.get("skills", []):
        ident = entry.get("id")
        if type(ident) is not int or ident < 1 or ident in seen_ids:
            errors.append(f"Invalid or duplicate entry ID: {ident}")
        seen_ids.add(ident)
        repo, path = entry.get("repo", ""), entry.get("path", "")
        key = (repo, path)
        if key in seen_entries:
            errors.append(f"Duplicate entry path: {key}")
        seen_entries.add(key)
        source = sources.get(repo)
        if source is None:
            errors.append(f"Unknown source: {repo}")
        elif entry.get("commit") != source.get("commit"):
            errors.append(f"Source/entry revision mismatch: {ident}")
        for field in ("commit", "blob_sha"):
            if not SHA.fullmatch(entry.get(field, "")):
                errors.append(f"Invalid {field}: {ident}")
        if not path.endswith("SKILL.md") or path.startswith("/") or ".." in Path(path).parts:
            errors.append(f"Invalid entry path: {ident}")
        expected = f"https://github.com/{repo}/blob/{entry.get('commit')}/{path}"
        if entry.get("url") != expected:
            errors.append(f"Pinned URL mismatch: {ident}")
        for field in ("name", "purpose", "requires", "note"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                errors.append(f"Missing {field}: {ident}")
        if entry.get("category") not in CATEGORIES:
            errors.append(f"Unknown category: {ident}")
        level = entry.get("review_level")
        if level not in ("entry-reviewed", "entry-overview"):
            errors.append(f"Invalid review level: {ident}")
        if entry.get("read") is not (level == "entry-reviewed") or entry.get("runtime_tested") is not False:
            errors.append(f"Schema v2 only supports source-reviewed, untested entries with matching scope: {ident}")
        if not isinstance(entry.get("tags"), list) or not entry["tags"]:
            errors.append(f"Missing tags: {ident}")
        if source and source.get("kind") != "skill-collection":
            errors.append(f"Skill points at a tool source: {ident}")
    if not sources or not (seen_entries or data.get("tools")):
        errors.append("Catalog must contain sources and entries")
    for evidence in data.get("evidence", []):
        repo = evidence.get("repo")
        source = sources.get(repo)
        if source is None or not SHA.fullmatch(evidence.get("blob_sha", "")):
            errors.append(f"Invalid supporting evidence: {repo}")
            continue
        path = evidence["path"]
        if path.startswith("/") or ".." in Path(path).parts:
            errors.append(f"Invalid supporting evidence path: {repo}")
        expected = f"https://github.com/{repo}/blob/{source['commit']}/{evidence.get('path')}"
        if evidence.get("url") != expected:
            errors.append(f"Supporting evidence URL mismatch: {repo}")
    seen_tools = set()
    for tool in data.get("tools", []):
        repo = tool.get("repo")
        source = sources.get(repo)
        if not source or source.get("kind") != "tool" or repo in seen_tools:
            errors.append(f"Invalid or duplicate tool source: {repo}")
        elif tool.get("url") != f"{source['url']}/tree/{source['commit']}":
            errors.append(f"Tool revision mismatch: {repo}")
        seen_tools.add(repo)
        if tool.get("runtime_tested") is not False or tool.get("review_level") != "readme-overview":
            errors.append(f"Unsupported tool execution claim: {repo}")
        if any(not tool.get(k) for k in ("name", "group", "purpose", "requires", "note")):
            errors.append(f"Incomplete tool: {repo}")
    if seen_tools != {s["repo"] for s in data.get("sources", []) if s.get("kind") == "tool"}:
        errors.append("Tool inventory does not match source register")
    return errors


def search(data, query, category=None, review=None, repo=None):
    needle = query.casefold()
    return [s for s in data["skills"]
            if (category is None or s["category"] == category)
            and (review is None or s["review_level"] == review)
            and (repo is None or s["repo"].casefold() == repo.casefold())
            and needle in " ".join(str(s[k]) for k in
                                    ("name", "repo", "purpose", "requires", "note")).casefold()]


def search_tools(data, query="", group=None):
    needle = query.casefold()
    return [t for t in data["tools"]
            if (group is None or t["group"].casefold() == group.casefold())
            and needle in " ".join(t[k] for k in
                                    ("name", "repo", "group", "purpose", "requires", "note")).casefold()]


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def rendered_files(data):
    catalog = ["# Skill catalog", "", "[Home](README.md) · [ภาษาไทย](README.th.md) · [Sources](SOURCES.md)", "",
               f"Snapshot: **{data['as_of']}** · **{len(data['skills'])} selected entries**.", "",
               "Thai editorial summaries with pinned entry links. **Entry** means the entry was read in the initial focused review; **Overview** means frontmatter and an opening excerpt were inspected, not the complete bundle. Neither status means runtime-tested.", "",
               "Generated from `catalog/arsenal.json` with `python3 scripts/arsenal.py render`.", ""]
    for category in CATEGORIES:
        entries = [s for s in data["skills"] if s["category"] == category]
        if not entries:
            continue
        catalog += [f"## {category}", "", "| Skill / source | ใช้ทำอะไร | Review | ต้องมี / หมายเหตุ |",
                    "| --- | --- | --- | --- |"]
        for s in entries:
            level = "Entry" if s["review_level"] == "entry-reviewed" else "Overview"
            catalog.append(f"| **#{s['id']}** [{s['name']}]({s['url']}) · `{s['repo']}` | {cell(s['purpose'])} | {level} | {cell(s['requires'])}. {cell(s['note'])} |")
        catalog += [""]
    sources = ["# Source register", "", "[Home](README.md) · [Skill catalog](CATALOG.md) · [Reuse notes](docs/attribution.md)", "",
               f"Snapshot: **{data['as_of']}**. The {len(data['sources'])} sources include skill collections, tools and frameworks. License descriptions apply to the inspected snapshot and scope; follow the linked texts before reuse.", "",
               "Generated from `catalog/arsenal.json` with `python3 scripts/arsenal.py render`.", "",
               "| Source / reviewed commit | License evidence | Editorial note |", "| --- | --- | --- |"]
    for s in data["sources"]:
        revision = f"{s['url']}/tree/{s['commit']}"
        license_url = s.get("license_url")
        license_text = cell(s["license"])
        if license_url:
            license_text = f"[{license_text}]({license_url})"
        sources.append(f"| [{s['repo']}]({s['url']}) · [{s['commit'][:8]}]({revision}) | {license_text} | {cell(s['note'])} |")
    sources += ["", "## Supporting files read in the initial focused review", "", "These supporting files are additional evidence, not extra skills.", ""]
    for e in data["evidence"]:
        sources.append(f"- [{e['repo']} / {e['path']}]({e['url']})")
    tools = ["# Companion tools", "", "[Home](README.md) · [Skill catalog](CATALOG.md) · [Sources and licenses](SOURCES.md)", "",
             "These are executable tools and frameworks, counted separately from agent skills. Their README/source overviews were inspected; this repository has not installed or run them. Links point to the recorded revision.", ""]
    groups = list(dict.fromkeys(t["group"] for t in data["tools"]))
    tools += [f"**{len(data['tools'])} tools and frameworks in {len(groups)} groups.** See [start here](docs/start-here.md) for task-oriented selections.", "",
              "| Group | Tools |", "| --- | ---: |"]
    for group in groups:
        anchor = re.sub(r"[^a-z0-9]+", "-", group.lower()).strip("-")
        tools.append(f"| [{group}](#{anchor}) | {sum(t['group'] == group for t in data['tools'])} |")
    tools += [""]
    for group in groups:
        anchor = re.sub(r"[^a-z0-9]+", "-", group.lower()).strip("-")
        tools += [f'<a id="{anchor}"></a>', "", f"## {group}", "", "| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |", "| --- | --- | --- |"]
        for t in (t for t in data["tools"] if t["group"] == group):
            tools.append(f"| [{t['name']}]({t['url']}) | {cell(t['purpose'])} | {cell(t['requires'])}. {cell(t['note'])} |")
        tools += [""]
    counts = stats(data)
    review = ["# Review coverage", "", "[Home](../README.md) · [Methodology](methodology.md)", "",
              f"Snapshot: **{data['as_of']}** · `{data['snapshot']}`", "",
              "| Measure | Count |", "| --- | ---: |",
              *[f"| {key} | {value} |" for key, value in counts.items() if isinstance(value, int)], "",
              "## Meaning of the labels", "",
              "- **Entry / entry-reviewed:** the entry file was read in the first research pass; selected supporting files are listed in the source register. This does not imply every bundled file was reviewed.",
              "- **Overview / entry-overview:** the entry identity, frontmatter and opening excerpt were inspected. Supporting instructions, scripts and references still need a deeper review before adoption.",
              "- **Tool / readme-overview:** introductory README and licensing evidence were inspected. No installation or execution claim is made.",
              "- **Runtime-tested:** none. Local repository checks apply to the catalog and its CLI, not to upstream packages.", "",
              "## Entries by track", "", "| Track | Entries |", "| --- | ---: |",
              *[f"| {name} | {count} |" for name, count in counts["categories"].items()], ""]
    return {"CATALOG.md": "\n".join(catalog).rstrip() + "\n",
            "SOURCES.md": "\n".join(sources).rstrip() + "\n",
            "TOOLS.md": "\n".join(tools).rstrip() + "\n",
            "docs/review-status.md": "\n".join(review).rstrip() + "\n"}


def stats(data):
    return {"Skill entries": len(data["skills"]),
            "Skill collections": sum(s["kind"] == "skill-collection" for s in data["sources"]),
            "Companion tools": len(data["tools"]),
            "Tool categories": len({t["group"] for t in data["tools"]}),
            "Source repositories": len(data["sources"]),
            "Entry-reviewed": sum(s["review_level"] == "entry-reviewed" for s in data["skills"]),
            "Entry-overview": sum(s["review_level"] == "entry-overview" for s in data["skills"]),
            "Runtime-tested upstream skills": sum(s["runtime_tested"] for s in data["skills"]),
            "categories": {c: sum(s["category"] == c for s in data["skills"]) for c in CATEGORIES}}


def local_link_errors(root):
    errors = []
    for path in root.rglob("*.md"):
        content = path.read_text(encoding="utf-8")
        targets = re.findall(r"!?\[[^\]]*\]\(([^\s)]+)\)", content)
        targets += re.findall(r'(?:href|src)="([^"]+)"', content)
        for target in targets:
            try:
                parsed = urlsplit(target)
            except ValueError:
                errors.append(f"Invalid link target: {path.relative_to(root)} -> {target}")
                continue
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            try:
                resolved = (path.parent / unquote(parsed.path)).resolve()
            except (OSError, ValueError):
                errors.append(f"Invalid local file link: {path.relative_to(root)} -> {target}")
                continue
            if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                errors.append(f"Broken local file link: {path.relative_to(root)} -> {target}")
    return errors


def check(data, root=ROOT):
    errors = validate_catalog(data)
    if errors:
        return errors
    for name, expected in rendered_files(data).items():
        path = root / name
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            errors.append(f"Generated file is stale: {name}; run render")
    errors += local_link_errors(root)
    try:
        ET.parse(root / "assets" / "banner.svg")
    except (OSError, ET.ParseError) as exc:
        errors.append(f"Invalid banner SVG: {exc}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    find = commands.add_parser("search", help="Search names and Thai annotations offline")
    find.add_argument("query")
    find.add_argument("--category", choices=CATEGORIES)
    find.add_argument("--review", choices=("entry-reviewed", "entry-overview"))
    find.add_argument("--repo", help="Exact owner/repo filter")
    find.add_argument("--json", action="store_true", help="Emit structured matching entries")
    tool_find = commands.add_parser("tools", help="Search companion tools and frameworks offline")
    tool_find.add_argument("query", nargs="?", default="")
    tool_find.add_argument("--group", help="Exact category name, case-insensitive")
    tool_find.add_argument("--json", action="store_true")
    show = commands.add_parser("show", help="Show one entry by its stable numeric ID")
    show.add_argument("id", type=int)
    commands.add_parser("stats", help="Print catalog counts and review coverage as JSON")
    commands.add_parser("check", help="Validate metadata and local documentation offline")
    commands.add_parser("render", help="Regenerate catalog and source Markdown")
    args = parser.parse_args()
    try:
        data = read_catalog()
        errors = validate_catalog(data)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f"Cannot read catalog: {exc}", file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    if args.command == "search":
        found = search(data, args.query, args.category, args.review, args.repo)
        if args.json:
            print(json.dumps(found, ensure_ascii=False, indent=2))
            return 0
        for entry in found:
            print(f"[{entry['id']:02d}] {entry['name']} ({entry['category']})")
            print(f"  {entry['purpose']}\n  {entry['url']}")
        print(f"{len(found)} match(es). Source review only; no runtime certification.")
    elif args.command == "tools":
        groups = {t["group"].casefold() for t in data["tools"]}
        if args.group and args.group.casefold() not in groups:
            print(f"Unknown tool group: {args.group}", file=sys.stderr)
            return 1
        found = search_tools(data, args.query, args.group)
        if args.json:
            print(json.dumps(found, ensure_ascii=False, indent=2))
        else:
            for tool in found:
                print(f"{tool['name']} ({tool['group']})\n  {tool['purpose']}\n  {tool['url']}")
            print(f"{len(found)} match(es). README overview only; no runtime certification.")
    elif args.command == "show":
        found = next((s for s in data["skills"] if s["id"] == args.id), None)
        if found is None:
            print(f"No entry with ID {args.id}", file=sys.stderr)
            return 1
        print(json.dumps(found, ensure_ascii=False, indent=2))
    elif args.command == "stats":
        print(json.dumps(stats(data), ensure_ascii=False, indent=2))
    elif args.command == "render":
        for name, content in rendered_files(data).items():
            (ROOT / name).write_text(content, encoding="utf-8")
            print(f"Wrote {name}")
    else:
        errors = check(data)
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        print(f"PASS: {len(data['skills'])} entries, {len(data['sources'])} sources; metadata and local files consistent.")
        print("Offline check only. Upstream execution and availability were not tested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
