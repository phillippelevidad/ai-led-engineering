# Counting Recipes: Grounding Frequency Analysis

Frequency analysis is only as trustworthy as its counts. This skill's credibility collapses the moment it
reports "Variant A appears in ~30 files" from memory and a reviewer finds it appears in 6. **Count from the
code.** This file lists how — what is mechanically countable (use a tool, the number is exact) versus what
needs semantic reading (read the files, report an honest estimate).

## Mechanically countable — use a tool, report exact numbers

### Structural census (preferred first move)
`scripts/inventory.py` gives per-module directory shape, file-suffix histograms, naming conformance, and
cross-module import edges in one pass. Run it before anything else:
```bash
python scripts/inventory.py src --modules-subdir modules --json /tmp/census.json
```

### File-naming / suffix conventions
```bash
# How many of each suffix exist (DTO, mapper, repository, etc.)
rg --files src/modules | rg -o '\.[a-z-]+\.ts$' | sort | uniq -c | sort -rn

# Modules that have a /public dir vs. those that don't
for d in src/modules/*/; do
  [ -d "$d/public" ] && echo "has-public: $d" || echo "NO-public:  $d"
done
```

### Decorator / framework usage (NestJS example)
```bash
rg -c '@Injectable\(\)' src/modules        # services per file
rg -l 'extends Repository<'  src/modules    # ORM-native repository usage
rg -l 'dataSource\.query'    src/modules    # raw-query repository usage
rg -l 'class-validator'      src/modules    # validation approach A
rg -l 'zod'                  src/modules    # validation approach B
```

### Import / boundary edges
```bash
# Cross-module imports that bypass /public (candidate boundary violations)
rg -n "from '.*modules/([a-z-]+)/(?!public)" src/modules

# Default vs named exports
rg -c 'export default' src/modules
```

### Test layout
```bash
# Colocated tests vs. a central __tests__/ tree
rg --files src/modules | rg -c '\.(test|spec)\.ts$'
fd -t d '__tests__' src                      # presence of centralized test dirs
```

## Needs semantic reading — read files, report an honest estimate

Some patterns cannot be regex-counted because the distinction is in *meaning*, not syntax:

- **Return-type semantics** — does a repository return a domain entity or an ORM row? Both may use
  `dataSource.query`. Read a sample.
- **Mapper direction / completeness** — is mapping centralized in a `*.mapper.ts`, inline in the
  repository, or absent? Partly countable (file presence), partly semantic (inline mapping).
- **Error-handling shape** — whether code throws a domain error, a framework `HttpException`, or a bare
  `Error`. Countable as a first pass (`rg 'throw new'`), but classifying *intent* needs reading.
- **Validation placement** — DTO-level vs. use-case-level vs. none. Read to confirm.
- **Dependency-boundary intent** — an import may be technically cross-module but legitimately routed through
  an adapter. Confirm flagged violations by reading before reporting them.

When you read rather than count, **say so**: report "estimated from reading 8 of ~40 repository files"
rather than presenting an exact-looking number you did not actually compute. False precision is worse than
an honest estimate, because it gets quoted in the ADR and then propagated as fact.

## AST-based counting (when regex is not enough)

For structural patterns where regex produces too many false positives (e.g. "services that inject another
module's concrete class rather than its interface"), a TypeScript AST pass via `ts-morph` is more reliable.
This is heavier; reach for it only when the distinction is load-bearing for the decision and regex cannot
make it cleanly. A minimal sketch:

```typescript
import { Project } from "ts-morph";
const project = new Project({ tsConfigFilePath: "tsconfig.json" });
for (const sf of project.getSourceFiles("src/modules/**/*.ts")) {
  for (const cls of sf.getClasses()) {
    for (const ctor of cls.getConstructors()) {
      for (const p of ctor.getParameters()) {
        // inspect p.getType().getText() to classify the dependency
      }
    }
  }
}
```

Reserve AST work for the genuinely-ambiguous case; for most concepts the structural census plus targeted
ripgrep is sufficient and far cheaper.
