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
import subprocess
import sys
import tempfile
from datetime import datetime

import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "F2DR_Van_Hanh.html")
BUILD = os.path.join(HERE, "_build", "build_van_hanh.py")
DATA = os.path.join(HERE, "data")

# _build không phải package (không có __init__.py) nên phải thêm vào đường
# tìm module. Lấy hàm ghep() từ đó thay vì chép lại — chép lại là mở đường
# cho bản deploy lệch khỏi bản xem trước.
sys.path.insert(0, os.path.join(HERE, "_build"))
import xem_truoc                             # noqa: E402

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
  /* Huy hiệu Streamlit ở góc phải dưới đè lên nút chat của dashboard. Tên
     data-testid đổi theo phiên bản nên liệt kê mấy cách viết cùng lúc —
     trình duyệt lặng lẽ bỏ qua selector nó không hiểu. Đây chỉ là lớp thứ
     hai: nút chat tự nâng lên khi biết mình nằm trong iframe (lớp f2-nhung
     trong _chat_ui.js), nên dù Streamlit đổi tên lần nữa vẫn không bị che. */
  [data-testid="stAppViewerBadge"], [data-testid="stStatusWidget"],
  .viewerBadge_container__1QSob, .stAppViewerBadge,
  a[href^="https://streamlit.io/cloud"]{display:none !important}
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


def khoa_api():
    """Khoá Gemini cho trợ lý, lấy từ Streamlit Secrets.

    Nhận cả hai cách viết trong Secrets:
        GEMINI_API_KEYS = ["...", "...", ...]   ← nhiều khoá, nên dùng cách này
        GEMINI_API_KEY  = "..."                 ← một khoá

    Mỗi khoá là một project riêng nên có hạn mức riêng; trợ lý tự xoay sang
    khoá kế tiếp khi một cặp (khoá, model) hết lượt trong ngày.

    Khoá KHÔNG BAO GIỜ nằm trong repo. Trên máy thì đọc từ
    .streamlit/secrets.toml (đã gitignore), trên web thì đọc từ ô Secrets
    của Streamlit Cloud.
    """
    ds = []
    try:                                    # chưa cấu hình secrets thì st.secrets ném lỗi
        nhieu = st.secrets.get("GEMINI_API_KEYS")
        if nhieu:
            ds = [k for k in list(nhieu) if k]
        mot = st.secrets.get("GEMINI_API_KEY")
        if mot and mot not in ds:
            ds.insert(0, mot)
    except Exception:
        pass
    if not ds and os.environ.get("GEMINI_API_KEY"):
        ds = [os.environ["GEMINI_API_KEY"]]
    return ds


def nhung(html):
    """Nhúng dashboard (đã kèm trợ lý) vào trang, chiếm trọn chiều cao màn hình.

    Chiều cao phải là 100vh chứ KHÔNG phải một số pixel cố định. Nút chat
    dùng position:fixed, mà mốc của position:fixed là khung nhìn của chính
    iframe — iframe cao 3400px thì nút rơi xuống tận đáy 3400px đó, người
    dùng cuộn mỏi tay mới thấy. Cho iframe đúng bằng màn hình thì dashboard
    tự cuộn bên trong và nút nằm đúng góc phải dưới như bản HTML.

    Dùng srcdoc chứ KHÔNG dùng components.html() (Streamlit bọc thêm một lớp
    iframe nữa, hai lớp lồng nhau làm thanh cuộn trong ngoài đá nhau) và cũng
    KHÔNG dùng data: URL nữa.

    Vì sao bỏ data: URL — đã trả giá: Chrome chặn data: URL quá ~2 MB. Kỳ 7
    ngày thì HTML chỉ 520 KB nên chạy tốt, nhưng kỳ 67 ngày làm HTML lên
    4,96 MB, base64 thành 6,63 MB → trình duyệt lặng lẽ từ chối tải, iframe
    TRẮNG TRƠN mà không báo lỗi gì. srcdoc không có giới hạn kích thước.
    """
    # srcdoc nằm trong thuộc tính HTML nên phải escape " & < >, nếu không một
    # dấu nháy kép trong dashboard sẽ cắt đứt thuộc tính giữa chừng.
    an = (html.replace("&", "&amp;").replace('"', "&quot;")
              .replace("<", "&lt;").replace(">", "&gt;"))
    st.markdown(
        f'<iframe srcdoc="{an}" '
        f'style="width:100%;height:calc(100vh - 3.2rem);border:0;display:block" '
        f'sandbox="allow-scripts allow-same-origin allow-popups"></iframe>',
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
        st.caption("File tải về là dashboard thuần — không kèm trợ lý, "
                   "vì kèm thì khoá API đi theo file luôn.")

    st.divider()
    # Trạng thái khoá: thiếu khoá thì trợ lý mở ra được nhưng hỏi gì cũng
    # chịu. Nói thẳng ở đây, đừng để người dùng ngồi đoán.
    _k = khoa_api()
    if _k:
        st.markdown("**Trợ lý hỏi đáp**  \n✅ %d khoá (%s)"
                    % (len(_k), ", ".join("…" + k[-4:] for k in _k)))
    else:
        st.markdown("**Trợ lý hỏi đáp**  \n⚠️ chưa có khoá API")
        st.caption("Dán khoá vào Settings → Secrets:  \n"
                   "`GEMINI_API_KEYS = [\"khoa1\", \"khoa2\"]`")

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
        "Dashboard là HTML tĩnh: lọc, sắp xếp và tính điểm đều chạy ngay "
        "trong trình duyệt. Chỉ khi hỏi trợ lý mới có một lượt gọi ra "
        "Gemini; số liệu trong câu trả lời vẫn lấy từ dữ liệu của trang."
    )

# ══════════ NỘI DUNG ══════════
if not os.path.exists(HTML):
    st.error("Chưa có file `F2DR_Van_Hanh.html`.")
    st.markdown(
        "Upload một file CSV alert ở thanh bên rồi bấm **Dựng lại dashboard**, "
        "hoặc chạy tại máy:\n\n"
        "```\npy -3.10 _build/build_van_hanh.py --csv data/<file>.csv\n```")
    st.stop()

# ══════════ DASHBOARD + TRỢ LÝ ══════════
#
# Trợ lý được ghép vào dashboard NGAY LÚC CHẠY, bằng đúng hàm mà bản xem
# trước dùng (_build/xem_truoc.py: ghep). Nhờ vậy bản deploy và bản HTML mở
# bằng trình duyệt là một, không thể lệch nhau: cùng _chat_ui.html, cùng ba
# file JS, cùng thứ tự nạp.
#
# Khác biệt duy nhất: khoá API không nằm trong file trên đĩa mà lấy từ
# Streamlit Secrets, nên repo không bao giờ chứa khoá.
try:
    ra = xem_truoc.ghep(doc_html(HTML), khoa_api())
except Exception as e:                      # ghép hỏng thì vẫn còn dashboard
    st.warning("Không ghép được trợ lý — dashboard vẫn dùng bình thường.")
    st.caption(str(e))
    ra = doc_html(HTML)

nhung(ra)
