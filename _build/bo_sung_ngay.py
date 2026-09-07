# -*- coding: utf-8 -*-
"""
BO SUNG alert cua MOT KICH BAN cho mot ngay bi thieu vao score_clean.

Dung khi mot kich ban chay lai/lay bu data cho mot ngay ma ky truoc bi hut.
File thô vao co dang:
    request_id, ma_khach_hang, viettel_bank_code, thoi_gian_gd, ten_khach_hang

Script dung lai du 21 cot theo DUNG khuon cua score_clean, lay Level/Score_KB
tu chinh cac dong cu cua kich ban do (khong doan, khong viet cung).

Chay:
    py -3.10 _build/bo_sung_ngay.py <file_tho.csv> --kb "<ten kich ban>"
    py -3.10 _build/bo_sung_ngay.py <file_tho.csv> --kb "Blacklist  B" --that

Mac dinh chi CHAY THU va in ra doi chieu; them --that moi ghi de file.
"""
import argparse
import io
import os
import re
import shutil
import sys
from datetime import datetime

import pandas as pd

# Console Windows mac dinh cp1252, in ten kich ban co dau la no nem
# UnicodeEncodeError. Bọc lai stdout thay vi bo dau di.
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
CSV = os.path.join(PARENT, "data", "score_clean_2608_0109.csv")

ap = argparse.ArgumentParser()
ap.add_argument("tho", help="File CSV tho cua kich ban")
ap.add_argument("--csv", default=CSV, help="File score_clean can bo sung vao")
ap.add_argument("--kb", required=True,
                help="Chuoi nhan dang kich ban trong usecase_clean")
ap.add_argument("--that", action="store_true",
                help="Ghi that. Khong co co nay thi chi chay thu.")
a = ap.parse_args()

for p in (a.tho, a.csv):
    if not os.path.exists(p):
        sys.exit("THIEU FILE: " + p)

print("=" * 72)
print("BO SUNG ALERT MOT NGAY")
print("=" * 72)

d = pd.read_csv(a.csv, encoding="utf-8-sig", dtype=str)
n = pd.read_csv(a.tho, encoding="utf-8-sig", dtype=str)
print("score_clean : %s dong" % format(len(d), ","))
print("File tho    : %s dong" % format(len(n), ","))

# ── Lay khuon tu chinh cac dong CU cua kich ban nay ──────────────────────
mau = d[d.usecase_clean.str.contains(a.kb, na=False, regex=False)]
if not len(mau):
    sys.exit("Khong tim thay kich ban khop '%s' trong score_clean" % a.kb)
m0 = mau.iloc[0]
print("Kich ban    : %s" % m0.usecase_clean)
print("              %s dong san co, Level=%s Score_KB=%s"
      % (format(len(mau), ","), m0.risk_level_kb, m0.Score_KB))

# ── Ngay cua file tho ────────────────────────────────────────────────────
ngay = sorted(n.thoi_gian_gd.astype(str).str[:10].unique())
if len(ngay) != 1:
    print("!! File chua %d ngay: %s" % (len(ngay), ngay))
g = ngay[0]
print("Ngay bo sung: %s" % g)

da_co = mau[mau.ngay_alert.astype(str).str[:10] == g]
if len(da_co):
    print("!! Kich ban nay DA CO %d dong ngay %s -> dung, tranh nhan doi"
          % (len(da_co), g))
    sys.exit(1)

# ── Dung du 21 cot theo dung khuon ───────────────────────────────────────
# ma khach hang bo hau to _backupDDMM: hau to la ngay CHAY LAI rule, khong
# phai mot khach khac. De nguyen thi dashboard dem thanh nguoi moi.
RX_HAU = re.compile(r"_backup\d{4}$")
ma = n.ma_khach_hang.astype(str).str.replace(RX_HAU, "", regex=True)
# van uu tien request_id neu co - do la ma goc
ma = n.request_id.astype(str).where(n.request_id.notna() & (n.request_id != ""), ma)

