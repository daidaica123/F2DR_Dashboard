# -*- coding: utf-8 -*-
"""
KHUNG CHAT — ghep giao dien voi tro ly.

Ve panel noi goc phai duoi, nhan cau hoi, goi tro_ly.hoi(), hien ket qua
kem nhan chat luong va khoi "nguon so lieu" gap duoc.
"""
import html
import json
import re

import streamlit as st

from . import giao_dien as GD
from . import phien as PH
from . import tro_ly as TL
from .nap import LoiDuLieu

GOI_Y_DAU = [
    "Kịch bản nào nhiều alert nhất?",
    "Ngày nào bất thường?",
    "Khách nào bị bắn nhiều nhất?",
    "Có kịch bản nào im lặng không?",
]


def _md(s):
    """Markdown rat gon -> HTML. Chi ho tro nhung gi bot thuc su dung.

    Tu viet thay vi keo thu vien: chi can dam, code, gach dau dong va xuong
    dong. Va quan trong hon, phai thoat HTML TRUOC de noi dung tu model
    khong chen duoc the la vao trang.
    """
    s = html.escape(s)

    # khoi code ```...```
    s = re.sub(r"```(?:\w+)?\n(.*?)```", r"<pre>\1</pre>", s, flags=re.S)
    s = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s, flags=re.S)
    s = re.sub(r"(?<![\*\w])\*(?!\s)([^\*\n]+?)(?<!\s)\*(?![\*\w])",
               r"<em>\1</em>", s)

    # gach dau dong
    dong = s.split("\n")
    ra, trong_ds = [], False
    for d in dong:
        m = re.match(r"^\s*[-*•]\s+(.*)$", d)
        if m:
            if not trong_ds:
                ra.append("<ul>")
                trong_ds = True
            ra.append("<li>%s</li>" % m.group(1))
        else:
            if trong_ds:
                ra.append("</ul>")
                trong_ds = False
            ra.append(d)
    if trong_ds:
        ra.append("</ul>")
    s = "\n".join(ra)

    # doan van. Giu <pre> nguyen ven: xuong dong trong khoi code la that,
    # doi thanh <br> se lam hong thut le.
    kho = []

    def _cat(m):
        kho.append(m.group(0))
        return "\x00%d\x00" % (len(kho) - 1)

    s = re.sub(r"<pre>.*?</pre>", _cat, s, flags=re.S)

    s = re.sub(r"\n{2,}", "</p><p>", s)
    s = s.replace("\n", "<br>")
    s = "<p>%s</p>" % s

    # go <br> bam quanh cac the khoi — chung tu xuong dong roi
    s = re.sub(r"(<br>\s*)+(</?(?:ul|ol|li|pre)>)", r"\2", s)
    s = re.sub(r"(</?(?:ul|ol|li|pre)>)(\s*<br>)+", r"\1", s)
    s = s.replace("<p><ul>", "<ul>").replace("</ul></p>", "</ul>")
    s = s.replace("<p><ol>", "<ol>").replace("</ol></p>", "</ol>")
    s = re.sub(r"<p>\s*</p>", "", s)

    for i, k in enumerate(kho):
        s = s.replace("\x00%d\x00" % i, k)
    s = s.replace("<p><pre>", "<pre>").replace("</pre></p>", "</pre>")
    return s


def _khoi_nguon(R):
    """Khoi gap duoc: du kien goc + code bot tu viet + nguon web."""
    if not R or not R.du_kien:
        return

    with st.expander("▸ nguồn số liệu", expanded=False):
        for b in R.cac_buoc:
            kq = b.get("ket_qua", {})
            if kq.get("_loi"):
                continue
            st.caption(kq.get("_mo_ta", b["mo_ta"]))
            if kq.get("_code"):
                st.code(kq["_code"], language="python")
            st.json({k: v for k, v in kq.items() if not k.startswith("_")},
                    expanded=False)
        for x in R.nguon_web:
            st.markdown("- [%s](%s)" % (x["tieu_de"][:70], x["url"]))


