# -*- coding: utf-8 -*-
"""
TRO LY — vong lap suy luan.

Khac voi kieu "mot cau hoi -> mot truy van -> mot cau tra loi", tro ly nay
di NHIEU BUOC: goi mot ham, doc ket qua, thay chua du thi tu goi tiep, toi
da 4 vong.

Vi du "sao ngay 01/09 it alert the?":
    vong 1  alert_theo_ngay        -> 1.489 alert, 0.67x TB, thap nhat ky
    vong 2  so_sanh_ngay(31/08)    -> giam 500 alert, Blacklist B ve 0
    vong 3  ma_tran_kich_ban_ngay  -> 2 kich ban im lang han
    ket     "khong phai gian lan giam, la 2 kich ban ngung ban - can kiem tra"

Ranh gioi khong bao gio pha:
  - LLM chon HAM va THAM SO, code chay phep tinh. LLM khong tu tinh so.
  - Ham dong san khong phu duoc thi LLM viet code pandas, chay trong hop cat.
  - Moi con so trong cau tra loi phai truy duoc ve du kien. Xem kiem_chung.py
"""
import json
import re
import time

from . import chan_pii as CP
from . import hop_cat as HC
from . import kiem_chung as KC
from . import llm as LLM
from . import truy_van as TV

SO_VONG_TOI_DA = 4
SO_LAN_HONG_LIEN_TIEP = 2       # hong lien tiep bao nhieu lan thi dung han
SO_KY_TU_DU_KIEN_TOI_DA = 24000


# ══════════════════ PROMPT ══════════════════

def _mo_ta_ky(kt):
    """Tom tat ky du lieu — nhet vao prompt de model biet co gi trong tay."""
    kb = "\n".join(
        "    - %s | nhom %s | %s | %d diem goc | %d alert"
        % (k["ten"], k["nhom"], k["muc"], k["diem_goc"], k["alert"])
        for k in kt["kich_ban"])
    nhom = "\n".join(
        "    - %s: %d alert, %d khach, %d/%d kich ban co alert"
        % (n["ten"], n["alert"], n["kh"], n["kb_co_alert"], n["kb_cau_hinh"])
        for n in kt["nhom"])
    return """KY DU LIEU HIEN TAI (doc tu file %s, cap nhat %s):
  - %d ngay: %s den %s
  - %s alert | %s khach hang | %s luot (khach x ngay)
  - %d/%d kich ban co alert
  - Tham so diem dang dung: r = %.2f, k = %.2f | nguong Impact: %s

  CAC NGAY CO DU LIEU: %s

  CAC NHOM NGHIEP VU:
%s

  CAC KICH BAN CO ALERT:
%s""" % (
        kt["file"], kt["cap_nhat"], kt["so_ngay"], kt["ngay_dau"],
        kt["ngay_cuoi"], f'{kt["tong_alert"]:,}', f'{kt["tong_kh"]:,}',
        f'{kt["tong_luot"]:,}', kt["so_kb_co_alert"], kt["so_kb_cau_hinh"],
        kt["r"], kt["k"], kt["nguong"], ", ".join(kt["ngay"]), nhom, kb)


QUY_TAC_DU_LIEU = """QUY TAC DU LIEU BAT BUOC (sai la ra so sai ma khong ai biet):

  1. Dem alert = SO DONG. Du lieu KHONG co khoa duy nhat nao. AlertID ghep tu
     PARTITION_DATE + request_id, mot khach co the bi cung mot kich ban ban
     nhieu lan trong mot ngay. Dung nunique('AlertID') se ra thieu ~7%.

  2. Dem khach = so ma RIENG BIET. KHONG cong ngang so khach cua cac nhom —
     mot khach dinh hai nhom van chi la mot nguoi.

  3. Diem luon TINH LAI bang cong thuc PP-D. KHONG doc cot last_risk_score
     hay Level tu file — hai cot do tinh tu thoi r=k=0.5, khong khop dashboard.

  4. ALERT va LUOT la hai don vi khac nhau. Diem cham theo LUOT (mot khach
     trong mot ngay), khong cong don qua ngay. Noi ro dang dung don vi nao."""


