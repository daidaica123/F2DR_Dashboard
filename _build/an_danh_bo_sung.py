# -*- coding: utf-8 -*-
"""
AN DANH BO SUNG — va lo hong cua an_danh_sdt.py.

Ban an_danh_sdt.py chi bat so dien thoai dang 0[35789]xxxxxxxx nam trong
chi_tiet_alert. No BO SOT:

  tb_duoc_nap    1.569 so dien thoai dang 84xxxxxxxxx  (dinh danh nguoi that)
  cccd             321 so can cuoc cong dan 12 so
  so_gttt          137 so giay to tuy than
  merchant_code     40 ma so thue doanh nghiep

Script nay quet theo TEN KHOA trong JSON chu khong theo dang so, nen khong
phu thuoc vao viec so do trong nhu the nao. An toan hon nhieu so voi regex.

GIU NGUYEN moi ma bam 20 ky tu da co (object_value, nguoi_gui, kh_duoc_nap...)
— bam lai se lam doi ma, dashboard va ghi chep dieu tra cu mat lien ket.

Chay:
    $env:F2DR_SALT = "chuoi-bi-mat-cua-ban"
    py -3.13 _build/an_danh_bo_sung.py data/score_clean_2608_0109.csv
"""
import argparse
import hashlib
import json
import os
import re
import secrets
import sys

import pandas as pd

# ── Khoa trong chi_tiet_alert can bam. Phan theo muc do nhay cam. ──
# Gia tri da la ma bam 20 ky tu hex hoac chuoi "enc:..." thi bo qua, giu nguyen.
KHOA_BAM = {
    # ── HO TEN va NGAY SINH ──
    # Bo sung 05/09/2026 sau danh gia doc lap. Ban dau chi quet theo DANG SO
    # nen bat duoc so dien thoai va CCCD, nhung BO SOT hoan toan ten nguoi —
    # thu hien nhien nhat. 3.530 dong (22,7%) dang co ten that trong repo
    # PUBLIC, ke ca ten nhan vien Viettel.
    "ten_khach_hang":     "ho ten khach hang",
    "ten_kh":             "ho ten khach hang",
    "ho_ten":             "ho ten",
    "ten_nhan_vien_kenh": "ho ten nhan vien",
    "ten_nguoi_duoc_gd":  "ho ten nguoi nhan",
    "ngay_sinh":          "ngay sinh",
    "merchant_ten":       "ten doanh nghiep",
    "noi_dung_gd":        "noi dung giao dich",
    "kh_msisdn":          "so thue bao khach",

    # ── dinh danh truc tiep mot con nguoi ──
    "tb_duoc_nap":   "so dien thoai",
    "cccd":          "can cuoc cong dan",
    "so_gttt":       "giay to tuy than",
    "sdt_kenh":      "so dien thoai kenh",
    "ngay_cap_cccd": "ngay cap can cuoc",

    # ── dinh danh tai khoan / to chuc ──
    "tk_thu_huong":  "so tai khoan thu huong",
    "dau_moi":       "dau moi nhan tien",
    "doi_tac_stk":   "so tai khoan doi tac",
    "doi_tac":       "doi tac",
    "merchant_code": "ma so thue merchant",
    "ma_kenh":       "ma kenh",
    "nguoi_gui":     "nguoi gui",
    "kh_duoc_nap":   "khach duoc nap",
    "doi_tac_sdt":   "so dien thoai doi tac",
    "ds_dich_nhan":  "danh sach dich nhan",
}

# KHONG bam: day la ten SAN PHAM / TRANG THAI, khong dinh danh ai ca.
# Liet ke ra day de lan sau khong ai bam nham roi mat y nghia nghiep vu.
#   process_name  "Rut tien", "Dai ly thanh toan - Nap tien"
#   trang_thai    "Chua cham", "Da cham"
#   ten_goi       "Nang cao", "Trai nghiem"
#   chi_tiet      "cap truoc vay 16 ngay"  (mo ta dau hieu)
#   san_pham      "FASTMONEY", "PAYDAY"
#   loai_*        cac ma phan loai

