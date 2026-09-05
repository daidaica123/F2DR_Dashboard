# -*- coding: utf-8 -*-
"""
TRA NGUOC ma an danh <-> so dien thoai that.

Ma an danh sinh ra bang:  sha256(MUOI + so_dien_thoai)[:20]

Vi tap so dien thoai VN huu han (~100 trieu dau so), ai giu MUOI deu tra
nguoc duoc bang cach bam lai roi so. Ai KHONG co MUOI thi khong lam gi duoc
-- do la ly do MUOI phai giu kin, dung bao gio commit len repo.

Dat muoi mot lan trong PowerShell:
    $env:F2DR_SALT = "chuoi-bi-mat-cua-rieng-ban"

Ba cach dung:

1. Biet SO DIEN THOAI, muon tim ma trong dashboard:
       py -3.10 _build/tra_nguoc.py --sdt 09xxxxxxxx

2. Thay MA la tren dashboard, muon biet so nao:
       py -3.10 _build/tra_nguoc.py --ma 7f3a9c2e1b8d4056a1c2

3. Tra ca danh sach tu file (moi dong mot so hoac mot ma):
       py -3.10 _build/tra_nguoc.py --file ds.txt
"""
import argparse
import hashlib
import os
import re
import sys

RX_SDT = re.compile(r"^0?\d{9,10}$")
RX_MA = re.compile(r"^[0-9a-f]{20}$")

ap = argparse.ArgumentParser()
ap.add_argument("--sdt", help="So dien thoai -> ma an danh")
ap.add_argument("--ma", help="Ma an danh -> so dien thoai")
ap.add_argument("--file", help="File danh sach, moi dong mot so hoac mot ma")
ap.add_argument("--goc", help="File CSV GOC (chua an danh) — dung cho --ma, "
                             "tra rat nhanh vi chi do trong tap so co that")
ap.add_argument("--salt", default=os.environ.get("F2DR_SALT"))
a = ap.parse_args()

if not a.salt:
    sys.exit("Chua co MUOI. Dat truoc khi chay:\n"
             '    $env:F2DR_SALT = "chuoi-bi-mat-cua-ban"')


def bam(sdt):
    return hashlib.sha256((a.salt + sdt).encode()).hexdigest()[:20]


def chuan(s):
    """Chap nhan ca 0348..., 84348..., +84348... -> ve dung dang trong file goc."""
    s = re.sub(r"[^\d]", "", str(s))
    if s.startswith("84") and len(s) > 10:
        s = "0" + s[2:]
    return s


# ── 1. so dien thoai -> ma ──
if a.sdt:
    s = chuan(a.sdt)
    if not RX_SDT.match(s):
        sys.exit("Khong phai so dien thoai hop le: " + a.sdt)
    print("%s  ->  %s" % (s, bam(s)))

# ── 2. ma -> so dien thoai ──
# Doi chieu voi BAN GOC (file chua an danh) neu con giu. Nhanh, chinh xac.
# Khong con ban goc thi do can theo dau so VN -- cham hon nhung van chay duoc.
if a.ma:
    if not RX_MA.match(a.ma):
        sys.exit("Ma phai la 20 ky tu hex")
    thay = None

    if a.goc and os.path.exists(a.goc):
        import pandas as pd
        g = pd.read_csv(a.goc, encoding="utf-8-sig", dtype={"object_value": str})
        ds = g.object_value.astype(str).drop_duplicates()
        ds = ds[ds.str.fullmatch(RX_SDT)]
        print("Doi chieu voi ban goc: %s so dien thoai" % format(len(ds), ","))
        for s in ds:
            if bam(s) == a.ma:
                thay = s
                break
    else:
        DAU = ["032", "033", "034", "035", "036", "037", "038", "039",
               "086", "096", "097", "098",                      # Viettel
               "070", "076", "077", "078", "079", "089", "090", "093",
               "081", "082", "083", "084", "085", "088", "091", "094",
               "056", "058", "059", "092", "099"]
        print("Khong co ban goc -> do can %d dau so x 10 trieu."
              % len(DAU))
        print("Mat vai phut. Ctrl+C de dung.")
        for i, dau in enumerate(DAU, 1):
            for n in range(10_000_000):
                if bam("%s%07d" % (dau, n)) == a.ma:
                    thay = "%s%07d" % (dau, n)
                    break
            if thay:
                break
            print("   ...xong %s (%d/%d)" % (dau, i, len(DAU)))

    print("KET QUA: %s" % (thay or "khong tim thay"))

# ── 3. tra ca danh sach ──
if a.file:
    if not os.path.exists(a.file):
        sys.exit("Khong thay file: " + a.file)
    print("%-16s  %s" % ("SO DIEN THOAI", "MA AN DANH"))
    print("-" * 40)
    for dong in open(a.file, encoding="utf-8"):
        t = dong.strip()
        if not t:
            continue
        s = chuan(t)
        if RX_SDT.match(s):
            print("%-16s  %s" % (s, bam(s)))
        else:
            print("%-16s  (khong phai so dien thoai)" % t[:16])

if not (a.sdt or a.ma or a.file):
    ap.print_help()
