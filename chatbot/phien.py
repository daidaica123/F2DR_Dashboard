# -*- coding: utf-8 -*-
"""
QUAN LY PHIEN CHAT.

Boc phan trang thai va nap du lieu co cache, tach khoi app.py cho gon.

Diem quan trong nhat o day la KHOA CACHE: no mang theo mtime va kich thuoc
file. Thieu, Streamlit se vui ve phuc vu du lieu tuan truoc sau khi da do
file moi — bot van tra loi tron tru, chi la bang so cu. Kieu loi am tham
nguy hiem nhat.
"""
import streamlit as st

from .nap import (FILE_GHI_CHEP, FILE_NHOM, LoiDuLieu, dau_vet, nap_tho,
                  dung_kien_thuc, tim_file_moi_nhat)

SO_LUOT_TOI_DA = 40          # chan chi phi neu link app lan ra ngoai
SO_LUOT_NHO = 6              # so luot hoi dap giu lai lam ngu canh


@st.cache_data(show_spinner=False)
def _nap_co_cache(duong_dan, dau_vet_csv, dau_vet_nhom, dau_vet_ghi_chep):
    """Ba tham so dau_vet_* KHONG duoc dung trong than ham — chung o day chi
    de lam khoa cache. File nao doi -> khoa doi -> cache tu bo, nap lai."""
    d = nap_tho(duong_dan)
    return d, dung_kien_thuc(d, duong_dan)


def _dau_vet_neu_co(duong_dan):
    """Dau vet file, hoac None neu file chua ton tai."""
    try:
        return dau_vet(duong_dan)
    except OSError:
        return None


def nap_du_lieu(duong_dan=None):
    """Nap du lieu, tu nhan file moi. Tra ve (DataFrame, kien_thuc).

    Khoa cache mang dau vet cua CA BA file ma bang kien thuc phu thuoc:
    file CSV, nhom_kb.json (anh xa kich ban -> nhom) va ghi_chep_dieu_tra.json
    (ket luan dieu tra cac ky truoc). Chi theo doi CSV thi sua anh xa nhom
    hoac them ghi chep se khong co tac dung — app tiep tuc phuc vu ban cu ma
    khong bao gi.
    """
    duong_dan = duong_dan or tim_file_moi_nhat()
    return _nap_co_cache(duong_dan,
                         dau_vet(duong_dan),
                         _dau_vet_neu_co(FILE_NHOM),
                         _dau_vet_neu_co(FILE_GHI_CHEP))


def khoi_tao():
    """Dung san cac o trang thai cua phien."""
    st.session_state.setdefault("chat_mo", False)
    st.session_state.setdefault("chat_lich_su", [])     # [{hoi, dap, ...}]
    st.session_state.setdefault("chat_so_luot", 0)
    st.session_state.setdefault("chat_cho_hoi", None)   # cau dang cho tra loi
    st.session_state.setdefault("chat_goi_y", [])


def con_luot():
    return st.session_state.chat_so_luot < SO_LUOT_TOI_DA


def ngu_canh():
    """Vai luot gan nhat, chi giu cau hoi va cau tra loi.

    KHONG giu bang so cu: giu thi prompt phinh ra va model de lan so cua luot
    truoc voi luot nay.
    """
    return [{"hoi": x["hoi"], "dap": x["dap"]}
            for x in st.session_state.chat_lich_su[-SO_LUOT_NHO:]]


def them_luot(hoi, dap, goi_y=None, R=None):
    st.session_state.chat_lich_su.append({
        "hoi": hoi, "dap": dap, "goi_y": goi_y or [],
        "R": R,
    })
    st.session_state.chat_so_luot += 1
    st.session_state.chat_goi_y = goi_y or []


def xoa_lich_su():
    st.session_state.chat_lich_su = []
    st.session_state.chat_goi_y = []
