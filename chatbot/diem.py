# -*- coding: utf-8 -*-
"""
CONG THUC DIEM PP-D 2 TANG.

Ban Python cua ham scoreKH() trong _van_hanh_template.html. Hai ben PHAI ra
cung ket qua, neu khong so cua chatbot se lech so tren man hinh.

  Tang 1 — mot kich ban no n lan:
      e = cap - (cap - base) * r^(n-1)
      Cang no cang tien sat tran cap, khong bao gio vuot.

  Tang 2 — dinh nhieu kich ban:
      score = M + (100 - M) * k * (1 - PROD(1 - e_j/100))
      M la diem cua kich ban nang nhat; cac kich ban con lai cong don giam dan.

QUAN TRONG: khong bao gio doc cot last_risk_score hay Level tu CSV — hai cot
do tinh tu thoi r=k=0.5, con dashboard dung r=k=0.70. Luon tinh lai.
"""
import numpy as np


def hieu_luc(base, cap, n, r):
    """Tang 1: diem cua MOT kich ban khi no n lan trong ngay."""
    if cap <= base:
        return float(base)
    return float(cap - (cap - base) * (r ** (n - 1)))


def diem_luot(cac_kb, r, k):
    """Tang 2: diem cua MOT khach trong MOT ngay.

    cac_kb: list [(diem_goc, tran, so_lan), ...] — cac kich ban khach do dinh
    """
    if not cac_kb:
        return 0.0

    es = [hieu_luc(base, cap, n, r) for base, cap, n in cac_kb]
    M = max(es)

    # Bo DUNG MOT lan xuat hien cua M ra khoi tich — phan con lai cong don
    # vao. Dung remove() de neu co hai kich ban cung diem M thi chi bo mot.
    con_lai = list(es)
    con_lai.remove(M)

    tich = 1.0
    for e in con_lai:
        tich *= (1 - e / 100)

    return min(100.0, max(0.0, M + (100 - M) * k * (1 - tich)))


def muc_diem(diem, nguong):
    """Diem -> chi so muc 0..3 theo ba vach nguong.

    Lam tron 1 chu so truoc khi so, giong het giao dien: neu khong se co canh
    hai dong cung hien 80.0 ma mot dong High mot dong Very High (79.96 vs 80.02).
    """
    d = round(diem, 1)
    t1, t2, t3 = nguong
    if d < t1:
        return 0
    if d < t2:
        return 1
    if d < t3:
        return 2
    return 3


TEN_MUC = ["Low", "Medium", "High", "Very High"]
XU_LY_MUC = [
    "Khong lam gi",
    "Canh bao VANG khi co nguoi chuyen tien toi",
    "Canh bao DO khi co nguoi chuyen tien toi",
    "PENDING giao dich",
]


def diem_moi_luot(d, r, k):
    """Tinh diem cho TOAN BO cac luot (khach x ngay) trong DataFrame.

    Tra ve DataFrame co cot: object_value, ngay, diem, so_alert, so_kb.
    Day la ham nang nhat cua tang du lieu — goi mot lan roi dung lai.
    """
    # Gom: moi (khach, ngay, kich ban) -> so lan no
    g = (d.groupby(["object_value", "ngay", "ten_kb"])
           .agg(so_lan=("AlertID", "size"),
                diem_goc=("Score_KB", "first"),
                tran=("cap_kb", "first"))
           .reset_index())

    ket = []
    for (kh, ngay), nhom in g.groupby(["object_value", "ngay"], sort=False):
        cac_kb = list(zip(nhom.diem_goc, nhom.tran, nhom.so_lan))
        ket.append((kh, ngay, diem_luot(cac_kb, r, k),
                    int(nhom.so_lan.sum()), len(nhom)))

    import pandas as pd
    return pd.DataFrame(ket, columns=["object_value", "ngay", "diem",
                                      "so_alert", "so_kb"])
