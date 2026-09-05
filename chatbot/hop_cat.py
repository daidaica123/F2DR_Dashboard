# -*- coding: utf-8 -*-
"""
HOP CAT — chay code pandas do LLM sinh ra, co kiem soat.

25 ham dong san khong bao gio phu het moi cau hoi. Vi du:
  "Trong nhom AML, khach nao vua bi ban nhieu ngay vua dinh tu 2 kich ban
   tro len?"
La giao cua ba dieu kien — khong ham nao lam duoc.

Thay vi bo cuoc, cho LLM tu viet mot bieu thuc pandas. Nhung code do KHONG
duoc tin tuong, nen chay trong hop cat nay voi 5 lop chan:

  1. Chan cu phap  — cam import / open / exec / eval / __ / gan de
  2. Chan ten      — chi cho dung mot danh sach ten da duyet
  3. Chan module   — pd/np boc mat na, moi ham doc/ghi file deu bi chan
  4. Chan cot      — bo han cac cot nhay cam khoi DataFrame
  5. Chan tai nguyen — chan vong lap khong lo va phep noi bang bung no,
                     ngat that su bang trace thay vi chi bo cuoc cho
  6. Hien ra man hinh — nguoi dung doc duoc code da chay, tu kiem chung

Ket qua tra ve luon kem chinh doan code, de nguoi dung soi lai.
"""
import ast
import sys
import threading
import time

import numpy as np
import pandas as pd


class LoiHopCat(Exception):
    """Code khong an toan hoac chay hong."""


# ── Lop 1: cu phap cam tiet doi ──
CAM_NUT = (ast.Import, ast.ImportFrom, ast.Lambda,
           ast.Global, ast.Nonlocal, ast.Delete,
           ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
           ast.With, ast.AsyncWith, ast.Try, ast.Raise,
           ast.While, ast.Await, ast.Yield, ast.YieldFrom)

# Ten ham/thuoc tinh cam — mo duong ra ngoai hop cat
CAM_TEN = {
    "eval", "exec", "compile", "open", "input", "__import__", "globals",
    "locals", "vars", "dir", "getattr", "setattr", "delattr", "hasattr",
    "breakpoint", "memoryview", "help", "exit", "quit", "copyright",
    # Moi duong GHI ra dia. to_html/to_string/to_latex nhan tham so duong dan
    # hoac buf= nen cung ghi file duoc — de sot la thung.
    "to_csv", "to_pickle", "to_excel", "to_json", "to_sql", "to_parquet",
    "to_html", "to_string", "to_latex", "to_markdown", "to_xml",
    "to_feather", "to_hdf", "to_stata", "to_orc", "to_clipboard",
    "to_gbq", "to_records", "tofile", "dump", "dumps", "save", "savez",
    "savetxt",
    # Moi duong DOC tu dia (mat na pd/np da chan, day la lop thu hai)
    "read_csv", "read_pickle", "read_excel", "read_json", "read_sql",
    "read_table", "read_fwf", "read_html", "read_xml", "read_parquet",
    "read_feather", "read_hdf", "read_stata", "read_orc", "read_clipboard",
    "read_sas", "read_spss", "read_gbq", "read_sql_query", "read_sql_table",
    "genfromtxt", "loadtxt", "fromfile", "load", "memmap", "fromstring",
    "eval_", "query_", "pipe", "apply_", "system", "popen", "spawn",
}

# ── Lop 2: chi nhung ten nay duoc dung ──
CHO_PHEP_HAM = {
    # dung san
    "len", "sum", "min", "max", "abs", "round", "sorted", "list", "dict",
    "set", "tuple", "int", "float", "str", "bool", "range", "enumerate",
    "zip", "any", "all", "reversed", "divmod",
    # pandas / numpy — chi qua bien pd, np da chuan bi san
    "pd", "np",
    # bien du lieu
    "d", "kt",
    # ket qua
    "kq",
}

# ── Lop 3: cot BO HAN khoi DataFrame ma code tu sinh nhin thay ──
#
# Bo cot la cach chan kin duy nhat: chan theo TEN thi lach duoc bang vi tri
# (d.iloc[:, -1]) hoac ghep chuoi ('chi_tiet' + '_alert'). Cot khong ton tai
# thi khong duong nao lay duoc.
#
# Danh sach nay do nguoi dung duyet ngay 05/09/2026.
COT_CAM = {
    # Bang chung nghiep vu tho. Doc qua ham bang_chung_alert() — ham do da
    # loc bo truong dinh danh; code tu sinh thi khong loc duoc gi.
    "chi_tiet_alert",

    # ĐIỂM CŨ SAI — cai bay nguy hiem nhat con sot.
    # Hai cot nay tinh tu thoi r=k=0.5, con dashboard dung r=k=0.70. Bot tu
    # viet code doc chung se ra so LECH ma trong van hoan toan hop ly, khong
    # ai soi ra. Bo han thi buoc phai tinh lai bang cong thuc PP-D.
    "last_risk_score",
    "Level",

    # Ban sao cua dinh danh: 1.716/15.581 dong co request_id CHINH LA
    # object_value. Khong ham nao dung toi, AlertID da chua no roi.
    "request_id",

    # Chi mot gia tri duy nhat hoac toan rong — khong phan biet duoc gi,
    # chi lam LLM roi them khi doc danh sach cot.
    "requestor",        # luon la "QTRR"
    "status",           # luon la "0"
    "object_key",       # luon la "userId"
    "reject_reason",    # 100% rong
}


