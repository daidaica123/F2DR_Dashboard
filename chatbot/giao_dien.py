# -*- coding: utf-8 -*-
"""
GIAO DIEN CHAT — nut tron goc phai duoi, bam mo ra panel kieu ChatGPT.

Streamlit khong sinh ra de dung widget noi, nen phai keo khoi chat ra khoi
luong trang roi ghim vao goc man hinh bang CSS.

Cho de sai nhat la SELECTOR. Streamlit boc moi thanh phan trong
div[data-testid="stElementContainer"], moi st.container() trong
div[data-testid="stVerticalBlock"] — nhung do sau long nhau doi theo phien
ban. Viet mot selector duy nhat la dat cuoc; khong khop thi panel roi xuong
day trang, sau ca iframe dashboard cao 3400px, va nguoi dung khong thay dau.

Nen ham _ghim() liet ke BA cach viet cung luc. Chi can mot cai khop la du —
trinh duyet lang le bo qua selector no khong hieu.

He mau lay dung cua dashboard ben trong cho khong choi nhau:
  nen #070b14 · panel #0d1524 · vien #1c2a47 · nhan xanh ngoc #2ee8ff
"""
import re

import streamlit as st


# ══════════════════ LOGO ══════════════════
# Robot trong bong bong chat, ve inline bang SVG. Khong dung file anh ngoai:
# app chay tren Streamlit Cloud, them mot file anh la them mot thu co the
# thieu khi deploy.
_LOGO = """<svg viewBox="0 0 64 64" width="{w}" height="{w}" fill="none"
 xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
<defs>
 <linearGradient id="fg{i}" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#4fe3ff"/><stop offset="1" stop-color="#1568cf"/>
 </linearGradient>
 <linearGradient id="fm{i}" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#1c62c8"/><stop offset="1" stop-color="#0c2a7d"/>
 </linearGradient>
</defs>
<path d="M32 3C17 3 5 13.7 5 27c0 7.6 4 14.3 10.2 18.6l-2.3 9.9c-.3 1.4 1.2
 2.5 2.4 1.7l11.2-6.7c1.8.3 3.6.5 5.5.5 15 0 27-10.7 27-24S47 3 32 3z"
 fill="url(#fg{i})"/>
<circle cx="14.5" cy="12" r="2.5" fill="#8af2ff"/>
<circle cx="49.5" cy="12" r="2.5" fill="#8af2ff"/>
<path d="M14.5 12.5v6.5M49.5 12.5v6.5" stroke="#8af2ff" stroke-width="2.3"
 stroke-linecap="round"/>
<rect x="8" y="20" width="6.5" height="14" rx="3.2" fill="#1568cf"/>
<rect x="49.5" y="20" width="6.5" height="14" rx="3.2" fill="#1568cf"/>
<rect x="13.5" y="15.5" width="37" height="14.5" rx="7.2" fill="#0e3c96"
 opacity=".5"/>
<path d="M21.5 21h11M21.5 24.5h8.5" stroke="#8af2ff" stroke-width="1.7"
 stroke-linecap="round" opacity=".7"/>
<rect x="12.5" y="26" width="39" height="22" rx="10.5" fill="url(#fm{i})"/>
<circle cx="23.5" cy="35.5" r="4.2" fill="#5aecff"/>
<circle cx="40.5" cy="35.5" r="4.2" fill="#5aecff"/>
<rect x="27.5" y="41.5" width="9" height="3.2" rx="1.6" fill="#5aecff"/>
</svg>"""


def logo(kich_thuoc=30, ma="a"):
    """SVG logo robot.

    `ma` phai khac nhau giua cac lan goi tren cung mot trang: hai the <defs>
    trung id se lam gradient cua cai sau de len cai truoc.
    """
    return _LOGO.format(w=kich_thuoc, i=ma)


# ══════════════════ SELECTOR ══════════════════

def _ghim(moc):
    """Ba cach viet de bat khoi Streamlit chua phan tu danh dau `moc`."""
    t = 'div[data-testid="stVerticalBlock"]'
    e = 'div[data-testid="stElementContainer"]'
    return ",\n".join([
        t + ':has(> ' + e + ' .' + moc + ')',
        t + ':has(> div > .' + moc + ')',
        t + ':has(.' + moc + '):not(:has(' + t + ' .' + moc + '))',
    ])


NUT = _ghim("f2dr-nut-moc")        # khoi chi chua nut tron thu gon
KHUNG = _ghim("f2dr-chat-moc")     # khoi panel chat mo rong


