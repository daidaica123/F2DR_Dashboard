# -*- coding: utf-8 -*-
"""
F2DR VẬN HÀNH — app Streamlit bọc dashboard HTML.

Dashboard là một file HTML tĩnh dựng sẵn (biểu đồ, bảng, bộ lọc đều chạy bằng
JavaScript trong trình duyệt). App này chỉ làm 3 việc:
  1. Nhúng file HTML đó vào trang
  2. Cho tải file về để mở offline / gửi cho người khác
  3. Cho upload CSV alert mới → dựng lại dashboard ngay trên web

Chạy tại máy:   streamlit run app.py
"""
import os
import base64
import subprocess
import sys
import tempfile
from datetime import datetime

import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "F2DR_Van_Hanh.html")
BUILD = os.path.join(HERE, "_build", "build_van_hanh.py")
DATA = os.path.join(HERE, "data")

st.set_page_config(page_title="F2DR Vận hành",
                   page_icon="🛡️", layout="wide",
                   initial_sidebar_state="collapsed")

# Giao diện khung Streamlit — đặt thẳng ở đây thay vì .streamlit/config.toml,
# để repo không cần thư mục ẩn (Windows không kéo thả được folder tên có dấu chấm).
# Màu lấy đúng hệ màu của dashboard bên trong cho khỏi chỏi nhau.
st.markdown("""
<style>
  /* Chừa đúng chiều cao thanh công cụ Streamlit (~3rem) rồi mới tới dashboard —
     để nguyên padding:0 thì thanh đó đè lên tiêu đề, nhìn như một dải tối. */
  .block-container{padding:3.2rem 0 0 !important;max-width:100% !important}
  /* Thanh công cụ: trong suốt, chỉ còn mấy nút nổi lên trên nền chung */
  header[data-testid="stHeader"]{background:transparent;height:3rem}
  [data-testid="stToolbar"]{background:transparent}
  #MainMenu, footer{visibility:hidden}
  .stApp{background:#070b14;color:#eef3fe}
  section[data-testid="stSidebar"]{background:#0b1120;border-right:1px solid #1c2a47}
  section[data-testid="stSidebar"] *{color:#eef3fe}
  section[data-testid="stSidebar"] hr{border-color:#1c2a47}
  /* nút, ô upload: bám hệ màu xanh ngọc của dashboard */
  .stButton button, .stDownloadButton button{
    background:#111c33;border:1px solid #2a3f6b;color:#eef3fe}
  .stButton button:hover, .stDownloadButton button:hover{
    border-color:#2ee8ff;color:#2ee8ff}
  .stButton button[kind="primary"]{
    background:rgba(46,232,255,.14);border-color:#2ee8ff;color:#2ee8ff}
  [data-testid="stFileUploaderDropzone"]{
    background:#0e1628;border:1px dashed #2a3f6b}
</style>
""", unsafe_allow_html=True)


def doc_html(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def nhung(html, cao=3400):
    """Nhúng dashboard vào trang.

    Dùng srcdoc thay vì components.html() để tránh Streamlit bọc thêm một lớp
    iframe nữa — hai lớp lồng nhau làm thanh cuộn trong ngoài đá nhau.
    """
    b64 = base64.b64encode(html.encode("utf-8")).decode("ascii")
    st.markdown(
        f'<iframe src="data:text/html;base64,{b64}" '
        f'style="width:100%;height:{cao}px;border:0;display:block" '
        f'sandbox="allow-scripts allow-same-origin"></iframe>',
        unsafe_allow_html=True)


# ══════════ THANH BÊN ══════════
with st.sidebar:
    st.markdown("### 🛡️ F2DR Vận hành")
    st.caption("Theo dõi alert định kỳ hằng tuần")

    if os.path.exists(HTML):
        t = datetime.fromtimestamp(os.path.getmtime(HTML))
        kb = os.path.getsize(HTML) / 1024
        st.markdown(f"**Bản đang xem**  \n{t:%d/%m/%Y %H:%M} · {kb:,.0f} KB")
        with open(HTML, "rb") as f:
            st.download_button("⬇️ Tải file HTML", f, "F2DR_Van_Hanh.html",
                               "text/html", use_container_width=True)

    st.divider()
    st.markdown("**Dựng lại từ CSV mới**")
    up = st.file_uploader("File alert đã clean (.csv)", type="csv",
                          label_visibility="collapsed")
    if up is not None:
        if st.button("🔨 Dựng lại dashboard", type="primary",
                     use_container_width=True):
            with st.spinner("Đang dựng…"):
                tmp = os.path.join(tempfile.gettempdir(), up.name)
                with open(tmp, "wb") as f:
                    f.write(up.getbuffer())
                r = subprocess.run(
                    [sys.executable, BUILD, "--csv", tmp, "--out", HTML],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace")
            if r.returncode == 0:
                st.success("Xong. Đang tải lại…")
                st.code(r.stdout[-600:] or "(không có log)")
                st.rerun()
            else:
                st.error("Dựng lỗi")
                st.code((r.stderr or r.stdout)[-1500:])

    st.divider()
    st.caption(
        "Dashboard là HTML tĩnh, mọi thao tác lọc và tính điểm chạy ngay "
        "trong trình duyệt — không gọi về server."
    )

# ══════════ NỘI DUNG ══════════
if not os.path.exists(HTML):
    st.error("Chưa có file `F2DR_Van_Hanh.html`.")
    st.markdown(
        "Upload một file CSV alert ở thanh bên rồi bấm **Dựng lại dashboard**, "
        "hoặc chạy tại máy:\n\n"
        "```\npy -3.10 _build/build_van_hanh.py --csv data/<file>.csv\n```")
    st.stop()

nhung(doc_html(HTML))

# ══════════ TRỢ LÝ HỎI ĐÁP ══════════
# Panel chat nổi ở góc phải dưới. Toàn bộ việc gọi Gemini chạy ở server này,
# nên khoá API không bao giờ xuống trình duyệt.
try:
    from chatbot import khung_chat
    khung_chat.ve()
except Exception as e:                      # chat hỏng thì dashboard vẫn chạy
    st.session_state.setdefault("_loi_chat_da_bao", False)
    if not st.session_state["_loi_chat_da_bao"]:
        st.session_state["_loi_chat_da_bao"] = True
        st.caption("Trợ lý hỏi đáp chưa sẵn sàng: %s" % e)
