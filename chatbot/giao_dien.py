# -*- coding: utf-8 -*-
"""
GIAO DIEN CHAT — panel noi goc phai duoi, kieu ChatGPT / Intercom.

Streamlit khong sinh ra de dung widget noi, nen phan CSS o day co viec keo
khoi chat ra khoi luong trang binh thuong roi ghim vao goc man hinh. Cach
lam: boc toan bo chat trong mot container co class rieng, roi dung CSS
:has() de nhan dien va dinh vi lai.

He mau lay dung cua dashboard ben trong cho khong choi nhau:
  nen #070b14 · panel #0d1524 · vien #1c2a47 · nhan xanh ngoc #2ee8ff
"""
import streamlit as st

CSS = """
<style>
/* ═══════════ PANEL CHAT NOI ═══════════ */

/* Khoi bao ngoai: ghim goc phai duoi, tren cung moi thu khac.

   Selector KHONG duoc phu thuoc do sau DOM. Ban dau viet
   ":has(> div > div > div > .f2dr-chat-moc)" — dung ba cap div — va no
   khop hay khong la tuy phien ban Streamlit. Khong khop thi panel roi xuong
   DUOI CUNG trang, sau ca iframe cao 3400px: nguoi dung khong thay dau ca.

   Cach viet duoi day doc lap do sau:
     :has(.f2dr-chat-moc)                    -> moi khoi to bao ngoai deu khop
     :not(:has(<khoi con> .f2dr-chat-moc))   -> loai het, chi con khoi TRONG CUNG
*/
div[data-testid="stVerticalBlock"]:has(.f2dr-chat-moc):not(:has(div[data-testid="stVerticalBlock"] .f2dr-chat-moc)){
  position: fixed !important;
  right: 22px; bottom: 22px;
  width: 400px; max-width: calc(100vw - 32px);
  z-index: 999990;
  background: #0d1524;
  border: 1px solid #2a3f6b;
  border-radius: 16px;
  box-shadow: 0 18px 50px rgba(0,0,0,.62), 0 0 0 1px rgba(46,232,255,.09);
  padding: 0 !important;
  gap: 0 !important;
  overflow: hidden;
  animation: f2dr-len .22s cubic-bezier(.22,1,.36,1);
}
@keyframes f2dr-len{
  from{ opacity:0; transform: translateY(14px) scale(.985) }
  to  { opacity:1; transform: none }
}
@media (prefers-reduced-motion: reduce){
  div[data-testid="stVerticalBlock"]:has(.f2dr-chat-moc):not(:has(div[data-testid="stVerticalBlock"] .f2dr-chat-moc)){
    animation: none }
}

/* Thanh tieu de */
.f2dr-dau{
  display:flex; align-items:center; gap:10px;
  padding:13px 15px;
  background: linear-gradient(180deg, rgba(46,232,255,.10), rgba(46,232,255,.03));
  border-bottom: 1px solid #1c2a47;
}
.f2dr-cham{
  width:9px; height:9px; border-radius:50%; background:#2ee98a;
  box-shadow:0 0 8px #2ee98a; flex:none;
  animation: f2dr-nhay 2.4s infinite;
}
@keyframes f2dr-nhay{ 0%,100%{opacity:1} 50%{opacity:.35} }
.f2dr-ten{
  font-size:13.5px; font-weight:700; color:#eef3fe; letter-spacing:.2px;
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
}
.f2dr-phu{
  font-size:10.5px; color:#7a88a5; margin-left:auto; text-align:right;
  font-family: ui-monospace, 'Cascadia Code', Consolas, monospace;
  line-height:1.35;
}

/* Chip pham vi dang loc */
.f2dr-chip{
  display:inline-block; margin:9px 15px 0;
  font-family: ui-monospace, Consolas, monospace; font-size:10px;
  color:#2ee8ff; background:rgba(46,232,255,.09);
  border:1px solid rgba(46,232,255,.28); border-radius:20px;
  padding:3px 10px;
}

/* Vung tin nhan */
div[data-testid="stVerticalBlock"]:has(.f2dr-chat-moc):not(:has(div[data-testid="stVerticalBlock"] .f2dr-chat-moc))
  div[data-testid="stVerticalBlockBorderWrapper"]{ background:transparent }

.f2dr-khung{ max-height: 46vh; overflow-y:auto; padding:4px 4px 0 }
.f2dr-khung::-webkit-scrollbar{ width:7px }
.f2dr-khung::-webkit-scrollbar-thumb{ background:#1c2a47; border-radius:4px }
.f2dr-khung::-webkit-scrollbar-track{ background:transparent }

/* Bong bong */
.f2dr-hang{ display:flex; margin:9px 13px }
.f2dr-hang.toi{ justify-content:flex-end }
.f2dr-bong{
  max-width: 86%; padding:9px 13px; border-radius:14px;
  font-size:12.8px; line-height:1.62; color:#dbe4f5;
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
  word-wrap:break-word; overflow-wrap:anywhere;
}
.f2dr-bong.bot{
  background:#131d30; border:1px solid #1c2a47;
  border-bottom-left-radius:5px;
}
.f2dr-bong.toi{
  background:linear-gradient(135deg, #1c6f83, #16596b);
  color:#f2fbff; border:1px solid #2a8fa6;
  border-bottom-right-radius:5px;
}
.f2dr-bong p{ margin:0 0 7px } .f2dr-bong p:last-child{ margin:0 }
.f2dr-bong strong{ color:#2ee8ff; font-weight:700 }
.f2dr-bong.toi strong{ color:#bdf3ff }
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

/* Dong trang thai khi bot dang chay cac buoc */
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

/* Nut goi y */
div[data-testid="stVerticalBlock"]:has(.f2dr-chat-moc):not(:has(div[data-testid="stVerticalBlock"] .f2dr-chat-moc))
  div[data-testid="stHorizontalBlock"]{ gap:6px !important; padding:0 12px }
div[data-testid="stVerticalBlock"]:has(.f2dr-chat-moc):not(:has(div[data-testid="stVerticalBlock"] .f2dr-chat-moc))
  .stButton button{
  background:#111c33 !important; border:1px solid #2a3f6b !important;
  color:#9fb3d4 !important; font-size:10.5px !important;
  padding:4px 10px !important; border-radius:20px !important;
  min-height:0 !important; height:auto !important;
  white-space:normal !important; line-height:1.35 !important;
  transition: all .13s;
}
div[data-testid="stVerticalBlock"]:has(.f2dr-chat-moc):not(:has(div[data-testid="stVerticalBlock"] .f2dr-chat-moc))
  .stButton button:hover{
  border-color:#2ee8ff !important; color:#2ee8ff !important;
  background:rgba(46,232,255,.07) !important;
}

/* O nhap */
div[data-testid="stVerticalBlock"]:has(.f2dr-chat-moc):not(:has(div[data-testid="stVerticalBlock"] .f2dr-chat-moc))
  div[data-testid="stChatInput"]{
  background:#0a1020 !important; border:1px solid #2a3f6b !important;
  border-radius:22px !important; margin:9px 12px 12px !important;
}
div[data-testid="stVerticalBlock"]:has(.f2dr-chat-moc):not(:has(div[data-testid="stVerticalBlock"] .f2dr-chat-moc))
  div[data-testid="stChatInput"]:focus-within{
  border-color:#2ee8ff !important;
  box-shadow:0 0 0 3px rgba(46,232,255,.11) !important;
}
div[data-testid="stVerticalBlock"]:has(.f2dr-chat-moc):not(:has(div[data-testid="stVerticalBlock"] .f2dr-chat-moc))
  div[data-testid="stChatInput"] textarea{
  color:#eef3fe !important; font-size:12.5px !important;
}
div[data-testid="stVerticalBlock"]:has(.f2dr-chat-moc):not(:has(div[data-testid="stVerticalBlock"] .f2dr-chat-moc))
  div[data-testid="stChatInput"] textarea::placeholder{ color:#5f6f8f !important }

/* Khoi nguon so lieu gap duoc */
div[data-testid="stVerticalBlock"]:has(.f2dr-chat-moc):not(:has(div[data-testid="stVerticalBlock"] .f2dr-chat-moc))
  details{
  margin:0 15px 8px; border:1px solid #1c2a47; border-radius:7px;
  background:#0a1020;
}
div[data-testid="stVerticalBlock"]:has(.f2dr-chat-moc):not(:has(div[data-testid="stVerticalBlock"] .f2dr-chat-moc))
  summary{
  font-family: ui-monospace, Consolas, monospace; font-size:10px;
  color:#7a88a5; padding:6px 10px; cursor:pointer;
}
div[data-testid="stVerticalBlock"]:has(.f2dr-chat-moc):not(:has(div[data-testid="stVerticalBlock"] .f2dr-chat-moc))
  summary:hover{ color:#2ee8ff }

/* Man hinh hep: panel chiem gan het be ngang */
@media (max-width: 640px){
  div[data-testid="stVerticalBlock"]:has(.f2dr-chat-moc):not(:has(div[data-testid="stVerticalBlock"] .f2dr-chat-moc)){
    right:10px; left:10px; bottom:10px; width:auto;
  }
  .f2dr-khung{ max-height:52vh }
}
</style>
"""


