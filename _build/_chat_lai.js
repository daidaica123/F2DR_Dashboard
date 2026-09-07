/* ══════════════════════════════════════════════════════════════════════
   LÁI DASHBOARD  —  cho trợ lý cuộn, lọc và tô sáng thay người dùng

   Ý tưởng: trả lời bằng chữ xong thì chỉ luôn chỗ đó trên dashboard. Hỏi
   "top 5 kịch bản từ 01/08 đến 31/08" -> bấm một nút là trang tự cuộn tới
   mục ⑤, bật chế độ chọn khoảng, điền hai mốc ngày, và tô sáng đúng 5
   dòng vừa nói.

   Vì sao KHÔNG tự chạy ngay mà phải bấm nút (chủ dự án chốt):
   người dùng có thể đang xem dở một bộ lọc khác; nhảy đi mà không hỏi là
   cướp mất thao tác của họ. Nút hiện sẵn, bấm mới đi.

   Nguyên tắc khi thêm hành động mới:
     · CHỈ gọi các hàm dashboard đã có sẵn (doiCachNgay, onKhoang, render…)
       — không tự dựng lại logic lọc, không thì hai bên lệch nhau.
     · Mọi hành động phải ĐẢO NGƯỢC được: chụp trạng thái trước khi đổi,
       nút "hoàn tác" trả về y như cũ.
     · Hỏng ở đây không được làm hỏng chat: mọi lối vào đều bọc try.
   ══════════════════════════════════════════════════════════════════════ */