def _tra_loi(cau_hoi, d, kt):
    """Goi tro ly va hien ket qua."""
    o_go = st.empty()
    with o_go.container():
        GD.dang_go()

    o_buoc = st.empty()

    def _log(s):
        o_buoc.markdown('<div class="f2dr-buoc">%s</div>' % html.escape(s[:88]),
                        unsafe_allow_html=True)

    try:
        R = TL.hoi(cau_hoi, d, kt, lich_su=PH.ngu_canh(), ghi_log=_log)
    except Exception as e:
        o_go.empty()
        o_buoc.empty()
        loi = "Có lỗi khi xử lý câu hỏi: %s" % e
        GD.bong_bong("bot", _md(loi))
        PH.them_luot(cau_hoi, loi)
        return

    o_go.empty()
    o_buoc.empty()

    van, goi_y = TL.tach_goi_y(R.cau_tra_loi)
    GD.bong_bong("bot", _md(van))
    GD.nhan_chat_luong(R)
    _khoi_nguon(R)
    PH.them_luot(cau_hoi, van, goi_y, R)


def _nut_tron():
    """Trang thai THU GON: chi mot nut tron o goc phai duoi."""
    with st.container():
        GD.moc("f2dr-nut-moc")
        if st.button("💬", key="f2dr_mo", help="Mở trợ lý hỏi đáp"):
            st.session_state.chat_mo = True
            st.rerun()


def ve():
    """Ve tro ly: nut tron khi thu gon, panel day du khi mo."""
    PH.khoi_tao()
    GD.bat_css()

    if not st.session_state.chat_mo:
        _nut_tron()
        return

    try:
        d, kt = PH.nap_du_lieu()
    except LoiDuLieu as e:
        st.caption("Trợ lý chưa dùng được — dữ liệu lỗi: %s" % e)
        return

    with st.container():
        GD.moc("f2dr-chat-moc")
        GD.dau_trang(kt)

        # Nut thu gon. Moc dat NGAY TRUOC nut de CSS bat bang selector anh em
        # (+) — chinh xac hon nhieu so voi do tim theo do sau DOM.
        GD.moc("f2dr-thu-moc")
        if st.button("−", key="f2dr_thu", help="Thu gọn"):
            st.session_state.chat_mo = False
            st.rerun()

        # ── vung tin nhan ──
        st.markdown('<div class="f2dr-khung">', unsafe_allow_html=True)

        if not st.session_state.chat_lich_su:
            GD.bong_bong("bot", _md(
                "Chào bạn. Tôi đọc được dữ liệu alert của kỳ này và trả lời "
                "bằng số lấy thẳng từ đó — không đoán.\n\n"
                "Hỏi gì cũng được, hoặc bấm một câu gợi ý bên dưới."))
        else:
            for luot in st.session_state.chat_lich_su:
                GD.bong_bong("toi", _md(luot["hoi"]))
                GD.bong_bong("bot", _md(luot["dap"]))
                if luot.get("R"):
                    GD.nhan_chat_luong(luot["R"])
                    _khoi_nguon(luot["R"])

        # ── cau hoi dang cho tra loi ──
        cho = st.session_state.chat_cho_hoi
        if cho:
            st.session_state.chat_cho_hoi = None
            GD.bong_bong("toi", _md(cho))
            _tra_loi(cho, d, kt)

        st.markdown('</div>', unsafe_allow_html=True)

        # ── nut goi y ──
        goi_y = (st.session_state.chat_goi_y
                 if st.session_state.chat_lich_su else GOI_Y_DAU)
        if goi_y and PH.con_luot():
            cot = st.columns(2)
            for i, g in enumerate(goi_y[:4]):
                if cot[i % 2].button(g, key="gy_%d_%s" % (
                        st.session_state.chat_so_luot, i),
                        use_container_width=True):
                    st.session_state.chat_cho_hoi = g
                    st.rerun()

        # ── o nhap ──
        if PH.con_luot():
            hoi = st.chat_input("Hỏi về dữ liệu kỳ này…", key="f2dr_o_nhap")
            if hoi:
                st.session_state.chat_cho_hoi = hoi
                st.rerun()
        else:
            st.caption("Đã hết %d lượt hỏi của phiên này. Tải lại trang để "
                       "bắt đầu phiên mới." % PH.SO_LUOT_TOI_DA)
