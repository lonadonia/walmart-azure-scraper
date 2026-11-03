P=/c/w7/wt/headless/walmart-azure-headless/.venv/Scripts/python.exe
OUT="$1"
for st in S4 S5a S6 S7; do
  echo "=========== $st"
  $P -I -X utf8 /c/w7/tools/agreement_152.py "C:/w7/ev152/${2:-replay_a1}/runs/$st/exports" 'C:\w7\r152\pgdata' walmart_live150 "$OUT/$st.json" 'C:\w7\r152\data' 2>&1 | cut -c1-430
done
echo "=========== B3"
$P -I -X utf8 /c/w7/tools/agreement_152.py "C:/w7/ev152/${3:-reprocessing_b3_1_5_2}/export_replay_1_5_2" 'C:\w7\reproc\pgdata' walmart_reproc152_a4 "$OUT/B3.json" 'C:\w7\reproc\data' 2>&1 | cut -c1-430
