# -*- coding: utf-8 -*-
"""
DUNG BAN XEM TRUOC: dashboard that + panel chat, gop thanh MOT file HTML.

Muc dich: sua giao dien chat ma khong phai deploy moi lan. Mo file ra bang
trinh duyet la thay ngay ket qua.

    py -3.13 _build/xem_truoc.py
    -> F2DR_Van_Hanh_xemtruoc.html

File ra la ban DAY DU: dashboard voi du lieu that cua ky hien tai, cong
panel chat day du chuc nang giao dien (mo/thu, cuon, go chu, goi y, nhan
kiem chung, khoi nguon so lieu).

Ban deploy (app.py tren Streamlit) dung CHUNG ham ghep() o duoi, chi khac
mot cho: khoa API lay tu Streamlit Secrets thay vi tu file tren dia. Nho vay
ban xem truoc va ban deploy khong the lech nhau.

CANH BAO: file ra CO KHOA API viet thang trong HTML. Da nam trong
.gitignore — tuyet doi khong commit, khong gui cho nguoi khac.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)          # de import duoc soat_js
GOC = os.path.dirname(HERE)

DASH = os.path.join(GOC, "F2DR_Van_Hanh.html")
UI = os.path.join(HERE, "_chat_ui.html")
JS_TRI_THUC = os.path.join(HERE, "_chat_tri_thuc.js")
JS_BO_NAO = os.path.join(HERE, "_chat_bo_nao.js")
JS_KHO = os.path.join(HERE, "_chat_kho.js")
JS_LAI = os.path.join(HERE, "_chat_lai.js")
JS_UI = os.path.join(HERE, "_chat_ui.js")
RA = os.path.join(GOC, "F2DR_Van_Hanh_xemtruoc.html")


def _khoa_tu_secrets():
    """Doc TAT CA khoa tu .streamlit/secrets.toml — do la cho da dat san.

    Tra ve danh sach. Moi khoa la mot project rieng nen co han muc rieng,
    bot doi khoa khi mot cap (khoa, model) het luot.
    """
    f = os.path.join(GOC, ".streamlit", "secrets.toml")
    if not os.path.exists(f):
        return []
    try:
        s = open(f, encoding="utf-8").read()
    except OSError:
        return []

    ds = []
    m = re.search(r"GEMINI_API_KEYS\s*=\s*\[(.*?)\]", s, re.S)
    if m:
        ds = re.findall(r'"([^"\s]+)"', m.group(1))
    m1 = re.search(r'GEMINI_API_KEY\s*=\s*"([^"]+)"', s)
    if m1 and m1.group(1) not in ds:
        ds.insert(0, m1.group(1))
    return ds


def doc(p):
    if not os.path.exists(p):
        sys.exit("Thieu file: %s" % p)
    with open(p, encoding="utf-8") as f:
        return f.read()


def tach_style(ui):
    """Lay rieng khoi <style> cua file thiet ke."""
    m = re.search(r"<style[^>]*>(.*?)</style>", ui, re.S)
    if not m:
        sys.exit("_chat_ui.html khong co khoi <style>")
    return m.group(1)


def tach_than(ui):
    """Phan HTML sau khoi <style> — nut tron + panel."""
    m = re.search(r"</style>(.*)$", ui, re.S)
    return m.group(1).strip() if m else ""


def ghep(dash, khoa):
    """Gop dashboard + panel chat thanh MOT trang HTML.

    Dung chung cho hai duong:
      - xem_truoc.py : ghi ra file de mo bang trinh duyet khi sua giao dien
      - app.py       : ghep NGAY LUC CHAY tren Streamlit, khoa lay tu Secrets

    Nho dung chung ham nay ma ban xem truoc va ban deploy khong the lech
    nhau: cung mot _chat_ui.html, cung ba file JS, cung mot thu tu nap.

    Thu tu nap QUAN TRONG: tri thuc -> bo nao -> giao dien. Giao dien goi bo
    nao, bo nao goi tri thuc, tri thuc doc bien D cua dashboard. Nap sai thu
    tu la undefined.
    """
    ui = doc(UI)
    chen = ("\n<!-- ═══ PANEL CHAT ═══ -->\n"
            + "<style>\n" + tach_style(ui) + "\n</style>\n"
            + tach_than(ui) + "\n"
            + "<script>window.F2_CAU_HINH = "
            + json.dumps({"khoaAPI": list(khoa or [])}, ensure_ascii=False)
            + ";</script>\n"
            + "<script>\n" + doc(JS_TRI_THUC) + "\n</script>\n"
            + "<script>\n" + doc(JS_BO_NAO) + "\n</script>\n"
            # Kho hoi thoai phai nap TRUOC giao dien: giao dien doc
            # window.F2Kho ngay luc khoi tao de mo lai cuoc dang do.
            + "<script>\n" + doc(JS_KHO) + "\n</script>\n"
            # Lai dashboard: phai nap TRUOC bo nao (bo nao doc window.F2Lai
            # de biet co suy lenh lai hay khong) va truoc giao dien.
            + "<script>\n" + doc(JS_LAI) + "\n</script>\n"
            + "<script>\n" + doc(JS_UI) + "\n</script>\n")
    # Dashboard co dung </body> o cuoi file.
    if "</body>" in dash:
        return dash.replace("</body>", chen + "</body>", 1)
    return dash + chen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dash", default=DASH, help="File dashboard nguon")
    ap.add_argument("--out", default=RA, help="File xem truoc ghi ra")
    ap.add_argument("--khoa", action="append", default=None,
                    help="Khoa Gemini nhung vao file. Lap lai duoc de dua "
                         "nhieu khoa. Khong dat thi lay tu secrets.toml "
                         "hoac bien moi truong GEMINI_API_KEY.")
    a = ap.parse_args()

    print("=" * 70)
    print("DUNG BAN XEM TRUOC")
    print("=" * 70)

    # Soat cu phap TRUOC khi gop. Mot chuoi bi xuong dong that trong
    # _chat_bo_nao.js lam ca file loi cu phap -> window.F2BoNao khong ton tai
    # -> panel treo o dau ba cham ma khong bao gi. Da dinh hai lan roi.
    import soat_js
    print("Soat cu phap JS:")
    if soat_js.main([JS_TRI_THUC, JS_BO_NAO, JS_KHO, JS_LAI, JS_UI]):
        sys.exit("Dung lai: sua loi JS o tren roi chay lai.")
    print()

    dash = doc(a.dash)

    khoa = a.khoa or _khoa_tu_secrets()
    if not khoa and os.environ.get("GEMINI_API_KEY"):
        khoa = [os.environ["GEMINI_API_KEY"]]

    print("Dashboard : %s  (%s bytes)"
          % (os.path.basename(a.dash), format(len(dash), ",")))
    print("Giao dien : _chat_ui.html")
    print("Bo nao    : _chat_tri_thuc.js + _chat_bo_nao.js + _chat_ui.js")
    if khoa:
        print("Khoa API  : da nhung %d khoa (%s)"
              % (len(khoa), ", ".join("..." + k[-6:] for k in khoa)))
    else:
        print("Khoa API  : KHONG CO -> chat chi xem duoc giao dien")

    ra = ghep(dash, khoa)

    with open(a.out, "w", encoding="utf-8") as f:
        f.write(ra)

    print("-" * 70)
    print("XONG: %s" % os.path.basename(a.out))
    print("      %s bytes  (tang %s so voi dashboard goc)"
          % (format(len(ra), ","), format(len(ra) - len(dash), ",")))
    print()
    print()
    print("Mo file do bang trinh duyet. Chat chay THAT: goi Gemini, chay")
    print("dung 21 ham truy van, kiem chung tung con so, chan thong tin")
    print("nhan than — y het ban deploy.")
    print()
    print("Sua giao dien : _chat_ui.html")
    print("Sua cach nghi : _chat_bo_nao.js")
    print("Sua truy van  : _chat_tri_thuc.js")
    print("Roi chay lai lenh nay.")
    if khoa:
        print()
        print("!! File nay CO KHOA API. Da nam trong .gitignore, dung commit.")


if __name__ == "__main__":
    main()
