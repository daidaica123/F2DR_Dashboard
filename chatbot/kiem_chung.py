# -*- coding: utf-8 -*-
"""
KIEM CHUNG SO — chan bia so.

Sau khi LLM viet xong cau tra loi, quet moi con so trong do va doi chieu
voi du kien ma tang du lieu vua tra ve. So nao khong truy duoc ve du kien
thi coi la BIA.

Day la lop chan quan trong nhat cua ca he thong, va cung la thu it he thong
nao lam. Chi phi: mot lan quet regex, khoang 1 ms.

Gioi han da biet: chi kiem duoc CON SO, khong kiem duoc LAP LUAN. Bot van co
the ghep hai so dung thanh mot nhan dinh sai. Vi the prompt cam bot suy luan
nhan qua — xem GIOI_HAN trong tro_ly.py.
"""
import json
import re

# So trong van ban tieng Viet: 1.234,5 hoac 1,234.5 hoac 1234.5 hoac 15%
RX_SO = re.compile(r"(?<![\w/])(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)")

# So bo qua — chi 0 va 1, vi hai so nay xuat hien khap van xuoi.
# Cac so nho khac (3, 7, 9...) VAN KIEM: "7 nhom im lang" ma thuc te co 2
# thi do la bia, dung loai so bot hay noi sai nhat.
BO_QUA = {0, 1}


