/* ══════════════════════════════════════════════════════════════════════
   TRI THỨC — bản JavaScript của tầng dữ liệu.

   Đọc thẳng biến `D` mà dashboard đã nhúng sẵn: 35 kịch bản kèm chuỗi alert
   từng ngày, 7 nhóm nghiệp vụ, 9.174 lượt, top 80 khách. Không phải tải
   file CSV về — mọi thứ đã tính sẵn trong trang.

   Đây là bản đối chiếu của chatbot/truy_van.py. Ba quy tắc bắt buộc giống
   hệt bên đó, sai một cái là ra số sai mà không ai biết:

     1. Đếm alert = SỐ DÒNG. Dữ liệu không có khoá duy nhất nào; `AlertID`
        ghép từ ngày + request_id nên trùng được. Ở đây đã tính sẵn trong D
        nên chỉ cần cộng đúng.

     2. Đếm khách = số mã RIÊNG BIỆT, không cộng ngang các nhóm. Một khách
        dính hai nhóm vẫn chỉ là một người.

     3. Điểm luôn TÍNH LẠI bằng công thức PP-D với r = k = 0,70.

   Mỗi hàm trả về object có khoá `_mo_ta` — câu tiếng Việt nói rõ vừa tính
   gì, để LLM diễn đạt lại và người dùng kiểm chứng.
   ══════════════════════════════════════════════════════════════════════ */
