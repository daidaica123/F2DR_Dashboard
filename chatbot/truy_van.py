# -*- coding: utf-8 -*-
"""
TANG DU LIEU — cac ham truy van dong san.

Day la danh muc DUY NHAT ma LLM duoc goi. LLM chon ten ham + dien tham so;
moi phep tinh deu chay o day bang pandas. LLM khong bao gio tu tinh.

Ly do khong cho LLM sinh SQL: no se co ngay viet COUNT(DISTINCT AlertID) va
ra so sai ma trong van hop ly. Voi du lieu rui ro thi do la rui ro khong
chap nhan duoc.

BA QUY TAC BAT BUOC, moi ham deu phai theo:

  1. Dem alert = SO DONG. Du lieu KHONG co khoa duy nhat nao — AlertID ghep
     tu PARTITION_DATE + request_id, mot khach co the bi cung mot kich ban
     ban nhieu lan trong cung mot ngay. DISTINCT AlertID ra 14.533 thay vi
     15.581, lech 6,7%.

  2. Dem khach = so ma RIENG BIET, khong cong ngang cac nhom. Mot khach dinh
     hai nhom van chi la mot nguoi.

  3. Diem luon TINH LAI bang cong thuc PP-D voi r,k hien hanh. Khong bao gio
     doc cot last_risk_score hay Level tu CSV (tinh tu thoi r=k=0.5).

Moi ham tra ve dict co khoa "_mo_ta" — cau tieng Viet noi ro ham nay vua
tinh gi, de LLM dien dat lai va de nguoi dung kiem chung.
"""
import json
import re
import unicodedata

import numpy as np
import pandas as pd

from . import chan_pii as CP
from . import diem as DIEM
from .nap import chuan_hoa, nhan_ngay, thu


class LoiTruyVan(Exception):
    """Tham so khong hop le — bao ro cho nguoi dung thay vi tra so sai."""


# ══════════════════ tien ich chung ══════════════════

def _loc_ngay(d, ngay=None):
    """Loc theo mot ngay, hoac tra nguyen ban neu ngay=None.

    Ngay khong co trong ky thi BAO LOI chu khong tra bang rong — nguoi dung
    can biet la ngay do khong co du lieu, khong phai 'ngay do khong co alert'.
    """
    if ngay is None:
        return d
    ngay = str(ngay).strip()
    co = set(d.ngay.unique())
    if ngay not in co:
        raise LoiTruyVan(
            "Ngay %s khong co trong ky du lieu (%s den %s)"
            % (ngay, min(co), max(co)))
    return d[d.ngay == ngay]


def _kiem_rk(r, k):
    """Cong thuc PP-D chi dung khi 0 < r < 1 va 0 < k < 1.

    Ngoai khoang do, cong thuc van "chay" nhung cho ra so vo nghia: r=2 lam
    diem GIAM khi kich ban no nhieu lan hon (24 diem cho 3 lan, thap hon ca
    diem goc 66); r am lam diem nhay lung tung. Bot se trinh bay bang so rac
    do nhu that. Chan o day, bao loi ro rang.
    """
    for ten, v in (("r", r), ("k", k)):
        if v is None:
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            raise LoiTruyVan("%s phai la so, dang nhan %r" % (ten, v))
        if not (0 < v < 1):
            raise LoiTruyVan(
                "%s = %s nam ngoai khoang hop le. Cong thuc PP-D chi dung "
                "khi 0 < %s < 1 (dashboard dang dung %s = 0,70)."
                % (ten, v, ten, ten))


def _pham_vi(ngay, kt):
    """Cau mo ta pham vi dang xet — gan vao _mo_ta cho ro rang."""
    if ngay:
        return "ngay %s (%s)" % (nhan_ngay(ngay), thu(ngay))
    return "toan ky %d ngay (%s - %s)" % (
        kt["so_ngay"], nhan_ngay(kt["ngay_dau"]), nhan_ngay(kt["ngay_cuoi"]))


def tim_kich_ban(ten, kt, nguong_khop=0.55):
    """So khop mo ten kich ban nguoi dung go tat / go thieu dau.

    Tra ve (ten_chinh_xac, cac_ung_vien). Khop duy nhat thi ung_vien rong;
    khop nhieu thi ten=None va ung_vien la danh sach de hoi lai.
    """
    q = chuan_hoa(ten)
    if not q:
        return None, []

    ds = kt["kich_ban"]

    # 1. khop chinh xac
    for k in ds:
        if k["khoa"] == q:
            return k["ten"], []

    # 2. chuoi con — nguoi dung go MOT PHAN ten kich ban.
    #
    # Chi xet mot chieu (q nam trong ten kich ban), khong xet chieu nguoc lai:
    # neu chap nhan ca "khoa nam trong q" thi go mot ten day du da bi go khoi
    # ky se khop nham sang kich ban ngan hon tinh co la chuoi con cua no.
    chua = [k for k in ds if q in k["khoa"]]
    if len(chua) == 1:
        return chua[0]["ten"], []
    if len(chua) > 1:
        # nhieu ket qua: uu tien ten NGAN nhat neu no ngan hon han cac ten kia
        chua.sort(key=lambda k: len(k["khoa"]))
        if len(chua[0]["khoa"]) * 1.5 < len(chua[1]["khoa"]):
            return chua[0]["ten"], []
        return None, [k["ten"] for k in chua]

    # 3. do trung tu — bat truong hop go sai chinh ta.
    #
    # Dung Jaccard (giao / hop) chu KHONG phai giao/len(tu): neu chi chia cho
    # so tu nguoi dung go, mot ten dai day du se khop nham sang kich ban ngan
    # hon cua cung nhom chi vi trung may tu dau ("TB thue bao..."). Jaccard
    # phat ca phan du lan phan thieu nen chat hon han.
    #
    # Bo qua tu qua ngan va tu dem chung — chung co mat o hau het ten kich ban
    # nen khong phan biet duoc gi.
    TU_CHUNG = {"kh", "tk", "tb", "cua", "co", "va", "cac", "trong", "cung",
                "khach", "hang", "gd", "so", "1", "n", "bat", "thuong"}

    def _tu(s):
        return {t for t in re.findall(r"[a-z0-9]+", chuan_hoa_co_khoang(s))
                if len(t) > 1 and t not in TU_CHUNG}

    tu = _tu(ten)
    if tu:
        diem_khop = []
        for k in ds:
            tu_kb = _tu(k["ten"])
            if not tu_kb:
                continue
            ty = len(tu & tu_kb) / len(tu | tu_kb)      # Jaccard
            if ty >= nguong_khop:
                diem_khop.append((ty, k["ten"]))
        if diem_khop:
            diem_khop.sort(reverse=True)
            if len(diem_khop) == 1 or diem_khop[0][0] > diem_khop[1][0] + 0.15:
                return diem_khop[0][1], []
            return None, [t for _, t in diem_khop[:5]]

    return None, []


