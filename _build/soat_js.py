# -*- coding: utf-8 -*-
"""Soat cu phap chuoi trong file .js — khong can Node.

Bat dung mot loai loi, nhung la loai da lam chet chatbot hai lan:
chuoi "..." bi xuong dong THAT o giua (do escape \n bi dien giai khi ghi file).
JS khong cho chuoi thuong tra dai qua dong -> ca file loi cu phap ->
window.F2BoNao khong bao gio duoc tao -> giao dien treo o dau ba cham.
"""
import glob
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TRUOC_REGEX = set("(,=:[!&|?{};+-*%~^<>") | {"\n"}


def soat(duong_dan):
    """Tra ve danh sach (dong, mo_ta) cac loi tim duoc."""
    src = open(duong_dan, encoding="utf-8").read()
    loi, i, dong, n = [], 0, 1, len(src)
    truoc_co_nghia = "\n"          # ky tu co nghia gan nhat, de doan regex

    while i < n:
        c = src[i]

        if c == "\n":
            dong += 1
            i += 1
            continue

        if c.isspace():
            i += 1
            continue

        # chu thich
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            i += 2
            while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                if src[i] == "\n":
                    dong += 1
                i += 1
            i += 2
            continue

        # regex literal
        if c == "/" and truoc_co_nghia in TRUOC_REGEX:
            d0, i = dong, i + 1
            trong_ngoac = False
            while i < n:
                if src[i] == "\\":
                    i += 2
                    continue
                if src[i] == "[":
                    trong_ngoac = True
                elif src[i] == "]":
                    trong_ngoac = False
                elif src[i] == "\n":
                    loi.append((d0, "regex khong dong truoc khi het dong"))
                    break
                elif src[i] == "/" and not trong_ngoac:
                    i += 1
                    break
                i += 1
            truoc_co_nghia = "/"
            continue

        # chuoi thuong: khong duoc chua xuong dong that
        if c in "\"'":
            dau, d0, i = c, dong, i + 1
            while i < n:
                if src[i] == "\\":
                    i += 2
                    continue
                if src[i] == "\n":
                    loi.append((d0, "chuoi %s... bi xuong dong THAT o giua "
                                    "(phai viet \\n)" % dau))
                    dong += 1
                    i += 1
                    break
                if src[i] == dau:
                    i += 1
                    break
                i += 1
            truoc_co_nghia = dau
            continue

        # Template literal: duoc phep xuong dong. Phai dem lop ${...} vi ben
        # trong do co the lai la mot template khac — dashboard dung rat nhieu,
        # khong dem thi bo soat mat dong bo roi bao oan hang loat.
        if c == "`":
            i, sau = i + 1, 0
            while i < n:
                if src[i] == "\\":
                    i += 2
                    continue
                if src[i] == "\n":
                    dong += 1
                elif src[i] == "$" and i + 1 < n and src[i + 1] == "{":
                    sau += 1
                    i += 2
                    continue
                elif src[i] == "`":
                    if sau == 0:
                        i += 1
                        break
                    sau += 1              # template long trong ${...}
                elif src[i] == "}" and sau:
                    sau -= 1
                i += 1
            truoc_co_nghia = "`"
            continue

        truoc_co_nghia = c
        i += 1

    # ky tu dieu khien lot vao ma nguon (loi heredoc dang \b -> 0x08)
    b = open(duong_dan, "rb").read()
    for ma, ten in [(8, "\b"), (0, "NUL"), (12, "\f"), (11, "\v"),
                    (7, "\a"), (27, "ESC")]:
        if b.count(bytes([ma])):
            loi.append((0, "co %d ky tu dieu khien 0x%02X (%s) lot vao ma nguon"
                        % (b.count(bytes([ma])), ma, ten)))
    return loi


def main(cac_file=None):
    cac_file = cac_file or sorted(glob.glob(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "_chat_*.js")))
    tong = 0
    for p in cac_file:
        loi = soat(p)
        tong += len(loi)
        if loi:
            print("[X] %s" % os.path.basename(p))
            for d, mo in loi:
                print("      dong %-5s %s" % (d or "?", mo))
        else:
            print("[OK] %s" % os.path.basename(p))
    if tong:
        print("\n=> %d loi. KHONG dung file nay de dung ban xem truoc." % tong)
    return 1 if tong else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or None))