def bat_css():
    st.markdown(CSS, unsafe_allow_html=True)


def moc():
    """Neo de CSS nhan ra khoi chat. Phai dat dau tien trong container."""
    st.markdown('<div class="f2dr-chat-moc"></div>', unsafe_allow_html=True)


def dau_trang(kt, dang_chay=False):
    st.markdown(
        '<div class="f2dr-dau">'
        '<span class="f2dr-cham"></span>'
        '<span class="f2dr-ten">Trợ lý F2DR</span>'
        '<span class="f2dr-phu">%s ngày · %s alert<br>%s</span>'
        '</div>' % (kt["so_ngay"], f'{kt["tong_alert"]:,}'.replace(",", "."),
                    kt["ngay_dau"][5:].replace("-", "/") + " – "
                    + kt["ngay_cuoi"][5:].replace("-", "/")),
        unsafe_allow_html=True)


def chip(van_ban):
    st.markdown('<div class="f2dr-chip">%s</div>' % van_ban,
                unsafe_allow_html=True)


def bong_bong(vai, noi_dung_html):
    st.markdown(
        '<div class="f2dr-hang %s"><div class="f2dr-bong %s">%s</div></div>'
        % ("toi" if vai == "toi" else "", "toi" if vai == "toi" else "bot",
           noi_dung_html),
        unsafe_allow_html=True)