window.F2TriThuc = (function () {
  "use strict";

  /* `D` là biến toàn cục do dashboard khai báo. Khai báo bằng `const` ở
     tầng ngoài cùng nên không nằm trong window, nhưng vẫn tra được bằng tên. */
  function duLieu() {
    if (typeof D === "undefined") throw new Error("Chưa thấy dữ liệu dashboard");
    return D;
  }

  var THU = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];
  function thu(iso) {
    var g = new Date(iso + "T00:00:00").getDay();
    return THU[g];
  }
  function nhan(iso) { return iso.slice(8, 10) + "/" + iso.slice(5, 7); }
  function lam(x, n) { var m = Math.pow(10, n || 1); return Math.round(x * m) / m; }

  /* ───────── bỏ dấu, dùng để so khớp tên kịch bản gõ tắt ───────── */
  function bo(s) {
    return String(s == null ? "" : s)
      .replace(/^\[(SCORE|NEW)\]_/, "")
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/đ/g, "d").replace(/Đ/g, "D")
      .toLowerCase().replace(/[^a-z0-9]/g, "");
  }
  function boCoKhoang(s) {
    return String(s == null ? "" : s)
      .replace(/^\[(SCORE|NEW)\]_/, "")
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/đ/g, "d").replace(/Đ/g, "D")
      .toLowerCase().replace(/[^a-z0-9 ]/g, " ");
  }

  var TU_CHUNG = ["kh", "tk", "tb", "cua", "co", "va", "cac", "trong", "cung",
                  "khach", "hang", "gd", "so", "1", "n", "bat", "thuong"];

  /* Khớp mờ tên kịch bản. Trả về {ten} hoặc {ungVien:[...]} khi khớp nhiều. */
  function timKichBan(ten) {
    var d = duLieu(), q = bo(ten);
    if (!q) return { ungVien: [] };

    for (var i = 0; i < d.kb.length; i++) {
      if (bo(d.kb[i].ten) === q) return { ten: d.kb[i].ten };
    }
    var chua = d.kb.filter(function (k) { return bo(k.ten).indexOf(q) >= 0; });
    if (chua.length === 1) return { ten: chua[0].ten };
    if (chua.length > 1) {
      chua.sort(function (a, b) { return bo(a.ten).length - bo(b.ten).length; });
      if (bo(chua[0].ten).length * 1.5 < bo(chua[1].ten).length)
        return { ten: chua[0].ten };
      return { ungVien: chua.slice(0, 5).map(function (k) { return k.ten; }) };
    }

    /* Độ trùng từ, dùng Jaccard (giao / hợp). Chia cho số từ người dùng gõ
       thì một tên dài đầy đủ sẽ khớp nhầm sang kịch bản ngắn cùng nhóm chỉ
       vì trùng mấy từ đầu. */
    function tuCua(s) {
      return boCoKhoang(s).split(/\s+/).filter(function (t) {
        return t.length > 1 && TU_CHUNG.indexOf(t) < 0;
      });
    }
    var tu = tuCua(ten);
    if (!tu.length) return { ungVien: [] };
    var diem = [];
    d.kb.forEach(function (k) {
      var tk = tuCua(k.ten);
      if (!tk.length) return;
      var giao = tu.filter(function (t) { return tk.indexOf(t) >= 0; }).length;
      var hop = new Set(tu.concat(tk)).size;
      var ty = giao / hop;
      if (ty >= 0.55) diem.push([ty, k.ten]);
    });
    if (!diem.length) return { ungVien: [] };
    diem.sort(function (a, b) { return b[0] - a[0]; });
    if (diem.length === 1 || diem[0][0] > diem[1][0] + 0.15)
      return { ten: diem[0][1] };
    return { ungVien: diem.slice(0, 5).map(function (x) { return x[1]; }) };
  }

  function chiSoNgay(ngay) {
    var d = duLieu(), s = String(ngay).trim();
    var i = d.days.indexOf(s);
    if (i < 0) {
      /* "Chưa có dữ liệu" KHÁC HẲN "có dữ liệu và bằng 0" — với dashboard
         rủi ro, nhầm hai cái là nhầm giữa "hệ thống sạch" và "chưa biết
         gì". Nói rõ ngày đó rơi vào đâu để model không trả lời thành 0. */
      var d0 = d.days[0], d1 = d.days[d.days.length - 1], vi;
      if (s < d0) {
        vi = "TRƯỚC kỳ dữ liệu — kỳ này chỉ bắt đầu từ " + d0 + ".";
      } else if (s > d1) {
        vi = "SAU kỳ dữ liệu — dữ liệu mới nhất là " + d1 +
             ". Ngày này CHƯA CÓ DỮ LIỆU, không phải bằng 0.";
      } else {
        vi = "nằm trong kỳ nhưng KHÔNG CÓ trong dữ liệu (ngày hụt). " +
             "Đây là thiếu dữ liệu, KHÔNG phải ngày 0 alert.";
      }
      throw new Error("Ngày " + s + " " + vi +
        " Kỳ dữ liệu: " + d0 + " đến " + d1 + " (" + d.days.length + " ngày). " +
        "TUYỆT ĐỐI không trả lời là 0 alert — hãy nói rõ là chưa có dữ liệu.");
    }
    return i;
  }

  /* ───────── công thức PP-D hai tầng ─────────
     Bản đối chiếu của chatbot/diem.py. Đã kiểm khớp từng lượt với bản
     Python: 9.174/9.174 lượt, sai lệch 0. */
  function hieuLuc(base, cap, n, r) {
    return cap <= base ? base : cap - (cap - base) * Math.pow(r, n - 1);
  }
  function diemLuot(picks, r, k) {
    var d = duLieu(), es = [];
    for (var i = 0; i < picks.length; i += 2) {
      var kb = d.kb[picks[i]];
      es.push(hieuLuc(kb.sc, kb.cap, picks[i + 1], r));
    }
    if (!es.length) return 0;
    var M = Math.max.apply(null, es), tich = 1, daDung = false;
    es.forEach(function (e) {
      if (!daDung && e === M) { daDung = true; return; }
      tich *= (1 - e / 100);
    });
    return Math.min(100, Math.max(0, M + (100 - M) * k * (1 - tich)));
  }
  /* ───────── r, k và ngưỡng ĐANG ĐẶT trên trang ─────────
     Trước đây bot luôn dùng d.r / d.k / d.nguong — giá trị chốt lúc build —
     và còn nói với model rằng chúng "CỐ ĐỊNH". Nhưng cả ba thanh trượt trên
     dashboard sinh ra để thử "nếu ngưỡng là 82 thì sao". Người dùng kéo sang
     82 rồi hỏi "ai là Very High", bot trả lời theo 80 mà không ai biết —
     hai bên nói hai chuyện khác nhau trong im lặng. Giờ bot đọc đúng thứ
     đang hiện trên màn hình. Bản deploy không có thanh trượt nên tự lùi về
     giá trị build, không hỏng. */
  function thamSoDiem() {
    var d = duLieu();
    var g = (typeof document !== "undefined") ? document : null;
    function lay(id, mac, chia) {
      if (!g) return mac;
      var e = g.getElementById(id);
      if (!e || e.value === "" || e.value === null || isNaN(+e.value)) return mac;
      var v = +e.value;
      return chia ? v / chia : v;
    }
    return {
      r: lay("pR", d.r, 100),
      k: lay("pK", d.k, 100),
      nguong: [lay("tLM", d.nguong[0]),
               lay("tMH", d.nguong[1]),
               lay("tHV", d.nguong[2])],
      mac_dinh: { r: d.r, k: d.k, nguong: d.nguong }
    };
  }
  function daDoiThamSo(p) {
    return p.r !== p.mac_dinh.r || p.k !== p.mac_dinh.k ||
           p.nguong.join() !== p.mac_dinh.nguong.join();
  }

  var TEN_MUC = ["Low", "Medium", "High", "Very High"];
  /* So ngưỡng bằng ĐIỂM THẬT. Trần điểm là tiệm cận nên một kịch bản gốc 70
     trần 80 lặp nhiều lần chỉ tới 79,99x — làm tròn trước khi so sẽ đẩy nó
     thành 80,0 và ở ngưỡng 80 thì bị xếp nhầm Very High. */
  /* KHÔNG ghim khi so ngưỡng: 79,999999999966 là điểm THẬT của một kịch bản
     lặp ~75 lần, chưa chạm 80. Ghim lên là dựng lại đúng lỗi vừa sửa. */
  function chuanDiem(s) { return s; }
  /* Cắt xuống 1 chữ số CHỈ để hiển thị; epsilon chỉ gạt bụi của phép nhân 10. */
  function catDiem(s) {
    return Math.floor(s * 10 + 1e-9) / 10;
  }
  function mucDiem(diem, ng) {
    var s = chuanDiem(diem);
    return s < ng[0] ? 0 : s < ng[1] ? 1 : s < ng[2] ? 2 : 3;
  }

  function phamVi(ngay) {
    var d = duLieu();
    return ngay
      ? "ngày " + nhan(ngay) + " (" + thu(ngay) + ")"
      : "toàn kỳ " + d.tong.nd + " ngày (" + nhan(d.tong.d0) + " – " +
        nhan(d.tong.d1) + ")";
  }

  /* ══════════ LỌC THEO KHOẢNG NGÀY ══════════
     Trước đây các hàm chỉ nhận `ngay` (một ngày duy nhất). Hỏi "từ 01/08 đến
     31/08" thì không có tham số nào nhận được, model đành bịa lý do "khoảng
     này không nằm trong kỳ" — sai mà nghe rất chắc, đúng kiểu hỏng tệ nhất.
     Nay mọi hàm thống kê đều nhận thêm {tu, den}.

     Trả về danh sách CHỈ SỐ ngày, hoặc null nếu không lọc (= toàn kỳ). */
  function chiSoKhoang(ts) {
    ts = ts || {};
    var d = duLieu();
    if (ts.ngay) {                       // một ngày — giữ cách gọi cũ
      var j = chiSoNgay(ts.ngay);
      return [j];
    }
    if (!ts.tu && !ts.den) return null;  // không lọc
    /* Kẹp vào trong kỳ thay vì báo lỗi: hỏi "tháng 8" mà kỳ bắt đầu 15/08
       thì trả 15/08–31/08 kèm ghi chú, hữu ích hơn là từ chối trả lời. */
    var tu = ts.tu ? chuanNgay(ts.tu) : d.days[0];
    var den = ts.den ? chuanNgay(ts.den) : d.days[d.days.length - 1];
    if (tu > den) { var t = tu; tu = den; den = t; }
    var ds = [];
    for (var i = 0; i < d.days.length; i++)
      if (d.days[i] >= tu && d.days[i] <= den) ds.push(i);
    return ds;
  }

  /* Nhận 2026-08-01, 01/08/2026, 01/08 -> 2026-08-01 */
  function chuanNgay(s) {
    s = String(s || '').trim();
    var m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (m) return m[0];
    var d = duLieu();
    m = s.match(/^(\d{1,2})[\/-](\d{1,2})(?:[\/-](\d{4}))?$/);
    if (m) {
      var nam = m[3] || d.days[0].slice(0, 4);
      return nam + '-' + ('0' + m[2]).slice(-2) + '-' + ('0' + m[1]).slice(-2);
    }
    return s;
  }

  /* Mô tả phạm vi cho _mo_ta, kèm cảnh báo nếu khoảng hỏi vượt ra ngoài kỳ */
  function moTaKhoang(ts, idx) {
    var d = duLieu();
    if (idx === null) return phamVi(null);
    if (idx.length === 1) return phamVi(d.days[idx[0]]);
    if (!idx.length) return 'KHÔNG có ngày nào trong khoảng này';
    var t = nhan(d.days[idx[0]]), s = nhan(d.days[idx[idx.length - 1]]);
    var goc = ts.tu ? chuanNgay(ts.tu) : null;
    var goc2 = ts.den ? chuanNgay(ts.den) : null;
    var them = '';
    if ((goc && goc < d.days[0]) || (goc2 && goc2 > d.days[d.days.length - 1]))
      them = ' (khoảng hỏi rộng hơn kỳ dữ liệu, đã cắt về phần có thật)';
    return 'từ ' + t + ' đến ' + s + ' — ' + idx.length + ' ngày' + them;
  }

  /* Cộng alert của một kịch bản trong các ngày idx */
  function congKB(k, idx) {
    if (idx === null) return { alert: k.alert, khach: k.kh };
    var a = 0, kh = 0;
    for (var i = 0; i < idx.length; i++) { a += k.v[idx[i]]; kh += k.vkh[idx[i]]; }
    return { alert: a, khach: kh };
  }

  /* ══════════════════ DANH MỤC HÀM ══════════════════ */
  var H = {};

  H.tong_quan = function () {
    var d = duLieu();
    var al = d.ngay.map(function (x) { return x.alert; });
    var mx = Math.max.apply(null, al), mn = Math.min.apply(null, al);
    return {
      _mo_ta: "Tổng quan " + phamVi(null),
      ky: d.tong.d0 + " đến " + d.tong.d1,
      so_ngay: d.tong.nd,
      tong_alert: d.tong.alert,
      tong_khach: d.tong.kh,
      tong_luot: d.tong.luot,
      so_kich_ban_co_alert: d.tong.kb,
      so_kich_ban_cau_hinh: d.tong.kbCauHinh,
      so_nhom: d.nhom.length,
      alert_tb_moi_ngay: d.tong.tbNgay,
      ngay_cao_nhat: d.ngay[al.indexOf(mx)].ngay,
      alert_ngay_cao_nhat: mx,
      ngay_thap_nhat: d.ngay[al.indexOf(mn)].ngay,
      alert_ngay_thap_nhat: mn,
      alert_moi_khach: lam(d.tong.alert / d.tong.kh, 2)
    };
  };

  H.alert_theo_ngay = function () {
    var d = duLieu(), tb = d.tong.tbNgay;
    return {
      _mo_ta: "Alert từng ngày trong " + phamVi(null),
      trung_binh_ngay: tb,
      cac_ngay: d.ngay.map(function (x) {
        return {
          ngay: x.ngay, thu: thu(x.ngay), alert: x.alert, khach: x.kh,
          khach_moi: x.khMoi, kich_ban_no: x.kb,
          alert_moi_khach: lam(x.alert / x.kh, 2),
          so_voi_tb: lam(x.alert / tb, 2)
        };
      })
    };
  };

  /* Gom alert theo TUẦN hoặc THÁNG — chỉ có nghĩa khi kỳ đủ dài.
     Kỳ 7 ngày thì gom tuần ra đúng một dòng, vô ích; nhưng kỳ vài chục ngày
     thì "tuần này so tuần trước" là câu hỏi tự nhiên nhất, mà so từng ngày
     lại nhiễu vì cuối tuần luôn thấp hơn ngày thường.
     Tự chặn khi kỳ quá ngắn thay vì trả về một dòng rồi để model tự diễn
     giải thành xu hướng. */
  H.gom_theo_ky = function (ts) {
    var d = duLieu();
    var muc = (ts && ts.muc) || "tuan";
    if (muc !== "tuan" && muc !== "thang")
      throw new Error("muc phải là 'tuan' hoặc 'thang'");
    var toiThieu = muc === "tuan" ? 14 : 45;
    if (d.tong.nd < toiThieu) {
      return {
        _mo_ta: "Kỳ chỉ có " + d.tong.nd + " ngày",
        _khong_du_dai: true,
        _giai_thich: "Gom theo " + (muc === "tuan" ? "tuần" : "tháng") +
          " cần ít nhất " + toiThieu + " ngày mới so sánh được. Kỳ này " +
          d.tong.nd + " ngày — dùng alert_theo_ngay hoặc so_sanh_ngay."
      };
    }
    /* Khoá gom: tuần lấy thứ Hai đầu tuần, tháng lấy YYYY-MM */
    function khoa(s) {
      if (muc === "thang") return s.slice(0, 7);
      var t = new Date(s + "T00:00:00");
      var g = t.getDay();                       // 0 = CN
      t.setDate(t.getDate() - (g === 0 ? 6 : g - 1));
      /* Ghép tay từ giờ địa phương — toISOString() quy về UTC nên ở múi +7
         sẽ lùi mất một ngày, thứ Hai hoá Chủ nhật tuần trước. */
      return t.getFullYear() + "-" +
        ("0" + (t.getMonth() + 1)).slice(-2) + "-" +
        ("0" + t.getDate()).slice(-2);
    }
    var gom = {}, thuTu = [];
    d.ngay.forEach(function (x) {
      var k = khoa(x.ngay);
      if (!gom[k]) { gom[k] = { k: k, alert: 0, nd: 0, kh: 0, khMoi: 0 };
                     thuTu.push(k); }
      gom[k].alert += x.alert; gom[k].nd++;
      gom[k].kh += x.kh; gom[k].khMoi += x.khMoi;
    });
    var ds = thuTu.map(function (k) {
      var g = gom[k];
      return {
        ky: muc === "thang" ? g.k : "tuần từ " + g.k,
        so_ngay: g.nd,
        alert: g.alert,
        alert_moi_ngay: lam(g.alert / g.nd, 1),
        /* Cộng ngang số khách của từng ngày KHÔNG ra số người thật — một
           người bị bắt 3 ngày sẽ đếm 3 lần. Gọi đúng tên là 'lượt'. */
        luot_khach: g.kh,
        khach_lan_dau: g.khMoi
      };
    });
    for (var i = 1; i < ds.length; i++) {
      var tr = ds[i - 1].alert_moi_ngay;
      ds[i].so_ky_truoc_phan_tram = tr ? lam((ds[i].alert_moi_ngay - tr) / tr * 100, 1) : null;
    }
    return {
      _mo_ta: "Alert gom theo " + (muc === "tuan" ? "TUẦN" : "THÁNG") +
              " trong " + phamVi(null),
      _ghi_chu: "So sánh dùng alert_moi_ngay chứ không dùng tổng: kỳ đầu và " +
        "kỳ cuối thường thiếu ngày nên tổng không so được với nhau. " +
        "'luot_khach' là lượt (khách × ngày), KHÔNG phải số người riêng biệt.",
      cac_ky: ds
    };
  };

  H.ngay_bat_thuong = function (ts) {
    var d = duLieu(), ng = (ts && ts.nguong) || 1.3, tb = d.tong.tbNgay;
    var cao = [], thap = [];
    d.ngay.forEach(function (x) {
      var ty = x.alert / tb;
      var m = { ngay: x.ngay, thu: thu(x.ngay), alert: x.alert,
                so_voi_tb: lam(ty, 2) };
      if (ty >= ng) cao.push(m); else if (ty <= 1 / ng) thap.push(m);
    });
    return {
      _mo_ta: "Ngày bất thường (lệch từ " + ng + " lần trở lên so trung bình)",
      trung_binh_ngay: tb, nguong_ap_dung: ng,
      ngay_cao: cao.sort(function (a, b) { return b.alert - a.alert; }),
      ngay_thap: thap.sort(function (a, b) { return a.alert - b.alert; })
    };
  };

  H.so_sanh_ngay = function (ts) {
    var d = duLieu();
    if (!ts || !ts.ngay_a || !ts.ngay_b)
      throw new Error("Cần chỉ rõ hai ngày để so sánh");
    /* LUÔN sắp theo thời gian, bất kể người gọi truyền thứ tự nào. Không thì
       nhãn tăng/giảm đảo nghĩa: số đúng nhưng người đọc kết luận ngược. */
    var ia = chiSoNgay(ts.ngay_a), ib = chiSoNgay(ts.ngay_b);
    var it = Math.min(ia, ib), is = Math.max(ia, ib);
    var T = d.ngay[it], S = d.ngay[is];

    var lech = d.kb.map(function (k) {
      return { kich_ban: k.ten, ngay_truoc: k.v[it], ngay_sau: k.v[is],
               thay_doi: k.v[is] - k.v[it] };
    }).filter(function (x) { return x.thay_doi !== 0; });
    lech.sort(function (a, b) { return a.thay_doi - b.thay_doi; });

    return {
      _mo_ta: "So ngày " + nhan(T.ngay) + " (trước) với ngày " +
              nhan(S.ngay) + " (sau)",
      _ghi_chu_thu_tu: "Hai ngày đã sắp theo THỜI GIAN. 'thay_doi' = ngày sau " +
        "trừ ngày trước: âm là GIẢM, dương là TĂNG.",
      ngay_truoc: { ngay: T.ngay, thu: thu(T.ngay), alert: T.alert,
                    khach: T.kh, kich_ban_no: T.kb },
      ngay_sau: { ngay: S.ngay, thu: thu(S.ngay), alert: S.alert,
                  khach: S.kh, kich_ban_no: S.kb },
      thay_doi_alert: S.alert - T.alert,
      thay_doi_phan_tram: T.alert ? lam((S.alert - T.alert) / T.alert * 100, 1) : null,
      chieu: S.alert < T.alert ? "giảm" : S.alert > T.alert ? "tăng" : "không đổi",
      kich_ban_giam_manh_nhat: lech.slice(0, 6),
      kich_ban_tang_manh_nhat: lech.slice().reverse().slice(0, 6),
      kich_ban_tat_han: d.kb.filter(function (k) {
        return k.v[it] > 0 && k.v[is] === 0;
      }).map(function (k) {
        return { kich_ban: k.ten, ngay_truoc: k.v[it], ngay_sau: 0 };
      }).sort(function (a, b) { return b.ngay_truoc - a.ngay_truoc; }),
      kich_ban_moi_xuat_hien: d.kb.filter(function (k) {
        return k.v[it] === 0 && k.v[is] > 0;
      }).map(function (k) {
        return { kich_ban: k.ten, ngay_truoc: 0, ngay_sau: k.v[is] };
      }).sort(function (a, b) { return b.ngay_sau - a.ngay_sau; })
    };
  };

  H.top_kich_ban = function (ts) {
    var d = duLieu(); ts = ts || {};
    var n = ts.n || 10;
    var idx = chiSoKhoang(ts);           // null = toàn kỳ, [j] = 1 ngày, [..] = khoảng
    var ds = d.kb.filter(function (k) {
      return !ts.nhom || k.nhom === ts.nhom;
    }).map(function (k) {
      var c = congKB(k, idx);
      return { ten: k.ten, nhom: k.nhom, muc: k.lv, diem_goc: k.sc,
               alert: c.alert, khach: c.khach };
    }).filter(function (k) { return k.alert > 0; });
    ds.sort(function (a, b) { return b.alert - a.alert; });

    var tong = idx === null
      ? d.tong.alert
      : idx.reduce(function (a, j) { return a + d.ngay[j].alert; }, 0);
    return {
      _mo_ta: "Top " + n + " kịch bản nhiều alert nhất, " + moTaKhoang(ts, idx) +
              (ts.nhom ? ", nhóm " + ts.nhom : ""),
      /* 'khach' là LƯỢT khách cộng qua các ngày, KHÔNG phải số người riêng
         biệt: một người bị bắt 3 ngày thì đếm 3 lượt. Nói rõ để model không
         diễn giải thành 'có bấy nhiêu khách hàng'. */
      _ghi_chu: idx === null || idx.length === 1 ? undefined
        : "'khach' là LƯỢT (khách × ngày) cộng qua " + idx.length +
          " ngày, không phải số người riêng biệt.",
      so_ngay_trong_pham_vi: idx === null ? d.tong.nd : idx.length,
      tong_alert_pham_vi: tong,
      so_kich_ban_co_alert: ds.length,
      danh_sach: ds.slice(0, n).map(function (k, i) {
        return {
          hang: i + 1, kich_ban: k.ten, nhom: k.nhom, muc: k.muc,
          diem_goc: k.diem_goc, alert: k.alert, khach: k.khach,
          alert_moi_khach: k.khach ? lam(k.alert / k.khach, 2) : 0,
          phan_tram_tong: tong ? lam(k.alert / tong * 100, 1) : 0
        };
      })
    };
  };

  H.chi_tiet_kich_ban = function (ts) {
    var d = duLieu();
    if (!ts || !ts.ten) throw new Error("Cần tên kịch bản");
    var kq = timKichBan(ts.ten);
    if (!kq.ten) {
      throw new Error(kq.ungVien.length
        ? "Tên '" + ts.ten + "' khớp nhiều kịch bản: " + kq.ungVien.join("; ")
        : "Không tìm thấy kịch bản nào tên giống '" + ts.ten + "'");
    }
    var k = d.kb.filter(function (x) { return x.ten === kq.ten; })[0];
    return {
      _mo_ta: "Chi tiết kịch bản '" + k.ten + "' trong " + phamVi(null),
      kich_ban: k.ten, nhom: k.nhom, muc_do: k.lv,
      diem_goc: k.sc, tran_diem: k.cap,
      tong_alert: k.alert, tong_khach: k.kh,
      alert_moi_khach: lam(k.alert / k.kh, 2),
      phan_tram_toan_ky: lam(k.alert / d.tong.alert * 100, 2),
      alert_tung_ngay: d.days.map(function (g, i) {
        return { ngay: g, thu: thu(g), alert: k.v[i] };
      }),
      trung_binh_ngay: k.tb,
      ngay_cao_nhat: k.ngayDinh,
      alert_ngay_cao_nhat: k.dinh,
      ty_le_dot_bien: k.dot
    };
  };

  H.kich_ban_dot_bien = function (ts) {
    var d = duLieu();
    var ng = (ts && ts.nguong) || d.cauhinh.dotbien;
    var ds = d.kb.filter(function (k) {
      return k.alert >= 20 && k.dot >= ng;
    }).map(function (k) {
      return { kich_ban: k.ten, nhom: k.nhom, tong_alert: k.alert,
               trung_binh_ngay: k.tb, dinh: k.dinh, ngay_dinh: k.ngayDinh,
               ty_le: k.dot };
    }).sort(function (a, b) { return b.ty_le - a.ty_le; });
    return {
      _mo_ta: "Kịch bản đột biến: ngày cao nhất gấp từ " + ng +
              " lần mức thường, và có ít nhất 20 alert",
      nguong_ap_dung: ng, so_kich_ban: ds.length, danh_sach: ds
    };
  };

  H.kich_ban_ban_day = function (ts) {
    var d = duLieu();
    var ng = (ts && ts.nguong) || d.cauhinh.apk;
    var ds = d.kb.filter(function (k) {
      return k.alert >= 20 && k.apk >= ng;
    }).map(function (k) {
      return { kich_ban: k.ten, nhom: k.nhom, alert: k.alert, khach: k.kh,
               alert_moi_khach: k.apk };
    }).sort(function (a, b) { return b.alert_moi_khach - a.alert_moi_khach; });
    return {
      _mo_ta: "Kịch bản bắn dày: từ " + ng + " alert mỗi khách trở lên",
      nguong_ap_dung: ng, so_kich_ban: ds.length, danh_sach: ds
    };
  };

  H.kich_ban_im_lang = function () {
    var d = duLieu();
    var theoNhom = d.nhom.map(function (n) {
      return { nhom: n.ten, kich_ban_co_alert: n.kb,
               kich_ban_cau_hinh: n.kbTong,
               so_kich_ban_im_lang: Math.max(0, n.kbTong - n.kb) };
    }).filter(function (x) { return x.so_kich_ban_im_lang > 0; })
      .sort(function (a, b) { return b.so_kich_ban_im_lang - a.so_kich_ban_im_lang; });
    return {
      _mo_ta: "Kịch bản đã cấu hình lên F2DR nhưng không có alert nào trong " +
              phamVi(null),
      so_kich_ban_im_lang: d.tong.kbCauHinh - d.tong.kb,
      so_kich_ban_co_alert: d.tong.kb,
      so_kich_ban_cau_hinh: d.tong.kbCauHinh,
      theo_nhom: theoNhom,
      ghi_chu: "Nhóm đã cấu hình kịch bản mà không có alert nào thường là " +
               "dấu hiệu kịch bản chưa chạy, cần kiểm tra."
    };
  };

  H.kich_ban_im_lang_trong_ngay = function (ts) {
    var d = duLieu();
    var g = (ts && ts.ngay) || d.days[d.days.length - 1];
    var j = chiSoNgay(g);
    var ds = d.kb.filter(function (k) { return k.v[j] === 0 && k.alert > 0; })
      .map(function (k) {
        return { kich_ban: k.ten, nhom: k.nhom, alert_ca_ky: k.alert,
                 so_ngay_co_alert: k.v.filter(function (x) { return x > 0; }).length,
                 trung_binh_moi_ngay: k.tb,
                 alert_hut_so_voi_trung_binh: k.tb };
      }).sort(function (a, b) { return b.alert_ca_ky - a.alert_ca_ky; });
    var hut = ds.reduce(function (a, x) { return a + x.trung_binh_moi_ngay; }, 0);
    return {
      _mo_ta: "Kịch bản im lặng trong ngày " + nhan(g),
      ngay: g, thu: thu(g),
      alert_ngay_nay: d.ngay[j].alert,
      trung_binh_ky: d.tong.tbNgay,
      so_kich_ban_im_lang: ds.length,
      danh_sach: ds,
      tong_alert_hut_uoc_tinh: lam(hut, 1),
      ghi_chu: "Kịch bản có alert đều cả kỳ mà im hẳn một ngày thường là " +
               "dấu hiệu job không chạy hoặc dữ liệu về muộn, KHÔNG phải " +
               "hành vi gian lận giảm. Cần kiểm tra job trước khi kết luận."
    };
  };

  H.xu_huong_kich_ban = function (ts) {
    var d = duLieu();
    if (!ts || !ts.ten) throw new Error("Cần tên kịch bản");
    var kq = timKichBan(ts.ten);
    if (!kq.ten) {
      throw new Error(kq.ungVien.length
        ? "Tên '" + ts.ten + "' khớp nhiều kịch bản: " + kq.ungVien.join("; ")
        : "Không tìm thấy kịch bản nào tên giống '" + ts.ten + "'");
    }
    var k = d.kb.filter(function (x) { return x.ten === kq.ten; })[0];
    var n = k.v.length;
    if (n < 2) throw new Error("Kỳ dữ liệu chỉ có " + n + " ngày, chưa đủ xét xu hướng");
    /* Chia đôi CÓ CHỒNG LẤN ở giữa khi số ngày lẻ, thay vì bỏ ngày giữa ra
       khỏi cả hai nửa — đúng lúc đó là ngày đỉnh thì kết luận sai hẳn. */
    var nuaDau = k.v.slice(0, Math.ceil(n / 2));
    var nuaCuoi = k.v.slice(Math.floor(n / 2));
    var c = function (a) { return a.reduce(function (x, y) { return x + y; }, 0) / a.length; };
    var dau = c(nuaDau), cuoi = c(nuaCuoi);
    return {
      _mo_ta: "Xu hướng của kịch bản '" + k.ten + "' qua " + n + " ngày",
      kich_ban: k.ten,
      chuoi_ngay: d.days.map(function (g, i) {
        return { ngay: g, thu: thu(g), alert: k.v[i] };
      }),
      trung_binh_nua_dau: lam(dau, 1),
      trung_binh_nua_cuoi: lam(cuoi, 1),
      so_ngay_nua_dau: nuaDau.length,
      so_ngay_nua_cuoi: nuaCuoi.length,
      thay_doi_phan_tram: dau ? lam((cuoi - dau) / dau * 100, 1) : null,
      chieu_huong: cuoi > dau * 1.1 ? "tăng" : cuoi < dau * 0.9 ? "giảm" : "ổn định",
      ghi_chu: "So trung bình nửa đầu kỳ với nửa cuối kỳ. Kỳ " + n + " ngày" +
        (n % 2 ? ", ngày giữa được tính vào cả hai nửa" : "") +
        " nên đây chỉ là tín hiệu sơ bộ."
    };
  };

  H.ma_tran_kich_ban_ngay = function (ts) {
    var d = duLieu(); ts = ts || {};
    var sn = Math.max(1, Math.min(ts.so_ngay || 7, d.tong.nd));
    var top = Math.max(1, ts.top || 15);
    var tu = d.tong.nd - sn;
    var ngayXet = d.days.slice(tu);
    var hang = d.kb.map(function (k) {
      var v = k.v.slice(tu);
      return { kich_ban: k.ten, nhom: k.nhom, theo_ngay: v,
               tong: v.reduce(function (a, b) { return a + b; }, 0) };
    }).filter(function (x) { return x.tong > 0; })
      .sort(function (a, b) { return b.tong - a.tong; }).slice(0, top);
    var cot = ngayXet.map(function (_, j) {
      return hang.reduce(function (a, k) { return a + k.theo_ngay[j]; }, 0);
    });
    return {
      _mo_ta: "Ma trận " + hang.length + " kịch bản × " + ngayXet.length +
              " ngày gần nhất",
      cac_ngay: ngayXet.map(function (g) { return { ngay: g, thu: thu(g) }; }),
      tong_theo_ngay: cot,
      ngay_cao_nhat: ngayXet[cot.indexOf(Math.max.apply(null, cot))],
      cac_hang: hang
    };
  };

  H.thong_ke_nhom = function (ts) {
    var d = duLieu(); ts = ts || {};
    var idx = chiSoKhoang(ts);
    var tong = idx === null ? d.tong.alert
      : idx.reduce(function (a, j) { return a + d.ngay[j].alert; }, 0);
    var tongKh = idx === null ? d.tong.kh
      : idx.reduce(function (a, j) { return a + d.ngay[j].kh; }, 0);
    var ds = d.nhom.map(function (n) {
      var al = 0, kh = 0, kb = 0;
      if (idx === null) { al = n.alert; kh = n.kh; kb = n.kb; }
      else {
        /* Cộng qua từng ngày trong khoảng. Riêng 'kịch bản có alert' thì
           lấy MAX chứ không cộng — cộng lại thì một kịch bản nổ cả 30 ngày
           hoá thành 30 kịch bản. */
        for (var i = 0; i < idx.length; i++) {
          var g = (n.ng || {})[idx[i]];
          if (!g) continue;
          al += g[0]; kh += g[1];
          if (g[2] > kb) kb = g[2];
        }
      }
      return {
        nhom: n.ten, alert: al, khach: kh,
        kich_ban_co_alert: kb, kich_ban_cau_hinh: n.kbTong,
        phan_tram_tong: tong ? lam(al / tong * 100, 1) : 0,
        alert_moi_khach: kh ? lam(al / kh, 2) : 0
      };
    }).sort(function (a, b) { return b.alert - a.alert; });
    return {
      _mo_ta: "Thống kê " + d.nhom.length + " nhóm nghiệp vụ, " +
              moTaKhoang(ts, idx),
      so_ngay_trong_pham_vi: idx === null ? d.tong.nd : idx.length,
      tong_alert_pham_vi: tong,
      tong_khach_pham_vi: tongKh,
      danh_sach: ds,
      ghi_chu: "Khách hàng KHÔNG cộng ngang các nhóm được — một khách dính " +
               "hai nhóm vẫn chỉ là một người." +
               (idx !== null && idx.length > 1
                 ? " Với khoảng nhiều ngày, 'khach' là LƯỢT (khách × ngày), " +
                   "không phải số người riêng biệt."
                 : "")
    };
  };

  H.nhom_im_lang = function () {
    var d = duLieu();
    var im = d.nhom.filter(function (n) { return n.alert === 0; });
    return {
      _mo_ta: "Nhóm nghiệp vụ không có alert nào trong " + phamVi(null),
      so_nhom_im_lang: im.length,
      danh_sach: im.map(function (n) {
        return { nhom: n.ten, kich_ban_da_cau_hinh: n.kbTong };
      }),
      ghi_chu: "Nhóm đã cấu hình kịch bản mà không có alert nào thường là " +
               "dấu hiệu kịch bản chưa chạy, cần kiểm tra."
    };
  };

  H.nhom_theo_ngay = function (ts) {
    var d = duLieu();
    if (!ts || !ts.nhom) throw new Error("Cần tên nhóm nghiệp vụ");
    var n = d.nhom.filter(function (x) { return x.ten === ts.nhom; })[0];
    if (!n) {
      var gan = d.nhom.filter(function (x) {
        return bo(x.ten).indexOf(bo(ts.nhom)) >= 0;
      });
      if (gan.length === 1) n = gan[0];
      else throw new Error("Không có nhóm '" + ts.nhom + "'. Các nhóm: " +
        d.nhom.map(function (x) { return x.ten; }).join(", "));
    }
    return {
      _mo_ta: "Nhóm '" + n.ten + "' qua " + d.tong.nd + " ngày",
      nhom: n.ten, tong_alert: n.alert,
      theo_ngay: d.days.map(function (g, i) {
        var x = (n.ng || {})[i];
        return { ngay: g, thu: thu(g), alert: x ? x[0] : 0,
                 khach: x ? x[1] : 0 };
      })
    };
  };

  /* ───────── hành vi của một CỤM ĐIỂM ─────────
     Câu hỏi kiểu "khách 80–82 điểm thì làm gì" là câu hỏi hiệu chỉnh ngưỡng:
     sắp kéo vạch Very High từ 80 lên 82 thì phải biết ai nằm trong khe 2 điểm
     đó và họ đã làm gì. Trước đây bot không có hàm nào nhận khoảng điểm nên
     nó vơ lấy thứ "điểm" duy nhất nhìn thấy — điểm gốc của kịch bản — rồi
     trả lời trôi chảy về sai chuyện.
     Tính thẳng trên TOÀN BỘ lượt (khách × ngày), không phải top 100 của mục ⑥,
     và tính lại mỗi lần hỏi theo r/k/ngưỡng đang đặt — nên đổi ngưỡng hay đổ
     dữ liệu mới thì câu trả lời tự đúng theo, không có gì để cũ đi. */
  H.hanh_vi_theo_cum_diem = function (ts) {
    var d = duLieu(), p = thamSoDiem();
    var tu, den, nhanCum;
    if (ts && ts.muc) {
      var im = -1;
      TEN_MUC.forEach(function (t, i) {
        if (t.toLowerCase() === String(ts.muc).toLowerCase().trim()) im = i;
      });
      if (im < 0) throw new Error("Mức phải là một trong: " + TEN_MUC.join(", "));
      tu  = im === 0 ? 0 : p.nguong[im - 1];
      den = im === 3 ? 100 : p.nguong[im] - 0.1;
      nhanCum = "mức " + TEN_MUC[im];
    } else {
      tu  = (ts && ts.tu  !== undefined) ? +ts.tu  : 0;
      den = (ts && ts.den !== undefined) ? +ts.den : 100;
      if (isNaN(tu) || isNaN(den)) throw new Error("tu/den phải là số 0-100");
      if (tu > den) { var q = tu; tu = den; den = q; }
      nhanCum = tu + "–" + den + " điểm";
    }

    var jNgay = null;
    if (ts && ts.ngay) {
      jNgay = d.days.indexOf(ts.ngay);
      if (jNgay < 0) throw new Error("Không có ngày " + ts.ngay + " trong kỳ");
    }

    var trong = [], tongXet = 0;
    for (var i = 0; i < d.picks.length; i++) {
      if (jNgay !== null && d.luotNg[i] !== jNgay) continue;
      tongXet++;
      /* Lọc bằng ĐIỂM THẬT, chỉ ghim bụi số. Trước đây làm tròn 1 chữ số nên
         79,9525 lọt vào cụm bắt đầu từ 80 — sai, nó vẫn dưới 80. */
      var s = chuanDiem(diemLuot(d.picks[i], p.r, p.k));
      if (s >= tu && s <= den) trong.push({ i: i, diem: s, hien: catDiem(s) });
    }
    if (!trong.length) {
      return {
        _mo_ta: "Không lượt nào có Impact trong khoảng " + nhanCum,
        khoang_diem: [tu, den], pham_vi: phamVi(ts && ts.ngay),
        so_luot: 0, so_khach: 0,
        _goi_y: "Thử nới khoảng điểm, hoặc hỏi phổ điểm chung trước."
      };
    }

    /* Đếm lại theo ĐÚNG cách biểu đồ ② gom cột (theo sàn), để người dùng đọc
       số từ biểu đồ rồi hỏi lại thì bot đối chiếu được ngay. */
    var demTron = 0, tuN = Math.floor(tu), denN = Math.floor(den);
    for (var q0 = 0; q0 < d.picks.length; q0++) {
      if (jNgay !== null && d.luotNg[q0] !== jNgay) continue;
      var sN = Math.min(100, Math.max(0,
        Math.floor(chuanDiem(diemLuot(d.picks[q0], p.r, p.k)))));
      if (sN >= tuN && sN <= denN) demTron++;
    }
    /* phổ điểm thật trong cụm */
    var goiDiem = {};
    trong.forEach(function (x) { goiDiem[x.hien] = (goiDiem[x.hien] || 0) + 1; });
    var phoDiem = Object.keys(goiDiem).map(Number)
      .sort(function (a, b) { return a - b; })
      .map(function (v) { return { diem: v, so_luot: goiDiem[v] }; });

    /* gom theo kịch bản và theo TỔ HỢP kịch bản — điểm của một lượt sinh ra
       từ tổ hợp chứ không từ một kịch bản đơn lẻ, nên phải nhìn cả hai */
    var theoKb = {}, theoToHop = {}, demKb = [0, 0, 0], khach = {};
    var tongDiem = 0, thap = 999, cao = -1, tongLan = 0, tongCap = 0;
    trong.forEach(function (x) {
      var pk = d.picks[x.i], ids = [], lan = 0;
      for (var w = 0; w < pk.length; w += 2) {
        ids.push(pk[w]); lan += pk[w + 1];
        var kb = d.kb[pk[w]];
        if (!theoKb[kb.ten]) theoKb[kb.ten] = { ten: kb.ten, nhom: kb.nhom,
          muc: kb.lv, diem_goc: kb.sc, tran_diem: kb.cap,
          so_luot: 0, tong_lan: 0, khach: {}, it_nhat: 1e9, nhieu_nhat: 0 };
        theoKb[kb.ten].so_luot++;
        theoKb[kb.ten].tong_lan += pk[w + 1];
        theoKb[kb.ten].khach[d.luotKh[x.i]] = 1;
        if (pk[w + 1] < theoKb[kb.ten].it_nhat) theoKb[kb.ten].it_nhat = pk[w + 1];
        if (pk[w + 1] > theoKb[kb.ten].nhieu_nhat) theoKb[kb.ten].nhieu_nhat = pk[w + 1];
      }
      tongLan += lan; tongCap += ids.length;
      demKb[Math.min(2, ids.length - 1)]++;
      khach[d.luotKh[x.i]] = 1;
      tongDiem += x.diem;
      if (x.diem < thap) thap = x.diem;
      if (x.diem > cao) cao = x.diem;
      var kho = ids.slice().sort(function (a, b) { return a - b; }).join("+");
      if (!theoToHop[kho]) theoToHop[kho] = { ids: ids.slice().sort(
        function (a, b) { return a - b; }), so_luot: 0, tong_diem: 0 };
      theoToHop[kho].so_luot++;
      theoToHop[kho].tong_diem += x.diem;
    });

    /* kịch bản nào ĐẶC TRƯNG cho cụm: xuất hiện trong cụm dày hơn hẳn so với
       mặt bằng toàn kỳ — đây mới là câu trả lời cho "cái gì đẩy người ta vào
       đúng khoảng điểm này", chứ không phải kịch bản nào đông nhất */
    var tongLuotKy = d.picks.length;
    var demKyKb = {};
    d.picks.forEach(function (pk) {
      var da = {};
      for (var w = 0; w < pk.length; w += 2) da[d.kb[pk[w]].ten] = 1;
      Object.keys(da).forEach(function (t) { demKyKb[t] = (demKyKb[t] || 0) + 1; });
    });

    var dsKb = Object.keys(theoKb).map(function (t) {
      var x = theoKb[t];
      var tyCum = x.so_luot / trong.length * 100;
      var tyKy  = (demKyKb[t] || 0) / tongLuotKy * 100;
      return { kich_ban: x.ten, nhom: x.nhom,
        level_kb: x.muc, score_kb: x.diem_goc, tran_diem_kb: x.tran_diem,
        so_luot_trong_cum: x.so_luot,
        so_khach_trong_cum: Object.keys(x.khach).length,
        ty_le_trong_cum: lam(tyCum, 1),
        tan_suat_trung_binh_alert_moi_luot: lam(x.tong_lan / x.so_luot, 1),
        tan_suat_it_nhat: x.it_nhat, tan_suat_nhieu_nhat: x.nhieu_nhat,
        tong_alert_trong_cum: x.tong_lan,
        ty_le_toan_ky: lam(tyKy, 1),
        dam_hon_toan_ky_gap: tyKy > 0 ? lam(tyCum / tyKy, 1) : null };
    }).sort(function (a, b) { return b.so_luot_trong_cum - a.so_luot_trong_cum; });

    /* Sàn phải đủ dày mới được gọi là "đặc trưng". Bản đầu để sàn 3 lượt nên
       một kịch bản 3/43 lượt mà tỉ lệ vượt 160 lần đã leo lên đầu danh sách,
       và model đọc thành "đặc điểm chính của cụm" — sai hẳn. Bội số lớn trên
       nền vài lượt là nhiễu, không phải đặc trưng. Những cái đó vẫn giữ lại
       nhưng để riêng, gọi đúng tên là TÍN HIỆU HIẾM. */
    var sanDac = Math.max(5, Math.ceil(trong.length * 0.1));
    function gonDac(x) {
      return { kich_ban: x.kich_ban,
               so_luot_trong_cum: x.so_luot_trong_cum,
               ty_le_trong_cum: x.ty_le_trong_cum,
               ty_le_toan_ky: x.ty_le_toan_ky,
               dam_hon_mat_bang_gap: x.dam_hon_toan_ky_gap };
    }
    var dacTrung = dsKb.filter(function (x) {
      return x.dam_hon_toan_ky_gap !== null && x.dam_hon_toan_ky_gap >= 1.5 &&
             x.so_luot_trong_cum >= sanDac;
    }).sort(function (a, b) {
      return b.dam_hon_toan_ky_gap - a.dam_hon_toan_ky_gap;
    }).slice(0, 4).map(gonDac);
    var hiem = dsKb.filter(function (x) {
      return x.dam_hon_toan_ky_gap !== null && x.dam_hon_toan_ky_gap >= 3 &&
             x.so_luot_trong_cum < sanDac;
    }).sort(function (a, b) {
      return b.dam_hon_toan_ky_gap - a.dam_hon_toan_ky_gap;
    }).slice(0, 3).map(gonDac);

    var dsToHop = Object.keys(theoToHop).map(function (kho) {
      var x = theoToHop[kho];
      return { kich_ban: x.ids.map(function (q) { return d.kb[q].ten; }),
               so_kich_ban: x.ids.length, so_luot: x.so_luot,
               ty_le_trong_cum: lam(x.so_luot / trong.length * 100, 1),
               diem_trung_binh: lam(x.tong_diem / x.so_luot, 1) };
    }).sort(function (a, b) { return b.so_luot - a.so_luot; }).slice(0, 5);

    /* Mức Impact phải đếm trên LƯỢT CÓ THẬT, không suy từ hai đầu khoảng.
       Bản đầu chỉ so tu/den với vạch ngưỡng rồi kết luận "nửa trên là Very
       High" — trong khi thực tế không lượt nào chạm tới đó. Đúng về mặt
       khoảng số, nhưng nói sai về dữ liệu, mà bot thì cứ thế chép lại. */
    var demMuc = [0, 0, 0, 0];
    trong.forEach(function (x) { demMuc[mucDiem(x.diem, p.nguong)]++; });
    var coMuc = [];
    demMuc.forEach(function (c, i) {
      if (c) coMuc.push({ muc: TEN_MUC[i], so_luot: c,
                          ty_le: lam(c / trong.length * 100, 1) });
    });
    var mTu = mucDiem(tu, p.nguong), mDen = mucDiem(den, p.nguong);
    var canhBao = null;
    if (coMuc.length > 1) {
      canhBao = "Khoảng này cắt ngang vạch ngưỡng và dữ liệu THẬT nằm ở " +
        coMuc.length + " mức: " + coMuc.map(function (x) {
          return x.muc + " " + x.so_luot + " lượt"; }).join(", ") + ".";
    } else if (mTu !== mDen) {
      canhBao = "Khoảng " + tu + "–" + den + " có cắt ngang vạch ngưỡng " +
        p.nguong.join("/") + ", NHƯNG thực tế toàn bộ " + trong.length +
        " lượt đều rơi vào mức " + coMuc[0].muc + " — điểm cao nhất chỉ " +
        cao + ", không lượt nào chạm nửa trên của khoảng.";
    }

    return {
      _mo_ta: "Hành vi của các lượt có điểm Impact trong khoảng " + nhanCum +
        " — " + phamVi(ts && ts.ngay) + ". Đây là ĐIỂM CỦA KHÁCH (mỗi khách " +
        "trong một ngày), không phải điểm gốc của kịch bản.",
      khoang_diem: [tu, den],
      pham_vi: phamVi(ts && ts.ngay),
      nguong_dang_dat: p.nguong,
      tham_so_diem: { r: p.r, k: p.k },
      muc_impact_thuc_te: coMuc,
      canh_bao_cat_nguong: canhBao,
      so_luot: trong.length,
      so_khach_rieng: Object.keys(khach).length,
      ty_trong_luot: lam(trong.length / tongXet * 100, 2),
      diem: { thap_nhat: catDiem(thap), cao_nhat: catDiem(cao),
              trung_binh: catDiem(tongDiem / trong.length) },
      /* Phổ điểm thật trong cụm — thường dồn hết vào một hai mốc chứ không
         trải đều, và đó mới là thứ quyết định khi đặt vạch ngưỡng. */
      pho_diem_trong_cum: phoDiem,
      /* Phép khớp với biểu đồ ②. Biểu đồ gom cột theo sàn nên với khoảng có
         hai đầu là số nguyên, hai bên phải ra đúng một con số. Khoảng lẻ
         (80,5–82,3) thì lệch là chuyện đương nhiên, nói rõ để khỏi cãi nhau. */
      doi_chieu_bieu_do_phan_bo_score: {
        so_luot_neu_dem_theo_cot_bieu_do: demTron,
        khop: demTron === trong.length,
        cach_dem: demTron === trong.length
          ? "Khớp với biểu đồ ② mục Phân bố score: cộng các cột từ " +
            Math.floor(tu) + " đến " + Math.floor(den) + " cũng ra " +
            trong.length + " lượt."
          : "Biểu đồ ② gom cột theo số nguyên (cột 80 = từ 80,0 đến dưới 81,0). " +
            "Khoảng hỏi là " + tu + "–" + den + " nên có mép lẻ: cộng cột được " +
            demTron + ", đếm đúng khoảng được " + trong.length + "."
      },
      /* điểm cao vì DÍNH NHIỀU KỊCH BẢN hay vì LẶP LẠI MỘT KỊCH BẢN — hai
         hướng xử lý khác hẳn nhau: một bên là người, một bên là rule */
      cach_hinh_thanh: {
        chi_1_kich_ban: demKb[0], ket_hop_2_kich_ban: demKb[1],
        ket_hop_3_kich_ban_tro_len: demKb[2],
        so_kich_ban_trung_binh: lam(tongCap / trong.length, 2),
        so_alert_trung_binh_moi_luot: lam(tongLan / trong.length, 1)
      },
      kich_ban_chiem_da_so: dsKb[0] ? {
        kich_ban: dsKb[0].kich_ban, so_luot: dsKb[0].so_luot_trong_cum,
        ty_le_trong_cum: dsKb[0].ty_le_trong_cum } : null,
      kich_ban_dac_trung_cua_cum: dacTrung,
      tin_hieu_hiem: hiem,
      to_hop_pho_bien: dsToHop,
      kich_ban_gop_mat: dsKb.slice(0, 10),
      _ghi_chu: "ty_le_trong_cum = % số LƯỢT trong cụm có dính kịch bản đó — " +
        "cộng lại có thể vượt 100% vì một lượt dính nhiều kịch bản. " +
        "dam_hon_mat_bang_gap chỉ nói kịch bản đó DÀY HƠN mặt bằng bao nhiêu " +
        "lần, KHÔNG có nghĩa nó chiếm đa số — muốn biết cái nào chiếm đa số " +
        "thì đọc kich_ban_chiem_da_so. tin_hieu_hiem là bội số cao trên nền " +
        "rất ít lượt, chỉ để tham khảo, tuyệt đối không nói thành đặc điểm chung.",
      _cach_tra_loi: "Câu này cần BẢNG chi tiết, không phải một câu tóm tắt. " +
        "Nêu số lượt và số khách của cụm, rồi liệt kê từng kịch bản trong " +
        "kich_ban_gop_mat theo dạng gạch đầu dòng, mỗi dòng có: tên kịch bản, " +
        "số lượt, số khách, tần suất trung bình (alert mỗi lượt), Level KB và " +
        "Score KB. Không tự đặt ra đặc điểm chung nào không có sẵn trong dữ kiện. " +
        "Nếu người hỏi nhắc tới con số họ đọc từ biểu đồ ②, đối chiếu bằng " +
        "doi_chieu_bieu_do_phan_bo_score chứ đừng đổi số."
    };
  };

  H.top_khach_hang = function (ts) {
    var d = duLieu(); ts = ts || {};
    var n = ts.n || 10;
    var j = ts.ngay ? chiSoNgay(ts.ngay) : null;
    var p = thamSoDiem(), r = p.r, k = p.k;

    var ds = d.topkh.map(function (x) {
      var js = j === null ? Object.keys(x.ng).map(Number) : [j];
      var al = 0, gom = {}, ngayCo = [], dMax = 0, dNgay = null;
      js.forEach(function (jj) {
        var p = x.ng[jj];
        if (!p) return;
        ngayCo.push(jj);
        var phang = [];
        p.forEach(function (c) { al += c[1]; gom[c[0]] = 1; phang.push(c[0], c[1]); });
        var s = diemLuot(phang, r, k);
        if (s > dMax) { dMax = s; dNgay = jj; }
      });
      return { ma_khach: x.kh, alert: al, so_kich_ban: Object.keys(gom).length,
               so_ngay_bi_ban: ngayCo.length, diem: dMax, ngayDiem: dNgay };
    }).filter(function (x) { return x.alert > 0; });
    ds.sort(function (a, b) { return b.alert - a.alert; });

    return {
      _mo_ta: "Top " + n + " khách nhiều alert nhất, " + phamVi(ts.ngay),
      danh_sach: ds.slice(0, n).map(function (x, i) {
        return {
          hang: i + 1, ma_khach: x.ma_khach, alert: x.alert,
          so_kich_ban: x.so_kich_ban, so_ngay_bi_ban: x.so_ngay_bi_ban,
          alert_moi_ngay: lam(x.alert / x.so_ngay_bi_ban, 1),
          diem_cao_nhat: catDiem(x.diem),
          muc: TEN_MUC[mucDiem(x.diem, p.nguong)],
          ngay_diem_cao_nhat: x.ngayDiem === null ? null : d.days[x.ngayDiem]
        };
      }),
      ghi_chu: "Điểm chấm theo từng NGÀY, không cộng dồn qua ngày. Alert " +
        "nhiều mà chỉ dính 1–2 kịch bản thường do chống lặp của kịch bản đó, " +
        "không phải người này nguy hiểm hơn."
    };
  };

  H.ho_so_khach = function (ts) {
    var d = duLieu();
    if (!ts || !ts.ma) throw new Error("Cần mã khách hàng");
    var ma = String(ts.ma).trim();
    var x = d.topkh.filter(function (y) { return y.kh === ma; })[0];
    if (!x) {
      throw new Error("Mã '" + ma + "' không nằm trong top " + d.topkh.length +
        " khách nhiều alert nhất. Bản này chỉ có chi tiết của nhóm đó.");
    }
    var p = thamSoDiem(), r = p.r, k = p.k, ct = [];
    Object.keys(x.ng).map(Number).sort(function (a, b) { return a - b; })
      .forEach(function (j) {
        var p = x.ng[j], phang = [], na = 0;
        p.forEach(function (c) { phang.push(c[0], c[1]); na += c[1]; });
        var s = diemLuot(phang, r, k);
        ct.push({
          ngay: d.days[j], thu: thu(d.days[j]), alert: na,
          diem: catDiem(s), muc: TEN_MUC[mucDiem(s, p.nguong)],
          kich_ban: p.map(function (c) {
            return { ten: d.kb[c[0]].ten, so_lan: c[1],
                     muc: d.kb[c[0]].lv, diem_goc: d.kb[c[0]].sc };
          })
        });
      });
    var cao = ct.reduce(function (a, b) { return b.diem > a.diem ? b : a; }, ct[0]);
    return {
      _mo_ta: "Hồ sơ khách " + ma + " trong " + phamVi(null),
      ma_khach: ma, tong_alert: x.alert,
      so_ngay_bi_ban: x.nngay, so_kich_ban_khac_nhau: x.nkb,
      diem_cao_nhat: cao.diem, muc_cao_nhat: cao.muc,
      ngay_diem_cao_nhat: cao.ngay,
      chi_tiet_tung_ngay: ct
    };
  };

  H.khach_tai_pham = function (ts) {
    var d = duLieu();
    var n = (ts && ts.so_ngay_toi_thieu) || 3;
    var tai = d.taipham.filter(function (x) { return x.n >= n; })
      .reduce(function (a, x) { return a + x.kh; }, 0);
    return {
      _mo_ta: "Khách bị alert từ " + n + " ngày trở lên trong kỳ " +
              d.tong.nd + " ngày",
      so_khach_tai_pham: tai,
      tong_khach: d.tong.kh,
      phan_tram: lam(tai / d.tong.kh * 100, 1),
      phan_bo_so_ngay: d.taipham.map(function (x) {
        return { so_ngay: x.n, so_khach: x.kh };
      }),
      ghi_chu: "Nhóm này nếu giữ nguyên tần suất sẽ không bao giờ đủ 30 ngày " +
               "sạch để được ân xá."
    };
  };

  H.khach_nhieu_kich_ban = function (ts) {
    var d = duLieu(); ts = ts || {};
    var toi = ts.so_kb_toi_thieu || 3, n = ts.n || 10;
    var ds = d.topkh.filter(function (x) { return x.nkb >= toi; })
      .map(function (x) {
        var gom = {};
        Object.keys(x.ng).forEach(function (j) {
          x.ng[j].forEach(function (c) { gom[c[0]] = 1; });
        });
        return { ma_khach: x.kh, so_kich_ban: x.nkb, alert: x.alert,
                 so_ngay: x.nngay,
                 cac_kich_ban: Object.keys(gom).map(function (i) {
                   return d.kb[i].ten;
                 }).sort() };
      }).sort(function (a, b) {
        return (b.so_kich_ban - a.so_kich_ban) || (b.alert - a.alert);
      }).slice(0, n);
    return {
      _mo_ta: "Khách dính từ " + toi + " kịch bản khác nhau trở lên",
      so_khach: ds.length, danh_sach: ds,
      ghi_chu: "Dính nhiều kịch bản KHÁC NHAU đáng điều tra hơn là bị một " +
               "kịch bản bắn nhiều lần."
    };
  };

  H.tim_khach = function (ts) {
    var d = duLieu();
    if (!ts || !ts.ma) throw new Error("Cần mã khách hàng");
    var ma = String(ts.ma).trim();
    var x = d.topkh.filter(function (y) { return y.kh === ma; })[0];
    if (!x) {
      return { _mo_ta: "Tìm mã khách '" + ma + "'", tim_thay: false,
               ghi_chu: "Không nằm trong top " + d.topkh.length +
                        " khách nhiều alert nhất." };
    }
    return { _mo_ta: "Tìm mã khách '" + ma + "'", tim_thay: true,
             ma_khach: ma, tong_alert: x.alert, so_ngay: x.nngay,
             so_kich_ban: x.nkb };
  };

  H.ghi_chep_dieu_tra = function () {
    var d = duLieu();
    return {
      _mo_ta: "Ghi chép điều tra các kỳ trước",
      so_muc: (d.ghichep || []).length,
      cac_muc: d.ghichep || [],
      ghi_chu: (d.ghichep || []).length ? "" : "Kỳ này chưa có ghi chép nào."
    };
  };

  /* ══════════════════ ĐỒNG PHẠM GIỮA KỊCH BẢN ══════════════════
     Hai kịch bản hay nổ cùng MỘT khách nói lên một trong hai điều, và cả
     hai đều đáng biết:
       · chúng bắt cùng một hành vi  -> trùng lặp, cân nhắc bỏ bớt một
       · chúng là hai mặt của một thủ đoạn -> đây mới là đầu mối điều tra

     Tính trên toàn bộ 126.616 lượt (khách × ngày) — dữ liệu giàu nhất của
     dashboard mà trước nay không hàm nào chạm tới.

     Đo bằng LIFT chứ không bằng số lượt trùng: hai kịch bản đông alert thì
     đương nhiên hay gặp nhau, đếm thô sẽ luôn cho ra đúng mấy cặp to nhất.
     Lift = (tỉ lệ gặp nhau thực tế) / (tỉ lệ nếu chúng độc lập). Lift 5
     nghĩa là gặp nhau dày gấp 5 lần mức ngẫu nhiên. */
  H.kich_ban_di_cung_nhau = function (ts) {
    ts = ts || {};
    var d = duLieu();
    var n = Math.max(1, Math.min(+ts.n || 10, 25));
    /* Sàn: cặp chỉ trùng vài lượt thì lift vọt lên rất cao mà vô nghĩa —
       đúng cái bẫy đã mắc ở hanh_vi_theo_cum_diem. */
    var san = Math.max(5, +ts.toi_thieu || 20);

    var demKb = {}, demCap = {}, tong = d.picks.length;
    d.picks.forEach(function (pk) {
      var ids = [], da = {};
      for (var w = 0; w < pk.length; w += 2) {
        if (!da[pk[w]]) { da[pk[w]] = 1; ids.push(pk[w]); }
      }
      ids.forEach(function (a) { demKb[a] = (demKb[a] || 0) + 1; });
      ids.sort(function (x, y) { return x - y; });
      for (var i = 0; i < ids.length; i++)
        for (var j = i + 1; j < ids.length; j++) {
          var kh = ids[i] + "|" + ids[j];
          demCap[kh] = (demCap[kh] || 0) + 1;
        }
    });

    var ds = Object.keys(demCap).map(function (kh) {
      var p = kh.split("|"), a = +p[0], b = +p[1], c = demCap[kh];
      var pa = demKb[a] / tong, pb = demKb[b] / tong, pab = c / tong;
      return {
        kich_ban_a: d.kb[a].ten, kich_ban_b: d.kb[b].ten,
        nhom_a: d.kb[a].nhom, nhom_b: d.kb[b].nhom,
        so_luot_di_cung: c,
        /* Tỉ lệ có điều kiện hai chiều: A nổ thì bao nhiêu % kèm B, và
           ngược lại. Lệch nhau nhiều nghĩa là quan hệ một chiều — B gần
           như luôn kèm A nhưng A thì không, đáng chú ý hơn hẳn. */
        khi_co_a_thi_co_b: lam(c / demKb[a] * 100, 1),
        khi_co_b_thi_co_a: lam(c / demKb[b] * 100, 1),
        lift: lam(pab / (pa * pb), 1),
        so_luot_a: demKb[a], so_luot_b: demKb[b]
      };
    }).filter(function (x) { return x.so_luot_di_cung >= san; });

    ds.sort(function (x, y) { return y.lift - x.lift; });

    return {
      _mo_ta: "Cặp kịch bản hay nổ cùng một khách trong cùng ngày (toàn kỳ " +
              tong.toLocaleString("vi") + " lượt)",
      tong_luot: tong,
      san_toi_thieu: san,
      so_cap_dat_san: ds.length,
      danh_sach: ds.slice(0, n),
      _ghi_chu: "lift = gặp nhau dày gấp mấy lần mức ngẫu nhiên. " +
        "lift > 3 là đáng soi: hoặc hai rule trùng nhau, hoặc đó là một " +
        "thủ đoạn có cấu trúc. 'khi_co_a_thi_co_b' lệch hẳn " +
        "'khi_co_b_thi_co_a' = quan hệ một chiều."
    };
  };

  /* Alert của một kịch bản dồn vào ít khách hay rải đều?
     Cùng 10.000 alert nhưng 500 khách với 10 khách là hai câu chuyện khác
     hẳn: rải đều thường là rule quét rộng, dồn cục là vài đối tượng bắn
     liên tục — cái sau mới đáng điều tra. */
  H.do_tap_trung_kich_ban = function (ts) {
    ts = ts || {};
    var d = duLieu();
    var ten = ts.kich_ban ? String(ts.kich_ban) : null;
    var idx = {};
    d.kb.forEach(function (k, i) { idx[i] = { ten: k.ten, nhom: k.nhom,
      alert: 0, khach: {}, theoKhach: {} }; });

    d.picks.forEach(function (pk, li) {
      for (var w = 0; w < pk.length; w += 2) {
        var o = idx[pk[w]], kh = d.luotKh[li];
        o.alert += pk[w + 1];
        o.khach[kh] = 1;
        o.theoKhach[kh] = (o.theoKhach[kh] || 0) + pk[w + 1];
      }
    });

    var ra = Object.keys(idx).map(function (i) {
      var o = idx[i];
      var ks = Object.keys(o.theoKhach);
      if (!ks.length) return null;
      var v = ks.map(function (t) { return o.theoKhach[t]; })
                .sort(function (a, b) { return b - a; });
      var tong = v.reduce(function (a, b) { return a + b; }, 0);
      /* Bao nhiêu % alert đến từ 10% khách đông nhất — chỉ số dễ đọc hơn
         hệ số Gini mà nói lên đúng điều cần biết. */
      var top = Math.max(1, Math.round(v.length * 0.1));
      var tongTop = v.slice(0, top).reduce(function (a, b) { return a + b; }, 0);
      return {
        kich_ban: o.ten, nhom: o.nhom,
        tong_alert: tong, so_khach: v.length,
        alert_moi_khach: lam(tong / v.length, 1),
        khach_nang_nhat: v[0],
        ty_le_alert_tu_10pc_khach_dong_nhat: lam(tongTop / tong * 100, 1),
        /* NHẬN ĐỊNH TÍNH SẴN — model phải dùng đúng chữ này, không được
           tự diễn giải con số.
           Đã mắc lỗi thật: kịch bản có 33,1% (tức RẢI ĐỀU) mà model viết
           thành "đang dồn vào một nhóm khách nhỏ" — số đúng, kết luận
           ngược, lại kèm nhãn "đã đối chiếu" nên nghe rất chắc.
           Mốc lấy từ phân bố thực tế của bảng này: phần lớn kịch bản nằm
           60–96%, nên dưới 45% là rải đều thật sự. */
        muc_do_tap_trung: (function (t) {
          return t >= 80 ? "DỒN CỤC (rất tập trung vào ít khách)"
               : t >= 60 ? "KHÁ TẬP TRUNG"
               : t >= 45 ? "TRUNG BÌNH"
               : "RẢI ĐỀU (không dồn vào nhóm nhỏ)";
        })(lam(tongTop / tong * 100, 1))
      };
    }).filter(Boolean);

    /* Mốc của cả bảng: một con số trần trụi thì không biết cao hay thấp.
       Có trung vị để đối chiếu thì model mới nói đúng "cao hơn/thấp hơn
       mặt bằng" thay vì đoán. */
    var tyLe = ra.map(function (x) {
      return x.ty_le_alert_tu_10pc_khach_dong_nhat;
    }).sort(function (a, b) { return a - b; });
    var trungVi = tyLe.length
      ? lam(tyLe[Math.floor(tyLe.length / 2)], 1) : null;

    if (ten) {
      var mot = ra.filter(function (x) {
        return x.kich_ban.toLowerCase().indexOf(ten.toLowerCase()) >= 0;
      });
      return { _mo_ta: "Độ tập trung của kịch bản khớp '" + ten + "'",
               danh_sach: mot,
               trung_vi_toan_bang: trungVi,
               _ghi_chu: "So với trung vị " + trungVi + "% của toàn bảng. " +
                 "PHẢI dùng đúng chữ trong muc_do_tap_trung, không tự diễn " +
                 "giải con số theo cảm tính." };
    }
    ra.sort(function (a, b) {
      return b.ty_le_alert_tu_10pc_khach_dong_nhat -
             a.ty_le_alert_tu_10pc_khach_dong_nhat;
    });
    return {
      _mo_ta: "Kịch bản nào dồn alert vào ít khách nhất (xếp giảm dần)",
      danh_sach: ra.slice(0, Math.max(1, Math.min(+ts.n || 12, 38))),
      trung_vi_toan_bang: trungVi,
      _ghi_chu: "Tỉ lệ càng cao = alert càng dồn vào một nhúm khách. " +
        "Trung vị toàn bảng là " + trungVi + "%. " +
        "PHẢI dùng đúng chữ trong muc_do_tap_trung của từng dòng — không " +
        "được tự diễn giải con số. Dưới 45% là RẢI ĐỀU, đừng gọi là 'dồn " +
        "vào nhóm nhỏ'."
    };
  };

  /* ══════════════════ SO HAI KHOẢNG THỜI GIAN ══════════════════
     "Tháng 8 khác tháng 7 chỗ nào" — trước phải gọi hai lần rồi tự trừ
     nhẩm, vừa dễ sai vừa không nêu được cái gì đổi mạnh nhất. */
  H.so_sanh_hai_ky = function (ts) {
    ts = ts || {};
    var d = duLieu();
    var A = chiSoKhoang({ tu: ts.tu_a, den: ts.den_a });
    var B = chiSoKhoang({ tu: ts.tu_b, den: ts.den_b });
    if (!A || !A.length || !B || !B.length) {
      return { _mo_ta: "Thiếu mốc thời gian",
               _loi: "Cần đủ bốn tham số: tu_a, den_a, tu_b, den_b " +
                     "(dạng YYYY-MM-DD hoặc DD/MM). Kỳ dữ liệu: " +
                     d.days[0] + " đến " + d.days[d.days.length - 1] };
    }

    function gom(idx) {
      var al = 0, kbo = {};
      d.kb.forEach(function (k, i) {
        var s = 0;
        idx.forEach(function (j) { s += k.v[j]; });
        al += s;
        if (s) kbo[k.ten] = { alert: s, nhom: k.nhom };
      });
      return { alert: al, kb: kbo, so_ngay: idx.length };
    }
    var ga = gom(A), gb = gom(B);

    var ten = {};
    Object.keys(ga.kb).forEach(function (t) { ten[t] = 1; });
    Object.keys(gb.kb).forEach(function (t) { ten[t] = 1; });

    var doi = Object.keys(ten).map(function (t) {
      var a = ga.kb[t] ? ga.kb[t].alert : 0;
      var b = gb.kb[t] ? gb.kb[t].alert : 0;
      /* So TRUNG BÌNH MỖI NGÀY, không so tổng: hai kỳ lệch số ngày thì so
         tổng là sai hẳn (tháng 9 mới 5 ngày so với tháng 8 đủ 31 ngày). */
      var ta = a / ga.so_ngay, tb = b / gb.so_ngay;
      return {
        kich_ban: t, nhom: (ga.kb[t] || gb.kb[t]).nhom,
        alert_ky_a: a, alert_ky_b: b,
        tb_ngay_ky_a: lam(ta, 1), tb_ngay_ky_b: lam(tb, 1),
        thay_doi_pc: ta > 0 ? lam((tb - ta) / ta * 100, 1)
                            : (tb > 0 ? null : 0),
        trang_thai: ta === 0 && tb > 0 ? "MỚI XUẤT HIỆN"
                  : tb === 0 && ta > 0 ? "TẮT HẲN" : ""
      };
    });

    var co = doi.filter(function (x) { return x.thay_doi_pc !== null; });
    co.sort(function (a, b) { return b.thay_doi_pc - a.thay_doi_pc; });
    var moi = doi.filter(function (x) { return x.trang_thai === "MỚI XUẤT HIỆN"; });
    var tat = doi.filter(function (x) { return x.trang_thai === "TẮT HẲN"; });

    var tbA = ga.alert / ga.so_ngay, tbB = gb.alert / gb.so_ngay;
    return {
      _mo_ta: "So kỳ A (" + d.days[A[0]] + " – " + d.days[A[A.length-1]] +
              ", " + ga.so_ngay + " ngày) với kỳ B (" + d.days[B[0]] + " – " +
              d.days[B[B.length-1]] + ", " + gb.so_ngay + " ngày)",
      ky_a: { tu: d.days[A[0]], den: d.days[A[A.length-1]],
              so_ngay: ga.so_ngay, tong_alert: ga.alert, tb_ngay: lam(tbA, 1) },
      ky_b: { tu: d.days[B[0]], den: d.days[B[B.length-1]],
              so_ngay: gb.so_ngay, tong_alert: gb.alert, tb_ngay: lam(tbB, 1) },
      thay_doi_chung_pc: tbA > 0 ? lam((tbB - tbA) / tbA * 100, 1) : null,
      tang_manh_nhat: co.slice(0, 6),
      giam_manh_nhat: co.slice(-6).reverse(),
      moi_xuat_hien: moi,
      tat_han: tat,
      _ghi_chu: "Mọi so sánh theo TRUNG BÌNH MỖI NGÀY vì hai kỳ có thể " +
        "lệch số ngày. Kỳ A là mốc so sánh, kỳ B là kỳ đang xét."
    };
  };

  /* ══════════════════ TÍNH ĐIỂM GIẢ ĐỊNH ══════════════════
     "Khách dính 3 kịch bản Low thì mấy điểm?" — trước đây bot từ chối vì
     tưởng không có công thức, trong khi diemLuot() nằm ngay trong file này
     và dashboard có hẳn mục ⓪ giải thích công thức. Đó là lỗ to với một
     dashboard xoay quanh chấm điểm. */
  H.tinh_diem_gia_dinh = function (ts) {
    ts = ts || {};
    var d = duLieu(), p = thamSoDiem();
    var ds = ts.kich_ban || ts.danh_sach || [];
    if (typeof ds === "string") ds = [{ ten: ds, so_lan: 1 }];
    if (!ds.length) {
      return { _mo_ta: "Thiếu dữ kiện",
        _loi: "Cần danh sách kịch bản. Ví dụ: kich_ban=[{ten:'...', " +
              "so_lan:2}] hoặc muc='Low' + so_kich_ban=3 để lấy kịch bản " +
              "đại diện của mức đó." };
    }

    var picks = [], chiTiet = [], thieu = [];
    ds.forEach(function (x) {
      var ten = typeof x === "string" ? x : (x.ten || x.kich_ban);
      var lan = Math.max(1, +(x.so_lan || x.lan || 1));
      var i = timKb(d, ten);
      if (i < 0) { thieu.push(ten); return; }
      picks.push(i, lan);
      var kb = d.kb[i];
      chiTiet.push({
        kich_ban: kb.ten, muc: kb.lv, diem_goc: kb.sc, tran_diem: kb.cap,
        so_lan: lan,
        hieu_luc: lam(hieuLuc(kb.sc, kb.cap, lan, p.r), 2)
      });
    });

    if (!picks.length) {
      return { _mo_ta: "Không tìm thấy kịch bản nào khớp",
               _loi: "Không có kịch bản nào tên giống: " + thieu.join(", ") };
    }

    var diem = chuanDiem(diemLuot(picks, p.r, p.k));
    var muc = ["Low", "Medium", "High", "Very High"][mucDiem(diem, p.nguong)];
    return {
      _mo_ta: "Điểm giả định cho một khách dính " + chiTiet.length +
              " kịch bản trong CÙNG MỘT NGÀY",
      tham_so_dang_dat: { r: p.r, k: p.k, nguong: p.nguong },
      cac_kich_ban: chiTiet,
      diem: lam(diem, 1),
      muc_impact: muc,
      khong_tim_thay: thieu.length ? thieu : undefined,
      _ghi_chu: "Công thức PP-D hai tầng: mỗi kịch bản cho hiệu lực " +
        "e = tran - (tran-goc)*r^(n-1); rồi score = M + (100-M)*k*" +
        "(1-tích(1-e/100)) với M là hiệu lực lớn nhất. Điểm tính THEO NGÀY, " +
        "không cộng dồn qua các ngày."
    };
  };

  /* Vì sao khách X ngày Y được chừng đó điểm — phân rã từng kịch bản. */
  H.giai_thich_diem = function (ts) {
    ts = ts || {};
    var d = duLieu(), p = thamSoDiem();
    var ma = String(ts.ma_khach || ts.ma || "").trim();
    if (!ma) return { _mo_ta: "Thiếu mã khách", _loi: "Cần tham số ma_khach" };

    var ket = [];
    for (var i = 0; i < d.picks.length; i++) {
      if (d.luotKh[i] !== ma) continue;
      if (ts.ngay && d.days[d.luotNg[i]] !== chuanNgayTs(ts.ngay)) continue;
      var pk = d.picks[i], ct = [];
      for (var w = 0; w < pk.length; w += 2) {
        var kb = d.kb[pk[w]];
        ct.push({ kich_ban: kb.ten, muc: kb.lv, diem_goc: kb.sc,
                  tran_diem: kb.cap, so_lan: pk[w + 1],
                  hieu_luc: lam(hieuLuc(kb.sc, kb.cap, pk[w + 1], p.r), 2) });
      }
      var s = chuanDiem(diemLuot(pk, p.r, p.k));
      ket.push({
        ngay: d.days[d.luotNg[i]], diem: lam(s, 1),
        muc_impact: ["Low", "Medium", "High", "Very High"][mucDiem(s, p.nguong)],
        so_alert_trong_ngay: d.luotAl[i],
        cac_kich_ban: ct
      });
    }
    if (!ket.length) {
      return { _mo_ta: "Không có lượt nào",
               _loi: "Không tìm thấy khách '" + ma + "'" +
                     (ts.ngay ? " trong ngày " + ts.ngay : "") + "." };
    }
    ket.sort(function (a, b) { return b.diem - a.diem; });
    return {
      _mo_ta: "Phân rã điểm của khách " + ma + " (" + ket.length + " ngày)",
      tham_so_dang_dat: { r: p.r, k: p.k, nguong: p.nguong },
      so_ngay: ket.length,
      diem_cao_nhat: ket[0].diem,
      cac_ngay: ket.slice(0, Math.max(1, Math.min(+ts.n || 8, 30))),
      _ghi_chu: "hieu_luc là đóng góp của từng kịch bản sau khi tính số lần " +
        "lặp; điểm cuối gộp các hiệu lực đó theo công thức PP-D."
    };
  };

  /* ══════════════════ XẾP HẠNG ƯU TIÊN ĐIỀU TRA ══════════════════
     Trước đây hỏi "nên điều tra gì trước" thì bot chọn kịch bản nhiều alert
     nhất, hết. Nhưng nhiều alert chưa chắc đáng điều tra: rule quét rộng
     bắn 30 nghìn alert rải đều 5 nghìn khách thì không có đầu mối nào,
     trong khi 511 alert dồn vào 3 khách là thứ điều tra được ngay.

     Cho điểm theo BỐN yếu tố rồi cộng có trọng số, và trả về điểm từng
     yếu tố để model giải thích được "vì sao", không phải chỉ đọc kết quả. */
  H.uu_tien_dieu_tra = function (ts) {
    ts = ts || {};
    var d = duLieu();
    var tap = H.do_tap_trung_kich_ban({ n: 99 });
    var bangTap = {};
    (tap.danh_sach || []).forEach(function (x) { bangTap[x.kich_ban] = x; });

    /* Xu hướng: nửa sau kỳ so nửa đầu. Kịch bản đang nóng lên đáng soi
       trước cái đã nguội. */
    var nd = d.tong.nd, giua = Math.floor(nd / 2);
    var maxAl = Math.max.apply(null, d.kb.map(function (k) { return k.alert; })) || 1;

    var ds = d.kb.map(function (k) {
      var dau = 0, sau = 0;
      for (var i = 0; i < nd; i++) (i < giua ? (dau += k.v[i]) : (sau += k.v[i]));
      var xu = dau > 0 ? (sau - dau) / dau * 100 : (sau > 0 ? 999 : 0);
      var t = bangTap[k.ten] || {};
      var tyTap = t.ty_le_alert_tu_10pc_khach_dong_nhat || 0;

      /* Bốn điểm thành phần, mỗi cái 0-100 */
      var eKhoiLuong = Math.min(100, k.alert / maxAl * 100);
      var eTapTrung = Math.min(100, tyTap);
      var eXuHuong = Math.max(0, Math.min(100, 50 + xu / 4));
      var eMuc = { "Low": 20, "Medium": 50, "High": 80, "Very High": 100 }[k.lv] || 50;

      /* Trọng số: mức rủi ro và độ tập trung nặng hơn khối lượng thô —
         khối lượng lớn mà rải đều thì không cho đầu mối nào. */
      var diem = eMuc * 0.35 + eTapTrung * 0.3 + eXuHuong * 0.2 +
                 eKhoiLuong * 0.15;
      return {
        kich_ban: k.ten, nhom: k.nhom, muc: k.lv,
        diem_uu_tien: lam(diem, 1),
        tong_alert: k.alert, so_khach: k.kh,
        do_tap_trung: tyTap ? lam(tyTap, 1) : null,
        nhan_dinh_tap_trung: t.muc_do_tap_trung || null,
        xu_huong_nua_sau_pc: lam(xu, 1),
        vi_sao: [
          "mức " + k.lv,
          t.muc_do_tap_trung ? t.muc_do_tap_trung.split(" ")[0].toLowerCase() +
            " (" + lam(tyTap, 1) + "%)" : null,
          xu > 30 ? "đang tăng " + lam(xu, 0) + "%" :
            xu < -30 ? "đang giảm " + lam(Math.abs(xu), 0) + "%" : null,
          k.alert >= maxAl * 0.3 ? "khối lượng lớn (" + k.alert + ")" : null
        ].filter(Boolean).join(", ")
      };
    }).filter(function (x) { return x.tong_alert > 0; });

    ds.sort(function (a, b) { return b.diem_uu_tien - a.diem_uu_tien; });
    return {
      _mo_ta: "Xếp hạng ưu tiên điều tra — cân 4 yếu tố, không chỉ nhìn " +
              "số alert",
      cach_cham: "mức rủi ro 35% + độ tập trung 30% + xu hướng 20% + " +
                 "khối lượng 15%",
      danh_sach: ds.slice(0, Math.max(1, Math.min(+ts.n || 6, 20))),
      _cach_tra_loi: "PHẢI nêu lý do theo trường vi_sao của từng kịch bản, " +
        "đừng chỉ nói 'nhiều alert nhất'. Nếu người dùng hỏi 'vì sao', giải " +
        "thích bằng 4 yếu tố trên."
    };
  };

  /* "Cái này có đáng lo không" — trả về một phán quyết kèm mốc so sánh,
     thay vì bắt model tự cảm nhận từ số trần trụi. */
  H.danh_gia_kich_ban = function (ts) {
    ts = ts || {};
    var ten = String(ts.kich_ban || ts.ten || "").trim();
    if (!ten) return { _mo_ta: "Thiếu tên kịch bản",
                       _loi: "Cần tham số kich_ban" };
    var d = duLieu();
    var iKb = timKb(d, ten);
    if (iKb < 0) return { _mo_ta: "Không tìm thấy",
                          _loi: "Không có kịch bản nào tên giống '" + ten + "'" };
    var kb = d.kb[iKb];

    var uu = H.uu_tien_dieu_tra({ n: 99 });
    var hang = -1, muc = null;
    (uu.danh_sach || []).forEach(function (x, i) {
      if (hang < 0 && x.kich_ban === kb.ten) { hang = i + 1; muc = x; }
    });

    /* So với các kịch bản CÙNG NHÓM — so với toàn bảng thì nhóm AML luôn
       thắng nhóm khác, không nói lên gì. */
    var cungNhom = d.kb.filter(function (k) { return k.nhom === kb.nhom; })
                       .sort(function (a, b) { return b.alert - a.alert; });
    var hangNhom = cungNhom.findIndex(function (k) { return k.ten === kb.ten; }) + 1;

    var t = H.do_tap_trung_kich_ban({ kich_ban: kb.ten });
    var tt = (t.danh_sach && t.danh_sach[0]) || {};

    /* Phán quyết: gộp mức rủi ro + độ tập trung + xu hướng thành một câu
       dứt khoát, để model không phải tự đoán. */
    var diem = muc ? muc.diem_uu_tien : 0;
    var phan = diem >= 70 ? "ĐÁNG LO — nên điều tra sớm"
             : diem >= 55 ? "CẦN THEO DÕI"
             : diem >= 40 ? "BÌNH THƯỜNG"
             : "ÍT RỦI RO";

    return {
      _mo_ta: "Đánh giá kịch bản: " + kb.ten,
      kich_ban: kb.ten, nhom: kb.nhom, muc: kb.lv, diem_goc: kb.sc,
      tong_alert: kb.alert, so_khach: kb.kh,
      alert_moi_khach: lam(kb.alert / (kb.kh || 1), 1),
      do_tap_trung_pc: tt.ty_le_alert_tu_10pc_khach_dong_nhat,
      nhan_dinh_tap_trung: tt.muc_do_tap_trung,
      trung_vi_tap_trung_toan_bang: t.trung_vi_toan_bang,
      xu_huong_nua_sau_pc: muc ? muc.xu_huong_nua_sau_pc : null,
      hang_uu_tien: hang > 0 ? hang + "/" + (uu.danh_sach || []).length : null,
      hang_trong_nhom: hangNhom + "/" + cungNhom.length + " (theo alert)",
      PHAN_QUYET: phan,
      ly_do: muc ? muc.vi_sao : null,
      _cach_tra_loi: "Trả lời thẳng bằng PHAN_QUYET rồi mới giải thích. " +
        "Người ta hỏi 'có đáng lo không' thì cần một câu trả lời dứt khoát, " +
        "không phải một mớ số."
    };
  };

  /* Không dự báo được tương lai, nhưng mô tả được đà gần đây — đó mới là
     thứ trả lời được cho câu "sắp tới thế nào". */
  H.xu_huong_gan_day = function (ts) {
    ts = ts || {};
    var d = duLieu();
    var n = Math.max(3, Math.min(+ts.so_ngay || 14, d.tong.nd));
    var i0 = d.tong.nd - n;
    var v = [];
    for (var i = i0; i < d.tong.nd; i++) {
      v.push({ ngay: d.days[i], alert: d.ngay[i].alert });
    }
    var nua = Math.floor(n / 2);
    var dau = v.slice(0, nua).reduce(function (a, x) { return a + x.alert; }, 0) / nua;
    var sau = v.slice(nua).reduce(function (a, x) { return a + x.alert; }, 0) /
              (n - nua);
    var doi = dau > 0 ? (sau - dau) / dau * 100 : 0;
    var da = doi > 20 ? "ĐANG TĂNG" : doi < -20 ? "ĐANG GIẢM" : "ĐI NGANG";

    return {
      _mo_ta: "Đà " + n + " ngày gần nhất (KHÔNG phải dự báo)",
      cac_ngay: v,
      trung_binh_nua_dau: lam(dau, 0),
      trung_binh_nua_sau: lam(sau, 0),
      thay_doi_pc: lam(doi, 1),
      DA_HIEN_TAI: da,
      _cach_tra_loi: "Đây là ĐÀ ĐÃ QUA, không phải dự báo. Nếu người dùng " +
        "hỏi 'tuần tới thế nào', hãy nói rõ là dữ liệu không dự báo được " +
        "tương lai, rồi mô tả đà gần đây để họ tự suy xét."
    };
  };

  /* (Đã có thamSoDiem() ở đầu file — nó đọc cả ô r/k/ngưỡng người dùng
     đang kéo trên dashboard và trả kèm mac_dinh. Tôi từng định nghĩa một
     hàm TRÙNG TÊN ở đây, đè mất bản gốc và làm hỏng moTaKy() -> cả chatbot
     chết. Đừng đặt lại tên đã có trong file.) */

  /* Khớp tên kịch bản LINH HOẠT.
     Model gõ tên rút gọn rất nhiều ("Blacklist B" thay vì "TB_Thuê bao PTM
     nằm trong Blacklist B của BI"), khớp chuỗi con nguyên văn thì trượt
     sạch và hàm báo "không tìm thấy" oan.
     Ba mức, dừng ở mức đầu tiên tìm được:
       1. chứa nguyên văn (bỏ dấu, bỏ hoa thường)
       2. chứa TẤT CẢ các từ trong tên hỏi
       3. khớp nhiều từ nhất, miễn được quá nửa */
  function khongDau(s) {
    return String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "")
      .replace(/đ/gi, "d").toLowerCase()
      /* Gộp khoảng trắng: tên thật có chỗ dính HAI dấu cách
         ("Blacklist  B của BI"), không gộp thì "blacklist b" trượt mức
         khớp nguyên văn rồi rơi xuống mức đoán — và đoán nhầm sang
         "Blacklist A". Đã mắc đúng lỗi này. */
      .replace(/\s+/g, " ").trim();
  }
  function timKb(d, ten) {
    var q = khongDau(ten).trim();
    if (!q) return -1;
    var i, t;
    for (i = 0; i < d.kb.length; i++) {
      if (khongDau(d.kb[i].ten).indexOf(q) >= 0) return i;
    }
    var tu = q.split(/[\s_,./]+/).filter(function (x) { return x.length > 1; });
    if (!tu.length) return -1;
    for (i = 0; i < d.kb.length; i++) {
      t = khongDau(d.kb[i].ten);
      if (tu.every(function (x) { return t.indexOf(x) >= 0; })) return i;
    }
    /* Mức 3 — đoán theo số từ khớp. Nguy hiểm: "blacklist a" và
       "blacklist b" chỉ khác một ký tự, đoán sai thì trả về kịch bản KHÁC
       mà vẫn tự tin. Nên chỉ chấp nhận khi có MỘT ứng viên tốt nhất duy
       nhất; hoà điểm thì thà báo không tìm thấy còn hơn trả nhầm. */
    var tot = -1, diem = 0, hoa = 0;
    for (i = 0; i < d.kb.length; i++) {
      t = khongDau(d.kb[i].ten);
      var n = tu.filter(function (x) { return t.indexOf(x) >= 0; }).length;
      if (n > diem) { diem = n; tot = i; hoa = 1; }
      else if (n === diem && n > 0) hoa++;
    }
    return (hoa === 1 && diem > tu.length / 2) ? tot : -1;
  }
  function chuanNgayTs(s) {
    s = String(s || "").trim();
    var m = s.match(/^\d{4}-\d{2}-\d{2}/);
    if (m) return m[0];
    var d = duLieu();
    m = s.match(/^(\d{1,2})[\/-](\d{1,2})(?:[\/-](\d{4}))?$/);
    if (m) {
      return (m[3] || d.days[0].slice(0, 4)) + "-" +
             ("0" + m[2]).slice(-2) + "-" + ("0" + m[1]).slice(-2);
    }
    return s;
  }

  /* ══════════════════ MÔ TẢ CHO LLM ══════════════════ */
  var MO_TA = {
    tong_quan: "Bức tranh chung cả kỳ: tổng alert, khách, kịch bản, ngày cao nhất",
    alert_theo_ngay: "Số alert/khách/kịch bản từng ngày trong kỳ",
    ngay_bat_thuong: "Ngày nào lệch hẳn so trung bình. Tham số: nguong (mặc định 1.3)",
    so_sanh_ngay: "So hai ngày với nhau. Tham số: ngay_a, ngay_b (YYYY-MM-DD)",
    gom_theo_ky: "Gom alert theo TUẦN hoặc THÁNG, kèm % so kỳ liền trước. " +
      "Dùng khi hỏi xu hướng dài hơn một ngày. Tham số: muc = 'tuan' | 'thang'",
    top_kich_ban: "Kịch bản nhiều alert nhất. Tham số: n (mặc định 10), nhom, và MỘT trong hai cách chọn thời gian: ngay=YYYY-MM-DD (một ngày) HOẶC tu + den (khoảng ngày, vd tu=2026-08-01 den=2026-08-31). Không truyền gì = toàn kỳ",
    chi_tiet_kich_ban: "Hồ sơ đầy đủ một kịch bản. Tham số: ten",
    kich_ban_dot_bien: "Kịch bản có ngày vọt hẳn. Tham số: nguong",
    kich_ban_ban_day: "Kịch bản nhiều alert mỗi khách. Tham số: nguong",
    kich_ban_im_lang: "Kịch bản đã cấu hình nhưng không có alert nào cả kỳ",
    kich_ban_im_lang_trong_ngay: "Kịch bản có alert đều cả kỳ nhưng im hẳn MỘT ngày — lời giải cho 'sao ngày X ít alert'. Tham số: ngay",
    xu_huong_kich_ban: "Kịch bản đang tăng hay giảm. Tham số: ten",
    ma_tran_kich_ban_ngay: "Ma trận kịch bản × ngày. Tham số: so_ngay, top",
    thong_ke_nhom: "Alert/khách/kịch bản theo nhóm nghiệp vụ. Tham số: ngay (một ngày) hoặc tu + den (khoảng ngày). Không truyền = toàn kỳ",
    nhom_im_lang: "Nhóm nghiệp vụ không có alert nào",
    nhom_theo_ngay: "Một nhóm biến động qua các ngày. Tham số: nhom",
    tinh_diem_gia_dinh: "Tính điểm Impact cho một trường hợp GIẢ ĐỊNH: khách dính những kịch bản nào, mỗi cái mấy lần, thì ra bao nhiêu điểm và mức gì. Dùng khi hỏi 'khách dính 3 kịch bản Low thì mấy điểm', 'nếu bị bắn 5 lần cùng rule X thì sao'. Tham số: kich_ban=[{ten:'...', so_lan:2}, ...]. CÓ công thức, ĐỪNG từ chối câu hỏi kiểu này.",
    giai_thich_diem: "Vì sao một khách CÓ THẬT được chừng đó điểm — phân rã từng kịch bản, từng lần lặp. Tham số: ma_khach (bắt buộc), ngay (tùy chọn), n.",
    uu_tien_dieu_tra: "Xếp hạng kịch bản nên điều tra trước, cân BỐN yếu tố: mức rủi ro 35% + độ tập trung 30% + xu hướng 20% + khối lượng 15%. Dùng khi hỏi 'nên ưu tiên gì', 'điều tra cái nào trước', 'cái nào đáng lo nhất'. ĐỪNG chỉ chọn kịch bản nhiều alert nhất — nhiều alert mà rải đều thì không cho đầu mối nào. Mỗi dòng có trường vi_sao, phải dùng nó để giải thích.",
    danh_gia_kich_ban: "Phán quyết một kịch bản CÓ ĐÁNG LO KHÔNG, kèm mốc so sánh (hạng ưu tiên, hạng trong nhóm, độ tập trung so trung vị). Dùng khi hỏi 'cái này có đáng lo không', 'X có nghiêm trọng không'. Trả lời thẳng bằng trường PHAN_QUYET rồi mới giải thích. Tham số: kich_ban.",
    xu_huong_gan_day: "Đà alert những ngày gần nhất (KHÔNG phải dự báo). Dùng khi hỏi 'sắp tới thế nào', 'đang tăng hay giảm'. Với câu hỏi về TƯƠNG LAI, phải nói rõ dữ liệu không dự báo được, rồi mô tả đà đã qua. Tham số: so_ngay (mặc định 14).",
    kich_ban_di_cung_nhau: "Cặp kịch bản nào hay nổ cùng MỘT khách trong cùng ngày. Dùng khi hỏi: hai rule có trùng nhau không, kịch bản nào đi kèm kịch bản nào, tổ hợp nào là thủ đoạn có cấu trúc. Xếp theo lift (dày gấp mấy lần mức ngẫu nhiên), KHÔNG phải theo số lượt — hai rule đông alert thì đương nhiên hay gặp nhau. Tham số: n (số cặp, mặc định 10), toi_thieu (sàn số lượt, mặc định 20).",
    do_tap_trung_kich_ban: "Alert của kịch bản dồn vào ít khách hay rải đều. Dùng khi hỏi: rule nào bắn vào vài đối tượng, rule nào quét rộng, alert có tập trung không. Tham số: kich_ban (tên, để trống thì xếp hạng tất cả), n.",
    so_sanh_hai_ky: "So HAI KHOẢNG THỜI GIAN với nhau: kịch bản nào tăng/giảm mạnh nhất, cái gì mới xuất hiện, cái gì tắt hẳn. Dùng khi hỏi 'tháng 8 so tháng 7', 'tuần này so tuần trước'. Tham số BẮT BUỘC đủ bốn: tu_a, den_a (kỳ mốc), tu_b, den_b (kỳ đang xét). Mọi so sánh theo trung bình mỗi ngày nên hai kỳ lệch số ngày vẫn đúng.",
    hanh_vi_theo_cum_diem: "Khách trong MỘT KHOẢNG ĐIỂM IMPACT thì hành vi ra sao: dính kịch bản nào, tổ hợp nào, lặp mấy lần, kịch bản nào đặc trưng cho khoảng đó. Tham số: tu + den (điểm của KHÁCH, 0-100) HOẶC muc ('Low'/'Medium'/'High'/'Very High'), thêm ngay nếu chỉ xét một ngày. LƯU Ý: 'điểm' ở đây là điểm Impact của KHÁCH trong một ngày — KHÁC hẳn 'điểm gốc' của kịch bản. Hỏi 'khách 80-82 điểm làm gì' thì dùng hàm này, đừng tra điểm gốc kịch bản.",
    top_khach_hang: "Khách bị bắn nhiều alert nhất. Tham số: n, ngay",
    ho_so_khach: "Hồ sơ một khách: từng ngày dính kịch bản gì. Tham số: ma",
    khach_tai_pham: "Khách bị bắn nhiều ngày. Tham số: so_ngay_toi_thieu",
    khach_nhieu_kich_ban: "Khách dính nhiều kịch bản khác nhau. Tham số: so_kb_toi_thieu, n",
    tim_khach: "Kiểm tra một mã khách có trong kỳ không. Tham số: ma",
    ghi_chep_dieu_tra: "Kết luận điều tra các kỳ trước"
  };

  function moTaDanhMuc() {
    return Object.keys(MO_TA).map(function (t) {
      return "  " + t + new Array(Math.max(1, 30 - t.length)).join(" ") + MO_TA[t];
    }).join("\n");
  }

  function goi(ten, thamSo) {
    if (!H[ten]) {
      throw new Error("Không có hàm '" + ten + "'. Các hàm có: " +
        Object.keys(H).join(", "));
    }
    var kq = H[ten](thamSo || {});
    kq._ham = ten;
    if (thamSo && Object.keys(thamSo).length) kq._tham_so = thamSo;
    return kq;
  }

  /* Danh sách ngày: kỳ ngắn thì liệt kê hết, kỳ dài thì nói khoảng + chỉ nêu
     ngày HỤT (nếu có). Kỳ 63 ngày mà rải hết ra tốn 779 ký tự chỉ để nói một
     điều model tự suy được từ ngày đầu và ngày cuối. Ngày hụt thì ngược lại
     — model KHÔNG tự biết, mà đó chính là thứ nó cần để khỏi trả lời về một
     ngày không có dữ liệu. */
  function moTaNgay(d) {
    var ds = d.days;
    if (ds.length <= 14) {
      return "  CÁC NGÀY CÓ DỮ LIỆU: " + ds.join(", ");
    }
    var co = {}, i;
    for (i = 0; i < ds.length; i++) co[ds[i]] = 1;
    /* KHÔNG dùng toISOString(): nó quy về UTC, máy ở múi giờ +7 thì
       new Date("2026-07-01T00:00:00").toISOString() ra "2026-06-30T17:00:00Z",
       cắt 10 ký tự thành 2026-06-30 — sinh ra một "ngày hụt" không có thật.
       Tự ghép từ giờ ĐỊA PHƯƠNG mới đúng. */
    var hut = [], t = new Date(ds[0] + "T00:00:00");
    var het = new Date(ds[ds.length - 1] + "T00:00:00");
    while (t <= het) {
      var s = t.getFullYear() + "-" +
        ("0" + (t.getMonth() + 1)).slice(-2) + "-" +
        ("0" + t.getDate()).slice(-2);
      if (!co[s]) hut.push(s);
      t.setDate(t.getDate() + 1);
    }
    return "  CÁC NGÀY CÓ DỮ LIỆU: " + ds.length + " ngày LIÊN TIẾP từ " +
      ds[0] + " đến " + ds[ds.length - 1] +
      (hut.length
        ? "\n  ⚠ HỤT " + hut.length + " ngày (không có dữ liệu, đừng trả lời " +
          "về những ngày này): " + hut.slice(0, 12).join(", ") +
          (hut.length > 12 ? " …" : "")
        : " — không hụt ngày nào");
  }

  /* Bảng kiến thức nhét vào prompt — để LLM biết cái gì là thực thể nội bộ */
  function moTaKy() {
    var d = duLieu(), tsd = thamSoDiem();
    return "KỲ DỮ LIỆU HIỆN TẠI (đọc từ file " + d.file + "):\n" +
      "  - " + d.tong.nd + " ngày: " + d.tong.d0 + " đến " + d.tong.d1 + "\n" +
      "  - " + d.tong.alert.toLocaleString("vi") + " alert | " +
      d.tong.kh.toLocaleString("vi") + " khách hàng | " +
      d.tong.luot.toLocaleString("vi") + " lượt (khách × ngày)\n" +
      "  - " + d.tong.kb + "/" + d.tong.kbCauHinh + " kịch bản có alert\n" +
      "  - Tham số điểm ĐANG ĐẶT: r = " + tsd.r + ", k = " + tsd.k +
      " | ngưỡng Impact: " + tsd.nguong.join(" / ") +
      (daDoiThamSo(tsd)
        ? " (người dùng đã kéo khác mặc định " + tsd.mac_dinh.r + " / " +
          tsd.mac_dinh.k + " / " + tsd.mac_dinh.nguong.join(" / ") +
          " — mọi con số về mức Impact phải tính theo giá trị ĐANG ĐẶT)"
        : " (đúng mặc định)") + "\n\n" +
      moTaNgay(d) + "\n\n" +
      "  CÁC NHÓM NGHIỆP VỤ:\n" +
      d.nhom.map(function (n) {
        return "    - " + n.ten + ": " + n.alert + " alert, " + n.kh +
               " khách, " + n.kb + "/" + n.kbTong + " kịch bản có alert";
      }).join("\n") + "\n\n" +
      "  CÁC KỊCH BẢN CÓ ALERT:\n" +
      d.kb.map(function (k) {
        return "    - " + k.ten + " | nhóm " + k.nhom + " | " + k.lv +
               " | " + k.sc + " điểm gốc | " + k.alert + " alert";
      }).join("\n") +
      moTaGioiHanBang(d);
  }

  /* Ranh giới của DỮ LIỆU trong file — khác với giới hạn về cách trả lời.
     Kỳ 7 ngày thì mấy chỗ này không lộ (bảng top phủ gần hết khách), nhưng
     kỳ 63 ngày thì lệch hẳn: 87.187 khách mà bảng chỉ giữ 500 người nặng
     nhất. Model không biết thì sẽ nói "khách X không có trong kỳ" trong khi
     thật ra chỉ là X không lọt top. */
  function moTaGioiHanBang(d) {
    var n = (d.topkh || []).length, t = d.tong.kh;
    if (!n || n >= t) return "";
    var it = d.topkh[n - 1];
    return "\n\n  ⚠ RANH GIỚI DỮ LIỆU — đọc kỹ trước khi kết luận:\n" +
      "    - Bảng xếp hạng khách (top_khach_hang, khach_tai_pham, " +
      "khach_nhieu_kich_ban) chỉ chứa " + n.toLocaleString("vi") +
      " người NẶNG NHẤT trong tổng số " + t.toLocaleString("vi") + " khách.\n" +
      "      Người thứ " + n + " có " + (it ? it.alert : "?") + " alert. " +
      "Không tìm thấy một khách trong bảng KHÔNG có nghĩa là khách đó không " +
      "bị alert — chỉ nghĩa là không lọt top. Nói rõ điều này thay vì " +
      "khẳng định 'không có trong kỳ'.\n" +
      "    - Ngược lại, các hàm thống kê theo NGÀY / KỊCH BẢN / NHÓM và " +
      "hanh_vi_theo_cum_diem tính trên TOÀN BỘ " +
      d.tong.luot.toLocaleString("vi") + " lượt, không bị cắt.";
  }

  return {
    goi: goi, moTaDanhMuc: moTaDanhMuc, moTaKy: moTaKy,
    timKichBan: timKichBan, diemLuot: diemLuot, TEN_MUC: TEN_MUC,
    danhSachHam: Object.keys(H), duLieu: duLieu
  };
})();
