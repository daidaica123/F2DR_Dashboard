# -*- coding: utf-8 -*-
"""
CHAN THONG TIN NHAN THAN.

Du lieu alert thi tra loi thoai mai. Nhung thong tin DINH DANH MOT CON NGUOI
— so dien thoai, CCCD, so tai khoan, ten tuoi, dia chi — thi tuyet doi khong.

Chan o BA TANG, vi mot tang deu co the bi lach:

  Tang 1 — DAU VAO   Bat y do ngay tu cau hoi, TRUOC khi goi LLM.
                     Chay bang luat, khong qua model, nen khong the bi
                     "thuyet phuc" hay danh lua bang cach dien dat khac.

  Tang 2 — DU LIEU   Che cac truong dinh danh trong chi_tiet_alert truoc khi
                     dua cho LLM. LLM khong nhin thay thi khong lo duoc.

  Tang 3 — DAU RA    Quet cau tra loi lan cuoi. Con sot chuoi giong so dien
                     thoai / CCCD thi cat bo.

Tang 1 co the bat nham (chan ca cau hoi vo hai). Chap nhan: tha chan nham
mot cau hoi con hon lo mot so dien thoai.
"""
import re

# ══════════════════ TANG 1: chan y do tu cau hoi ══════════════════

# Tu chi THONG TIN NHAN THAN. Rieng chung thi chua du ket luan.
TU_NHAN_THAN = [
    r"so\s*dien\s*thoai", r"\bsdt\b", r"\bs[dđ]t\b", r"dien\s*thoai",
    r"\bcccd\b", r"can\s*cuoc", r"chung\s*minh\s*(thu|nhan\s*dan)",
    r"\bcmnd\b", r"\bcmt\b", r"giay\s*to\s*tuy\s*than", r"\bgttt\b",
    r"so\s*tai\s*khoan", r"\bstk\b", r"tai\s*khoan\s*ngan\s*hang",
    r"ten\s*(that|khach|nguoi|chu\s*tk)", r"ho\s*(va\s*)?ten",
    r"dia\s*chi", r"ngay\s*sinh", r"nam\s*sinh", r"gioi\s*tinh",
    r"email", r"\bmst\b", r"ma\s*so\s*thue",
    r"thong\s*tin\s*(ca\s*nhan|nhan\s*than|dinh\s*danh)",
    r"danh\s*tinh", r"\bpii\b",
    # Muoi khong phai thong tin nhan than, nhung ai co no la tra nguoc duoc
    # TOAN BO ma bam — nguy hiem hon ca mot so dien thoai le.
    r"\bmuoi\b", r"\bsalt\b",
]

# Tu chi hanh vi MOI RA / TRA NGUOC
TU_MOI_RA = [
    r"cho\s*(toi|minh|tao|tui)?\s*(biet|xem)", r"la\s*(ai|gi|so\s*nao)",
    r"tra\s*(nguoc|ra|cuu)", r"giai\s*ma", r"go\s*(bam|hash)",
    r"\bhash\b", r"\bbam\b", r"khoi\s*phuc", r"\bdecode\b", r"\bdecrypt\b",
    r"in\s*ra", r"liet\s*ke", r"xuat\s*ra", r"hien\s*(thi|ra)",
    r"\bday\s*du\b", r"chi\s*tiet\s*(ve|cua)?\s*khach",
    r"ai\s*la\s*nguoi", r"nguoi\s*nao", r"khach\s*nao\s*la",
    r"tim\s*(ra|duoc)?\s*nguoi", r"lien\s*(he|lac)", r"goi\s*dien",
    r"\bmuoi\b", r"\bsalt\b",
]

# Cum chac chan la khai thac — chan ngay, khong can them dieu kien
CUM_CHAN_NGAY = [
    r"so\s*dien\s*thoai\s*(cua|la|nao)",
    r"sdt\s*(cua|la|nao)",
    r"tra\s*nguoc\s*(ma|hash|bam)",
    r"giai\s*ma\s*(ma|hash|bam)",
    r"(ma|hash|bam)\s*nay\s*la\s*(so|ai|nguoi)",
    r"khach\s*nay\s*la\s*ai",
    r"danh\s*sach\s*so\s*dien\s*thoai",
    r"export.*khach\s*hang",

    # Hoi ve MUOI: ai co muoi la tra nguoc duoc toan bo ma bam, nen day la
    # cau hoi nguy hiem nhat trong tat ca. Bat moi cach dien dat.
    r"\b(muoi|salt)\b.{0,24}\b(la|dung|nao|gi|bao\s*nhieu|o\s*dau)\b",
    r"\b(la|dung|biet|cho|xem|in|noi)\b.{0,16}\b(muoi|salt)\b",
    r"\b(muoi|salt)\b.{0,16}\b(he\s*thong|bam|hash|f2dr)\b",
    r"f2dr_salt",

    # "ma X la ai / la nguoi nao / thuoc ve ai" — doi truy nguoc danh tinh.
    # Phai bat rieng vi "ma ... la ai" khong co tu nhan than nao.
    r"\b(ma|khach|kh|nguoi\s*dung|user|id)\b[^.?!]{0,40}\bla\s*ai\b",
    r"\bla\s*ai\b",
    r"\b(ma|hash|bam)\b[^.?!]{0,40}\b(thuoc\s*ve|ung\s*voi|tuong\s*ung)\b",
    r"\bdanh\s*tinh\s*(cua|that)\b",
]