_CSS_THAN = """
/* ═══════════ NUT TRON KHI THU GON ═══════════ */
__NUT__{
  position: fixed !important;
  right: 24px; bottom: 24px;
  width: auto !important; min-width: 0 !important;
  z-index: 999991;
  gap: 0 !important; padding: 0 !important;
  background: none !important; border: 0 !important;
}
__NUT__ .stButton button{
  width: 62px !important; height: 62px !important;
  min-height: 62px !important; padding: 0 !important;
  border-radius: 50% !important;
  background: linear-gradient(148deg, #1d86a0, #0d4f66) !important;
  border: 1px solid rgba(46,232,255,.55) !important;
  color: #eafcff !important;
  font-size: 26px !important; line-height: 1 !important;
  box-shadow: 0 9px 28px rgba(0,0,0,.55), 0 0 0 4px rgba(46,232,255,.09) !important;
  transition: transform .16s cubic-bezier(.22,1,.36,1), box-shadow .16s;
}
__NUT__ .stButton button:hover{
  transform: translateY(-3px) scale(1.06);
  box-shadow: 0 14px 34px rgba(0,0,0,.62), 0 0 0 8px rgba(46,232,255,.17) !important;
}
/* vong song lan toa quanh nut, bao la co the bam */
__NUT__:after{
  content:''; position:absolute; inset:-6px; border-radius:50%;
  border:1px solid rgba(46,232,255,.30); pointer-events:none;
  animation: f2dr-song 2.8s ease-out infinite;
}
@keyframes f2dr-song{
  0%{ transform:scale(.94); opacity:.75 }
  70%,100%{ transform:scale(1.22); opacity:0 }
}

/* ═══════════ PANEL CHAT KHI MO ═══════════ */
__KHUNG__{
  position: fixed !important;
  right: 22px; bottom: 22px;
  width: 404px; max-width: calc(100vw - 32px);
  z-index: 999990;
  background: #0d1524 !important;
  border: 1px solid #2a3f6b !important;
  border-radius: 18px;
  box-shadow: 0 20px 54px rgba(0,0,0,.64), 0 0 0 1px rgba(46,232,255,.09);
  padding: 0 !important;
  gap: 0 !important;
  overflow: hidden;
  animation: f2dr-len .24s cubic-bezier(.22,1,.36,1);
}
@keyframes f2dr-len{
  from{ opacity:0; transform: translateY(18px) scale(.97) }
  to  { opacity:1; transform: none }
}

/* ═══════════ THANH TIEU DE ═══════════ */
.f2dr-dau{
  display:flex; align-items:center; gap:11px;
  padding:12px 14px;
  background: linear-gradient(180deg, rgba(46,232,255,.12), rgba(46,232,255,.02));
  border-bottom: 1px solid #1c2a47;
}
.f2dr-dau svg{ flex:none; filter: drop-shadow(0 2px 6px rgba(46,232,255,.28)) }
.f2dr-ten{
  font-size:13.5px; font-weight:700; color:#eef3fe; letter-spacing:.2px;
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
  line-height:1.3;
}
.f2dr-ten small{
  display:block; font-size:10px; font-weight:400; color:#7a88a5;
  font-family: ui-monospace, Consolas, monospace; letter-spacing:0;
  margin-top:1px;
}
.f2dr-cham{
  width:7px; height:7px; border-radius:50%; background:#2ee98a;
  box-shadow:0 0 8px #2ee98a; flex:none; margin-left:auto;
  animation: f2dr-nhay 2.4s infinite;
}
@keyframes f2dr-nhay{ 0%,100%{opacity:1} 50%{opacity:.28} }

/* Nut thu gon (dau tru) — nam de len goc phai thanh tieu de */
__KHUNG__ div[data-testid="stElementContainer"]:has(.f2dr-thu-moc){
  height:0 !important; min-height:0 !important; overflow:visible;
}
__KHUNG__ div[data-testid="stElementContainer"]:has(.f2dr-thu-moc)
 + div[data-testid="stElementContainer"]{
  position:absolute !important; top:13px; right:13px; z-index:6;
  width:28px !important; min-width:0 !important;
}
__KHUNG__ div[data-testid="stElementContainer"]:has(.f2dr-thu-moc)
 + div[data-testid="stElementContainer"] .stButton button{
  width:28px !important; height:28px !important; min-height:28px !important;
  padding:0 !important; border-radius:8px !important;
  background:rgba(10,16,32,.6) !important;
  border:1px solid #2a3f6b !important;
  color:#9fb3d4 !important; font-size:16px !important; line-height:1 !important;
}
__KHUNG__ div[data-testid="stElementContainer"]:has(.f2dr-thu-moc)
 + div[data-testid="stElementContainer"] .stButton button:hover{
  border-color:#2ee8ff !important; color:#2ee8ff !important;
}

/* ═══════════ CHIP PHAM VI ═══════════ */
.f2dr-chip{
  display:inline-block; margin:9px 15px 0;
  font-family: ui-monospace, Consolas, monospace; font-size:10px;
  color:#2ee8ff; background:rgba(46,232,255,.09);
  border:1px solid rgba(46,232,255,.28); border-radius:20px;
  padding:3px 10px;
}

/* ═══════════ VUNG TIN NHAN ═══════════ */
__KHUNG__ div[data-testid="stVerticalBlockBorderWrapper"]{ background:transparent }
.f2dr-khung{ max-height: 44vh; overflow-y:auto; padding:4px 2px 0 }
.f2dr-khung::-webkit-scrollbar{ width:7px }
.f2dr-khung::-webkit-scrollbar-thumb{ background:#1c2a47; border-radius:4px }
.f2dr-khung::-webkit-scrollbar-track{ background:transparent }

.f2dr-hang{ display:flex; margin:9px 13px; gap:8px }
.f2dr-hang.toi{ justify-content:flex-end }
.f2dr-bong{
  max-width: 86%; padding:9px 13px; border-radius:15px;
  font-size:12.8px; line-height:1.62; color:#dbe4f5;
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
  word-wrap:break-word; overflow-wrap:anywhere;
}
.f2dr-bong.bot{
  background:#131d30; border:1px solid #1c2a47;
  border-bottom-left-radius:5px;
}
.f2dr-bong.toi{
  background:linear-gradient(135deg, #1c7386, #15566a);
  color:#f2fbff; border:1px solid #2a94ab;
  border-bottom-right-radius:5px;
}
.f2dr-bong p{ margin:0 0 7px } .f2dr-bong p:last-child{ margin:0 }
.f2dr-bong strong{ color:#2ee8ff; font-weight:700 }
.f2dr-bong.toi strong{ color:#c4f5ff }
.f2dr-bong ul, .f2dr-bong ol{ margin:6px 0; padding-left:19px }
.f2dr-bong li{ margin:2.5px 0 }
.f2dr-bong code{
  font-family: ui-monospace, Consolas, monospace; font-size:11.5px;
  background:#0a1020; padding:1px 5px; border-radius:3px; color:#8ce8ff;
}
.f2dr-bong pre{
  background:#070d18; border:1px solid #1c2a47; border-radius:7px;
  padding:9px 11px; overflow-x:auto; font-size:11px; margin:7px 0;
}

/* Ba cham "dang go" */
.f2dr-go{ display:flex; gap:4px; padding:11px 14px }
.f2dr-go i{
  width:6px; height:6px; border-radius:50%; background:#2ee8ff;
  opacity:.35; animation: f2dr-go 1.25s infinite;
}
.f2dr-go i:nth-child(2){ animation-delay:.18s }
.f2dr-go i:nth-child(3){ animation-delay:.36s }
@keyframes f2dr-go{
  0%,60%,100%{ opacity:.3; transform:translateY(0) }
  30%{ opacity:1; transform:translateY(-4px) }
}

.f2dr-buoc{
  font-family: ui-monospace, Consolas, monospace; font-size:10px;
  color:#5f6f8f; padding:2px 15px 7px;
}

/* Nhan chat luong duoi cau tra loi */
.f2dr-nhan{
  display:flex; align-items:center; gap:7px; flex-wrap:wrap;
  padding:2px 15px 8px;
  font-family: ui-monospace, Consolas, monospace; font-size:9.5px;
}
.f2dr-the{
  border:1px solid #1c2a47; border-radius:4px; padding:1.5px 7px;
  color:#5f6f8f; background:#0a1020;
}
.f2dr-the.tot{ color:#2ee98a; border-color:rgba(46,233,138,.32) }
.f2dr-the.canh{ color:#ff9550; border-color:rgba(255,149,80,.34) }

/* ═══════════ NUT GOI Y ═══════════ */
__KHUNG__ div[data-testid="stHorizontalBlock"]{
  gap:6px !important; padding:0 12px;
}
__KHUNG__ .stButton button{
  background:#111c33 !important; border:1px solid #2a3f6b !important;
  color:#9fb3d4 !important; font-size:10.5px !important;
  padding:5px 11px !important; border-radius:20px !important;
  min-height:0 !important; height:auto !important;
  white-space:normal !important; line-height:1.35 !important;
  transition: all .13s;
}
__KHUNG__ .stButton button:hover{
  border-color:#2ee8ff !important; color:#2ee8ff !important;
  background:rgba(46,232,255,.07) !important;
}

/* ═══════════ O NHAP ═══════════ */
__KHUNG__ div[data-testid="stChatInput"]{
  background:#0a1020 !important; border:1px solid #2a3f6b !important;
  border-radius:22px !important; margin:9px 12px 12px !important;
}
__KHUNG__ div[data-testid="stChatInput"]:focus-within{
  border-color:#2ee8ff !important;
  box-shadow:0 0 0 3px rgba(46,232,255,.11) !important;
}
__KHUNG__ div[data-testid="stChatInput"] textarea{
  color:#eef3fe !important; font-size:12.5px !important;
}
__KHUNG__ div[data-testid="stChatInput"] textarea::placeholder{
  color:#5f6f8f !important;
}

/* Khoi nguon so lieu gap duoc */
__KHUNG__ details{
  margin:0 15px 8px; border:1px solid #1c2a47; border-radius:7px;
  background:#0a1020;
}
__KHUNG__ summary{
  font-family: ui-monospace, Consolas, monospace; font-size:10px;
  color:#7a88a5; padding:6px 10px; cursor:pointer;
}
__KHUNG__ summary:hover{ color:#2ee8ff }

/* Man hinh hep: panel chiem gan het be ngang */
@media (max-width: 640px){
  __KHUNG__{ right:10px; left:10px; bottom:10px; width:auto }
  .f2dr-khung{ max-height:50vh }
  __NUT__{ right:16px; bottom:16px }
}
@media (prefers-reduced-motion: reduce){
  __KHUNG__, __NUT__:after, .f2dr-cham, .f2dr-go i{ animation:none !important }
}
"""