# ── Mat na cho pd / np ──
#
# Dua thang module pandas vao la mo toang cua: pd.read_table, pd.read_fwf,
# pd.read_html, np.genfromtxt, np.fromfile... deu doc duoc file tuy y tren
# dia — ke ca .streamlit/secrets.toml chua khoa API. Danh sach cam theo ten
# khong bao giu duoc, vi ho read_* rat dong va phien ban moi con them.
#
# Nen dao nguoc: chi CHO PHEP dung nhung ten thuc su can cho viec tinh toan.
# Ten khong co trong danh sach thi khong ton tai, du pandas co ho tro.
PD_CHO_PHEP = {
    "DataFrame", "Series", "Index", "MultiIndex", "Categorical",
    "concat", "merge", "crosstab", "pivot_table", "cut", "qcut",
    "to_numeric", "to_datetime", "date_range", "isna", "notna", "isnull",
    "notnull", "unique", "factorize", "NA", "NaT", "Timestamp", "Timedelta",
    "options", "set_option", "get_option", "melt", "get_dummies",
}
NP_CHO_PHEP = {
    "array", "asarray", "arange", "linspace", "zeros", "ones", "full",
    "mean", "median", "std", "var", "sum", "prod", "min", "max", "abs",
    "round", "floor", "ceil", "clip", "where", "unique", "sort", "argsort",
    "argmax", "argmin", "percentile", "quantile", "histogram", "bincount",
    "isnan", "isfinite", "nan", "inf", "log", "log10", "log2", "exp",
    "sqrt", "power", "cumsum", "diff", "corrcoef", "dot", "maximum",
    "minimum", "int64", "float64", "bool_",
}


class _MatNa:
    """Boc mot module, chi cho lay nhung thuoc tinh nam trong danh sach.

    Tra loi 'khong co' cho moi thu khac — code cua LLM se bao loi ro rang
    thay vi lang le doc duoc file no khong duoc phep doc.
    """

    __slots__ = ("_gia", "_cho", "_ten")

    def __init__(self, goc, cho_phep, ten):
        object.__setattr__(self, "_gia", goc)
        object.__setattr__(self, "_cho", cho_phep)
        object.__setattr__(self, "_ten", ten)

    def __getattr__(self, ten):
        cho = object.__getattribute__(self, "_cho")
        if ten not in cho:
            raise AttributeError(
                "%s.%s khong dung duoc trong hop cat. Chi cho phep: %s"
                % (object.__getattribute__(self, "_ten"), ten,
                   ", ".join(sorted(cho)[:14]) + "..."))
        return getattr(object.__getattribute__(self, "_gia"), ten)

    def __setattr__(self, ten, gia_tri):
        raise AttributeError("khong duoc gan thuoc tinh cho %s"
                             % object.__getattribute__(self, "_ten"))

    def __repr__(self):
        return "<%s (han che)>" % object.__getattribute__(self, "_ten")


# ── Lop 5: chan bung no tai nguyen ──
#
# "Het gio" chi CAT CAU TRA LOI, khong cat duoc cong viec: Python khong giet
# duoc thread dang chay. Mot cau hoi bom se de lai thread an CPU/RAM mai
# den khi tien trinh chet — vai cau nhu the la ha duoc server.
#
# Nen phai chan TRUOC khi chay, o tang cu phap:
VONG_LAP_TOI_DA = 2_000_000      # tong so vong for duoc phep (theo hang so)
DONG_TOI_DA = 3_000_000          # so dong ket qua mot phep noi bang