_RX_NHAN_THAN = [re.compile(p, re.I) for p in TU_NHAN_THAN]
_RX_MOI_RA = [re.compile(p, re.I) for p in TU_MOI_RA]
_RX_CHAN_NGAY = [re.compile(p, re.I) for p in CUM_CHAN_NGAY]


def _bo_dau(s):
    """Bo dau tieng Viet de luat bat duoc ca 'số điện thoại' lan 'so dien thoai'."""
    import unicodedata
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


def kiem_cau_hoi(cau_hoi):
    """Tra ve (co_chan, ly_do). co_chan=True thi KHONG duoc goi LLM.

    Luat, khong dung model — nen khong the bi thuyet phuc hay danh lua bang
    cach dien dat vong vo.
    """
    s = _bo_dau(cau_hoi)

    for rx in _RX_CHAN_NGAY:
        if rx.search(s):
            return True, "hoi truc tiep thong tin dinh danh hoac doi tra nguoc ma"

    co_nhan_than = any(rx.search(s) for rx in _RX_NHAN_THAN)
    co_moi_ra = any(rx.search(s) for rx in _RX_MOI_RA)

    # Hai dau hieu cung xuat hien -> gan nhu chac chan la khai thac
    if co_nhan_than and co_moi_ra:
        return True, "hoi thong tin nhan than cua khach hang"

    # Chi nhac toi thong tin nhan than, khong co dong tu moi ra:
    # van chan, nhung bao nhe hon — vi du "du lieu co so dien thoai khong?"
    if co_nhan_than:
        return True, "cau hoi lien quan thong tin nhan than"

    return False, ""


LOI_TU_CHOI = (
    "Tôi không cung cấp thông tin nhân thân của khách hàng — số điện thoại, "
    "căn cước, số tài khoản, tên hay địa chỉ.\n\n"
    "Dữ liệu trong dashboard đã được **ẩn danh**: mã khách hàng là chuỗi băm "
    "20 ký tự, không tra ngược được về người thật. Đây là ràng buộc cố định "
    "của hệ thống, không phải tuỳ chọn.\n\n"
    "Tôi trả lời được mọi câu về **alert**: kịch bản nào bắn nhiều, ngày nào "
    "bất thường, mã khách nào bị bắn nhiều lần, điểm và ngưỡng Impact, bằng "
    "chứng nghiệp vụ của từng cảnh báo.\n\n"
    "GOI_Y: Kịch bản nào nhiều alert nhất | Mã khách nào bị bắn nhiều nhất | "
    "Ngày nào bất thường"
)


# ══════════════════ TANG 2: che truong dinh danh trong du lieu ══════════════════

# Khoa trong chi_tiet_alert mang tinh DINH DANH. Gia tri da bam roi, nhung
# van che not: dua cho LLM khong duoc loi gi ma con tao co hoi lo lot.
KHOA_DINH_DANH = {
    "tb_duoc_nap", "cccd", "so_gttt", "sdt_kenh", "tk_thu_huong", "dau_moi",
    "doi_tac_stk", "doi_tac", "doi_tac_sdt", "merchant_code", "ma_kenh",
    "nguoi_gui", "kh_duoc_nap", "ds_dich_nhan", "so_dien_thoai", "sdt",
    "stk", "ten_kh", "ho_ten", "dia_chi", "email", "mst", "ngay_sinh",
}

# Khoa NGHIEP VU — giu lai, day moi la thu giup tra loi "vi sao alert no"
# (gia tri giao dich, so lan vuot trung binh, tuoi tai khoan...)


def che_bang_chung(ct):
    """Bo cac truong dinh danh khoi mot dict chi_tiet_alert."""
    if not isinstance(ct, dict):
        return ct
    sach = {}
    da_che = 0
    for k, v in ct.items():
        if _bo_dau(k) in KHOA_DINH_DANH:
            da_che += 1
            continue
        sach[k] = v
    if da_che:
        sach["_da_che"] = "%d truong dinh danh da bi bo" % da_che
    return sach


# ══════════════════ TANG 3: quet cau tra loi ══════════════════

# So dien thoai VN, ca dang 0xxx lan 84xxx
RX_SDT = re.compile(r"(?<![\w])(?:0[35789]\d{8}|84[35789]\d{8}|\+84[35789]\d{8})(?![\w])")
# CCCD 12 so bat dau bang 0
RX_CCCD = re.compile(r"(?<![\w])0\d{2}[0123]\d{8}(?![\w])")
# So tai khoan ngan hang: 9-19 chu so lien tiep, khong phai ngay thang
RX_STK = re.compile(r"(?<![\w.,])\d{9,19}(?![\w.,])")


def quet_cau_tra_loi(van_ban):
    """Tra ve (van_ban_sach, danh_sach_da_cat).

    Lop chan cuoi cung. Ly tuong thi khong bao gio bat duoc gi — neu bat
    duoc nghia la mot trong hai tang tren da lot, can xem lai.
    """
    da_cat = []

    def _cat(m, loai):
        da_cat.append({"loai": loai, "gia_tri": m.group(0)})
        return "[đã ẩn]"

    s = RX_SDT.sub(lambda m: _cat(m, "so dien thoai"), van_ban)
    s = RX_CCCD.sub(lambda m: _cat(m, "cccd"), s)

    # STK: chi cat khi KHONG phai so lieu thong ke. So alert lon nhat cung
    # chi 5-6 chu so, nen 9 chu so tro len gan nhu chac chan la dinh danh.
    s = RX_STK.sub(lambda m: _cat(m, "so tai khoan"), s)

    return s, da_cat
