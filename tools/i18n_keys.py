"""Koddagi barcha tr("...") kalitlarini chiqaradi (tarjima to'liqligini
tekshirish va ru.py ni to'ldirish uchun)."""
import ast, os

def keys(root="app"):
    out = {}
    for d, _, fs in os.walk(root):
        for f in sorted(fs):
            if not f.endswith(".py"): continue
            p = os.path.join(d, f)
            for n in ast.walk(ast.parse(open(p, encoding="utf-8").read())):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "tr" \
                   and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
                    out.setdefault(n.args[0].value, p)
    return out

if __name__ == "__main__":
    import json, sys
    k = keys()
    print(len(k), file=sys.stderr)
    for s, p in k.items(): print(json.dumps([s, p.replace("app/", "")], ensure_ascii=False))