tg = pd.to_datetime(n.thoi_gian_gd, format="mixed", utc=True).dt.tz_convert(
    "Asia/Ho_Chi_Minh").dt.strftime("%Y-%m-%d %H:%M:%S")
pdate = g.replace("-", "")

ra = pd.DataFrame({
    "AlertID": pdate + "_" + ma,
    "CATEGORY": m0.CATEGORY,
    "created_date": tg,
    "requestor": m0.requestor,
    "updated_date": tg,
    "reject_reason": float("nan"),
    "usecase_name": m0.usecase_name,
    "status": m0.status,
    "object_key": m0.object_key,
    "object_value": ma,
    "last_risk_score": m0.last_risk_score,
    "Level": m0.Level,
    "Score_KB": m0.Score_KB,
    "viettel_bank_code": n.viettel_bank_code,
    "PARTITION_DATE": pdate,
    "ngay_alert": g,
    "gio_alert": tg,
    "usecase_clean": m0.usecase_clean,
    "request_id": ma,
    "risk_level_kb": m0.risk_level_kb,
    # Cot ten_khach_hang KHONG dua vao: du lieu dinh danh, chu du an chot bo.
    "chi_tiet_alert": "{}",
})[list(d.columns)]

# ── Kiem tra truoc khi ghi ───────────────────────────────────────────────
print("-" * 72)
loi = []
if list(ra.columns) != list(d.columns):
    loi.append("Thu tu cot khong khop")
xau = ra.object_value.astype(str)
if xau.str.contains(r"_backup", regex=True).any():
    loi.append("Con hau to _backup trong object_value")
if not xau.str.fullmatch(r"[0-9a-f]{20}").all():
    n_la = (~xau.str.fullmatch(r"[0-9a-f]{20}")).sum()
    loi.append("%d ma khach hang khong phai 20 ky tu hex" % n_la)
# khong duoc con ten that o bat ky o nao
RX_TEN = re.compile(r"^[A-ZÀ-Ỹ][a-zà-ỹ]+(\s+[A-ZÀ-Ỹ][a-zà-ỹ]*){1,5}$")
for c in ra.columns:
    if ra[c].astype(str).str.match(RX_TEN).any():
        loi.append("Cot %s con ten nguoi that" % c)
RX_SDT = re.compile(r"(?<![0-9a-f.])(0[35789]\d{8})(?![0-9a-f.])")
for c in ra.columns:
    if ra[c].astype(str).str.contains(RX_SDT, regex=True, na=False).any():
        loi.append("Cot %s con so dien thoai" % c)

print("Dung duoc   : %d dong x %d cot" % (len(ra), len(ra.columns)))
print("object_value: %s ..." % ", ".join(ra.object_value.head(3)))
print("AlertID     : %s ..." % ra.AlertID.iloc[0])
print("gio_alert   : %s -> %s" % (ra.gio_alert.min(), ra.gio_alert.max()))
print("bank_code   : %s" % ra.viettel_bank_code.value_counts().to_dict())
print("-" * 72)
if loi:
    print("KHONG DAT:")
    for x in loi:
        print("   - " + x)
    sys.exit(1)
print("Moi kiem tra DAT (dung cot, khong hau to, khong ten, khong SDT)")

if not a.that:
    print()
    print("Day moi la CHAY THU. Them --that de ghi that.")
    sys.exit(0)

# ── Ghi: sao luu truoc, roi noi vao va sap lai theo thoi gian ────────────
bak = a.csv.replace(".csv", "_truoc_bosung_%s.csv"
                    % datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy2(a.csv, bak)
print("Sao luu     : %s" % os.path.basename(bak))

moi = pd.concat([d, ra], ignore_index=True)
moi = moi.sort_values(["ngay_alert", "gio_alert"], kind="stable")
moi.to_csv(a.csv, index=False, encoding="utf-8-sig")
print("Ghi         : %s dong (%s + %s)"
      % (format(len(moi), ","), format(len(d), ","), format(len(ra), ",")))
