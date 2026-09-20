# PyInstaller spec. Build from the repo root:  uv run pyinstaller packaging/app.spec --noconfirm
# One-dir mode: faster start than one-file, and .env sits next to the exe (see config.resource_path).
from PyInstaller.utils.hooks import collect_all

datas = [
    ("src/flowchartmaker/web/templates", "flowchartmaker/web/templates"),
    ("src/flowchartmaker/web/static", "flowchartmaker/web/static"),
    ("packaging/.env.example", "."),
]
binaries = []
hiddenimports = []
# Dynamic/plugin-style imports static analysis misses; extend after trial builds.
for pkg in ("langchain_core", "langchain_ollama", "langchain_google_genai", "google.genai", "pydantic"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ["src/flowchartmaker/main.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="flowchartmaker", console=True)
coll = COLLECT(exe, a.binaries, a.datas, name="flowchartmaker")