def chuan_hoa_co_khoang(s):
    """Nhu chuan_hoa nhung GIU khoang trang — de tach tu khi do trung."""
    s = re.sub(r"^\[(SCORE|NEW)\]_", "", str(s or ""))
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D").lower()
    return re.sub(r"[^a-z0-9 ]", " ", s)


# ══════════════════ 1. TONG QUAN ══════════════════

def tong_quan(d, kt, **_):
    """Buc tranh chung cua ky du lieu."""
    theo_ngay = d.groupby("ngay").size()
    return {
        "_mo_ta": "Tong quan %s" % _pham_vi(None, kt),
        "ky": "%s den %s" % (kt["ngay_dau"], kt["ngay_cuoi"]),
        "so_ngay": kt["so_ngay"],
        "tong_alert": int(len(d)),
        "tong_khach": int(d.object_value.nunique()),
        "tong_luot": kt["tong_luot"],
        "so_kich_ban_co_alert": int(d.ten_kb.nunique()),
        "so_kich_ban_cau_hinh": kt["so_kb_cau_hinh"],
        "so_nhom": len(kt["nhom"]),
        "alert_tb_moi_ngay": round(float(theo_ngay.mean()), 1),
        "ngay_cao_nhat": theo_ngay.idxmax(),
        "alert_ngay_cao_nhat": int(theo_ngay.max()),
        "ngay_thap_nhat": theo_ngay.idxmin(),
        "alert_ngay_thap_nhat": int(theo_ngay.min()),
        "alert_moi_khach": round(len(d) / d.object_value.nunique(), 2),
    }


def alert_theo_ngay(d, kt, **_):
    """So alert / khach / kich ban tung ngay trong ky."""
    r = []
    da_thay = set()
    for ngay in sorted(d.ngay.unique()):
        sub = d[d.ngay == ngay]
        kh = set(sub.object_value)
        r.append({
            "ngay": ngay,
            "thu": thu(ngay),
            "alert": int(len(sub)),
            "khach": len(kh),
            "khach_moi": len(kh - da_thay),
            "kich_ban_no": int(sub.ten_kb.nunique()),
            "alert_moi_khach": round(len(sub) / len(kh), 2) if kh else 0,
        })
        da_thay |= kh

    tb = float(np.mean([x["alert"] for x in r]))
    for x in r:
        x["so_voi_tb"] = round(x["alert"] / tb, 2) if tb else 0

    return {
        "_mo_ta": "Alert tung ngay trong %s" % _pham_vi(None, kt),
        "trung_binh_ngay": round(tb, 1),
        "cac_ngay": r,
    }


def ngay_bat_thuong(d, kt, nguong=1.3, **_):
    """Ngay nao lech han so voi trung binh ky."""
    theo_ngay = d.groupby("ngay").size()
    tb = float(theo_ngay.mean())
    cao, thap = [], []
    for ngay, n in theo_ngay.items():
        ty = n / tb if tb else 0
        muc = {"ngay": ngay, "thu": thu(ngay), "alert": int(n),
               "so_voi_tb": round(ty, 2)}
        if ty >= nguong:
            cao.append(muc)
        elif ty <= 1 / nguong:
            thap.append(muc)
    return {
        "_mo_ta": "Ngay bat thuong (lech tu %.1f lan tro len so voi trung binh)"
                  % nguong,
        "trung_binh_ngay": round(tb, 1),
        "nguong_ap_dung": nguong,
        "ngay_cao": sorted(cao, key=lambda x: -x["alert"]),
        "ngay_thap": sorted(thap, key=lambda x: x["alert"]),
    }


def so_sanh_ngay(d, kt, ngay_a=None, ngay_b=None, **_):
    """So hai ngay: alert, khach, kich ban nao lech nhieu nhat.

    LUON sap hai ngay theo THU TU THOI GIAN truoc khi tinh, bat ke nguoi goi
    truyen vao theo thu tu nao. Neu khong, goi so_sanh_ngay(a=01/09, b=31/08)
    se cho ra nhan "tang" trong khi thuc te la giam — so dung nhung nghia
    nguoc, kieu loi nguy hiem nhat vi nguoi doc ket luan sai ma khong ngo.

    Khoa ket qua dat ten theo thoi gian (ngay_truoc / ngay_sau) chu khong
    theo thu tu tham so, de khong con cho hieu nham.
    """
    if not ngay_a or not ngay_b:
        raise LoiTruyVan("Can chi ro hai ngay de so sanh")

    # kiem tra ca hai ngay co that truoc, roi moi sap
    _loc_ngay(d, ngay_a)
    _loc_ngay(d, ngay_b)
    truoc, sau = sorted([str(ngay_a).strip(), str(ngay_b).strip()])
    bi_dao = (truoc != str(ngay_a).strip())

    T = d[d.ngay == truoc]
    S = d[d.ngay == sau]

    kt_ = T.groupby("ten_kb").size()
    ks_ = S.groupby("ten_kb").size()
    bang = pd.DataFrame({"truoc": kt_, "sau": ks_}).fillna(0).astype(int)
    bang["thay_doi"] = bang.sau - bang.truoc

    def _goi(df, n=6):
        return [{"kich_ban": i,
                 "ngay_truoc": int(x.truoc), "ngay_sau": int(x.sau),
                 "thay_doi": int(x.thay_doi)}
                for i, x in df.head(n).iterrows() if x.thay_doi != 0]

    # kich ban tat han / moi xuat hien — thuong la tin hieu manh nhat
    tat_han = [{"kich_ban": i, "ngay_truoc": int(x.truoc), "ngay_sau": 0}
               for i, x in bang[(bang.truoc > 0) & (bang.sau == 0)]
               .sort_values("truoc", ascending=False).iterrows()]
    moi_hien = [{"kich_ban": i, "ngay_truoc": 0, "ngay_sau": int(x.sau)}
                for i, x in bang[(bang.truoc == 0) & (bang.sau > 0)]
                .sort_values("sau", ascending=False).iterrows()]

    return {
        "_mo_ta": "So ngay %s (truoc) voi ngay %s (sau)"
                  % (nhan_ngay(truoc), nhan_ngay(sau)),
        "_ghi_chu_thu_tu": "Hai ngay da duoc sap theo THOI GIAN. "
                           "'thay_doi' = so ngay sau tru so ngay truoc: "
                           "am la GIAM, duong la TANG."
                           + (" (nguoi goi truyen nguoc thu tu, da tu sap lai)"
                              if bi_dao else ""),
        "ngay_truoc": {"ngay": truoc, "thu": thu(truoc), "alert": int(len(T)),
                       "khach": int(T.object_value.nunique()),
                       "kich_ban_no": int(T.ten_kb.nunique())},
        "ngay_sau": {"ngay": sau, "thu": thu(sau), "alert": int(len(S)),
                     "khach": int(S.object_value.nunique()),
                     "kich_ban_no": int(S.ten_kb.nunique())},
        "thay_doi_alert": int(len(S) - len(T)),
        "thay_doi_phan_tram": round((len(S) - len(T)) / len(T) * 100, 1)
                              if len(T) else None,
        "chieu": "giam" if len(S) < len(T) else "tang" if len(S) > len(T)
                 else "khong doi",
        "kich_ban_giam_manh_nhat": _goi(bang.sort_values("thay_doi")),
        "kich_ban_tang_manh_nhat": _goi(bang.sort_values("thay_doi",
                                                         ascending=False)),
        "kich_ban_tat_han": tat_han,
        "kich_ban_moi_xuat_hien": moi_hien,
    }


