# -*- coding: utf-8 -*-
"""
NAP DU LIEU + BANG KIEN THUC.

Du lieu duoc do moi HANG NGAY, nen module nay khong duoc gia dinh bat cu
con so nao. Tat ca — danh sach kich ban, nhom, dai ngay, nguong — deu doc
tu file hien hanh.

Hai thu module nay lo:

  1. Nap CSV an toan: kiem du cot, dung kieu, du lieu hong thi DUNG HAN
     thay vi chay tiep voi so rac.
  2. Dung BANG KIEN THUC: ban tom tat cua ky du lieu hien tai, dung de
     nhet vao prompt cho router biet cai gi la "thuc the noi bo".

Khoa cache mang theo mtime + kich thuoc file. Thieu no, Streamlit se vui ve
phuc vu du lieu tuan truoc sau khi da do file moi — kieu loi am tham nguy
hiem nhat.
"""
import json
import os
import re
import unicodedata
from datetime import datetime

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
GOC = os.path.dirname(HERE)
THU_MUC_DATA = os.path.join(GOC, "data")
FILE_NHOM = os.path.join(GOC, "_build", "nhom_kb.json")
FILE_GHI_CHEP = os.path.join(GOC, "_build", "ghi_chep_dieu_tra.json")

# Cot bat buoc phai co. Thieu mot cot -> khong nap, bao loi ro rang.
COT_BAT_BUOC = ["AlertID", "object_value", "usecase_clean", "ngay_alert",
                "CATEGORY", "Score_KB"]
# Cot Level cua kich ban: chap nhan mot trong hai ten
COT_LEVEL = ["risk_level_kb", "Level"]

CAP = {"Low": 25, "Medium": 50, "High": 80, "Very High": 100}
R_MAC_DINH = K_MAC_DINH = 0.70
NGUONG_MAC_DINH = [25, 55, 80]

THU_VN = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"]


class LoiDuLieu(Exception):
    """Du lieu khong dung dinh dang — khong duoc chay tiep."""


def chuan_hoa(s):
    """Bo dau, bo tien to [NEW]_/[SCORE]_, chi giu chu va so.

    Dung de so khop ten kich ban ma nguoi dung go tat hoac go thieu dau.
    Giong het ham norm() trong build_van_hanh.py de hai ben ra cung ket qua.
    """
    s = re.sub(r"^\[(SCORE|NEW)\]_", "", str(s or ""))
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s.replace("đ", "d").replace("Đ", "D").lower())


def tim_file_moi_nhat(thu_muc=None):
    """File CSV moi nhat trong data/ — dung khi khong chi dinh ro file nao."""
    thu_muc = thu_muc or THU_MUC_DATA
    if not os.path.isdir(thu_muc):
        raise LoiDuLieu("Khong thay thu muc du lieu: %s" % thu_muc)
    ds = [os.path.join(thu_muc, f) for f in os.listdir(thu_muc)
          if f.lower().endswith(".csv")]
    if not ds:
        raise LoiDuLieu("Thu muc %s khong co file CSV nao" % thu_muc)
    return max(ds, key=os.path.getmtime)


def dau_vet(duong_dan):
    """(mtime, kich thuoc) — dua vao khoa cache de file doi thi cache tu bo."""
    st = os.stat(duong_dan)
    return (st.st_mtime, st.st_size)


# ══════════════════ NAP ══════════════════

def _kiem_tra(d, duong_dan):
    """Kiem du lieu truoc khi dung. Sai thi dung han, khong chay tiep."""
    thieu = [c for c in COT_BAT_BUOC if c not in d.columns]
    if thieu:
        raise LoiDuLieu("File %s thieu cot: %s"
                        % (os.path.basename(duong_dan), ", ".join(thieu)))

    if not any(c in d.columns for c in COT_LEVEL):
        raise LoiDuLieu("File thieu cot Level cua kich ban (%s)"
                        % " hoac ".join(COT_LEVEL))

    if d.empty:
        raise LoiDuLieu("File khong co dong du lieu nao")

    # Level phai nam trong bang CAP, khong thi cong thuc diem khong chay duoc
    cot_lv = "risk_level_kb" if "risk_level_kb" in d.columns else "Level"
    la = set(d[cot_lv].dropna().unique()) - set(CAP)
    if la:
        raise LoiDuLieu("Level la %s — chua co trong bang tran diem %s"
                        % (sorted(la), sorted(CAP)))

    # Ngay phai doc duoc
    ng = pd.to_datetime(d.ngay_alert.astype(str).str[:10],
                        format="%Y-%m-%d", errors="coerce")
    if ng.isna().any():
        n = int(ng.isna().sum())
        raise LoiDuLieu("%d dong co ngay_alert khong doc duoc (can YYYY-MM-DD)" % n)


def _doc_nhom():
    """Danh sach nhom nghiep vu + so KB da cau hinh, tu nhom_kb.json."""
    if not os.path.exists(FILE_NHOM):
        return {}, {}
    try:
        j = json.load(open(FILE_NHOM, encoding="utf-8"))
        return ({k: int(v) for k, v in j.get("nhom_tong", {}).items()},
                j.get("kb2nhom", {}))
    except Exception:
        return {}, {}


def _doc_ghi_chep():
    """Ghi chep dieu tra cac ky truoc (muc 7 cua dashboard)."""
    if not os.path.exists(FILE_GHI_CHEP):
        return []
    try:
        g = json.load(open(FILE_GHI_CHEP, encoding="utf-8"))
        return g if isinstance(g, list) else []
    except Exception:
        return []


