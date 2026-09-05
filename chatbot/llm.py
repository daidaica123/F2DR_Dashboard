# -*- coding: utf-8 -*-
"""
LOP GOI GEMINI.

Boc thu vien google-genai lai cho gon, va tap trung mot cho:
  - lay khoa tu st.secrets hoac bien moi truong (KHONG BAO GIO hard-code)
  - chon model theo viec: phan loai dung ban nhe, tra loi dung ban thuong
  - bat che do thinking cho khau can suy luan, tat cho khau chi dien dat
  - tra ve JSON co kiem tra, hong thi bao loi ro chu khong doan bua
"""
import json
import os
import re
import time

# Da do tren khoa dang dung (05/09/2026):
#   gemini-2.5-flash       2.0s khong nghi | 3.9s co nghi   <- nhanh nhat
#   gemini-3.1-flash-lite  2.9s / 5.1s
#   gemini-3.5-flash       5.3s / 9.5s
#   gemini-3.8-flash      14.2s, che do nghi con 503
# Ban *-flash-lite cua 2.5 khong mo cho khoa nay (404), nen dung chung
# mot model cho ca hai vai, chi khac o cho co bat che do nghi hay khong.
MODEL_NHANH = "gemini-2.5-flash"
MODEL_CHINH = "gemini-2.5-flash"

# Han muc token cho che do nghi. Do dat -1 (model tu quyet) tren prompt lap
# ke hoach: 150 giay cho MOT cau hoi. 1024 token du de model vach duong di
# hai ba buoc ma khong keo dai thoi gian cho.
NGAN_SACH_NGHI = 1024


class LoiLLM(Exception):
    """Goi model that bai hoac tra ve thu khong dung dinh dang."""


def lay_khoa():
    """Khoa API. Uu tien st.secrets (Streamlit Cloud), roi den bien moi truong.

    KHONG BAO GIO viet khoa thang vao code — file nay nam trong repo public.
    """
    try:
        import streamlit as st
        k = st.secrets.get("GEMINI_API_KEY")
        if k:
            return k
    except Exception:
        pass
    k = os.environ.get("GEMINI_API_KEY")
    if not k:
        raise LoiLLM(
            "Chua co GEMINI_API_KEY. Dat mot trong hai cach:\n"
            "  - Tai may : $env:GEMINI_API_KEY = \"...\"\n"
            "  - Tren web: them vao muc Secrets cua app Streamlit")
    return k


_khach = None


def khach():
    """Client dung chung — tao mot lan roi dung lai."""
    global _khach
    if _khach is None:
        try:
            from google import genai
        except ImportError:
            raise LoiLLM("Chua cai google-genai. Chay: pip install google-genai")
        _khach = genai.Client(api_key=lay_khoa())
    return _khach


# Model du phong khi model chinh qua tai. Xep theo do nhanh da do duoc.
MODEL_DU_PHONG = ["gemini-3.1-flash-lite", "gemini-3.5-flash"]

# Loi tam thoi — thu lai duoc. Loi khac (khoa sai, prompt hong) thi thu lai
# cung vo ich, nem ngay cho nhanh.
MA_TAM_THOI = ("503", "429", "500", "502", "504", "UNAVAILABLE",
               "RESOURCE_EXHAUSTED", "deadline", "timeout")


def _tam_thoi(e):
    s = str(e)
    return any(m.lower() in s.lower() for m in MA_TAM_THOI)


def goi(prompt, model=None, json_ra=False, suy_luan=False, web=False,
        nhiet_do=0.0, he_thong=None, so_lan_thu=3):
    """Goi model, tu thu lai khi gap loi tam thoi.

    Gemini tra 503 khi qua tai — chuyen xay ra thuong xuyen luc deploy that.
    Khong xu ly thi bot im lang giua chung, nguoi dung tuong hong han.

    Cach xu ly: thu lai voi khoang cho tang dan; het luot voi model chinh
    thi doi sang model du phong. Chi lan cuoi that bai moi bao loi.

    json_ra  — bat che do tra ve JSON, va tu parse
    suy_luan — cho model nghi truoc khi tra loi (cham hon, dung hon)
    web      — bat Google Search grounding
    """
    from google.genai import types

    cau_hinh = {"temperature": nhiet_do}
    if he_thong:
        cau_hinh["system_instruction"] = he_thong

    # Che do nghi.
    #
    # KHONG dung -1 ("de model tu quyet"): da do duoc, voi prompt lap ke hoach
    # ~11.500 ky tu no nghi toi 150 GIAY cho mot cau hoi. Nguoi dung khong doi
    # noi. Dat han muc cu the thi van du de vach duong di nhieu buoc, ma biet
    # truoc do tre toi da.
    cau_hinh["thinking_config"] = types.ThinkingConfig(
        thinking_budget=NGAN_SACH_NGHI if suy_luan else 0)

    if web:
        cau_hinh["tools"] = [types.Tool(google_search=types.GoogleSearch())]
    elif json_ra:
        # Khong dung chung duoc voi tool — Gemini cam
        cau_hinh["response_mime_type"] = "application/json"

    ds_model = [model or MODEL_CHINH] + [
        m for m in MODEL_DU_PHONG if m != (model or MODEL_CHINH)]
    loi_cuoi = None
    kq = None

    for i_model, m in enumerate(ds_model):
        for lan in range(so_lan_thu):
            try:
                kq = khach().models.generate_content(
                    model=m, contents=prompt,
                    config=types.GenerateContentConfig(**cau_hinh))
                break
            except Exception as e:
                loi_cuoi = e
                if not _tam_thoi(e):
                    raise LoiLLM("Goi model that bai: %s" % e)
                if lan < so_lan_thu - 1:
                    time.sleep(0.6 * (2 ** lan))     # 0.6s, 1.2s
        if kq is not None:
            break
        # het luot voi model nay -> thu model du phong
        if i_model < len(ds_model) - 1:
            time.sleep(0.3)

    if kq is None:
        raise LoiLLM("Model dang qua tai, da thu %d lan tren %d model. "
                     "Ban thu lai sau it phut. (%s)"
                     % (so_lan_thu, len(ds_model), loi_cuoi))

    van_ban = (kq.text or "").strip()

    nguon = []
    if web:
        nguon = _rut_nguon(kq)

    if json_ra:
        return _doc_json(van_ban), nguon
    return van_ban, nguon


def _doc_json(s):
    """Doc JSON tu cau tra loi. Model doi khi boc trong ```json ... ```."""
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # Vot lay khoi { } dau tien
        m = re.search(r"\{.*\}", s, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        raise LoiLLM("Model tra ve thu khong phai JSON: %s" % s[:200])


def _rut_nguon(kq):
    """Lay danh sach URL tu grounding metadata."""
    ds = []
    try:
        for ung in kq.candidates or []:
            gm = getattr(ung, "grounding_metadata", None)
            if not gm:
                continue
            for c in getattr(gm, "grounding_chunks", None) or []:
                w = getattr(c, "web", None)
                if w and getattr(w, "uri", None):
                    ds.append({"tieu_de": getattr(w, "title", "") or w.uri,
                               "url": w.uri})
    except Exception:
        pass
    # bo trung, giu thu tu
    thay = set()
    ra = []
    for x in ds:
        if x["url"] not in thay:
            thay.add(x["url"])
            ra.append(x)
    return ra
