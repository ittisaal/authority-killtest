#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import importlib.util
import json
import re
import tarfile
import urllib.request
from collections import defaultdict
from pathlib import Path

UA = "authority-provenance-discovery/0.1"
TEXT_EXTENSIONS = {
    ".md", ".rst", ".txt", ".py", ".sh", ".bash", ".zsh", ".yml", ".yaml",
    ".json", ".tf", ".hcl", ".js", ".ts", ".tsx", ".jsx", ".go", ".rb",
    ".java", ".kt", ".kts", ".toml", ".ini", ".cfg", ".conf", ".cue",
}
SKIP_PARTS = {"node_modules", ".git", "vendor", "dist", "build", "target", ".venv", "venv"}
MAX_ARCHIVE_BYTES = 75 * 1024 * 1024
MAX_FILE_BYTES = 750 * 1024
MAX_TEXT_FILES = 6000

HERE = Path(__file__).resolve().parents[1] / "public-corpus" / "extract_evidence.py"
spec = importlib.util.spec_from_file_location("extract_evidence", HERE)
extract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract)


def canonical(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def acceptable_name(name: str) -> bool:
    if not name or len(name) > 100:
        return False
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        return False
    if name.lower() in {
        "property", "property_name", "name", "value", "values", "true", "false",
        "string", "single_select", "multi_select", "true_false", "custom_properties",
    }:
        return False
    return len(canonical(name)) >= 3


def archive_url(repository: str, commit: str) -> str:
    owner, repo = repository.split("/", 1)
    return f"https://codeload.github.com/{owner}/{repo}/tar.gz/{commit}"


def read_limited(url: str, limit: int = MAX_ARCHIVE_BYTES) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    out = bytearray()
    with urllib.request.urlopen(req, timeout=60) as response:
        declared = response.headers.get("Content-Length")
        if declared and int(declared) > limit:
            raise RuntimeError(f"archive exceeds byte cap: {declared} > {limit}")
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.extend(chunk)
            if len(out) > limit:
                raise RuntimeError(f"archive exceeded byte cap while downloading: {limit}")
    return bytes(out)


def path_priority(path: str) -> tuple[int, int, str]:
    low = path.lower()
    score = 50
    if low.startswith(".github/") or "/.github/" in low:
        score -= 25
    for token, weight in (
        ("custom_propert", 24), ("ruleset", 22), ("workflow", 18), ("security", 16),
        ("policy", 15), ("terraform", 12), ("github", 11), ("config", 8),
        ("script", 7), ("docs", 5), ("readme", 4),
    ):
        if token in low:
            score -= weight
    return score, len(path), path


def eligible(path: str, size: int) -> bool:
    if size > MAX_FILE_BYTES:
        return False
    parts = set(Path(path).parts)
    if parts & SKIP_PARTS:
        return False
    suffix = Path(path).suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return True
    return Path(path).name.lower() in {"readme", "dockerfile", "makefile"}


def repository_documents(repository: str, commit: str):
    payload = read_limited(archive_url(repository, commit))
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as tf:
        members = []
        for member in tf.getmembers():
            if not member.isfile():
                continue
            bits = Path(member.name).parts
            path = str(Path(*bits[1:])) if len(bits) > 1 else member.name
            if eligible(path, member.size):
                members.append((path_priority(path), path, member))
        members.sort(key=lambda row: row[0])
        selected = members[:MAX_TEXT_FILES]
        docs = []
        for _, path, member in selected:
            fh = tf.extractfile(member)
            if fh is None:
                continue
            raw = fh.read(MAX_FILE_BYTES + 1)
            if len(raw) > MAX_FILE_BYTES or b"\x00" in raw[:8192]:
                continue
            text = raw.decode("utf-8", errors="replace")
            url = f"https://github.com/{repository}/blob/{commit}/{path}"
            docs.append((url, text))
    return docs, {
        "archive_bytes": len(payload),
        "eligible_text_files": len(members),
        "scanned_text_files": len(docs),
        "file_cap_reached": len(members) > MAX_TEXT_FILES,
    }


def string_constants(docs):
    constants = {}
    patterns = [
        re.compile(r"(?m)^\s*(?:export\s+)?([A-Z][A-Z0-9_]{2,})\s*=\s*['\"]([^'\"\n]{1,120})['\"]"),
        re.compile(r"(?m)^\s*(?:const\s+)?([A-Z][A-Z0-9_]{2,})\s*[:=]\s*['\"]([^'\"\n]{1,120})['\"]"),
    ]
    for _, text in docs:
        for pattern in patterns:
            for m in pattern.finditer(text):
                value = m.group(2).strip()
                if acceptable_name(value):
                    constants.setdefault(m.group(1), value)
    return constants


def resolve_token(token: str, constants) -> str | None:
    value = token.strip().strip(",)")
    if (len(value) >= 2) and value[0] in "'\"" and value[-1] == value[0]:
        value = value[1:-1]
    value = value.strip()
    value = re.sub(r"^\$\{?", "", value)
    value = value.rstrip("}")
    if value in constants:
        value = constants[value]
    return value if acceptable_name(value) else None


def add_candidate(found, name: str | None, url: str, signal: str):
    if not name or not acceptable_name(name):
        return
    key = canonical(name)
    row = found[key]
    if not row["name"]:
        row["name"] = name
    # Prefer a literal mixed-case/hyphen form over an all-uppercase variable alias.
    if row["name"].isupper() and not name.isupper():
        row["name"] = name
    row["signals"].add(signal)
    row["files"].add(url)


def discover_candidates(docs):
    constants = string_constants(docs)
    found = defaultdict(lambda: {"name": None, "signals": set(), "files": set()})

    direct_patterns = [
        ("event-dot", re.compile(r"github\.event\.repository\.custom_properties\.([A-Za-z0-9_.-]+)")),
        ("event-bracket", re.compile(r"github\.event\.repository\.custom_properties\s*\[\s*['\"]([^'\"]+)['\"]\s*\]")),
        ("repo-dot", re.compile(r"repository\.custom_properties\.([A-Za-z0-9_.-]+)")),
        ("repo-bracket", re.compile(r"repository\.custom_properties\s*\[\s*['\"]([^'\"]+)['\"]\s*\]")),
        ("oidc-claim", re.compile(r"\brepo_property_([A-Za-z][A-Za-z0-9_.-]{1,100})\b")),
        ("schema-path", re.compile(r"/properties/schema/([A-Za-z0-9_.-]+)\b")),
    ]

    property_assignment = re.compile(
        r"\bproperty_name\s*[:=]\s*(?P<token>['\"][^'\"\n]+['\"]|[A-Za-z_][A-Za-z0-9_]*)"
    )
    create_call = re.compile(
        r"\bcreate_property\s+(?P<token>['\"]?\$?\{?[A-Za-z_][A-Za-z0-9_.-]*\}?['\"]?)"
    )

    for url, text in docs:
        for signal, pattern in direct_patterns:
            for m in pattern.finditer(text):
                add_candidate(found, m.group(1), url, signal)

        for m in property_assignment.finditer(text):
            local = text[max(0, m.start() - 500): min(len(text), m.end() + 1000)].lower()
            if any(token in local for token in (
                "custom propert", "organizationcustomproperties", "values_editable_by",
                "allowed_values", "properties/schema", "repository_property",
            )):
                add_candidate(found, resolve_token(m.group("token"), constants), url, "property-name")

        for m in create_call.finditer(text):
            local = text[max(0, m.start() - 300): min(len(text), m.end() + 900)].lower()
            if "org_and_repo_actors" in local or "org_actors" in local or "property" in local:
                add_candidate(found, resolve_token(m.group("token"), constants), url, "create-property")

        # Ruleset condition form: {'name': PROPERTY_NAME, 'property_values': [...]}
        for m in re.finditer(r"['\"]name['\"]\s*:\s*(?P<token>['\"][^'\"\n]+['\"]|[A-Za-z_][A-Za-z0-9_]*)", text):
            local = text[max(0, m.start() - 300): min(len(text), m.end() + 500)].lower()
            if "property_values" in local and "repository_property" in text[max(0, m.start()-1200):m.end()+500].lower():
                add_candidate(found, resolve_token(m.group("token"), constants), url, "ruleset-property")

    rows = []
    for key, row in found.items():
        rows.append({
            "canonical": key,
            "property": row["name"],
            "signals": sorted(row["signals"]),
            "discovery_files": sorted(row["files"]),
        })
    rows.sort(key=lambda r: (-len(r["signals"]), r["property"].lower()))
    return rows


def candidate_documents(prop: str, docs):
    names = extract.variants(prop)
    selected = []
    for url, text in docs:
        low = text.lower()
        if any(name.lower() in low for name in names):
            selected.append((url, text))
    # Callable linking in the semantic extractor can require a definition in another file,
    # so include code files containing definitions of functions called near selected evidence.
    called = set()
    for _, text in selected:
        for w in extract.windows(text, names, 800):
            for name in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", w):
                if name not in {"if", "for", "while", "print", "get", "set"}:
                    called.add(name)
    if called:
        for url, text in docs:
            if (url, text) in selected:
                continue
            if any(re.search(r"(?m)^\s*def\s+" + re.escape(name) + r"\s*\(", text) for name in called):
                selected.append((url, text))
    return selected


def classify_property(prop: str, docs):
    subset = candidate_documents(prop, docs)
    actor, aev = extract.authority(prop, subset)
    relation, cev = extract.consumer(prop, subset)
    reduction, guard, sev = extract.semantics(prop, subset)
    no_edge, nev = extract.explicit_no_edge(prop, subset)
    label, reason = extract.classify(actor, relation, reduction, guard, no_edge)
    short = {"unsafe": "U", "safe": "S", "unknown": "N"}[label]
    return {
        "property": prop,
        "label": short,
        "reason": reason,
        "evidence_files_scanned": len(subset),
        "extracted": {
            "actor_can_modify": actor,
            "consumer_relation": "confirmed_no_policy_edge" if no_edge else relation,
            "protection_reducing_state_observed": reduction,
            "independent_guard_observed": guard,
        },
        "evidence_files": {
            "authority": aev,
            "consumer": cev,
            "semantics": sev,
            "no_edge": nev,
        },
    }


def discover(repository: str, commit: str):
    docs, scan = repository_documents(repository, commit)
    candidates = discover_candidates(docs)
    classified = []
    for candidate in candidates:
        row = classify_property(candidate["property"], docs)
        row.update({
            "canonical": candidate["canonical"],
            "discovery_signals": candidate["signals"],
            "discovery_files": candidate["discovery_files"],
        })
        classified.append(row)
    return {
        "repository": repository,
        "commit": commit,
        "scan": scan,
        "candidate_count": len(classified),
        "candidates": classified,
        "claim_boundary": (
            "Repository-level candidate discovery from an exact public snapshot. This prototype does not "
            "query private organization settings or external policy systems that are absent from the repository."
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repository")
    ap.add_argument("commit")
    ap.add_argument("--output", default="-")
    args = ap.parse_args()
    result = discover(args.repository, args.commit)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output == "-":
        print(text)
    else:
        Path(args.output).write_text(text + "\n")


if __name__ == "__main__":
    main()
