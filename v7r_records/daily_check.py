"""日次チェック: 台帳の整合性とテストの結果だけを確認する（予測や結果は書き換えない）。"""
import subprocess, sys, os
from ledger import Ledger, LedgerError, compare

here = os.path.dirname(os.path.abspath(__file__))
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "records.jsonl")

ok = True
try:
    n = Ledger(path).verify()
    print(f"台帳: 連鎖OK（{n}行）")
except LedgerError as e:
    ok = False
    print(f"台帳: 異常 -> {e}")

t = subprocess.run([sys.executable, "-m", "unittest", "test_ledger"], cwd=here,
                   capture_output=True, text=True)
print("テスト: " + ("すべて通過" if t.returncode == 0 else "失敗あり"))
if t.returncode != 0:
    ok = False
    print(t.stderr[-800:])

if os.path.getsize(path) > 0:
    print("比較(見立て・V7R・ベースライン):")
    for k, v in compare(path).items():
        print(f"  {k}: {v}")
print("結果: " + ("正常" if ok else "要確認"))
sys.exit(0 if ok else 1)