class _KiemTra(ast.NodeVisitor):
    """Duyet cay cu phap, chan moi thu khong nam trong danh sach cho phep."""

    def __init__(self):
        self.loi = []

    def visit(self, nut):
        if isinstance(nut, CAM_NUT):
            self.loi.append("cam dung %s" % type(nut).__name__)
            return
        super().visit(nut)

    def visit_Attribute(self, nut):
        if nut.attr.startswith("_"):
            self.loi.append("cam thuoc tinh bat dau bang _: %s" % nut.attr)
        if nut.attr in CAM_TEN:
            self.loi.append("cam goi %s" % nut.attr)
        self.generic_visit(nut)

    def visit_Name(self, nut):
        if nut.id.startswith("_"):
            self.loi.append("cam ten bat dau bang _: %s" % nut.id)
        if nut.id in CAM_TEN:
            self.loi.append("cam dung %s" % nut.id)
        self.generic_visit(nut)

    def visit_Constant(self, nut):
        if isinstance(nut.value, str) and nut.value in COT_CAM:
            self.loi.append("cam dung cot %s trong code tu sinh" % nut.value)
        # So nguyen khong lo trong ma nguon gan nhu luon la bom: range(10**9),
        # head(10**8)... Khong co cau hoi nghiep vu nao can den chung.
        if isinstance(nut.value, int) and not isinstance(nut.value, bool):
            if abs(nut.value) > VONG_LAP_TOI_DA:
                self.loi.append("so %s qua lon, khong cau hoi nao can den"
                                % nut.value)
        self.generic_visit(nut)

    def visit_For(self, nut):
        """Chan vong for co so vong khong lo.

        `while` da bi cam han. `for` thi van can — duyet mot danh sach ngan
        la viec binh thuong — nhung `for i in range(10**9)` thi khong.
        """
        it = nut.iter
        if (isinstance(it, ast.Call) and isinstance(it.func, ast.Name)
                and it.func.id == "range"):
            for tham in it.args:
                if isinstance(tham, ast.Constant) and isinstance(
                        tham.value, int) and abs(tham.value) > VONG_LAP_TOI_DA:
                    self.loi.append(
                        "range(%s) qua lon (toi da %s)"
                        % (tham.value, VONG_LAP_TOI_DA))
                # range(10**9) viet duoi dang phep luy thua
                if isinstance(tham, ast.BinOp) and isinstance(tham.op,
                                                              ast.Pow):
                    self.loi.append("range() voi phep luy thua — viet ro so")
        self.generic_visit(nut)

    def visit_Call(self, nut):
        """Chan phep noi bang bung no: cross join nhan doi so dong."""
        for tu_khoa in nut.keywords or []:
            if (tu_khoa.arg == "how" and isinstance(tu_khoa.value, ast.Constant)
                    and tu_khoa.value.value == "cross"):
                self.loi.append(
                    "merge(how='cross') tao tich Descartes — bung no so dong")
        # nhan chuoi/danh sach voi so lon: 'x' * 10**9
        self.generic_visit(nut)

    def visit_BinOp(self, nut):
        """Chan nhan chuoi/danh sach voi he so lon."""
        if isinstance(nut.op, ast.Mult):
            for canh in (nut.left, nut.right):
                if (isinstance(canh, ast.Constant)
                        and isinstance(canh.value, int)
                        and not isinstance(canh.value, bool)
                        and abs(canh.value) > 100_000):
                    khac = nut.right if canh is nut.left else nut.left
                    if isinstance(khac, (ast.Constant, ast.List, ast.Str)):
                        self.loi.append("nhan chuoi/danh sach voi he so qua lon")
        if isinstance(nut.op, ast.Pow):
            # 10**9 trong bat ky ngu canh nao
            if (isinstance(nut.right, ast.Constant)
                    and isinstance(nut.right.value, int)
                    and nut.right.value > 7):
                self.loi.append("phep luy thua bac %s — viet ro so thay vi "
                                "dung **" % nut.right.value)
        self.generic_visit(nut)

    def visit_Subscript(self, nut):
        # d["chi_tiet_alert"] — bat qua visit_Constant o tren
        self.generic_visit(nut)


def kiem_an_toan(code):
    """Tra ve danh sach loi. Rong = an toan."""
    if len(code) > 4000:
        return ["code qua dai (%d ky tu, toi da 4000)" % len(code)]
    try:
        cay = ast.parse(code, mode="exec")
    except SyntaxError as e:
        return ["sai cu phap Python: %s" % e.msg]

    kt = _KiemTra()
    kt.visit(cay)

    # Phai co gan vao bien kq
    co_kq = any(isinstance(n, ast.Name) and n.id == "kq" and
                isinstance(n.ctx, ast.Store)
                for n in ast.walk(cay))
    if not co_kq:
        kt.loi.append("code phai gan ket qua vao bien ten 'kq'")

    return kt.loi


