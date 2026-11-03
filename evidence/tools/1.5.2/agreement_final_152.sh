P=/c/w7/wt/headless/walmart-azure-headless/.venv/Scripts/python.exe
OUT="$1"
mkdir -p "$OUT"
for st in S1 S2 S3 S4 S5a S5b_serial S5b_parallel S6 S7; do
  [ -f "/c/w7/ev152/final_a1/runs/$st/exports/products.json" ] || { echo "=========== $st: no exports"; continue; }
  echo "=========== $st"
  $P -I -X utf8 /c/w7/tools/agreement_152.py "C:/w7/ev152/final_a1/runs/$st/exports" 'C:\w7\r152c\pgdata' walmart_live150 "$OUT/$st.json" 'C:\w7\r152c\data' 2>&1 | cut -c1-200 | tail -12
done
echo "=========== B3"
$P -I -X utf8 /c/w7/tools/agreement_152.py "C:/w7/ev152/final_b3/export_replay_1_5_2" 'C:\w7\reproc\pgdata' walmart_reproc152_a5 "$OUT/B3.json" 'C:\w7\reproc\data' 2>&1 | cut -c1-200 | tail -12
