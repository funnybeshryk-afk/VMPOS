"""Bir martalik: UI chaqiruvlaridagi o'zbekcha matnlarni tr(...) ga o'raydi.

Kalit — o'zbekcha asl matn. f-satrlar "{0}" shablonli tr("...").format(...) ga
aylantiriladi. Ishga tushirish: python tools/i18n_codemod.py app [--dry]
"""
import ast, os, re, sys

UI_CALLS = {
 "setText","setWindowTitle","setPlaceholderText","setToolTip","setHorizontalHeaderLabels",
 "setVerticalHeaderLabels","QLabel","addRow","SecondaryButton","PrimaryButton","DangerButton",
 "SuccessButton","QPushButton","QCheckBox","QRadioButton","QGroupBox","SummaryCard","badge_cell",
 "set_badge_variant","StatusBadge","QTableWidgetItem","make_chip","_make_alt_pay_button",
 "_make_view_toggle_button","AmountField","_tab","build_footer","addButton","setDetailedText",
 "setInformativeText","QProgressDialog","getOpenFileName","getSaveFileName","getExistingDirectory",
 "addItem","insertItem","set_value","setStatusTip","setTitle","setSuffix","setPrefix","setLabelText",
 "addTab","setSpecialValueText","setItemText","setPlainText","setCancelButtonText",
}
QMSG = {"information","warning","critical","question","about"}
LOGGERS = {"logger","log","logging","LOG","_log"}
EXC_NAMES = re.compile(r"(Error|Exception|Cancelled)$")

def fname(call):
    f = call.func
    if isinstance(f, ast.Name): return f.id, None
    if isinstance(f, ast.Attribute):
        r = f.value.id if isinstance(f.value, ast.Name) else None
        return f.attr, r
    return None, None

def is_ui_call(call, in_raise):
    n, recv = fname(call)
    if n is None: return False
    if n in UI_CALLS: return True
    if n in QMSG and recv == "QMessageBox": return True
    if in_raise and EXC_NAMES.search(n): return True
    return False

TEXT = re.compile(r"[A-Za-z']{2,}")

def text_ok(s):
    return bool(TEXT.search(s)) and not re.fullmatch(r"[a-z_0-9./:\-#%*]+", s)

def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'

def template(js):
    parts, args = [], []
    for v in js.values:
        if isinstance(v, ast.Constant):
            parts.append(v.value.replace("{", "{{").replace("}", "}}"))
        else:
            spec = ""
            if v.format_spec is not None:
                if not all(isinstance(x, ast.Constant) for x in v.format_spec.values): return None
                spec = ":" + "".join(x.value for x in v.format_spec.values)
            conv = {-1: "", 115: "!s", 114: "!r", 97: "!a"}[v.conversion]
            parts.append("{" + str(len(args)) + conv + spec + "}")
            args.append(ast.unparse(v.value))
    return "".join(parts), args

def collect(call, in_raise, out, skipped):
    def visit(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if text_ok(node.value): out.append((node, None))
        elif isinstance(node, ast.JoinedStr):
            t = template(node)
            if t is None: skipped.append(node); return
            if text_ok(re.sub(r"\{\d[^}]*\}", "", t[0])): out.append((node, t))
        elif isinstance(node, (ast.List, ast.Tuple)):
            for e in node.elts: visit(e)
        elif isinstance(node, ast.IfExp):
            visit(node.body); visit(node.orelse)
        elif isinstance(node, ast.BoolOp):
            for e in node.values: visit(e)
    for a in call.args: visit(a)
    for k in call.keywords:
        if k.arg in (None,) : continue
        if k.arg in ("text","title","label","placeholder","tooltip","caption","message","name"): visit(k.value)

def process(path, dry):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    parents = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n): parents[c] = n
    found, skipped, seen = [], [], set()
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call): continue
        in_raise = isinstance(parents.get(n), ast.Raise)
        if not is_ui_call(n, in_raise): continue
        tmp = []
        collect(n, in_raise, tmp, skipped)
        for node, t in tmp:
            if id(node) not in seen: seen.add(id(node)); found.append((node, t))
    if not found: return 0, skipped
    lines = src.split("\n")
    offs = [0]
    for l in lines: offs.append(offs[-1] + len(l.encode("utf-8")) + 1)
    b = src.encode("utf-8")
    def pos(l, c): return offs[l - 1] + c
    edits = []
    for node, t in found:
        s, e = pos(node.lineno, node.col_offset), pos(node.end_lineno, node.end_col_offset)
        if t is None: new = "tr(" + b[s:e].decode("utf-8") + ")"
        elif t[1]: new = "tr(" + q(t[0]) + ").format(" + ", ".join(t[1]) + ")"
        else: new = "tr(" + q(t[0].replace("{{", "{").replace("}}", "}")) + ")"
        edits.append((s, e, new))
    edits.sort(reverse=True)
    for s, e, new in edits: b = b[:s] + new.encode("utf-8") + b[e:]
    out = b.decode("utf-8")
    if "from app.i18n import tr" not in out:
        t2 = ast.parse(out)
        last = max((n.end_lineno for n in t2.body if isinstance(n, (ast.Import, ast.ImportFrom))), default=0)
        ol = out.split("\n"); ol.insert(last, "from app.i18n import tr"); out = "\n".join(ol)
    if not dry: open(path, "w", encoding="utf-8").write(out)
    return len(edits), skipped

if __name__ == "__main__":
    root, dry = sys.argv[1], "--dry" in sys.argv
    total = 0
    for d, _, fs in os.walk(root):
        for f in sorted(fs):
            if f.endswith(".py") and f not in ("i18n.py",):
                n, sk = process(os.path.join(d, f), dry)
                total += n
                if n or sk: print(f"{n:4d} {os.path.join(d, f)}" + (f"  SKIPPED f-str: {len(sk)}" if sk else ""))
    print("total", total)