def _rut_gon(x, gioi_han=60):
    """Doi ket qua pandas thanh thu JSON hoa duoc, cat bot neu qua dai."""
    if isinstance(x, pd.DataFrame):
        cat = len(x) > gioi_han
        return {
            "dang": "bang",
            "so_dong": int(len(x)),
            "bi_cat": cat,
            "cot": [str(c) for c in x.columns],
            "du_lieu": x.head(gioi_han).to_dict("records"),
        }
    if isinstance(x, pd.Series):
        cat = len(x) > gioi_han
        return {
            "dang": "chuoi",
            "so_dong": int(len(x)),
            "bi_cat": cat,
            "du_lieu": {str(k): (v.item() if hasattr(v, "item") else v)
                        for k, v in x.head(gioi_han).items()},
        }
    if isinstance(x, (np.integer, np.floating, np.bool_)):
        return x.item()
    if isinstance(x, (list, tuple)):
        return [_rut_gon(v, gioi_han) for v in list(x)[:gioi_han]]
    if isinstance(x, dict):
        return {str(k): _rut_gon(v, gioi_han) for k, v in list(x.items())[:gioi_han]}
    return x


def chay(code, d, kt, giay_toi_da=8):
    """Chay code trong hop cat. Tra ve dict ket qua hoac nem LoiHopCat."""
    loi = kiem_an_toan(code)
    if loi:
        raise LoiHopCat("Code khong an toan: " + "; ".join(loi))

    # Ban sao da BO HAN cot cam khoi DataFrame.
    #
    # Bo cot la cach chan duy nhat kin: chan theo TEN cot thi lach duoc bang
    # vi tri (d.iloc[:, -1]) hoac ghep chuoi ('chi_tiet' + '_alert'). Cot
    # khong ton tai thi khong duong nao lay duoc.
    d2 = d.drop(columns=[c for c in COT_CAM if c in d.columns]).copy()

    moi_truong = {
        "__builtins__": {n: __builtins__[n] if isinstance(__builtins__, dict)
                         else getattr(__builtins__, n)
                         for n in CHO_PHEP_HAM
                         if (n in __builtins__ if isinstance(__builtins__, dict)
                             else hasattr(__builtins__, n))},
        # KHONG dua module pd/np day du vao. Chung tu chung da la cua ra I/O:
        # pd.read_table, pd.read_fwf, np.genfromtxt... doc duoc bat ky file
        # nao tren dia, ke ca secrets.toml. Chi dua mot mat na chi co dung
        # nhung ham can cho viec tinh toan.
        "pd": _MatNa(pd, PD_CHO_PHEP, "pd"),
        "np": _MatNa(np, NP_CHO_PHEP, "np"),
        "d": d2,
        "kt": kt,
    }

    ket = {}
    bao_loi = {}
    han_chot = time.monotonic() + giay_toi_da

    class _HetGio(Exception):
        pass

    def _canh(khung, su_kien, doi_so):
        """Trace: goi o moi dong Python. Qua han thi nem loi ngay trong luong.

        Day la cach DUY NHAT ngat that su duoc mot luong Python dang chay.
        Chi bo cuoc cho (join roi di tiep) thi luong van chay tiep, an CPU va
        RAM mai — vai cau hoi bom la ha duoc server.

        Han che con lai: khong ngat duoc khi luong dang o trong mot loi goi C
        dai (vi du mot phep noi bang khong lo). Cho do da chan o tang cu phap
        ben tren, truoc khi code kip chay.
        """
        if time.monotonic() > han_chot:
            raise _HetGio()
        return _canh

    def _chay():
        # KHONG dung threading.settrace: no dat trace cho MOI luong sinh sau,
        # ke ca luong cua Streamlit. Chi dat cho luong nay thoi.
        #
        # Bat BaseException o vong ngoai cung: neu trace kip nem _HetGio sau
        # khi da ra khoi khoi try ben trong (luc dang tra ve, trong khung cua
        # threading.run), Python se in nguyen traceback ra man hinh. Voi app
        # that thi do la rac trong log, va nguoi dung thay app "co loi la".
        try:
            sys.settrace(_canh)
            try:
                exec(compile(ast.parse(code, mode="exec"),
                             "<code_bot>", "exec"), moi_truong, ket)
            finally:
                sys.settrace(None)
        except _HetGio:
            bao_loi["het_gio"] = True
        except BaseException as e:        # loi cua chinh code, khong phai cua ta
            bao_loi["e"] = "%s: %s" % (type(e).__name__, e)

    luong = threading.Thread(target=_chay, daemon=True)
    luong.start()
    luong.join(giay_toi_da + 1.5)         # chua cho trace kip nem loi

    if bao_loi.get("het_gio") or luong.is_alive():
        raise LoiHopCat("Code chay qua %d giay — viet lai cach gon hon"
                        % giay_toi_da)
    if "e" in bao_loi:
        raise LoiHopCat("Code chay loi — %s" % bao_loi["e"])
    if "kq" not in ket:
        raise LoiHopCat("Code chay xong nhung khong co bien 'kq'")

    return {
        "_mo_ta": "Ket qua code do tro ly tu viet (xem phan code de kiem chung)",
        "_code": code,
        "ket_qua": _rut_gon(ket["kq"]),
    }
