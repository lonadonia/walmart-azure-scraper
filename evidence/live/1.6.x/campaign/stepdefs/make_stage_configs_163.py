"""Stage configurations on release 1.6.3 (L8 final demonstration, L7 census): the frozen 1.6.3 edition's
config/collector.yaml, byte for byte, except its four relative file names made absolute (the copy lives outside the
edition's folder). No stage has follow-up seeds (the 275 queue items are decided, W3), so the edition's own
"seeds: []" line stays. Nothing else changes.

usage: python -I make_stage_configs_163.py   (writes C:/w9/evidence/live160/configs/collector.<stage>.yaml and
stage_configs_163.json)
"""

import hashlib
import json
from pathlib import Path

ED = Path("C:/w9/live/ed/walmart-oxylabs-1.6.3/config")
OUT = Path("C:/w9/evidence/live160/configs")
STAGES = ("l8_163", "census_163")
SEEDS_LINE = "      seeds: []                    # items an earlier report named, read first: {kind, item_id, url, listing_id}\n"

base = (ED / "collector.yaml").read_bytes().decode("utf-8")
for name in ("settings.yaml", "stores.yaml", "Walmart_Category_URLs.csv", "walmart_private_label_brands.yaml"):
    assert base.count(f": {name}") == 1, name
assert base.count(SEEDS_LINE) == 1
summary = {}
for stage in STAGES:
    p = OUT / f"collector.{stage}.yaml"
    if p.exists():
        raise SystemExit(f"{p} exists")
    text_cfg = base
    for name in ("settings.yaml", "stores.yaml", "Walmart_Category_URLs.csv", "walmart_private_label_brands.yaml"):
        text_cfg = text_cfg.replace(f": {name}", f": {(ED / name).as_posix()}")
    p.write_bytes(text_cfg.encode("utf-8"))
    summary[stage] = {
        "config": str(p),
        "sha256": hashlib.sha256(text_cfg.encode("utf-8")).hexdigest(),
        "edition_config_sha256": hashlib.sha256(base.encode("utf-8")).hexdigest(),
        "seeds": 0,
    }
(OUT / "stage_configs_163.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=1))
