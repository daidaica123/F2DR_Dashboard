# -*- coding: utf-8 -*-
"""
AN DANH so dien thoai trong file alert truoc khi day len repo PUBLIC.

Trong object_value co hai dang ma khach hang:
  - bam 20 ky tu hex  -> von da an danh, GIU NGUYEN
  - so dien thoai 9-10 so -> DINH DANH DUOC NGUOI THAT, phai bam lai

Cach bam: sha256(so_dien_thoai + MUOI) roi lay 20 ky tu dau -> cung dinh dang
voi ma bam san co, nen dashboard khong can sua gi.

MUOI (salt) doc tu bien moi truong F2DR_SALT. Khong dat thi sinh ngau nhien
va in ra man hinh -- luu lai neu sau nay can tra nguoc.

Chay:
    py -3.10 _build/an_danh_sdt.py data/score_clean_2608_0109.csv
    py -3.10 _build/an_danh_sdt.py <vao.csv> --out <ra.csv>
"""
import argparse
import hashlib
import os
import re
import secrets
import sys

import pandas as pd

RX_SDT = re.compile(r"^0?\d{9,10}$")
# So dien thoai di dong VN nam LONG trong chuoi (JSON, text...).
# Chan truoc/sau bang [0-9a-f.] chu khong chi [0-9.]: ma bam hex 20 ky tu
# nhu "0001fxxxxxxxxxxd8ff1" co the chua chuoi trong giong so dien thoai
# ("xxxxxxxxxx") -- do la trung ngau nhien, khong phai so that.
RX_TRONG_JSON = re.compile(r"(?<![0-9a-f.])(0[35789]\d{8})(?![0-9a-f.])")

ap = argparse.ArgumentParser()
ap.add_argument("csv", help="File alert can an danh")
ap.add_argument("--out", help="File ra (mac dinh: ghi de chinh file vao)")
ap.add_argument("--salt", default=os.environ.get("F2DR_SALT"),
                help="Chuoi muoi. Khong co thi sinh ngau nhien.")
a = ap.parse_args()

if not os.path.exists(a.csv):
    sys.exit("Khong thay file: " + a.csv)

salt = a.salt
if not salt:
    salt = secrets.token_hex(16)
    print("!! Chua dat F2DR_SALT -> sinh ngau nhien:")
    print("   %s" % salt)
    print("   Luu lai neu sau nay can bam lai cho khop.")

d = pd.read_csv(a.csv, encoding="utf-8-sig", dtype={"object_value": str})
ov = d.object_value.astype(str)
la_sdt = ov.str.fullmatch(RX_SDT)
n_sdt = int(la_sdt.sum())
n_ma = int(ov[la_sdt].nunique())

if not n_sdt:
    print("Khong co so dien thoai nao -> khong sua gi.")
    sys.exit(0)


def bam(s):
    return hashlib.sha256((salt + s).encode()).hexdigest()[:20]


d.loc[la_sdt, "object_value"] = ov[la_sdt].map(bam)

# Cot chi_tiet_alert la JSON nghiep vu, ben trong con so dien thoai cua
# BEN THU BA ("doi_tac", "ben_nhan"...) -- nhung so nay chua bao gio la ma KH
# nen phai quet RIENG, khong the chi tra theo danh sach ma KH.
n_json = 0
if "chi_tiet_alert" in d.columns:
    def thay(s):
        global n_json
        s = str(s)
        m = RX_TRONG_JSON.findall(s)
        if not m:
            return s
        n_json += len(set(m))
        return RX_TRONG_JSON.sub(lambda x: bam(x.group(1)), s)

    d["chi_tiet_alert"] = d.chi_tiet_alert.map(thay)

out = a.out or a.csv
d.to_csv(out, index=False, encoding="utf-8-sig")

print("=" * 60)
print("Ma khach hang : %s dong (%s so rieng biet)"
      % (format(n_sdt, ","), format(n_ma, ",")))
print("Trong JSON    : %s lan xuat hien so ben thu ba" % format(n_json, ","))

# Kiem lai: quet toan bo moi o trong file, khong sot cot nao
con = 0
for c in d.columns:
    con += int(d[c].astype(str).str.contains(RX_TRONG_JSON, regex=True,
                                             na=False).sum())
print("-" * 60)
print("Kiem lai toan file, con so dien thoai: %d  (phai bang 0)" % con)
if con:
    print("!! VAN CON -- KHONG duoc day len repo public")
    sys.exit(1)
print("Ghi: %s" % out)
