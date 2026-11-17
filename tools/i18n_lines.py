"""Bir martalik yordamchi: ko'rsatilgan qatorlardagi matnlarni tr() ga o'raydi.
python tools/i18n_lines.py file:line[,line...] ..."""
import ast, re, sys
sys.path.insert(0, "tools")
from i18n_codemod import template, text_ok, q

def run(path, lines):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    parents = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n): parents[c] = n
    targets = []
    for n in ast.walk(tree):
        if not isinstance(n, (ast.Constant, ast.JoinedStr)): continue
        if isinstance(n, ast.Constant) and not isinstance(n.value, str): continue
        if isinstance(parents.get(n), (ast.JoinedStr, ast.FormattedValue)): continue
        if n.lineno not in lines: continue
        if isinstance(n, ast.Constant):
            if text_ok(n.value): targets.append((n, None))
        else:
            t = template(n)
            if t and text_ok(re.sub(r"\{\d[^}]*\}", "", t[0])): targets.append((n, t))
    offs = [0]
    for l in src.split("\n"): offs.append(offs[-1] + len(l.encode()) + 1)
    b = src.encode()
    edits = []
    for n, t in targets:
        s, e = offs[n.lineno - 1] + n.col_offset, offs[n.end_lineno - 1] + n.end_col_offset
        if t is None: new = "tr(" + b[s:e].decode() + ")"
        elif t[1]: new = "tr(" + q(t[0]) + ").format(" + ", ".join(t[1]) + ")"
        else: new = "tr(" + q(t[0].replace("{{", "{").replace("}}", "}")) + ")"
        edits.append((s, e, new))
    for s, e, new in sorted(edits, reverse=True): b = b[:s] + new.encode() + b[e:]
    out = b.decode()
    if "from app.i18n import tr" not in out:
        t2 = ast.parse(out)
        last = max((n.end_lineno for n in t2.body if isinstance(n, (ast.Import, ast.ImportFrom))), default=0)
        ol = out.split("\n"); ol.insert(last, "from app.i18n import tr"); out = "\n".join(ol)
    open(path, "w", encoding="utf-8").write(out)
    return len(edits)

for arg in sys.argv[1:]:
    f, ls = arg.split(":")
    print(run(f, {int(x) for x in ls.split(",")}), f)