GIOI_HAN = """GIOI HAN CUA BAN (tuyet doi khong vuot):

  - KHONG suy luan nhan qua. Duoc noi "A giam cung luc B ngung ban",
    KHONG duoc noi "A giam VI B". Chi mo ta cai gi xay ra va goi y cho nen
    kiem tra tiep.
  - KHONG du bao tuong lai, KHONG tu de xuat chinh nguong nghiep vu.
  - KHONG bia so. Moi con so phai co trong du kien duoc dua cho ban.
  - Du lieu chi co cac cot da liet ke. Cau hoi ve thu khong co trong do
    (trang thai xu ly, tai khoan bi khoa, ket qua dieu tra...) thi noi thang
    la du lieu khong co, dung suy dien.
  - TUYET DOI KHONG dua ra THONG TIN NHAN THAN: so dien thoai, CCCD, so
    giay to, so tai khoan ngan hang, ten that, dia chi, email, ngay sinh.
    Ma khach hang la chuoi bam 20 ky tu — noi duoc, nhung KHONG duoc thu
    tra nguoc no ve nguoi that, va KHONG duoc doan ma do la ai.
    Ai hoi nhung thu do, du dien dat kieu gi, deu tu choi.
  - KHONG lam viec DAT DIEM va CHOT NGUONG IMPACT. Tham so r = k = 0,70 la
    CO DINH, khong doi duoc. Cau hoi kieu "neu dat r khac thi sao", "nen
    chot nguong bao nhieu", "phan bo diem the nao" deu NGOAI PHAM VI: viec
    do lam o tai lieu phuong phap luan rieng, va nguoi dung tu keo thanh
    truot o ba muc ⓪①② tren dashboard. Noi ro nhu vay.
    Diem cua tung khach thi van tra loi duoc (ai diem cao nhat, muc gi)."""