# ══════════════════ 2. KICH BAN ══════════════════

def top_kich_ban(d, kt, n=10, ngay=None, nhom=None, **_):
    """Cac kich ban ban nhieu alert nhat."""
    sub = _loc_ngay(d, ngay)
    if nhom:
        sub = sub[sub.nhom == nhom]
        if sub.empty:
            raise LoiTruyVan("Khong co nhom nghiep vu ten '%s'" % nhom)

    g = (sub.groupby("ten_kb")
            .agg(alert=("AlertID", "size"), khach=("object_value", "nunique"),
                 nhom=("nhom", "first"), muc=("lv_kb", "first"),
                 diem_goc=("Score_KB", "first"))
            .reset_index().sort_values("alert", ascending=False))

    tong = int(len(sub))
    ds = []
    for i, r in enumerate(g.head(int(n)).itertuples(), 1):
        ds.append({
            "hang": i,
            "kich_ban": r.ten_kb,
            "nhom": r.nhom,
            "muc": r.muc,
            "diem_goc": int(r.diem_goc),
            "alert": int(r.alert),
            "khach": int(r.khach),
            "alert_moi_khach": round(r.alert / r.khach, 2) if r.khach else 0,
            "phan_tram_tong": round(r.alert / tong * 100, 1) if tong else 0,
        })
    return {
        "_mo_ta": "Top %d kich ban nhieu alert nhat, %s%s"
                  % (n, _pham_vi(ngay, kt),
                     ", nhom %s" % nhom if nhom else ""),
        "tong_alert_pham_vi": tong,
        "so_kich_ban_co_alert": int(sub.ten_kb.nunique()),
        "danh_sach": ds,
    }


def chi_tiet_kich_ban(d, kt, ten=None, **_):
    """Ho so day du cua mot kich ban: alert tung ngay, khach, muc do."""
    if not ten:
        raise LoiTruyVan("Can ten kich ban")
    khop, ung_vien = tim_kich_ban(ten, kt)
    if not khop:
        if ung_vien:
            raise LoiTruyVan("Ten '%s' khop nhieu kich ban: %s"
                             % (ten, "; ".join(ung_vien)))
        raise LoiTruyVan("Khong tim thay kich ban nao ten giong '%s'" % ten)

    sub = d[d.ten_kb == khop]
    theo_ngay = sub.groupby("ngay").size()
    day_du = {g: int(theo_ngay.get(g, 0)) for g in kt["ngay"]}
    tb = float(np.mean(list(day_du.values())))
    dinh = max(day_du.values())
    ngay_dinh = max(day_du, key=day_du.get)
    r0 = sub.iloc[0]

    return {
        "_mo_ta": "Chi tiet kich ban '%s' trong %s" % (khop, _pham_vi(None, kt)),
        "kich_ban": khop,
        "nhom": r0.nhom,
        "muc_do": r0.lv_kb,
        "diem_goc": int(r0.Score_KB),
        "tran_diem": int(r0.cap_kb),
        "tong_alert": int(len(sub)),
        "tong_khach": int(sub.object_value.nunique()),
        "alert_moi_khach": round(len(sub) / sub.object_value.nunique(), 2),
        "phan_tram_toan_ky": round(len(sub) / len(d) * 100, 2),
        "alert_tung_ngay": [
            {"ngay": g, "thu": thu(g), "alert": v} for g, v in day_du.items()],
        "trung_binh_ngay": round(tb, 1),
        "ngay_cao_nhat": ngay_dinh,
        "alert_ngay_cao_nhat": dinh,
        "ty_le_dot_bien": round(dinh / tb, 2) if tb else 0,
    }


def kich_ban_dot_bien(d, kt, nguong=2.0, alert_toi_thieu=20, **_):
    """Kich ban co mot ngay vot han so voi cac ngay con lai."""
    r = []
    for ten, sub in d.groupby("ten_kb"):
        theo_ngay = [int((sub.ngay == g).sum()) for g in kt["ngay"]]
        tong = sum(theo_ngay)
        if tong < alert_toi_thieu:
            continue
        tb = tong / len(theo_ngay)
        dinh = max(theo_ngay)
        ty = dinh / tb if tb else 0
        if ty >= nguong:
            r.append({
                "kich_ban": ten,
                "nhom": sub.iloc[0].nhom,
                "tong_alert": tong,
                "trung_binh_ngay": round(tb, 1),
                "dinh": dinh,
                "ngay_dinh": kt["ngay"][theo_ngay.index(dinh)],
                "ty_le": round(ty, 2),
            })
    r.sort(key=lambda x: -x["ty_le"])
    return {
        "_mo_ta": "Kich ban dot bien: ngay cao nhat gap tu %.1f lan muc thuong, "
                  "va co it nhat %d alert" % (nguong, alert_toi_thieu),
        "nguong_ap_dung": nguong,
        "so_kich_ban": len(r),
        "danh_sach": r,
    }


def kich_ban_ban_day(d, kt, nguong=3.0, alert_toi_thieu=20, **_):
    """Kich ban ban nhieu alert tren moi khach — thuong do chong lap yeu."""
    g = (d.groupby("ten_kb")
           .agg(alert=("AlertID", "size"), khach=("object_value", "nunique"),
                nhom=("nhom", "first"))
           .reset_index())
    g = g[g.alert >= alert_toi_thieu].copy()
    g["alert_moi_khach"] = g.alert / g.khach
    g = g[g.alert_moi_khach >= nguong].sort_values("alert_moi_khach",
                                                   ascending=False)
    return {
        "_mo_ta": "Kich ban ban day: tu %.1f alert moi khach tro len, "
                  "va co it nhat %d alert" % (nguong, alert_toi_thieu),
        "nguong_ap_dung": nguong,
        "so_kich_ban": len(g),
        "danh_sach": [{"kich_ban": r.ten_kb, "nhom": r.nhom,
                       "alert": int(r.alert), "khach": int(r.khach),
                       "alert_moi_khach": round(r.alert_moi_khach, 2)}
                      for r in g.itertuples()],
    }


