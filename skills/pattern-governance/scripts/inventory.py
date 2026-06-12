#!/usr/bin/env python3
"""
inventory.py — deterministic structural census of a (TypeScript/NestJS-style) codebase.

Purpose: ground the pattern-governance frequency analysis in real, reproducible counts instead of
estimates. This script reports only what is mechanically true from the filesystem and from cheap text
scanning. It does NOT judge quality and it does NOT do semantic analysis (e.g. it cannot tell whether a
repository returns a domain entity or an ORM row). Import-edge detection is regex-based: high recall,
approximate — confirm any flagged boundary violation by reading the file before reporting it.

Stdlib only. Works anywhere with Python 3.8+.

Usage:
    python inventory.py <source-root> [options]

Options:
    --modules-subdir NAME     Directory under source-root holding modules (default: modules)
    --canonical-dirs CSV      Expected per-module subdirs to check for
                              (default: domain,use-cases,infrastructure,public,adapters)
    --suffixes CSV            File suffixes to histogram
                              (default: .use-case.ts,.service.ts,.repository.ts,.controller.ts,
                                        .dto.ts,.mapper.ts,.module.ts,.entity.ts,.spec.ts,.test.ts)
    --json PATH               Also write the full census as JSON to PATH
    --quiet                   Suppress the human-readable summary (use with --json)

Exit code is always 0 unless the source root is missing; this is a reporting tool, not a gate.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_CANONICAL_DIRS = ["domain", "use-cases", "infrastructure", "public", "adapters"]
DEFAULT_SUFFIXES = [
    ".use-case.ts", ".service.ts", ".repository.ts", ".controller.ts",
    ".dto.ts", ".mapper.ts", ".module.ts", ".entity.ts", ".spec.ts", ".test.ts",
]

# Matches any import/export specifier:  from '<spec>'   (we resolve <spec> ourselves below,
# because real codebases mix relative imports ('../../payments/public') with alias/absolute ones
# ('@app/modules/payments/public' or 'src/modules/...'). A regex keyed on the literal 'modules/'
# would silently miss every relative cross-module import — i.e. most of them.
SPEC_RE = re.compile(r"""from\s+['"]([^'"]+)['"]""")

SKIP_DIRS = {"node_modules", ".git", "dist", "build", "coverage", ".next", ".turbo"}


def resolve_target_module(spec, importing_file, modules_subdir):
    """Given an import specifier and the file doing the importing, return
    (target_module, segment_after_module) if the import lands inside some module under
    <modules_subdir>, else (None, None). Handles both relative and alias/absolute specifiers.
    segment_after_module is e.g. 'public' / 'domain' / 'infrastructure', used to decide whether the
    import goes through the module's public surface."""
    if spec.startswith("."):
        # Relative import: resolve against the importing file's directory.
        try:
            parts = (importing_file.parent / spec).resolve().parts
        except (OSError, RuntimeError):
            return (None, None)
    else:
        # Alias or absolute specifier (e.g. '@app/modules/x/...', 'src/modules/x/...').
        parts = tuple(re.split(r"[\\/]", spec))
    if modules_subdir in parts:
        idx = parts.index(modules_subdir)
        if idx + 1 < len(parts):
            target_mod = parts[idx + 1]
            after = parts[idx + 2] if idx + 2 < len(parts) else None
            return (target_mod, after)
    return (None, None)


def iter_ts_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith((".ts", ".tsx")):
                yield Path(dirpath) / fn


def list_modules(modules_root: Path):
    if not modules_root.is_dir():
        return []
    return sorted(p for p in modules_root.iterdir() if p.is_dir() and p.name not in SKIP_DIRS)


def suffix_of(filename: str, suffixes):
    # Longest-match wins so ".use-case.ts" is not swallowed by ".ts".
    for s in sorted(suffixes, key=len, reverse=True):
        if filename.endswith(s):
            return s
    return None