def _prompt_ke_hoach(cau_hoi, kt, lich_su, cac_buoc):
    """Prompt cho model quyet dinh buoc tiep theo."""
    da_lam = ""
    if cac_buoc:
        da_lam = "\n\nCAC BUOC DA CHAY VA KET QUA:\n" + "\n".join(
            "  Buoc %d: %s\n    -> %s" % (i + 1, b["mo_ta"],
                                          _tom_tat(b["ket_qua"]))
            for i, b in enumerate(cac_buoc))

    ngu_canh = ""
    if lich_su:
        ngu_canh = "\n\nHOI DAP TRUOC DO (de hieu 'no', 'cai do'):\n" + "\n".join(
            "  Hoi: %s\n  Dap: %s" % (h["hoi"], h["dap"][:200])
            for h in lich_su[-3:])

    return """Ban la tro ly phan tich du lieu canh bao rui ro F2DR (Viettel Money).
Nhiem vu: quyet dinh BUOC TIEP THEO de tra loi cau hoi.

%s

%s

%s

CAC HAM TRUY VAN CO SAN:
%s
%s%s

CAU HOI CUA NGUOI DUNG: "%s"

Tra ve JSON dung mot trong bon dang:

1. Goi ham co san (uu tien nhat):
   {"hanh_dong": "goi_ham", "ham": "ten_ham", "tham_so": {...}, "vi_sao": "..."}

2. Viet code pandas (CHI khi khong ham nao phu duoc):
   {"hanh_dong": "viet_code", "code": "kq = ...", "vi_sao": "..."}
   - Bien co san: d (DataFrame), kt (dict kien thuc), pd, np
   - Cot dung duoc cua d:
       object_value  ma khach hang (da an danh, chuoi bam 20 ky tu)
       ngay          'YYYY-MM-DD'
       ten_kb        ten kich ban (da bo tien to [NEW]_)
       nhom          nhom nghiep vu
       lv_kb         muc do kich ban: Low/Medium/High/Very High
       cap_kb        tran diem theo muc
       Score_KB      diem goc cua kich ban
       AlertID       ma alert — KHONG duy nhat, dung de dem thi lay len(d)
       gio_alert     'YYYY-MM-DD HH:MM:SS'
       CATEGORY, usecase_clean, usecase_name, ngay_alert, PARTITION_DATE,
       created_date, updated_date, risk_level_kb, viettel_bank_code
   - KHONG con cac cot sau (da bo khoi DataFrame, dung toi se loi):
       chi_tiet_alert   -> muon bang chung thi goi ham bang_chung_alert
       last_risk_score, Level  -> diem CU tinh voi r=k=0.5, khong khop
                                  dashboard. Can diem thi goi ham phan_bo_diem
                                  hoac ho_so_khach, chung tinh lai dung.
       request_id, requestor, status, object_key, reject_reason
   - PHAI gan ket qua vao bien ten kq
   - pd va np bi han che: chi dung duoc ham tinh toan (DataFrame, concat,
     groupby, percentile, mean...), moi ham doc/ghi file deu bi chan
   - Cam: import, open, eval, exec, dinh nghia ham, vong lap while

3. Da du du kien de tra loi:
   {"hanh_dong": "du_roi", "vi_sao": "..."}
   Chi dung khi da chay it nhat mot buoc, HOAC cau hoi chi can so tong quat
   da co san trong phan KY DU LIEU HIEN TAI o tren.

4. Cau hoi can kien thuc ngoai (quy dinh, thong le, dinh nghia nghiep vu
   khong co trong du lieu):
   {"hanh_dong": "tra_web", "cau_tim": "...", "vi_sao": "..."}

5. Cau hoi ve thu DU LIEU KHONG CO (trang thai xu ly alert, tai khoan bi
   khoa hay chua, ket qua dieu tra, thong tin ca nhan khach hang, so tien
   tung giao dich...):
   {"hanh_dong": "ngoai_pham_vi", "thieu_gi": "ten truong du lieu con thieu",
    "vi_sao": "..."}
   File chi co cac cot: AlertID, object_value (ma khach da an danh),
   usecase_clean, ngay_alert, gio_alert, CATEGORY, Score_KB, risk_level_kb,
   chi_tiet_alert. KHONG co trang thai xu ly, khong co thong tin dinh danh.

NGUYEN TAC LAP KE HOACH:
  - Cau hoi "vi sao / sao lai / nguyen nhan" thuong can 2-3 buoc: xac nhan
    hien tuong truoc, roi moi dao xuong tim cai gi thay doi.
  - Cau hoi don gian ("bao nhieu alert") chi can 1 buoc roi du_roi.
  - Da chay %d buoc. Toi da %d buoc. Du du kien thi dung lai ngay.""" % (
        _mo_ta_ky(kt), QUY_TAC_DU_LIEU, GIOI_HAN, TV.mo_ta_danh_muc(),
        da_lam, ngu_canh, cau_hoi, len(cac_buoc), SO_VONG_TOI_DA)


# Cau hoi ve NGUYEN NHAN can vach duong di nhieu buoc, dang de model nghi
# truoc. Cac cau con lai ("bao nhieu", "kich ban nao") thi mot buoc la xong,
# nghi them chi ton thoi gian.
_RX_NGUYEN_NHAN = re.compile(
    r"vi\s*sao|tai\s*sao|nguyen\s*nhan|do\s*dau|giai\s*thich|"
    r"phan\s*tich|dieu\s*tra|bat\s*thuong|la\s*sao|the\s*nao|"
    r"ra\s*sao|lien\s*quan|anh\s*huong|so\s*sanh|"
    r"sao\s+(lai|ma|no|ngay|kich|nhom|khach|it|nhieu|cao|thap|giam|tang)",
    re.I)