CSS = ("<style>\n"
       + _CSS_THAN.replace("__NUT__", NUT).replace("__KHUNG__", KHUNG)
       + "\n</style>")


def bat_css():
    st.markdown(CSS, unsafe_allow_html=True)


def moc(ten="f2dr-chat-moc"):
    """Neo de CSS nhan ra khoi. Phai dat dau tien trong container."""
    st.markdown('<div class="%s"></div>' % ten, unsafe_allow_html=True)


def dau_trang(kt):
    """Thanh tieu de: logo robot, ten, dai ngay, cham bao dang song."""
    st.markdown(
        '<div class="f2dr-dau">' + logo(32, "dau")
        + '<span class="f2dr-ten">Trợ lý F2DR'
          '<small>%s ngày · %s alert · %s</small></span>'
          '<span class="f2dr-cham"></span></div>' % (
              kt["so_ngay"],
              "{:,}".format(kt["tong_alert"]).replace(",", "."),
              kt["ngay_dau"][5:].replace("-", "/") + " – "
              + kt["ngay_cuoi"][5:].replace("-", "/")),
        unsafe_allow_html=True)


def chip(van_ban):
    st.markdown('<div class="f2dr-chip">%s</div>' % van_ban,
                unsafe_allow_html=True)


def bong_bong(vai, noi_dung_html):
    la_toi = (vai == "toi")
    st.markdown(
        '<div class="f2dr-hang %s"><div class="f2dr-bong %s">%s</div></div>'
        % ("toi" if la_toi else "", "toi" if la_toi else "bot", noi_dung_html),
        unsafe_allow_html=True)