# Da an danh roi -> khong dung toi
RX_DA_BAM = re.compile(r"^[0-9a-f]{20}$")
RX_DA_MA_HOA = re.compile(r"^enc:")

# ── Regex kiem lai toan file sau khi xu ly ──
RX_SDT_VN = re.compile(r"(?<![0-9a-f])(?:0[35789]\d{8}|84[35789]\d{8})(?![0-9a-f])")
RX_CCCD = re.compile(r"(?<![0-9a-f])(?:0[0-9]{2}[0-9]{9})(?![0-9a-f])")

ap = argparse.ArgumentParser()
ap.add_argument("csv", help="File alert can an danh bo sung")
ap.add_argument("--out", help="File ra (mac dinh: ghi de chinh file vao)")
ap.add_argument("--salt", default=os.environ.get("F2DR_SALT"),
                help="Chuoi muoi. Khong co thi sinh ngau nhien va in ra.")
ap.add_argument("--kho", action="store_true",
                help="Chi bao cao, khong ghi file")
a = ap.parse_args()

if not os.path.exists(a.csv):
    sys.exit("Khong thay file: " + a.csv)

salt = a.salt
if not salt:
    salt = secrets.token_hex(16)
    print("!! Chua dat F2DR_SALT -> sinh ngau nhien:")
    print("   %s" % salt)
    print("   LUU LAI neu sau nay can tra nguoc.")
    print()


def bam(s):
    """Cung dinh dang voi ma bam san co: 20 ky tu hex."""
    return hashlib.sha256((salt + str(s)).encode()).hexdigest()[:20]


print("=" * 70)
print("AN DANH BO SUNG")
print("=" * 70)
print("File:", os.path.basename(a.csv))

d = pd.read_csv(a.csv, encoding="utf-8-sig", dtype={"object_value": str})
if "chi_tiet_alert" not in d.columns:
    sys.exit("File khong co cot chi_tiet_alert -> khong co gi de lam.")

dem = {k: 0 for k in KHOA_BAM}          # so lan thay
rieng = {k: set() for k in KHOA_BAM}    # so gia tri rieng biet
bo_qua = {k: 0 for k in KHOA_BAM}       # da an danh san
loi_json = 0


def xu_ly(s):
    global loi_json
    if not isinstance(s, str) or not s.strip():
        return s
    try:
        o = json.loads(s)
    except Exception:
        loi_json += 1
        return s
    if not isinstance(o, dict):
        return s

    doi = False
    for k in list(o):
        if k not in KHOA_BAM:
            continue
        v = o[k]
        if v is None or v == "":
            continue
        vs = str(v)
        # da an danh roi -> giu nguyen, khong bam chong
        if RX_DA_BAM.match(vs) or RX_DA_MA_HOA.match(vs):
            bo_qua[k] += 1
            continue
        o[k] = bam(vs)
        dem[k] += 1
        rieng[k].add(vs)
        doi = True

    return json.dumps(o, ensure_ascii=False) if doi else s


d["chi_tiet_alert"] = d.chi_tiet_alert.map(xu_ly)

print()
print("%-18s %-26s %8s %8s %9s" % ("KHOA", "LA GI", "DA BAM", "RIENG", "BO QUA"))
print("-" * 70)
tong = 0
for k, mo_ta in KHOA_BAM.items():
    if dem[k] or bo_qua[k]:
        print("%-18s %-26s %8s %8s %9s"
              % (k, mo_ta, format(dem[k], ","), format(len(rieng[k]), ","),
                 format(bo_qua[k], ",")))
        tong += dem[k]
print("-" * 70)
print("%-45s %8s" % ("TONG DA BAM", format(tong, ",")))
if loi_json:
    print("!! %d o chi_tiet_alert khong doc duoc JSON -> giu nguyen" % loi_json)