window.F2Lai = (function () {
  "use strict";

  function $(id) { return document.getElementById(id); }

  /* Dashboard khai báo D, CACH_NGAY, THU_GON, GOM_NHOM bằng let/const nên
     chúng KHÔNG nằm trên window — chỉ đọc được bằng tên trần. Bọc trong
     try vì tên trần chưa khai báo thì ném ReferenceError chứ không trả
     undefined như thuộc tính của window. */
  function bien(ten) {
    try { return (0, eval)(ten); } catch (e) { return undefined; }
  }
  function co() {
    return !!$("m5") && !!$("matTu") && typeof window.renderMat === "function";
  }

  /* ───────── tô sáng ─────────
     Hết sau 9 giây rồi tự nhạt: để mãi thì lần hỏi sau không phân biệt
     được cái nào mới, mà xoá ngay thì mắt chưa kịp bắt. */
  var HEN_SANG = null;

  function xoaSang() {
    try {
      var ds = document.querySelectorAll(".f2-sang");
      for (var i = 0; i < ds.length; i++) ds[i].classList.remove("f2-sang");
    } catch (e) { /* không sao */ }
  }

  function toSang(tenKb) {
    if (!tenKb || !tenKb.length) return 0;
    xoaSang();
    clearTimeout(HEN_SANG);

    var chuan = tenKb.map(function (t) {
      return String(t).toLowerCase().replace(/\s+/g, " ").trim();
    });
    var so = 0;
    /* Quét cả bảng mục ⑤ lẫn mục ④: câu trả lời có thể nói về kịch bản
       (⑤) hoặc nhóm nghiệp vụ (④). */
    ["#matBox", "#nhomTbl", "#khTbl"].forEach(function (g) {
      var b = document.querySelector(g);
      if (!b) return;
      var hang = b.querySelectorAll("tbody tr");
      for (var i = 0; i < hang.length; i++) {
        var van = (hang[i].textContent || "").toLowerCase()
                    .replace(/\s+/g, " ").trim();
        for (var j = 0; j < chuan.length; j++) {
          /* So hai chiều: tên trong bảng có thể bị cắt ngắn, mà tên model
             nói ra có thể dài hơn hoặc ngược lại. */
          if (chuan[j].length > 8 &&
              (van.indexOf(chuan[j]) >= 0 ||
               chuan[j].indexOf(van.slice(0, 40)) >= 0)) {
            hang[i].classList.add("f2-sang");
            so++;
            break;
          }
        }
      }
    });
    if (so) HEN_SANG = setTimeout(xoaSang, 9000);
    return so;
  }

  /* ───────── cuộn tới một mục ───────── */
  function cuonToi(id) {
    var el = $(id);
    if (!el) return false;
    el.scrollIntoView({ behavior: "smooth", block: "start" });
    return true;
  }

  /* ───────── chụp / trả lại trạng thái ─────────
     Chỉ chụp những ô mà lệnh có thể đụng tới. Chụp cả trang thì vừa nặng
     vừa dễ trả nhầm thứ người dùng vừa tự đổi. */
  function chup() {
    var t = {};
    try {
      t.qKB = $("qKB") ? $("qKB").value : null;
      t.qKH = $("qKH") ? $("qKH").value : null;
      t.matTu = $("matTu") ? $("matTu").value : null;
      t.matDen = $("matDen") ? $("matDen").value : null;
      t.matNd = $("matNd") ? $("matNd").value : null;
      var cn = bien("CACH_NGAY"), tg = bien("THU_GON"), gn = bien("GOM_NHOM");
      t.cachNgay = cn === undefined ? null : cn;
      t.thuGon = tg === undefined ? null : tg;
      t.gom = gn === undefined ? null : gn;
      t.dayNd = $("dayNd") ? $("dayNd").value : null;
      t.nhomNgay = $("nhomNgay") ? $("nhomNgay").value : null;
      t.khTop = $("khTop") ? $("khTop").value : null;
      t.khNgay = $("khNgay") ? $("khNgay").value : null;
      t.cuon = window.scrollY;
    } catch (e) { /* thiếu ô nào thì bỏ qua ô đó */ }
    return t;
  }

  function traLai(t) {
    if (!t) return;
    try {
      xoaSang();
      if (t.qKB !== null && $("qKB")) $("qKB").value = t.qKB;
      if (t.qKH !== null && $("qKH")) $("qKH").value = t.qKH;
      if (t.matTu !== null && $("matTu")) $("matTu").value = t.matTu;
      if (t.matDen !== null && $("matDen")) $("matDen").value = t.matDen;
      if (t.matNd !== null && $("matNd")) $("matNd").value = t.matNd;
      if (t.dayNd !== null && $("dayNd")) $("dayNd").value = t.dayNd;
      if (t.nhomNgay !== null && $("nhomNgay")) $("nhomNgay").value = t.nhomNgay;
      if (t.khTop !== null && $("khTop")) $("khTop").value = t.khTop;
      if (t.khNgay !== null && $("khNgay")) $("khNgay").value = t.khNgay;

      /* Ba cái này là biến trạng thái, phải bấm nút để đổi chứ không gán
         thẳng — gán thẳng thì nhãn nút và bảng lệch nhau. */
      if (t.cachNgay !== null && bien("CACH_NGAY") !== t.cachNgay &&
          typeof window.doiCachNgay === "function") window.doiCachNgay();
      if (t.thuGon !== null && bien("THU_GON") !== t.thuGon &&
          typeof window.doiThuGon === "function") window.doiThuGon();
      if (t.gom !== null && bien("GOM_NHOM") !== t.gom &&
          typeof window.doiGom === "function") window.doiGom();

      if (typeof window.renderMat === "function") window.renderMat();
      if (typeof window.renderTopKH === "function") window.renderTopKH();
      if (typeof window.renderNhom === "function") window.renderNhom();
      if (typeof window.render === "function" &&
          (t.dayNd !== null)) window.render();
      window.scrollTo({ top: t.cuon, behavior: "smooth" });
    } catch (e) { /* trả không được thì thôi, người dùng tự chỉnh */ }
  }

  /* ───────── các hành động ─────────
     Mỗi hành động trả về một câu ngắn mô tả nó vừa làm gì, để hiện trong
     khung chat — người dùng phải biết trang vừa bị đổi cái gì. */
  var VIEC = {

    /* Đặt khoảng ngày ở mục ⑤ rồi cuộn tới đó. */
    khoang_ngay: function (ts) {
      var tu = chuanNgay(ts.tu), den = chuanNgay(ts.den);
      if (!tu || !den) return null;
      if (bien("CACH_NGAY") !== "khoang" &&
          typeof window.doiCachNgay === "function") window.doiCachNgay();
      $("matTu").value = tu;
      $("matDen").value = den;
      if ($("matNhanh")) $("matNhanh").value = "";
      if (typeof window.onKhoang === "function") window.onKhoang();
      cuonToi("m5");
      return "đặt khoảng " + nhan(tu) + " – " + nhan(den) + " ở mục ⑤";
    },

    /* Lọc theo tên kịch bản ở mục ⑤. */
    loc_kich_ban: function (ts) {
      if (!$("qKB")) return null;
      $("qKB").value = ts.tu_khoa || "";
      if (typeof window.renderMat === "function") window.renderMat();
      cuonToi("m5");
      return ts.tu_khoa ? 'lọc kịch bản chứa "' + ts.tu_khoa + '" ở mục ⑤'
                        : "bỏ lọc kịch bản";
    },

    /* Lọc theo mã khách ở mục ⑥. */
    loc_khach: function (ts) {
      if (!$("qKH")) return null;
      $("qKH").value = ts.tu_khoa || "";
      if (typeof window.renderTopKH === "function") window.renderTopKH();
      cuonToi("m6");
      return ts.tu_khoa ? 'tìm khách "' + String(ts.tu_khoa).slice(0, 14) +
                          '…" ở mục ⑥' : "bỏ lọc khách";
    },

    /* Thu gọn cột ngày — hợp khi vừa nói về tổng cả kỳ. */
    thu_gon: function (ts) {
      if (typeof window.doiThuGon !== "function") return null;
      var muon = ts.bat !== false;
      if (bien("THU_GON") !== muon) window.doiThuGon();
      cuonToi("m5");
      return muon ? "thu gọn cột ngày, chỉ xem tổng" : "hiện lại các cột ngày";
    },

    /* Gom theo nhóm nghiệp vụ. */
    gom_nhom: function (ts) {
      if (typeof window.doiGom !== "function") return null;
      var muon = ts.bat !== false;
      if (bien("GOM_NHOM") !== muon) window.doiGom();
      cuonToi("m5");
      return muon ? "gom kịch bản theo nhóm nghiệp vụ" : "bỏ gom nhóm";
    },

    /* Chỉ cuộn, không đổi gì — dùng khi câu trả lời chỉ cần chỉ chỗ. */
    cuon: function (ts) {
      var m = { "3": "m3", "4": "m4", "5": "m5", "6": "m6", "7": "m7",
                "8": "m8", "cong_thuc": "m1c", "phan_bo": "m2c" };
      var id = m[String(ts.muc)] || "m5";
      if (!cuonToi(id)) return null;
      return "cuộn tới mục " + (ts.muc || 5);
    }
  };

  function chuanNgay(s) {
    s = String(s || "").trim();
    var m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (m) return m[0];
    var d = bien("D");
    m = s.match(/^(\d{1,2})[\/-](\d{1,2})(?:[\/-](\d{4}))?$/);
    if (m && d && d.days) {
      var nam = m[3] || d.days[0].slice(0, 4);
      return nam + "-" + ("0" + m[2]).slice(-2) + "-" + ("0" + m[1]).slice(-2);
    }
    return null;
  }

  function nhan(s) {
    return s ? s.slice(8, 10) + "/" + s.slice(5, 7) : s;
  }

  return {
    dungDuoc: co,

    /* Chạy một chuỗi lệnh. Trả về {moTa, hoanTac} để giao diện vẽ nút. */
    chay: function (dsLenh, tenKbToSang) {
      if (!co() || !dsLenh || !dsLenh.length) return null;
      var truoc = chup(), da = [];
      try {
        dsLenh.forEach(function (l) {
          var f = VIEC[l.viec];
          if (!f) return;
          var s = f(l.tham_so || {});
          if (s) da.push(s);
        });
        /* Tô sáng SAU cùng: bảng phải vẽ lại xong mới có dòng để tô. */
        if (tenKbToSang && tenKbToSang.length) {
          setTimeout(function () {
            var n = toSang(tenKbToSang);
            if (n) {
              var e = document.querySelector(".f2-sang");
              if (e && !da.length) e.scrollIntoView({ behavior: "smooth",
                                                      block: "center" });
            }
          }, 260);
        }
      } catch (e) {
        return null;
      }
      if (!da.length) return null;
      return {
        moTa: da.join(" · "),
        hoanTac: function () { traLai(truoc); }
      };
    },

    toSang: toSang,
    xoaSang: xoaSang,
    danhSachViec: Object.keys(VIEC)
  };
})();