def dang_go():
    st.markdown('<div class="f2dr-hang"><div class="f2dr-bong bot">'
                '<span class="f2dr-go"><i></i><i></i><i></i></span>'
                '</div></div>', unsafe_allow_html=True)


def nhan_chat_luong(R):
    """Dong nhan duoi cau tra loi: ket qua kiem chung, so buoc, thoi gian."""
    the = []
    kc = R.kiem_chung or {}
    if kc.get("dat") and kc.get("so_da_kiem"):
        the.append(("tot", "✓ %d số đã đối chiếu" % kc["so_da_kiem"]))
    elif getattr(R, "da_bo_dien_giai", False):
        the.append(("canh", "⚠ đã bỏ phần diễn giải"))
    elif kc.get("dat") and not kc.get("so_da_kiem"):
        # Khong kiem duoc so nao ma cau tra loi van co chu so: noi ro ra,
        # de trong thi nguoi doc tuong la "da kiem sach".
        if re.search(r"\d", getattr(R, "cau_tra_loi", "") or ""):
            the.append(("canh", "⚠ không đối chiếu được số nào"))
    if R.cac_buoc:
        the.append(("", "%d bước" % len(R.cac_buoc)))
    the.append(("", "%.1fs" % R.thoi_gian))
    if R.nguon_web:
        the.append(("", "%d nguồn web" % len(R.nguon_web)))

    st.markdown('<div class="f2dr-nhan">%s</div>' % "".join(
        '<span class="f2dr-the %s">%s</span>' % (c, t) for c, t in the),
        unsafe_allow_html=True)