def census(root: Path, modules_subdir: str, canonical_dirs, suffixes):
    modules_root = root / modules_subdir
    modules = list_modules(modules_root)
    module_names = {m.name for m in modules}

    result = {
        "source_root": str(root),
        "modules_root": str(modules_root),
        "module_count": len(modules),
        "canonical_dirs_checked": canonical_dirs,
        "modules": {},
        "suffix_totals": Counter(),
        "directory_shape_totals": Counter(),  # which canonical dirs exist, across all modules
        "naming": {
            "default_exports": 0,
            "named_export_files": 0,
        },
        "boundaries": {
            "cross_module_imports": [],          # all imports from one module into another
            "public_bypassing_imports": [],      # cross-module imports NOT going through /public
        },
    }

    # Per-module directory shape + suffix histogram
    for m in modules:
        present = [d for d in canonical_dirs if (m / d).is_dir()]
        missing = [d for d in canonical_dirs if d not in present]
        mod_suffixes = Counter()
        file_count = 0
        for f in iter_ts_files(m):
            file_count += 1
            s = suffix_of(f.name, suffixes)
            if s:
                mod_suffixes[s] += 1
                result["suffix_totals"][s] += 1
        for d in present:
            result["directory_shape_totals"][d] += 1
        result["modules"][m.name] = {
            "path": str(m),
            "canonical_dirs_present": present,
            "canonical_dirs_missing": missing,
            "shape_complete": len(missing) == 0,
            "file_count": file_count,
            "suffix_histogram": dict(mod_suffixes),
        }

    # Whole-tree scans: exports + cross-module imports
    for f in iter_ts_files(root):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if "export default" in text:
            result["naming"]["default_exports"] += text.count("export default")
        if re.search(r"^export\s+(const|function|class|type|interface|enum)\s", text, re.MULTILINE):
            result["naming"]["named_export_files"] += 1

        # Which module does this file belong to (if any)?
        owner = None
        parts = f.parts
        if modules_subdir in parts:
            idx = parts.index(modules_subdir)
            if idx + 1 < len(parts):
                owner = parts[idx + 1]

        for spec in SPEC_RE.findall(text):
            target_mod, after = resolve_target_module(spec, f, modules_subdir)
            if target_mod is None or target_mod not in module_names:
                continue
            if owner == target_mod:
                continue  # intra-module import, fine
            edge = {
                "from_module": owner,
                "from_file": str(f),
                "to_module": target_mod,
                "import_path": spec,
                "via_public": after == "public",
            }
            result["boundaries"]["cross_module_imports"].append(edge)
            if after != "public":
                result["boundaries"]["public_bypassing_imports"].append(edge)

    # Make Counters JSON-serializable
    result["suffix_totals"] = dict(result["suffix_totals"])
    result["directory_shape_totals"] = dict(result["directory_shape_totals"])
    return result


def print_summary(c):
    print(f"\n=== Structural census: {c['source_root']} ===")
    print(f"Modules found: {c['module_count']} (under {c['modules_root']})")

    print("\n-- Directory-shape conformance (per canonical dir, count of modules that have it) --")
    total = c["module_count"] or 1
    for d in c["canonical_dirs_checked"]:
        n = c["directory_shape_totals"].get(d, 0)
        bar = "#" * round(20 * n / total)
        print(f"  {d:<16} {n:>3}/{c['module_count']:<3} {bar}")
    complete = sum(1 for m in c["modules"].values() if m["shape_complete"])
    print(f"  modules with complete canonical shape: {complete}/{c['module_count']}")

    print("\n-- File-suffix totals (naming-convention prevalence) --")
    for s, n in sorted(c["suffix_totals"].items(), key=lambda kv: -kv[1]):
        print(f"  {s:<18} {n:>4}")

    print("\n-- Exports --")
    print(f"  files with named exports : {c['naming']['named_export_files']}")
    print(f"  'export default' occurrences: {c['naming']['default_exports']}")

    print("\n-- Cross-module boundaries --")
    xm = c["boundaries"]["cross_module_imports"]
    bypass = c["boundaries"]["public_bypassing_imports"]
    print(f"  cross-module imports total : {len(xm)}")
    print(f"  imports bypassing /public  : {len(bypass)}  (CANDIDATE violations — verify by reading)")
    for e in bypass[:15]:
        frm = e["from_module"] or "?"
        print(f"    {frm} -> {e['to_module']}   {e['import_path']}")
    if len(bypass) > 15:
        print(f"    ... and {len(bypass) - 15} more")
    print()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deterministic structural census of a codebase.")
    ap.add_argument("root", help="source root to analyze (e.g. src)")
    ap.add_argument("--modules-subdir", default="modules")
    ap.add_argument("--canonical-dirs", default=",".join(DEFAULT_CANONICAL_DIRS))
    ap.add_argument("--suffixes", default=",".join(DEFAULT_SUFFIXES))
    ap.add_argument("--json", dest="json_path", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: source root not found: {root}", file=sys.stderr)
        return 1

    canonical_dirs = [d.strip() for d in args.canonical_dirs.split(",") if d.strip()]
    suffixes = [s.strip() for s in args.suffixes.split(",") if s.strip()]

    c = census(root, args.modules_subdir, canonical_dirs, suffixes)

    if args.json_path:
        Path(args.json_path).write_text(json.dumps(c, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"(wrote JSON census to {args.json_path})")
    if not args.quiet:
        print_summary(c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