def kich_ban_im_lang(d, kt, **_):
    """Kich ban da cau hinh nhung khong co alert nao — co the dang hong."""
    co = set(d.ten_kb.unique())
    # Danh sach cau hinh nam trong nhom_kb.json, doi chieu qua khoa chuan hoa
    from .nap import _doc_nhom
    _, kb2nhom = _doc_nhom()
    khoa_co = {chuan_hoa(t) for t in co}
    im = []
    for khoa, nhom in kb2nhom.items():
        if khoa not in khoa_co:
            im.append({"khoa": khoa, "nhom": nhom})
    theo_nhom = {}
    for x in im:
        theo_nhom.setdefault(x["nhom"], 0)
        theo_nhom[x["nhom"]] += 1
    return {
        "_mo_ta": "Kich ban da cau hinh len F2DR nhung khong co alert nao "
                  "trong %s" % _pham_vi(None, kt),
        "so_kich_ban_im_lang": len(im),
        "so_kich_ban_co_alert": len(co),
        "so_kich_ban_cau_hinh": kt["so_kb_cau_hinh"],
        "theo_nhom": [{"nhom": k, "so_kich_ban_im_lang": v}
                      for k, v in sorted(theo_nhom.items(), key=lambda x: -x[1])],
        "ghi_chu": "Ten kich ban im lang chi con dang khoa chuan hoa vi khong "
                   "co alert nao mang ten day du",
    }


def kich_ban_im_lang_trong_ngay(d, kt, ngay=None, **_):
    """Kich ban co alert deu trong ky nhung IM HAN trong mot ngay.

    Day thuong la loi giai that su cho cau "sao ngay X it alert the": khong
    phai gian lan giam, ma la mot vai kich ban ngung ban — dau hieu job hong,
    data ve muon, hoac ai do tat rule.
    """
    ngay = ngay or kt["ngay"][-1]
    _loc_ngay(d, ngay)              # kiem ngay co that

    co_trong_ngay = set(d[d.ngay == ngay].ten_kb.unique())
    r = []
    for ten, sub in d.groupby("ten_kb"):
        if ten in co_trong_ngay:
            continue
        tong = int(len(sub))
        so_ngay_co = int(sub.ngay.nunique())
        tb = tong / kt["so_ngay"]
        r.append({
            "kich_ban": ten,
            "nhom": sub.iloc[0].nhom,
            "alert_ca_ky": tong,
            "so_ngay_co_alert": so_ngay_co,
            "trung_binh_moi_ngay": round(tb, 1),
            "alert_hut_so_voi_trung_binh": round(tb, 1),
        })
    r.sort(key=lambda x: -x["alert_ca_ky"])

    hut = sum(x["alert_hut_so_voi_trung_binh"] for x in r)
    that = int((d.ngay == ngay).sum())
    tb_ky = len(d) / kt["so_ngay"]

    return {
        "_mo_ta": "Kich ban im lang trong ngay %s" % nhan_ngay(ngay),
        "ngay": ngay,
        "thu": thu(ngay),
        "alert_ngay_nay": that,
        "trung_binh_ky": round(tb_ky, 1),
        "so_kich_ban_im_lang": len(r),
        "danh_sach": r,
        "tong_alert_hut_uoc_tinh": round(hut, 1),
        "ghi_chu": "Kich ban co alert deu ca ky ma im han mot ngay thuong la "
                   "dau hieu job khong chay hoac data ve muon, KHONG phai "
                   "hanh vi gian lan giam. Can kiem tra job truoc khi ket luan.",
    }