# ── Kiem lai TOAN BO file, khong sot cot nao ──
print()
print("=" * 70)
print("KIEM LAI TOAN FILE")
print("=" * 70)
def go_da_ma_hoa(s):
    """Bo cac gia tri 'enc:...' truoc khi quet.

    Chuoi base64 trong 'enc:' co the tinh co chua 12 chu so lien tiep trong
    giong CCCD — do la trung ngau nhien, khong phai so that. Khong go ra thi
    kiem lai bao dong gia mai khong het.
    """
    return re.sub(r'"enc:[^"]*"', '""', str(s))


con_sdt = con_cccd = 0
for c in d.columns:
    ss = d[c].astype(str).map(go_da_ma_hoa)
    con_sdt += int(ss.str.contains(RX_SDT_VN, regex=True, na=False).sum())
    con_cccd += int(ss.str.contains(RX_CCCD, regex=True, na=False).sum())
print("  Con chuoi giong so dien thoai VN : %d" % con_sdt)
print("  Con chuoi giong so CCCD 12 so    : %d" % con_cccd)

# ── Quet HO TEN: quet theo GIA TRI, khong theo ten khoa ──
# Quet theo ten khoa thi chi bat duoc nhung khoa minh da biet. Ky du lieu
# sau co the co khoa moi ten khac ma van chua ten nguoi. Quet theo gia tri
# (chuoi nhieu tu, co chu cai tieng Viet) thi bat duoc ca cai chua biet.
RX_TEN_NGUOI = re.compile(
    r"^[A-ZÀ-Ỹ][a-zà-ỹ]*(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]*){1,5}$")
KHOA_BO_QUA_TEN = {"process_name", "trang_thai", "ten_goi", "chi_tiet",
                   "san_pham", "ds_san_pham", "nguon_vay", "loai_dau_hieu",
                   "loai_alert", "cac_loai_api", "loai_dv", "loai_gd",
                   "loai_topup", "loai_dau_moi", "cp_code", "keyword_khop"}

nghi_ten = {}
for s in d.chi_tiet_alert:
    if not isinstance(s, str) or not s.strip():
        continue
    try:
        o = json.loads(s)
    except Exception:
        continue
    if not isinstance(o, dict):
        continue
    for k, v in o.items():
        if k in KHOA_BO_QUA_TEN or k in KHOA_BAM:
            continue
        vs = str(v).strip()
        if RX_TEN_NGUOI.match(vs) and len(vs) > 5:
            nghi_ten.setdefault(k, set()).add(vs)

print("  Truong nghi con chua ho ten      : %d" % len(nghi_ten))
if nghi_ten:
    print()
    print("!! PHAT HIEN TRUONG CHUA BAM, CO THE LA HO TEN THAT:")
    for k, v in sorted(nghi_ten.items(), key=lambda x: -len(x[1])):
        print("     %-24s %4d gia tri rieng | vd: %s"
              % (k, len(v), " | ".join(sorted(v)[:2])[:44]))
    print()
    print("   Them cac khoa nay vao KHOA_BAM (neu la ten nguoi) hoac")
    print("   KHOA_BO_QUA_TEN (neu la ten san pham/trang thai) roi chay lai.")
    sys.exit(1)

if con_sdt:
    print()
    print("!! VAN CON SO DIEN THOAI -- KHONG duoc day len repo public")
    for c in d.columns:
        m = d[c].astype(str).map(go_da_ma_hoa).str.contains(
            RX_SDT_VN, regex=True, na=False)
        if m.any():
            print("   cot %s: %d dong, vi du: %s"
                  % (c, int(m.sum()), str(d.loc[m, c].iloc[0])[:70]))
    sys.exit(1)

if a.kho:
    print()
    print("(che do --kho: khong ghi file)")
    sys.exit(0)

out = a.out or a.csv
d.to_csv(out, index=False, encoding="utf-8-sig")
print()
print("Ghi: %s" % out)
print("     %s dong x %d cot" % (format(len(d), ","), len(d.columns)))