def nap_tho(duong_dan):
    """Doc CSV, kiem tra, them cac cot dan xuat. Khong cache o day."""
    if not os.path.exists(duong_dan):
        raise LoiDuLieu("Khong thay file: %s" % duong_dan)

    d = pd.read_csv(duong_dan, encoding="utf-8-sig",
                    dtype={"object_value": str, "request_id": str})
    _kiem_tra(d, duong_dan)

    # Level cua kich ban — gom ve mot ten duy nhat cho phan sau khoi phai if
    d["lv_kb"] = (d.risk_level_kb if "risk_level_kb" in d.columns else d.Level)
    d["cap_kb"] = d.lv_kb.map(CAP)
    d["ngay"] = d.ngay_alert.astype(str).str[:10]
    d["ten_kb"] = d.usecase_clean.str.replace(r"^\[NEW\]_", "", regex=True)

    # Nhom nghiep vu: tra tu nhom_kb.json, khong tra duoc thi lay CATEGORY
    _, kb2nhom = _doc_nhom()
    khoa = d.ten_kb.map(chuan_hoa)
    d["nhom"] = [kb2nhom.get(k, str(c)) for k, c in zip(khoa, d.CATEGORY)]

    return d


# ══════════════════ BANG KIEN THUC ══════════════════

def dung_kien_thuc(d, duong_dan):
    """Ban tom tat ky du lieu hien tai.

    Day la thu duoc nhet vao prompt cho router biet cai gi la thuc the noi
    bo. Sinh lai moi lan file doi, nen khong bao gio lac hau.
    """
    ngay = sorted(d.ngay.unique())
    nhom_tong, _ = _doc_nhom()

    # Kich ban: ten, nhom, muc do, diem goc, so alert trong ky
    kb = (d.groupby("ten_kb")
            .agg(nhom=("nhom", "first"), lv=("lv_kb", "first"),
                 diem=("Score_KB", "first"), cap=("cap_kb", "first"),
                 alert=("AlertID", "size"), kh=("object_value", "nunique"))
            .reset_index().sort_values("alert", ascending=False))
    ds_kb = [{"ten": r.ten_kb, "nhom": r.nhom, "muc": r.lv,
              "diem_goc": int(r.diem), "tran": int(r.cap),
              "alert": int(r.alert), "kh": int(r.kh),
              "khoa": chuan_hoa(r.ten_kb)}
             for r in kb.itertuples()]

    # Nhom: gop ca nhom khong co alert trong ky (de biet nhom nao im lang)
    co = d.groupby("nhom").agg(alert=("AlertID", "size"),
                               kh=("object_value", "nunique"),
                               kb=("ten_kb", "nunique")).to_dict("index")
    ds_nhom = []
    for ten in sorted(set(nhom_tong) | set(co),
                      key=lambda n: -co.get(n, {}).get("alert", 0)):
        x = co.get(ten, {})
        ds_nhom.append({"ten": ten,
                        "alert": int(x.get("alert", 0)),
                        "kh": int(x.get("kh", 0)),
                        "kb_co_alert": int(x.get("kb", 0)),
                        "kb_cau_hinh": int(nhom_tong.get(ten,
                                                         x.get("kb", 0)))})

    # So luot = so cap (khach, ngay) — don vi tinh diem, khac voi so alert
    so_luot = int(d.groupby(["object_value", "ngay"]).ngroups)

    return {
        "file": os.path.basename(duong_dan),
        "cap_nhat": datetime.fromtimestamp(
            os.path.getmtime(duong_dan)).strftime("%d/%m/%Y %H:%M"),
        "ngay": ngay,
        "so_ngay": len(ngay),
        "ngay_dau": ngay[0],
        "ngay_cuoi": ngay[-1],
        "tong_alert": int(len(d)),
        "tong_kh": int(d.object_value.nunique()),
        "tong_luot": so_luot,
        "so_kb_co_alert": int(d.ten_kb.nunique()),
        "so_kb_cau_hinh": int(sum(nhom_tong.values())) or int(d.ten_kb.nunique()),
        "kich_ban": ds_kb,
        "nhom": ds_nhom,
        "r": R_MAC_DINH,
        "k": K_MAC_DINH,
        "nguong": NGUONG_MAC_DINH,
        "tran_diem": CAP,
        "ghi_chep": _doc_ghi_chep(),
        # cac cot co that trong file — dung de bot biet minh KHONG co gi
        "cot_co": list(d.columns),
    }


def nap(duong_dan=None):
    """Nap du lieu + bang kien thuc. Tra ve (DataFrame, dict).

    Khong cache — ben goi (app Streamlit) tu boc cache voi khoa co dau vet
    file. De cache o day thi module nay phu thuoc Streamlit, chay doc lap
    khong duoc nua.
    """
    duong_dan = duong_dan or tim_file_moi_nhat()
    d = nap_tho(duong_dan)
    return d, dung_kien_thuc(d, duong_dan)


def thu(ngay_iso):
    """'2026-08-28' -> 'T6'.

    pandas dem thu Hai = 0 ... Chu nhat = 6; THU_VN dat Chu nhat o dau bang
    cho khop cach doc cua nguoi Viet, nen phai doi cho.
    """
    i = pd.Timestamp(ngay_iso).dayofweek        # T2=0 ... CN=6
    return THU_VN[0] if i == 6 else THU_VN[i + 1]


def nhan_ngay(ngay_iso):
    """'2026-08-28' -> '28/08'."""
    return "%s/%s" % (ngay_iso[8:10], ngay_iso[5:7])