def _ve_so(s):
    """'1.489' -> 1489.0 | '2.225,9' -> 2225.9 | '33.6' -> 33.6

    Tieng Viet dung dau cham phan nhom nghin va phay thap phan; nhung LLM
    hay tron ca hai kieu. Doan theo vi tri dau phan cach.
    """
    s = s.strip()
    co_cham, co_phay = "." in s, "," in s

    if co_cham and co_phay:
        # dau nao dung sau la dau thap phan
        if s.rindex(",") > s.rindex("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif co_phay:
        phan = s.split(",")
        # "1,234" -> nghin ; "33,6" -> thap phan
        if len(phan) == 2 and len(phan[1]) == 3 and len(phan[0]) <= 3:
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    elif co_cham:
        phan = s.split(".")
        # "0.336" la THAP PHAN, khong phai phan nhom nghin: khong co so nao
        # viet phan nhom nghin ma bat dau bang 0. Thieu ngoai le nay thi
        # 0.336 bi doc thanh 336, va mot ty le bia se khop nham voi so 336
        # nao do trong du kien.
        if phan[0] in ("0", "-0"):
            pass                        # giu nguyen, float() doc dung
        elif len(phan) > 2 or (len(phan) == 2 and len(phan[1]) == 3
                               and len(phan[0]) <= 3):
            s = s.replace(".", "")      # 1.489 hoac 1.234.567 = nghin
    try:
        return float(s)
    except ValueError:
        return None


def _gom_so(x, ra):
    """Duyet du kien, gom moi con so tim duoc vao tap ra."""
    if isinstance(x, bool):
        return
    if isinstance(x, (int, float)):
        ra.add(round(float(x), 4))
        return
    if isinstance(x, str):
        # so nam trong chuoi (vi du "_mo_ta": "Top 5 kich ban...")
        for m in RX_SO.finditer(x):
            v = _ve_so(m.group(1))
            if v is not None:
                ra.add(round(v, 4))
        return
    if isinstance(x, dict):
        for k, v in x.items():
            _gom_so(k, ra)
            _gom_so(v, ra)
        return
    if isinstance(x, (list, tuple)):
        for v in x:
            _gom_so(v, ra)


def so_trong_du_kien(du_kien):
    """Tap hop moi con so co trong du kien, ke ca cac dang dan xuat.

    Ngoai so goc, them san cac phep bien doi ma LLM hay dung khi dien dat:
    lam tron, phan tram, ty le giua hai so. Neu khong, mot cau tra loi hoan
    toan dung van bi bao la bia chi vi no viet 33.6% thay vi 0.336.
    """
    goc = set()
    _gom_so(du_kien, goc)

    ra = set(goc)
    for v in goc:
        ra.add(round(v, 0))
        ra.add(round(v, 1))
        ra.add(round(v, 2))
        ra.add(round(abs(v), 4))
        if v:
            ra.add(round(v * 100, 1))      # ty le -> phan tram
            ra.add(round(v * 100, 0))
            ra.add(round(v / 100, 4))

    # ── Ty le giua cac cap so ──
    #
    # Bot hay tu dien dat "gap 1,43 lan" hay "giam 25%", nen phai chap nhan
    # cac gia tri dan xuat. Nhung sinh tich Descartes cua MOI cap la sai lam:
    # do 150 so goc -> 4.586 gia tri dan xuat, phu kin den muc 93% moi ty le
    # bia trong khoang 0-100 deu khop. Lop chan thanh vo dung dung o cho no
    # can nhat.
    #
    # Sua: chi lay CAC SO LON NHAT (nhung con so that su duoc noi toi trong
    # cau tra loi), gioi han so cap, va KHONG sinh hieu so — hieu so cua hai
    # so bat ky gan nhu phu kin truc so.
    lon = sorted({v for v in goc if v > 1}, reverse=True)[:22]
    for i, a in enumerate(lon):
        for b in lon[i + 1:]:
            if b:
                ra.add(round(a / b, 1))
                ra.add(round(a / b, 2))
                ra.add(round((a - b) / b * 100, 1))    # tang bao nhieu %
                ra.add(round((b - a) / a * 100, 1))    # giam bao nhieu %
                ra.add(round(b / a * 100, 1))          # chiem bao nhieu %
    return ra


def kiem(cau_tra_loi, du_kien, sai_so=0.05):
    """Doi chieu moi so trong cau tra loi voi du kien.

    Tra ve dict:
      dat        — True neu moi so deu truy duoc
      so_la      — danh sach so khong truy duoc
      so_da_kiem — tong so da doi chieu
    """
    hop_le = so_trong_du_kien(du_kien)
    la = []
    da_kiem = 0

    # Bo phan GOI_Y va cac doan trich dan ten kich ban co so (Blacklist B...)
    van = re.sub(r"^\s*GOI_Y\s*:.*$", "", cau_tra_loi, flags=re.M | re.I)

    for m in RX_SO.finditer(van):
        v = _ve_so(m.group(1))
        if v is None:
            continue
        # Nam trong ngay thang (01/09, 2026-09-01) -> bo qua.
        #
        # PHAI kiem truoc/sau co RONG khong: chuoi rong luon "in" moi chuoi
        # trong Python, nen `truoc in "/-"` tra True khi so nam o DAU cau —
        # tuc moi so mo dau cau tra loi deu duoc mien kiem. Do la lo hong
        # nghiem trong: chi can viet "9999999 alert trong ky" la lot.
        truoc = van[m.start() - 1:m.start()] if m.start() else ""
        sau = van[m.end():m.end() + 1]
        if (truoc and truoc in "/-") or (sau and sau in "/-"):
            continue

        # Bo qua 0 va 1: hai so nay xuat hien khap noi trong van xuoi
        # ("mot vai", "khong co") nen kiem chung vo nghia. Cac so nho khac
        # (3 nhom, 7 ngay, 9 kich ban) VAN PHAI KIEM — do chinh la loai so
        # bot hay noi sai nhat.
        if v in (0.0, 1.0):
            continue
        da_kiem += 1

        # SO DEM (nguyen) phai khop CHINH XAC. Khong noi long o day: "1.490"
        # trong khi that su la 1.489 trong rat hop ly nen khong ai soi ra,
        # ma da sai thi la sai.
        #
        # Chi so THAP PHAN moi duoc sai so — vi do thuong la ty le hoac phan
        # tram do LLM lam tron khi dien dat (33.58% -> 33.6%).
        la_so_nguyen = (v == int(v))
        if la_so_nguyen:
            if any(h == v for h in hop_le):
                continue
        else:
            if any(abs(v - h) <= sai_so for h in hop_le):
                continue

        la.append({"so": m.group(1), "gia_tri": v,
                   "ngu_canh": van[max(0, m.start() - 45):m.end() + 25]
                              .replace("\n", " ").strip()})

    return {
        "dat": not la,
        "so_da_kiem": da_kiem,
        "so_la": la,
    }