def _hoi_nguyen_nhan(cau_hoi):
    """Cau hoi co doi hoi lan theo nhieu buoc khong?"""
    import unicodedata
    s = unicodedata.normalize("NFD", str(cau_hoi or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return bool(_RX_NGUYEN_NHAN.search(s.replace("đ", "d").replace("Đ", "D")))


def _du_kien_tong_quat(kt):
    """Toan bo so lieu cua bang kien thuc, dua vao du kien de kiem chung.

    Bang kien thuc do dung_kien_thuc() tinh bang pandas, khong phai LLM nghi
    ra, nen dung lam du kien la hop le.

    PHAI dua DAY DU ca danh sach nhom va kich ban, khong chi vai so tong.
    Ly do: bang kien thuc duoc nhet vao prompt (xem _mo_ta_ky), nen LLM se
    dung nhung so trong do. So nao co trong prompt ma khong co trong du kien
    se bi lop kiem chung bao la "bia" — bao dong gia, va cau tra loi dung bi
    vut di. Nguyen tac: moi so LLM NHIN THAY deu phai nam trong du kien.
    """
    return {
        "_mo_ta": "So lieu tong quat cua ky (tu bang kien thuc)",
        "file_du_lieu": kt["file"],
        "so_ngay": kt["so_ngay"],
        "ngay_dau": kt["ngay_dau"],
        "ngay_cuoi": kt["ngay_cuoi"],
        "tong_alert": kt["tong_alert"],
        "tong_khach": kt["tong_kh"],
        "tong_luot": kt["tong_luot"],
        "so_kich_ban_co_alert": kt["so_kb_co_alert"],
        "so_kich_ban_cau_hinh": kt["so_kb_cau_hinh"],
        "so_nhom": len(kt["nhom"]),
        "r": kt["r"], "k": kt["k"], "nguong": kt["nguong"],
        "cac_nhom": kt["nhom"],
        "cac_kich_ban": [{k: v for k, v in x.items() if k != "khoa"}
                         for x in kt["kich_ban"]],
    }


def _tom_tat(kq, gioi_han=1400):
    """Rut gon ket qua mot buoc de nhet vao prompt vong sau."""
    s = json.dumps(kq, ensure_ascii=False, default=str)
    if len(s) <= gioi_han:
        return s
    return s[:gioi_han] + "... (da cat)"


# ══════════════════ VONG LAP ══════════════════

class KetQuaTroLy:
    def __init__(self):
        self.cac_buoc = []      # cac buoc da chay
        self.du_kien = []       # ket qua tho, dung de kiem chung so
        self.nguon_web = []
        self.cau_tra_loi = ""
        self.canh_bao = []
        self.thoi_gian = 0.0
        self.so_lan_goi_llm = 0
        self.kiem_chung = None
        self.da_bo_dien_giai = False
        self.ngoai_pham_vi = None
        self.bi_chan_pii = None     # ly do bi chan o tang dau vao
        self.pii_da_cat = []        # chuoi dinh danh bi cat o tang dau ra


def _chay_mot_buoc(qd, d, kt):
    """Thuc thi mot quyet dinh cua model. Tra ve (mo_ta, ket_qua)."""
    hd = qd.get("hanh_dong")

    if hd == "goi_ham":
        ten = qd.get("ham", "")
        ts = qd.get("tham_so") or {}
        if not isinstance(ts, dict):
            ts = {}
        kq = TV.goi(ten, d, kt, **ts)
        mo_ta = "goi %s(%s)" % (ten, ", ".join(
            "%s=%s" % (k, v) for k, v in ts.items()))
        return mo_ta, kq

    if hd == "viet_code":
        code = qd.get("code", "")
        kq = HC.chay(code, d, kt)
        return "tu viet code pandas", kq

    raise ValueError("hanh dong khong hieu: %s" % hd)


def hoi(cau_hoi, d, kt, lich_su=None, cho_phep_web=True, ghi_log=None):
    """Tra loi mot cau hoi. Tra ve KetQuaTroLy."""
    t0 = time.time()
    R = KetQuaTroLy()
    lich_su = lich_su or []

    # ── Chan y do khai thac thong tin nhan than, TRUOC khi goi LLM ──
    # Chay bang luat chu khong qua model: khong the bi thuyet phuc, khong the
    # bi danh lua bang cach dien dat vong vo, va khong ton mot lan goi API.
    bi_chan, ly_do = CP.kiem_cau_hoi(cau_hoi)
    if bi_chan:
        if ghi_log:
            ghi_log("Chan: %s" % ly_do)
        R.cau_tra_loi = CP.LOI_TU_CHOI
        R.bi_chan_pii = ly_do
        R.kiem_chung = {"dat": True, "so_da_kiem": 0, "so_la": []}
        R.thoi_gian = time.time() - t0
        return R

    def _log(s):
        if ghi_log:
            ghi_log(s)

    can_web = None
    hong_lien_tiep = 0

    # ── Vong lap suy luan ──
    for vong in range(SO_VONG_TOI_DA):
        prompt = _prompt_ke_hoach(cau_hoi, kt, lich_su, R.cac_buoc)
        # Bat che do nghi CHI o vong dau cua cau hoi "vi sao / nguyen nhan" —
        # do la loai cau can vach duong di nhieu buoc. Da do: co nghi 8,2s,
        # khong nghi 4,2s cho cung mot prompt, va ca hai deu chon dung buoc.
        # Bat het moi vong thi mot cau ba buoc doi thanh gan ba phut cho.
        can_nghi = (vong == 0 and _hoi_nguyen_nhan(cau_hoi))
        try:
            qd, _ = LLM.goi(prompt, model=LLM.MODEL_CHINH, json_ra=True,
                            suy_luan=can_nghi)
            R.so_lan_goi_llm += 1
        except LLM.LoiLLM as e:
            R.canh_bao.append("Khong lap duoc ke hoach: %s" % e)
            break

        # Model doi khi tra ve MANG thay vi object — thuong la mang mot phan
        # tu, hoac mang nhieu buoc no muon lam lien. Lay phan tu dau, khong
        # de vo ca luong vi mot lan model tra sai dinh dang.
        if isinstance(qd, list):
            qd = next((x for x in qd if isinstance(x, dict)), None)
        if not isinstance(qd, dict):
            R.canh_bao.append("Model tra ve dinh dang la o vong %d" % (vong + 1))
            _log("Vong %d: dinh dang la — dung lai" % (vong + 1))
            break

        hd = qd.get("hanh_dong")
        _log("Vong %d: %s — %s" % (vong + 1, hd, str(qd.get("vi_sao", ""))[:90]))

        if hd == "ngoai_pham_vi":
            R.ngoai_pham_vi = qd.get("thieu_gi") or "truong du lieu nay"
            break

        if hd == "du_roi":
            # Chua chay buoc nao ma da bao du: cau hoi chi can so tong quat.
            # Bang kien thuc cung la so tinh tu code (trong dung_kien_thuc),
            # nen dua no vao du kien — khong phai LLM tu nghi ra.
            if not R.du_kien:
                R.du_kien.append(_du_kien_tong_quat(kt))
            break

        if hd == "tra_web":
            can_web = qd.get("cau_tim") or cau_hoi
            break

        try:
            mo_ta, kq = _chay_mot_buoc(qd, d, kt)
            R.cac_buoc.append({"mo_ta": mo_ta, "ket_qua": kq,
                               "vi_sao": qd.get("vi_sao", "")})
            R.du_kien.append(kq)
            hong_lien_tiep = 0
        except (TV.LoiTruyVan, HC.LoiHopCat, ValueError) as e:
            # Bao loi NGUOC lai cho model o vong sau de no tu sua
            hong_lien_tiep += 1
            ket_loi = {"_mo_ta": "Buoc nay khong chay duoc",
                       "_loi": str(e),
                       "_huong_dan": "Buoc nay hong. Doi cach khac hoac "
                                     "dung lai neu da du du kien."}
            R.cac_buoc.append({"mo_ta": "buoc that bai",
                               "ket_qua": ket_loi,
                               "vi_sao": qd.get("vi_sao", "")})
            # Dua loi vao du kien luon: nguoi dung hoi "neu dat r=2 thi sao"
            # can duoc nghe LY DO r=2 khong hop le, chu khong phai mot cau
            # lang tranh kieu "toi khong co thong tin ve dieu do".
            R.du_kien.append(ket_loi)
            _log("   loi: %s" % str(e)[:90])

            # Hong lien tiep may lan thi dung han. Moi vong ton mot lan goi
            # LLM co suy luan (~40 giay); co dam bon vong thi nguoi dung cho
            # gan ba phut roi van khong co gi. Tra loi bang du kien da co,
            # kem loi cuoi cung, van hon.
            if hong_lien_tiep >= SO_LAN_HONG_LIEN_TIEP:
                _log("Hong %d lan lien tiep — dung lai" % hong_lien_tiep)
                R.canh_bao.append(
                    "Da thu %d cach nhung deu khong lay duoc du lieu. "
                    "Loi cuoi: %s" % (hong_lien_tiep, str(e)[:150]))
                break

    # ── Tra web neu can ──
    if can_web and cho_phep_web:
        _log("Tra web: %s" % can_web[:70])
        try:
            vb, nguon = LLM.goi(
                "Tra loi ngan gon bang tieng Viet, chi dua tren nguon tim duoc. "
                "Neu khong tim thay nguon dang tin thi noi ro la khong tim thay.\n\n"
                "Cau hoi: %s" % can_web,
                model=LLM.MODEL_CHINH, web=True, suy_luan=False)
            R.so_lan_goi_llm += 1
            R.nguon_web = nguon
            R.du_kien.append({"_mo_ta": "Ket qua tra cuu web",
                              "_tu_web": True, "noi_dung": vb,
                              "nguon": nguon})
            if not nguon:
                R.canh_bao.append("Tra cuu web khong co nguon kem theo")
        except LLM.LoiLLM as e:
            R.canh_bao.append("Tra web that bai: %s" % e)

    # ── Cau hoi ve thu du lieu khong co: noi thang, khong vong vo ──
    if R.ngoai_pham_vi and not R.du_kien:
        R.cau_tra_loi = _tra_loi_ngoai_pham_vi(R.ngoai_pham_vi, kt)
        R.kiem_chung = {"dat": True, "so_da_kiem": 0, "so_la": []}
        R.thoi_gian = time.time() - t0
        return R

    # ── Viet cau tra loi, roi KIEM CHUNG tung con so ──
    R.cau_tra_loi = _viet_tra_loi(cau_hoi, kt, R, lich_su)
    R.so_lan_goi_llm += 1

    # Kiem chung doi chieu voi du kien CONG bang kien thuc: bang kien thuc
    # nam trong prompt nen LLM duoc phep trich so tu do, khong tinh la bia.
    nen_kiem = R.du_kien + [_du_kien_tong_quat(kt)]

    R.kiem_chung = KC.kiem(R.cau_tra_loi, nen_kiem)
    if not R.kiem_chung["dat"]:
        _log("Kiem chung: %d so khong truy duoc -> viet lai"
             % len(R.kiem_chung["so_la"]))
        # Viet lai MOT lan, nhac ro nhung so nao co van de
        R.cau_tra_loi = _viet_tra_loi(cau_hoi, kt, R, lich_su,
                                      so_la=R.kiem_chung["so_la"])
        R.so_lan_goi_llm += 1
        lan2 = KC.kiem(R.cau_tra_loi, nen_kiem)

        if not lan2["dat"]:
            # Van hong -> KHONG tra loi dien giai nua, tra thang bang so
            _log("Kiem chung lan 2 van hong -> tra bang du kien tho")
            R.canh_bao.append(
                "Cau tra loi dien giai co %d con so khong truy duoc ve du "
                "lieu goc nen da bi bo. Duoi day la so lieu tho."
                % len(lan2["so_la"]))
            R.cau_tra_loi = _tra_bang_tho(R)
            R.kiem_chung = lan2
            R.da_bo_dien_giai = True
        else:
            R.kiem_chung = lan2

    # ── Lop chan cuoi: quet cau tra loi, cat moi chuoi giong dinh danh ──
    # Ly tuong thi khong bao gio bat duoc gi. Bat duoc nghia la mot trong hai
    # tang tren da lot — ghi lai de con biet ma xem lai.
    R.cau_tra_loi, da_cat = CP.quet_cau_tra_loi(R.cau_tra_loi)
    if da_cat:
        R.pii_da_cat = da_cat
        R.canh_bao.append("Da cat %d chuoi giong thong tin dinh danh khoi cau "
                          "tra loi" % len(da_cat))
        _log("!! Cat %d chuoi dinh danh o dau ra" % len(da_cat))

    R.thoi_gian = time.time() - t0
    return R


def _tra_loi_ngoai_pham_vi(thieu_gi, kt):
    """Cau hoi ve thu du lieu khong co — noi thang thieu gi, va co gi thay the.

    Khong goi LLM cho viec nay: cau tra loi la su that ve cau truc file,
    khong can dien dat sang tao, va tiet kiem duoc mot lan goi.
    """
    return (
        "Dữ liệu không có **%s**, nên tôi không trả lời được câu này.\n\n"
        "File alert chỉ ghi lại *cảnh báo đã bắn*, không theo dõi việc xử lý "
        "sau đó. Các trường có trong file:\n"
        "- Mã khách hàng (đã ẩn danh), ngày và giờ alert\n"
        "- Tên kịch bản, nhóm nghiệp vụ, mức độ, điểm gốc\n"
        "- Bằng chứng nghiệp vụ của từng alert\n\n"
        "Tôi trả lời được về: alert theo ngày và kịch bản, khách bị bắn nhiều "
        "nhất, điểm và ngưỡng Impact, kịch bản đột biến hay im lặng.\n\n"
        "GOI_Y: Kịch bản nào nhiều alert nhất | Ngày nào bất thường | "
        "Khách nào bị bắn nhiều nhất" % thieu_gi)


def _tra_bang_tho(R):
    """Phuong an cuoi: bo dien giai, tra thang du kien.

    Tha tho ma dung con hon tron tru ma sai. Nguoi doc van dung duoc so.
    """
    khoi = []
    for kq in R.du_kien:
        if not isinstance(kq, dict) or kq.get("_loi"):
            continue
        khoi.append("**%s**\n\n```json\n%s\n```" % (
            kq.get("_mo_ta", "Du lieu"),
            json.dumps({k: v for k, v in kq.items()
                        if not k.startswith("_")},
                       ensure_ascii=False, indent=1, default=str)[:2200]))
    if not khoi:
        return ("Toi khong lay duoc du lieu dang tin cay cho cau nay. "
                "Ban thu hoi cu the hon xem sao.")
    return ("Toi co so lieu nhung khong dien giai chac chan duoc, nen tra "
            "thang bang du lieu goc de ban tu doc:\n\n" + "\n\n".join(khoi))


def _nhac_so_la(so_la):
    """Doan nhac them khi phai viet lai vi lan truoc co so khong truy duoc."""
    if not so_la:
        return ""
    ds = "\n".join("    - %s   (trong cau: \"...%s...\")"
                   % (x["so"], x["ngu_canh"][:80]) for x in so_la[:6])
    return """

!! VIET LAI. Lan truoc ban dua ra nhung con so KHONG CO trong du kien:
%s
Nhung so nay hoac ban tu tinh, hoac tu nghi ra — ca hai deu cam. Viet lai
cau tra loi CHI dung so co san trong du kien tren. Khong tu cong tru nhan
chia. Khong uoc luong. Thieu so nao thi noi thang la du lieu khong co,
dung tu dien vao.""" % ds


def _viet_tra_loi(cau_hoi, kt, R, lich_su, so_la=None):
    """Buoc cuoi: dien dat du kien thanh cau tieng Viet.

    so_la — danh sach so khong truy duoc o lan viet truoc. Co thi nhac model
    viet lai, chi dung so co that.
    """
    if not R.du_kien:
        return ("Toi chua lay duoc du lieu de tra loi cau nay. "
                + ("Ly do: " + R.canh_bao[0] if R.canh_bao else
                   "Ban thu dien dat lai cau hoi cu the hon xem sao."))

    du_kien = json.dumps(R.du_kien, ensure_ascii=False, indent=1, default=str)
    if len(du_kien) > SO_KY_TU_DU_KIEN_TOI_DA:
        du_kien = du_kien[:SO_KY_TU_DU_KIEN_TOI_DA] + "\n... (da cat bot)"

    ngu_canh = ""
    if lich_su:
        ngu_canh = "\n\nHOI DAP TRUOC DO:\n" + "\n".join(
            "  Hoi: %s\n  Dap: %s" % (h["hoi"], h["dap"][:200])
            for h in lich_su[-2:])

    prompt = """Ban la tro ly phan tich du lieu canh bao rui ro F2DR.
Viet cau tra loi bang TIENG VIET dua HOAN TOAN vao du kien duoi day.

%s

%s

DU KIEN DA TINH DUOC (day la nguon DUY NHAT cho moi con so):
%s
%s

CAU HOI: "%s"

CACH VIET:
  - Tra loi thang vao cau hoi ngay cau dau tien.
  - Moi con so ban viet PHAI co trong du kien tren. Tuyet doi khong tu tinh
    them, khong lam tron khac di, khong uoc luong.
  - Ngan gon, giong dong nghiep noi chuyen. Khong mo dau khach sao.
  - Dung Markdown: **dam** cho so quan trong, gach dau dong khi liet ke.
  - Neu du kien cho thay dieu gi dang chu y (kich ban im lang, so lech han)
    thi noi ra, va goi y buoc kiem tra tiep theo.
  - Cuoi cau tra loi, them dung mot dong:
    "GOI_Y: cau hoi 1 | cau hoi 2 | cau hoi 3"
    la 2-3 cau hoi noi tiep hop ly, moi cau duoi 10 tu.
  - Neu co du kien tu web (_tu_web), tach thanh doan rieng va noi ro do la
    thong tin ben ngoai, khong phai so lieu noi bo.
  - Neu du kien co truong "_loi", do la ly do mot buoc khong chay duoc.
    Noi LAI ly do do cho nguoi dung bang tieng Viet de hieu — vi du tham so
    nam ngoai khoang cho phep thi giai thich vi sao khoang do la bat buoc.
    Dung noi chung chung kieu "toi khong co thong tin".%s""" % (
        _mo_ta_ky(kt), GIOI_HAN, du_kien, ngu_canh, cau_hoi,
        _nhac_so_la(so_la))

    try:
        vb, _ = LLM.goi(prompt, model=LLM.MODEL_CHINH, suy_luan=False,
                        nhiet_do=0.1)
        return vb.strip()
    except LLM.LoiLLM as e:
        return "Toi lay duoc du lieu nhung khong viet duoc cau tra loi (%s)." % e


def tach_goi_y(van_ban):
    """Tach dong GOI_Y ra khoi cau tra loi. Tra ve (cau_tra_loi, [goi y])."""
    m = re.search(r"^\s*GOI_Y\s*:\s*(.+)$", van_ban, re.M | re.I)
    if not m:
        return van_ban.strip(), []
    goi_y = [x.strip() for x in m.group(1).split("|") if x.strip()]
    sach = (van_ban[:m.start()] + van_ban[m.end():]).strip()
    return sach, goi_y[:3]