def xu_huong_kich_ban(d, kt, ten=None, **_):
    """Kich ban do dang tang hay giam trong ky."""
    if not ten:
        raise LoiTruyVan("Can ten kich ban")
    khop, ung_vien = tim_kich_ban(ten, kt)
    if not khop:
        if ung_vien:
            raise LoiTruyVan("Ten '%s' khop nhieu kich ban: %s"
                             % (ten, "; ".join(ung_vien)))
        raise LoiTruyVan("Khong tim thay kich ban nao ten giong '%s'" % ten)

    sub = d[d.ten_kb == khop]
    chuoi = [int((sub.ngay == g).sum()) for g in kt["ngay"]]
    n = len(chuoi)
    if n < 2:
        raise LoiTruyVan("Ky du lieu chi co %d ngay, chua du de xet xu huong" % n)

    # Chia doi co CHONG LAN o giua khi so ngay le, thay vi bo ngay giua ra
    # khoi ca hai nua. Ky 7 ngay ma lay [:3] vs [4:] thi ngay thu 4 bien mat
    # — dung luc do la ngay dinh thi ket luan xu huong sai han.
    nua_dau = chuoi[:(n + 1) // 2]
    nua_cuoi = chuoi[n // 2:]
    dau = sum(nua_dau) / len(nua_dau)
    cuoi = sum(nua_cuoi) / len(nua_cuoi)
    return {
        "_mo_ta": "Xu huong cua kich ban '%s' qua %d ngay" % (khop, n),
        "kich_ban": khop,
        "chuoi_ngay": [{"ngay": g, "thu": thu(g), "alert": v}
                       for g, v in zip(kt["ngay"], chuoi)],
        "trung_binh_nua_dau": round(dau, 1),
        "trung_binh_nua_cuoi": round(cuoi, 1),
        "so_ngay_nua_dau": len(nua_dau),
        "so_ngay_nua_cuoi": len(nua_cuoi),
        "thay_doi_phan_tram": round((cuoi - dau) / dau * 100, 1) if dau else None,
        "chieu_huong": "tang" if cuoi > dau * 1.1
                       else "giam" if cuoi < dau * 0.9 else "on dinh",
        "ghi_chu": "So sanh trung binh nua dau ky voi nua cuoi ky. Ky %d "
                   "ngay%s nen day chi la tin hieu so bo, chua du ket luan "
                   "xu huong." % (n, ", ngay giua duoc tinh vao ca hai nua"
                                  if n % 2 else ""),
    }


def ma_tran_kich_ban_ngay(d, kt, so_ngay=7, top=15, **_):
    """Ma tran kich ban x ngay — dung de truy nguoc ngay la do kich ban nao."""
    # Ep >= 1: so_ngay=0 se thanh kt["ngay"][-0:] = LAY CA KY, con so am thi
    # lay nham so ngay khac han. Ca hai deu ra bang khong dung y nguoi hoi.
    so_ngay = max(1, min(int(so_ngay or 7), kt["so_ngay"]))
    top = max(1, int(top or 15))
    ngay_xet = kt["ngay"][-so_ngay:]
    sub = d[d.ngay.isin(ngay_xet)]
    g = sub.groupby("ten_kb").size().sort_values(ascending=False)
    ds_kb = list(g.head(int(top)).index)

    hang = []
    for ten in ds_kb:
        s2 = sub[sub.ten_kb == ten]
        chuoi = [int((s2.ngay == x).sum()) for x in ngay_xet]
        hang.append({"kich_ban": ten, "nhom": s2.iloc[0].nhom,
                     "theo_ngay": chuoi, "tong": sum(chuoi)})

    cot = [int((sub.ngay == x).sum()) for x in ngay_xet]
    return {
        "_mo_ta": "Ma tran %d kich ban x %d ngay gan nhat"
                  % (len(hang), len(ngay_xet)),
        "cac_ngay": [{"ngay": g2, "thu": thu(g2)} for g2 in ngay_xet],
        "tong_theo_ngay": cot,
        "ngay_cao_nhat": ngay_xet[cot.index(max(cot))],
        "cac_hang": hang,
    }


# ══════════════════ 3. NHOM NGHIEP VU ══════════════════

def thong_ke_nhom(d, kt, ngay=None, **_):
    """Alert / khach / kich ban theo tung nhom nghiep vu."""
    sub = _loc_ngay(d, ngay)
    tong = int(len(sub))
    cau_hinh = {x["ten"]: x["kb_cau_hinh"] for x in kt["nhom"]}

    g = sub.groupby("nhom").agg(alert=("AlertID", "size"),
                                khach=("object_value", "nunique"),
                                kich_ban=("ten_kb", "nunique"))
    ds = []
    for ten in sorted(set(cau_hinh) | set(g.index),
                      key=lambda t: -int(g.alert.get(t, 0))):
        a = int(g.alert.get(ten, 0))
        ds.append({
            "nhom": ten,
            "alert": a,
            "khach": int(g.khach.get(ten, 0)),
            "kich_ban_co_alert": int(g.kich_ban.get(ten, 0)),
            "kich_ban_cau_hinh": int(cau_hinh.get(ten, 0)),
            "phan_tram_tong": round(a / tong * 100, 1) if tong else 0,
            "alert_moi_khach": round(a / int(g.khach.get(ten, 1)), 2)
                               if g.khach.get(ten, 0) else 0,
        })
    return {
        "_mo_ta": "Thong ke 7 nhom nghiep vu, %s" % _pham_vi(ngay, kt),
        "tong_alert_pham_vi": tong,
        "tong_khach_pham_vi": int(sub.object_value.nunique()),
        "danh_sach": ds,
        "ghi_chu": "Khach hang KHONG cong ngang cac nhom duoc — mot khach "
                   "dinh hai nhom van chi la mot nguoi.",
    }


def nhom_im_lang(d, kt, **_):
    """Nhom nghiep vu khong co alert nao — dau hieu kich ban khong chay."""
    co = set(d.nhom.unique())
    im = [x for x in kt["nhom"] if x["ten"] not in co or x["alert"] == 0]
    return {
        "_mo_ta": "Nhom nghiep vu khong co alert nao trong %s" % _pham_vi(None, kt),
        "so_nhom_im_lang": len(im),
        "danh_sach": [{"nhom": x["ten"],
                       "kich_ban_da_cau_hinh": x["kb_cau_hinh"]} for x in im],
        "ghi_chu": "Nhom da cau hinh kich ban ma khong co alert nao thuong la "
                   "dau hieu kich ban chua chay, can kiem tra.",
    }


def nhom_theo_ngay(d, kt, nhom=None, **_):
    """Mot nhom nghiep vu bien dong the nao qua cac ngay."""
    if not nhom:
        raise LoiTruyVan("Can ten nhom nghiep vu")
    ten_co = {x["ten"] for x in kt["nhom"]}
    if nhom not in ten_co:
        gan = [t for t in ten_co if chuan_hoa(nhom) in chuan_hoa(t)]
        if len(gan) == 1:
            nhom = gan[0]
        else:
            raise LoiTruyVan("Khong co nhom '%s'. Cac nhom: %s"
                             % (nhom, ", ".join(sorted(ten_co))))
    sub = d[d.nhom == nhom]
    return {
        "_mo_ta": "Nhom '%s' qua %d ngay" % (nhom, kt["so_ngay"]),
        "nhom": nhom,
        "tong_alert": int(len(sub)),
        "theo_ngay": [
            {"ngay": g, "thu": thu(g),
             "alert": int((sub.ngay == g).sum()),
             "khach": int(sub[sub.ngay == g].object_value.nunique())}
            for g in kt["ngay"]],
    }


# ══════════════════ 4. KHACH HANG ══════════════════

def top_khach_hang(d, kt, n=10, ngay=None, **_):
    """Khach bi ban nhieu alert nhat, kem diem cao nhat cua ho.

    r, k CO DINH theo dashboard (0,70). Bot khong doi duoc — viec dat tham so
    va chot nguong Impact lam o tai lieu phuong phap luan rieng.
    """
    r, k = kt["r"], kt["k"]
    sub = _loc_ngay(d, ngay)

    g = (sub.groupby("object_value")
            .agg(alert=("AlertID", "size"), so_kb=("ten_kb", "nunique"),
                 so_ngay=("ngay", "nunique"))
            .reset_index().sort_values("alert", ascending=False).head(int(n)))

    diem_bang = DIEM.diem_moi_luot(sub[sub.object_value.isin(g.object_value)],
                                   r, k)
    dinh = diem_bang.groupby("object_value").diem.max().to_dict()
    ngay_dinh = (diem_bang.loc[diem_bang.groupby("object_value").diem.idxmax()]
                 .set_index("object_value").ngay.to_dict())

    ds = []
    for i, x in enumerate(g.itertuples(), 1):
        dd = float(dinh.get(x.object_value, 0))
        ds.append({
            "hang": i,
            "ma_khach": x.object_value,
            "alert": int(x.alert),
            "so_kich_ban": int(x.so_kb),
            "so_ngay_bi_ban": int(x.so_ngay),
            "alert_moi_ngay": round(x.alert / x.so_ngay, 1),
            "diem_cao_nhat": round(dd, 1),
            "muc": DIEM.TEN_MUC[DIEM.muc_diem(dd, kt["nguong"])],
            "ngay_diem_cao_nhat": ngay_dinh.get(x.object_value),
        })
    return {
        "_mo_ta": "Top %d khach nhieu alert nhat, %s" % (n, _pham_vi(ngay, kt)),
        "danh_sach": ds,
        "ghi_chu": "Diem cham theo tung NGAY, khong cong don qua ngay. "
                   "Alert nhieu ma chi dinh 1-2 kich ban thuong do chong lap "
                   "cua kich ban do, khong phai nguoi nay nguy hiem hon.",
    }


def ho_so_khach(d, kt, ma=None, **_):
    """Ho so mot khach: tung ngay dinh kich ban gi, diem bao nhieu.

    r, k CO DINH theo dashboard (0,70).
    """
    if not ma:
        raise LoiTruyVan("Can ma khach hang")
    r, k = kt["r"], kt["k"]

    sub = d[d.object_value == str(ma).strip()]
    if sub.empty:
        raise LoiTruyVan("Khong co khach nao ma '%s' trong ky nay" % ma)

    ngay_ct = []
    for ngay in sorted(sub.ngay.unique()):
        s2 = sub[sub.ngay == ngay]
        kbs = (s2.groupby("ten_kb")
                 .agg(so_lan=("AlertID", "size"), diem_goc=("Score_KB", "first"),
                      tran=("cap_kb", "first"), muc=("lv_kb", "first"))
                 .reset_index().sort_values("so_lan", ascending=False))
        dd = DIEM.diem_luot(list(zip(kbs.diem_goc, kbs.tran, kbs.so_lan)), r, k)
        ngay_ct.append({
            "ngay": ngay,
            "thu": thu(ngay),
            "alert": int(len(s2)),
            "diem": round(dd, 1),
            "muc": DIEM.TEN_MUC[DIEM.muc_diem(dd, kt["nguong"])],
            "kich_ban": [{"ten": x.ten_kb, "so_lan": int(x.so_lan),
                          "muc": x.muc, "diem_goc": int(x.diem_goc)}
                         for x in kbs.itertuples()],
        })

    cao = max(ngay_ct, key=lambda x: x["diem"])
    return {
        "_mo_ta": "Ho so khach %s trong %s" % (ma, _pham_vi(None, kt)),
        "ma_khach": str(ma),
        "tong_alert": int(len(sub)),
        "so_ngay_bi_ban": int(sub.ngay.nunique()),
        "so_kich_ban_khac_nhau": int(sub.ten_kb.nunique()),
        "diem_cao_nhat": cao["diem"],
        "muc_cao_nhat": cao["muc"],
        "ngay_diem_cao_nhat": cao["ngay"],
        "chi_tiet_tung_ngay": ngay_ct,
    }


def khach_tai_pham(d, kt, so_ngay_toi_thieu=3, **_):
    """Khach bi ban nhieu ngay khac nhau trong ky."""
    g = d.groupby("object_value").ngay.nunique()
    phan_bo = g.value_counts().sort_index()
    tai = g[g >= int(so_ngay_toi_thieu)]
    return {
        "_mo_ta": "Khach bi alert tu %d ngay tro len trong ky %d ngay"
                  % (so_ngay_toi_thieu, kt["so_ngay"]),
        "so_khach_tai_pham": int(len(tai)),
        "tong_khach": int(len(g)),
        "phan_tram": round(len(tai) / len(g) * 100, 1) if len(g) else 0,
        "phan_bo_so_ngay": [{"so_ngay": int(i), "so_khach": int(v)}
                            for i, v in phan_bo.items()],
        "ghi_chu": "Nhom nay neu giu nguyen tan suat se khong bao gio du 30 "
                   "ngay sach de duoc an xa.",
    }


def khach_nhieu_kich_ban(d, kt, so_kb_toi_thieu=3, n=10, **_):
    """Khach dinh nhieu kich ban KHAC NHAU — dang nay moi thuc su dang dieu tra."""
    g = (d.groupby("object_value")
           .agg(so_kb=("ten_kb", "nunique"), alert=("AlertID", "size"),
                so_ngay=("ngay", "nunique"))
           .reset_index())
    g = g[g.so_kb >= int(so_kb_toi_thieu)].sort_values(
        ["so_kb", "alert"], ascending=False).head(int(n))

    ds = []
    for x in g.itertuples():
        kbs = d[d.object_value == x.object_value].ten_kb.unique()
        ds.append({"ma_khach": x.object_value, "so_kich_ban": int(x.so_kb),
                   "alert": int(x.alert), "so_ngay": int(x.so_ngay),
                   "cac_kich_ban": sorted(kbs)})
    return {
        "_mo_ta": "Khach dinh tu %d kich ban khac nhau tro len"
                  % so_kb_toi_thieu,
        "so_khach": len(ds),
        "danh_sach": ds,
        "ghi_chu": "Dinh nhieu kich ban KHAC NHAU dang dieu tra hon la bi mot "
                   "kich ban ban nhieu lan.",
    }


def tim_khach(d, kt, ma=None, **_):
    """Kiem tra mot ma khach co trong ky khong."""
    if not ma:
        raise LoiTruyVan("Can ma khach hang")
    ma = str(ma).strip()
    sub = d[d.object_value == ma]
    if sub.empty:
        # Chi goi y khi tien to du dai. Voi tien to ngan ("00") thi day thanh
        # cong cu liet ke ma khach hang — dung y do la khai thac danh sach.
        gan = ([x for x in d.object_value.unique() if x.startswith(ma[:8])][:5]
               if len(ma) >= 8 else [])
        return {
            "_mo_ta": "Tim ma khach '%s'" % ma,
            "tim_thay": False,
            "ma_gan_giong": gan,
        }
    return {
        "_mo_ta": "Tim ma khach '%s'" % ma,
        "tim_thay": True,
        "ma_khach": ma,
        "tong_alert": int(len(sub)),
        "so_ngay": int(sub.ngay.nunique()),
        "so_kich_ban": int(sub.ten_kb.nunique()),
    }


# ══════════════════ 5. DIEM & NGUONG ══════════════════

def phan_bo_diem(d, kt, r=None, k=None, ngay=None, **_):
    """Phan bo diem cua cac luot, va so luot moi muc Impact."""
    _kiem_rk(r, k)
    r = kt["r"] if r is None else float(r)
    k = kt["k"] if k is None else float(k)
    sub = _loc_ngay(d, ngay)
    bang = DIEM.diem_moi_luot(sub, r, k)
    ds = bang.diem.values

    dem = [0, 0, 0, 0]
    for x in ds:
        dem[DIEM.muc_diem(x, kt["nguong"])] += 1
    N = len(ds)

    return {
        "_mo_ta": "Phan bo diem %d luot, %s (r=%.2f, k=%.2f, nguong %s)"
                  % (N, _pham_vi(ngay, kt), r, k, kt["nguong"]),
        "tham_so": {"r": r, "k": k, "nguong": kt["nguong"]},
        "so_luot": N,
        "diem_thap_nhat": round(float(ds.min()), 1) if N else 0,
        "diem_cao_nhat": round(float(ds.max()), 1) if N else 0,
        "trung_vi": round(float(np.percentile(ds, 50)), 1) if N else 0,
        "phan_vi_95": round(float(np.percentile(ds, 95)), 1) if N else 0,
        "phan_vi_99": round(float(np.percentile(ds, 99)), 1) if N else 0,
        "theo_muc": [
            {"muc": DIEM.TEN_MUC[i], "so_luot": dem[i],
             "phan_tram": round(dem[i] / N * 100, 2) if N else 0,
             "xu_ly": DIEM.XU_LY_MUC[i]}
            for i in range(4)],
        "ghi_chu": "Mot LUOT la mot khach trong mot ngay. Ky nay co %s luot "
                   "tu %s khach." % (f"{kt['tong_luot']:,}", f"{kt['tong_kh']:,}"),
    }


def khoi_luong_theo_nguong(d, kt, t1=None, t2=None, t3=None, r=None, k=None, **_):
    """Dat ba vach nguong nay thi phai xu ly bao nhieu luot moi muc."""
    ng = kt["nguong"]
    t1 = ng[0] if t1 is None else int(t1)
    t2 = ng[1] if t2 is None else int(t2)
    t3 = ng[2] if t3 is None else int(t3)
    if not (0 < t1 < t2 < t3 < 100):
        raise LoiTruyVan("Ba vach phai tang dan trong khoang 1-99, dang nhan "
                         "%s / %s / %s" % (t1, t2, t3))
    _kiem_rk(r, k)
    r = kt["r"] if r is None else float(r)
    k = kt["k"] if k is None else float(k)

    bang = DIEM.diem_moi_luot(d, r, k)
    dem = [0, 0, 0, 0]
    for x in bang.diem.values:
        dem[DIEM.muc_diem(x, [t1, t2, t3])] += 1
    N = len(bang)

    return {
        "_mo_ta": "Khoi luong phai xu ly voi nguong %d/%d/%d (r=%.2f, k=%.2f)"
                  % (t1, t2, t3, r, k),
        "nguong": [t1, t2, t3],
        "tong_luot": N,
        "theo_muc": [
            {"muc": DIEM.TEN_MUC[i], "so_luot": dem[i],
             "phan_tram": round(dem[i] / N * 100, 2) if N else 0,
             "xu_ly": DIEM.XU_LY_MUC[i]}
            for i in range(4)],
        "so_luot_can_xu_ly": dem[1] + dem[2] + dem[3],
        "ghi_chu": "Day la uoc luong khoi luong, KHONG phai noi chot nguong "
                   "Impact chinh thuc.",
    }


def anh_huong_tham_so(d, kt, r_moi=None, k_moi=None, **_):
    """Doi r,k thi so luot Very High thay doi ra sao."""
    if r_moi is None and k_moi is None:
        raise LoiTruyVan("Can it nhat mot trong hai tham so r_moi hoac k_moi")
    _kiem_rk(r_moi, k_moi)
    r0, k0 = kt["r"], kt["k"]
    r1 = r0 if r_moi is None else float(r_moi)
    k1 = k0 if k_moi is None else float(k_moi)

    def _dem(r, k):
        bang = DIEM.diem_moi_luot(d, r, k)
        dem = [0, 0, 0, 0]
        for x in bang.diem.values:
            dem[DIEM.muc_diem(x, kt["nguong"])] += 1
        return dem, float(bang.diem.mean())

    cu, tb_cu = _dem(r0, k0)
    moi, tb_moi = _dem(r1, k1)
    N = sum(cu)

    return {
        "_mo_ta": "Doi tham so tu r=%.2f,k=%.2f sang r=%.2f,k=%.2f"
                  % (r0, k0, r1, k1),
        "tham_so_cu": {"r": r0, "k": k0},
        "tham_so_moi": {"r": r1, "k": k1},
        "diem_trung_binh_cu": round(tb_cu, 2),
        "diem_trung_binh_moi": round(tb_moi, 2),
        "so_sanh": [
            {"muc": DIEM.TEN_MUC[i], "cu": cu[i], "moi": moi[i],
             "thay_doi": moi[i] - cu[i],
             "phan_tram_cu": round(cu[i] / N * 100, 2) if N else 0,
             "phan_tram_moi": round(moi[i] / N * 100, 2) if N else 0}
            for i in range(4)],
    }


def cong_thuc_diem(d, kt, **_):
    """Giai thich cong thuc PP-D va tham so hien hanh."""
    kb0 = kt["kich_ban"][0]
    base, cap = kb0["diem_goc"], kb0["tran"]
    r = kt["r"]
    return {
        "_mo_ta": "Cong thuc tinh diem PP-D 2 tang dang dung",
        "tang_1": "e = cap - (cap - base) * r^(n-1)",
        "tang_1_y_nghia": "Mot kich ban no n lan trong ngay: diem tien sat "
                          "tran cap nhung khong vuot",
        "tang_2": "score = M + (100 - M) * k * (1 - TICH(1 - e_j/100))",
        "tang_2_y_nghia": "Dinh nhieu kich ban: M la diem kich ban nang nhat, "
                          "cac kich ban con lai cong don giam dan",
        "r_hien_hanh": kt["r"],
        "k_hien_hanh": kt["k"],
        "nguong_hien_hanh": kt["nguong"],
        "tran_diem_theo_muc": kt["tran_diem"],
        "vi_du": {
            "kich_ban": kb0["ten"],
            "muc": kb0["muc"],
            "diem_goc": base,
            "tran": cap,
            "no_1_lan": base,
            "no_2_lan": round(DIEM.hieu_luc(base, cap, 2, r), 1),
            "no_3_lan": round(DIEM.hieu_luc(base, cap, 3, r), 1),
        },
        "canh_bao": "Cot last_risk_score va Level trong CSV tinh tu thoi "
                    "r=k=0.5, KHONG khop voi dashboard (r=k=0.70). Luon tinh lai.",
    }


# ══════════════════ 6. BANG CHUNG ══════════════════

def bang_chung_alert(d, kt, kich_ban=None, ngay=None, ma_khach=None,
                     gioi_han=15, **_):
    """Doc chi_tiet_alert — bang chung nghiep vu vi sao alert no.

    Day la ham DUY NHAT tra ve du lieu tho. LLM chi duoc MO TA lai, khong
    duoc tong hop hay tinh toan gi tren do.
    """
    # Kiem ngay tren d GOC truoc, roi moi loc kich ban. Kiem tren sub da loc
    # thi mot kich ban khong ban ngay X se bao "ngay X khong co trong ky" —
    # sai su that, va con in ra khoang ngay cut cua rieng kich ban do.
    if ngay:
        _loc_ngay(d, ngay)

    sub = d
    if kich_ban:
        khop, ung_vien = tim_kich_ban(kich_ban, kt)
        if not khop:
            if ung_vien:
                raise LoiTruyVan("Ten '%s' khop nhieu kich ban: %s"
                                 % (kich_ban, "; ".join(ung_vien)))
            raise LoiTruyVan("Khong tim thay kich ban '%s'" % kich_ban)
        sub = sub[sub.ten_kb == khop]
    if ngay:
        sub = sub[sub.ngay == str(ngay).strip()]
    if ma_khach:
        sub = sub[sub.object_value == str(ma_khach).strip()]

    if sub.empty:
        raise LoiTruyVan("Khong co alert nao khop dieu kien da cho")

    if "chi_tiet_alert" not in sub.columns:
        raise LoiTruyVan("File du lieu khong co cot chi_tiet_alert")

    ds = []
    for x in sub.head(int(gioi_han)).itertuples():
        try:
            ct = json.loads(x.chi_tiet_alert) if x.chi_tiet_alert else {}
        except Exception:
            ct = {}
        ds.append({
            "ma_khach": x.object_value,
            "ngay": x.ngay,
            "gio": getattr(x, "gio_alert", ""),
            "kich_ban": x.ten_kb,
            "muc": x.lv_kb,
            # Bo cac truong dinh danh TRUOC khi dua cho LLM. Gia tri da bam
            # roi, nhung LLM khong nhin thay thi khong lo duoc — va cung
            # khong bi du dan dien giai chung thanh thong tin nhan than.
            "bang_chung": CP.che_bang_chung(ct),
        })

    return {
        "_mo_ta": "Bang chung nghiep vu cua %d alert (trong tong %d khop dieu kien)"
                  % (len(ds), len(sub)),
        "tong_khop": int(len(sub)),
        "so_tra_ve": len(ds),
        "cac_alert": ds,
        "ghi_chu": "Du lieu tho tu cot chi_tiet_alert, DA BO cac truong dinh "
                   "danh (so dien thoai, tai khoan, CCCD...). Chi con so lieu "
                   "nghiep vu. CHI mo ta lai, khong tinh toan tren do.",
    }


def ghi_chep_dieu_tra(d, kt, tu_khoa=None, **_):
    """Ket luan dieu tra cac ky truoc (muc 7 cua dashboard)."""
    g = kt.get("ghi_chep", [])
    if tu_khoa:
        q = chuan_hoa(tu_khoa)
        g = [x for x in g
             if q in chuan_hoa(x.get("tieude", "") + " " + x.get("noidung", "")
                               + " " + " ".join(x.get("tag", [])))]
    return {
        "_mo_ta": "Ghi chep dieu tra%s" % (" khop '%s'" % tu_khoa if tu_khoa else ""),
        "so_muc": len(g),
        "cac_muc": g,
        "ghi_chu": "Trong khi chua co ghi chep nao thi muc nay rong." if not g else "",
    }


# ══════════════════ DANH MUC ══════════════════
# LLM chi duoc chon ten trong bang nay. Sai ten -> loi ngay, khong am tham
# ra so sai. Mo ta viet ngan gon vi se nhet thang vao prompt.

DANH_MUC = {
    # tong quan
    "tong_quan": (tong_quan, "Buc tranh chung ca ky: tong alert, khach, kich ban, ngay cao nhat"),
    "alert_theo_ngay": (alert_theo_ngay, "So alert/khach/kich ban tung ngay trong ky"),
    "ngay_bat_thuong": (ngay_bat_thuong, "Ngay nao lech han so trung binh. Tham so: nguong (mac dinh 1.3)"),
    "so_sanh_ngay": (so_sanh_ngay, "So hai ngay voi nhau. Tham so: ngay_a, ngay_b (YYYY-MM-DD)"),
    # kich ban
    "top_kich_ban": (top_kich_ban, "Kich ban nhieu alert nhat. Tham so: n, ngay, nhom"),
    "chi_tiet_kich_ban": (chi_tiet_kich_ban, "Ho so day du mot kich ban. Tham so: ten"),
    "kich_ban_dot_bien": (kich_ban_dot_bien, "Kich ban co ngay vot han. Tham so: nguong (mac dinh 2.0)"),
    "kich_ban_ban_day": (kich_ban_ban_day, "Kich ban nhieu alert moi khach. Tham so: nguong (mac dinh 3.0)"),
    "kich_ban_im_lang": (kich_ban_im_lang, "Kich ban da cau hinh nhung khong co alert nao ca ky"),
    "kich_ban_im_lang_trong_ngay": (kich_ban_im_lang_trong_ngay, "Kich ban co alert deu ca ky nhung im han MOT ngay - loi giai cho 'sao ngay X it alert'. Tham so: ngay"),
    "xu_huong_kich_ban": (xu_huong_kich_ban, "Kich ban dang tang hay giam. Tham so: ten"),
    "ma_tran_kich_ban_ngay": (ma_tran_kich_ban_ngay, "Ma tran kich ban x ngay. Tham so: so_ngay, top"),
    # nhom
    "thong_ke_nhom": (thong_ke_nhom, "Alert/khach/kich ban theo nhom nghiep vu. Tham so: ngay"),
    "nhom_im_lang": (nhom_im_lang, "Nhom nghiep vu khong co alert nao"),
    "nhom_theo_ngay": (nhom_theo_ngay, "Mot nhom bien dong qua cac ngay. Tham so: nhom"),
    # khach hang
    "top_khach_hang": (top_khach_hang, "Khach bi ban nhieu alert nhat. Tham so: n, ngay"),
    "ho_so_khach": (ho_so_khach, "Ho so mot khach: tung ngay dinh kich ban gi. Tham so: ma"),
    "khach_tai_pham": (khach_tai_pham, "Khach bi ban nhieu ngay. Tham so: so_ngay_toi_thieu"),
    "khach_nhieu_kich_ban": (khach_nhieu_kich_ban, "Khach dinh nhieu kich ban khac nhau. Tham so: so_kb_toi_thieu, n"),
    "tim_khach": (tim_khach, "Kiem tra mot ma khach co trong ky khong. Tham so: ma"),
    # ── KHONG dua vao danh muc: phan_bo_diem, khoi_luong_theo_nguong,
    #    anh_huong_tham_so, cong_thuc_diem ──
    #
    # Bot khong lam viec dat diem va chot nguong Impact. Do la viec cua tai
    # lieu phuong phap luan rieng, khong chot tren file nay — dung nhu muc ⑧
    # cua dashboard da ghi. Ba muc ⓪①② tren dashboard chi de uoc luong khoi
    # luong phai xu ly, va nguoi dung tu keo thanh truot o do.
    #
    # Cac ham van con trong file (ho_so_khach dung diem de xep muc khach), chi
    # la khong cho LLM goi truc tiep.
    # bang chung
    "bang_chung_alert": (bang_chung_alert, "Doc chi_tiet_alert - vi sao alert no. Tham so: kich_ban, ngay, ma_khach, gioi_han"),
    "ghi_chep_dieu_tra": (ghi_chep_dieu_tra, "Ket luan dieu tra cac ky truoc. Tham so: tu_khoa"),
}


def goi(ten_ham, d, kt, **tham_so):
    """Goi mot ham trong danh muc. Ten sai -> loi ro rang."""
    if ten_ham not in DANH_MUC:
        raise LoiTruyVan("Khong co ham '%s'. Cac ham co: %s"
                         % (ten_ham, ", ".join(sorted(DANH_MUC))))
    ham = DANH_MUC[ten_ham][0]
    kq = ham(d, kt, **tham_so)
    kq["_ham"] = ten_ham
    kq["_tham_so"] = {k: v for k, v in tham_so.items() if v is not None}
    return kq


def mo_ta_danh_muc():
    """Bang mo ta cac ham — nhet vao prompt cho LLM chon."""
    return "\n".join("  %-24s %s" % (t, DANH_MUC[t][1]) for t in DANH_MUC)