def dang_go():
    st.markdown('<div class="f2dr-hang"><div class="f2dr-bong bot">'
                '<span class="f2dr-go"><i></i><i></i><i></i></span>'
                '</div></div>', unsafe_allow_html=True)


def nhan_chat_luong(R):
    """Dong nhan duoi cau tra loi: thoi gian, so buoc, ket qua kiem chung."""
    the = []
    kc = R.kiem_chung or {}
    if kc.get("dat") and kc.get("so_da_kiem"):
        the.append(('tot', "✓ %d số đã đối chiếu" % kc["so_da_kiem"]))
    elif R.da_bo_dien_giai:
        the.append(('canh', "⚠ đã bỏ phần diễn giải"))
    elif kc.get("dat") and not kc.get("so_da_kiem"):
        # Khong kiem duoc so nao. Neu cau tra loi co chua chu so thi day la
        # dieu dang ngo — phai noi ro, khong duoc de trong lam nguoi doc
        # tuong la "da kiem sach".
        import re as _re
        if _re.search(r"\d", getattr(R, "cau_tra_loi", "") or ""):
            the.append(('canh', "⚠ không đối chiếu được số nào"))
    if R.cac_buoc:
        the.append(('', "%d bước" % len(R.cac_buoc)))
    the.append(('', "%.1fs" % R.thoi_gian))
    if R.nguon_web:
        the.append(('', "%d nguồn web" % len(R.nguon_web)))

    st.markdown('<div class="f2dr-nhan">%s</div>' % "".join(
        '<span class="f2dr-the %s">%s</span>' % (c, t) for c, t in the),
        unsafe_allow_html=True)
