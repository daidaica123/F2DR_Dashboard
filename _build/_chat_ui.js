/* ══════════════════════════════════════════════════════════════════════
   PANEL CHAT — phần giao diện.

   Chỉ lo vẽ và nhận thao tác. Toàn bộ phần nghĩ nằm ở _chat_bo_nao.js:
   vòng lặp suy luận, chặn thông tin nhân thân, kiểm chứng số. Tầng dữ liệu
   nằm ở _chat_tri_thuc.js.

   Tách ba lớp như vậy để bản HTML này và bản Streamlit dùng chung một cách
   nghĩ, chỉ khác nhau ở chỗ vẽ.
   ══════════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var nut = $("f2-nut"), panel = $("f2-panel"), tin = $("f2-tin"),
      o = $("f2-o"), gui = $("f2-gui"), goiy = $("f2-goiy"),
      chip = $("f2-chip"), phu = $("f2-phu"), conlai = $("f2-conlai"),
      thu = $("f2-thu"), phong = $("f2-phong");

  /* Dashboard đang nằm trong iframe của trang khác (bản deploy trên
     Streamlit) thì góc phải dưới không còn là của mình: huy hiệu Streamlit
     nằm ở trang cha, vẽ đè lên iframe và che mất một phần nút chat. Gắn cờ
     để CSS nâng nút lên. Trình duyệt chặn đọc window.top khi khác nguồn —
     chính lúc ném lỗi cũng là lúc chắc chắn đang bị nhúng. */
  try {
    if (window.self !== window.top) document.body.classList.add("f2-nhung");
  } catch (e) {
    document.body.classList.add("f2-nhung");
  }

  var BN = window.F2BoNao, TT = window.F2TriThuc;

  var SO_LUOT_TOI_DA = 40;
  var soLuot = 0, dangCho = false;
  var lichSu = [];          // {hoi, dap} — ngữ cảnh cho câu hỏi nối tiếp

  var GOI_Y_DAU = [
    "Kịch bản nào nhiều alert nhất?",
    "Ngày nào bất thường?",
    "Khách nào bị bắn nhiều nhất?",
    "Có kịch bản nào im lặng không?"
  ];

  /* ───────── markdown rất gọn → HTML ─────────
     Thoát HTML TRƯỚC để nội dung từ model không chèn được thẻ lạ vào trang. */
  function md(s) {
    s = String(s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");

    var kho = [];
    s = s.replace(/```(?:\w+)?\n([\s\S]*?)```/g, function (m, g) {
      kho.push("<pre>" + g + "</pre>");
      return "\u0000" + (kho.length - 1) + "\u0000";
    });
    s = s.replace(/`([^`\n]+)`/g, "<code>$1</code>");
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    /* Nghiêng: phải chạy SAU đậm, không thì cặp ** bị nuốt mất một sao.
       Đòi hai đầu dính chữ để dấu sao trong công thức không thành thẻ. */
    s = s.replace(/(^|[\s(>])\*([^*\n]+)\*(?=$|[\s.,;:)!?])/g,
                  "$1<em>$2</em>");

    var dong = s.split("\n"), ra = [], trongDs = false;
    for (var i = 0; i < dong.length; i++) {

      /* Bảng markdown: dòng | … | rồi dòng phân cách |:---|---:| rồi thân.
         Model rất hay trả lời dạng bảng khi được hỏi "top 5"; không dựng
         thành <table> thì nó đổ ra một mớ gạch đứng, đọc không nổi. */
      if (/^\s*\|.*\|\s*$/.test(dong[i]) &&
          i + 1 < dong.length &&
          /^\s*\|[\s:\-|]+\|\s*$/.test(dong[i + 1])) {
        if (trongDs) { ra.push("</ul>"); trongDs = false; }

        var o = function (d) {                 // tách ô, bỏ | ở hai đầu
          return d.replace(/^\s*\||\|\s*$/g, "").split("|")
                  .map(function (x) { return x.trim(); });
        };
        /* Cột căn phải nếu dấu phân cách có dạng ---: — số liệu căn phải
           mới so sánh được bằng mắt. */
        var canh = o(dong[i + 1]).map(function (x) {
          return /^:?-+:$/.test(x) ? "center" : /-+:$/.test(x) ? "right" : "left";
        });
        var dau = o(dong[i]), than = [], j = i + 2;
        while (j < dong.length && /^\s*\|.*\|\s*$/.test(dong[j])) {
          than.push(o(dong[j])); j++;
        }

        var t = ['<div class="f2-bang-bao"><table class="f2-bang"><thead><tr>'];
        dau.forEach(function (c, k) {
          t.push('<th style="text-align:' + (canh[k] || "left") + '">' + c + "</th>");
        });
        t.push("</tr></thead><tbody>");
        than.forEach(function (h) {
          t.push("<tr>");
          for (var k = 0; k < dau.length; k++)
            t.push('<td style="text-align:' + (canh[k] || "left") + '">' +
                   (h[k] || "") + "</td>");
          t.push("</tr>");
        });
        t.push("</tbody></table></div>");

        kho.push(t.join(""));
        ra.push("\u0000" + (kho.length - 1) + "\u0000");
        i = j - 1;
        continue;
      }

      var m = dong[i].match(/^\s*[-*•]\s+(.*)$/);
      if (m) {
        if (!trongDs) { ra.push("<ul>"); trongDs = true; }
        ra.push("<li>" + m[1] + "</li>");
      } else {
        if (trongDs) { ra.push("</ul>"); trongDs = false; }
        ra.push(dong[i]);
      }
    }
    if (trongDs) ra.push("</ul>");

    s = ra.join("\n").replace(/\n{2,}/g, "</p><p>").replace(/\n/g, "<br>");
    s = "<p>" + s + "</p>";
    s = s.replace(/(<br>\s*)+(<\/?(?:ul|li|pre)>)/g, "$2")
         .replace(/(<\/?(?:ul|li|pre)>)(\s*<br>)+/g, "$1")
         .replace(/<p><ul>/g, "<ul>").replace(/<\/ul><\/p>/g, "</ul>")
         .replace(/<p>\s*<\/p>/g, "");
    /* Bảng và khối code đứng riêng một dòng nên hay bị <br> kẹp hai bên —
       gỡ trước khi trả chỗ giữ về, không thì dôi ra một dòng trống. */
    s = s.replace(/(<br>\s*)+(\u0000\d+\u0000)/g, "$2")
         .replace(/(\u0000\d+\u0000)(\s*<br>)+/g, "$1");
    kho.forEach(function (k, j) {
      /* Truyền hàm chứ không truyền chuỗi: nội dung bảng có thể chứa "$&",
         đưa thẳng vào replace thì bị hiểu thành ký hiệu đặc biệt. */
      s = s.replace("\u0000" + j + "\u0000", function () { return k; });
    });
    return s.replace(/<p><pre>/g, "<pre>").replace(/<\/pre><\/p>/g, "</pre>")
            .replace(/<p>(<div class="f2-bang-bao">)/g, "$1")
            .replace(/(<\/table><\/div>)<\/p>/g, "$1");
  }

  function thoat(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;");
  }

  function cuonXuong() { tin.scrollTop = tin.scrollHeight; }

  function themHang(vai, html) {
    var d = document.createElement("div");
    d.className = "f2-hang" + (vai === "toi" ? " toi" : "");
    d.innerHTML = '<div class="f2-bong ' + (vai === "toi" ? "toi" : "bot") +
                  '">' + html + "</div>";
    tin.appendChild(d);
    cuonXuong();
    return d;
  }

  /* ───────── biến tên trong câu trả lời thành nút bấm ─────────

     Tên kịch bản dài tới bảy tám chữ, bắt người dùng gõ lại để hỏi tiếp là
     hành. Quét câu trả lời, thấy tên nào có thật trong dữ liệu thì bọc lại
     thành nút — bấm là hỏi tiếp về đúng thứ đó.

     Chỉ nhận diện tên CÓ THẬT trong D, nên không thể tạo ra nút trỏ vào một
     kịch bản không tồn tại. */
  var THAM_CHIEU = null;

  function bangThamChieu() {
    if (THAM_CHIEU) return THAM_CHIEU;
    var ds = [];
    try {
      var d = TT.duLieu();
      (d.kb || []).forEach(function (k) {
        ds.push({ ten: k.ten, hoi: "Chi tiết kịch bản " + k.ten });
      });
      var daNhom = {};
      (d.kb || []).forEach(function (k) {
        if (k.nhom && !daNhom[k.nhom]) {
          daNhom[k.nhom] = 1;
          ds.push({ ten: k.nhom, hoi: "Chi tiết nhóm " + k.nhom });
        }
      });
      /* Model lúc viết "01/09", lúc viết "2026-09-01" — nhận cả hai, không
         thì nửa số ngày trong câu trả lời không bấm được. */
      (d.days || []).forEach(function (n) {
        var nn = n.slice(8, 10) + "/" + n.slice(5, 7);
        var cau = "Ngày " + nn + " có gì đáng chú ý?";
        ds.push({ ten: n, hoi: cau });          // 2026-09-01
        ds.push({ ten: nn, hoi: cau });         // 01/09
      });
    } catch (e) { /* chưa có dữ liệu thì thôi, không có nút cũng không sao */ }

    /* Tên dài đứng trước: "THUÊ BAO" là con của "TB_Thuê bao topup..." nên
       khớp tên ngắn trước sẽ cắt nát tên dài. */
    ds.sort(function (a, b) { return b.ten.length - a.ten.length; });
    THAM_CHIEU = ds;
    return ds;
  }

  function noiThamChieu(goc) {
    var ds = bangThamChieu();
    if (!ds.length || !goc) return;

    var dsNut = document.createTreeWalker(goc, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        /* Không đụng vào khối mã, và không bọc nút trong nút. */
        for (var p = n.parentNode; p && p !== goc; p = p.parentNode) {
          var t = (p.tagName || "").toLowerCase();
          if (t === "pre" || t === "code" || t === "button") {
            return NodeFilter.FILTER_REJECT;
          }
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var hangDoi = [], nut;
    while ((nut = dsNut.nextNode())) hangDoi.push(nut);

    /* Hàng đợi chứ không phải duyệt một lượt: cắt xong còn phần đuôi, trong
       đuôi đó vẫn có thể còn tên khác. Một câu thường nhắc cả kịch bản, cả
       nhóm, cả ngày. */
    var canGac = 0;
    while (hangDoi.length && canGac++ < 400) {
      nut = hangDoi.shift();
      var van = nut.nodeValue, hit = null;
      for (var i = 0; i < ds.length; i++) {
        var v = van.indexOf(ds[i].ten);
        if (v >= 0 && (hit === null || v < hit.v)) hit = { v: v, m: ds[i] };
      }
      if (!hit) continue;

      var sau = nut.splitText(hit.v);
      sau.nodeValue = sau.nodeValue.slice(hit.m.ten.length);
      var b = document.createElement("button");
      b.className = "f2-ref";
      b.type = "button";
      b.textContent = hit.m.ten;
      b.title = hit.m.hoi;
      b.onclick = (function (cau) {
        return function () { hoi(cau); };
      })(hit.m.hoi);
      sau.parentNode.insertBefore(b, sau);
      hangDoi.push(sau);                    // quét tiếp phần đuôi
    }
  }

  function veGoiY(ds) {
    goiy.innerHTML = "";
    (ds || []).slice(0, 4).forEach(function (g) {
      var b = document.createElement("button");
      b.textContent = g;
      b.onclick = function () { hoi(g); };
      goiy.appendChild(b);
    });
  }

  function veNhan(R) {
    var the = [], kc = R.kiemChung || {};
    if (kc.dat && kc.soDaKiem) {
      the.push(["tot", "✓ " + kc.soDaKiem + " số đã đối chiếu"]);
    } else if (R.boDienGiai) {
      the.push(["canh", "⚠ đã bỏ phần diễn giải"]);
    } else if (kc.dat && !kc.soDaKiem && !R.khongCanDoiChieu &&
               /\d/.test(R.dap || "")) {
      /* Chỉ cảnh báo khi câu trả lời ĐÁNG LẼ phải dựa vào dữ liệu mà lại
         không đối chiếu được. Xã giao, phép tính tự làm, câu giới thiệu...
         không lấy số từ dữ liệu nên không có gì để đối chiếu — dán nhãn vào
         đó chỉ làm người đọc nghi ngờ một con số vốn chắc chắn đúng. */
      the.push(["canh", "⚠ không đối chiếu được số nào"]);
    }
    if (R.cacBuoc && R.cacBuoc.length)
      the.push(["", R.cacBuoc.length + " bước"]);
    the.push(["", (R.giay || 0).toFixed(1) + "s"]);
    if (R.piiDaCat && R.piiDaCat.length)
      the.push(["canh", "⚠ đã ẩn " + R.piiDaCat.length + " chuỗi định danh"]);
    if (!the.length) return;

    var d = document.createElement("div");
    d.className = "f2-nhan";
    d.innerHTML = the.map(function (t) {
      return '<span class="f2-the ' + t[0] + '">' + t[1] + "</span>";
    }).join("");
    tin.appendChild(d);
  }

  function veNguon(R) {
    if (!R.cacBuoc || !R.cacBuoc.length) return;
    var noi = R.cacBuoc.filter(function (b) { return !b.ketQua._loi; })
      .map(function (b) {
        var sach = {};
        Object.keys(b.ketQua).forEach(function (k) {
          if (k.charAt(0) !== "_") sach[k] = b.ketQua[k];
        });
        return "▸ " + b.moTa + "\n" + JSON.stringify(sach, null, 1);
      }).join("\n\n");
    if (!noi) return;
    var d = document.createElement("details");
    d.innerHTML = "<summary>▸ nguồn số liệu</summary><pre>" +
                  thoat(noi.slice(0, 4000)) + "</pre>";
    tin.appendChild(d);
  }

  /* Chữ hiện dần. Không làm bot nhanh hơn, nhưng người đọc thấy chữ đầu
     tiên ngay thay vì nhìn màn hình trống tới lúc có đủ câu. */
  function goChu(el, html, xong) {
    var i = 0, buoc = 11;
    var nhip = setInterval(function () {
      i += buoc;
      var s = html.slice(0, i);
      var mo = s.lastIndexOf("<"), dg = s.lastIndexOf(">");
      if (mo > dg) s = s.slice(0, mo);      // không cắt giữa một thẻ
      el.innerHTML = s;
      cuonXuong();
      if (i >= html.length) {
        clearInterval(nhip);
        el.innerHTML = html;
        cuonXuong();
        if (xong) xong();
      }
    }, 12);
  }

  /* ───────── luồng hỏi đáp ───────── */
  function hoi(cau) {
    cau = (cau || "").trim();
    if (!cau || dangCho || soLuot >= SO_LUOT_TOI_DA) return;

    soLuot++;
    themHang("toi", md(cau));
    o.value = "";
    o.style.height = "auto";
    veGoiY([]);
    capNhatConLai();

    dangCho = true;
    gui.disabled = true;
    nut.classList.add("f2-nghi");     /* robot nghieng dau khi dang nghi */
    var cho = themHang("bot",
      '<span class="f2-go"><i></i><i></i><i></i></span>');

    var oBuoc = document.createElement("div");
    oBuoc.className = "f2-buoc";
    tin.appendChild(oBuoc);

    function log(s) {
      oBuoc.textContent = s.slice(0, 86);
      cuonXuong();
    }

    var P;
    try { P = BN.hoi(cau, lichSu, log); }
    catch (e) { P = Promise.reject(e); }

    P.then(function (R) {
      oBuoc.remove();
      cho.remove();

      var t = BN.tachGoiY(R.dap);
      var d = themHang("bot", "");
      var bong = d.querySelector(".f2-bong");
      goChu(bong, md(t.van), function () {
        noiThamChieu(bong);
        veNhan(R);
        veNguon(R);
        veGoiY(t.goiY.length ? t.goiY : GOI_Y_DAU.slice(0, 3));
        lichSu.push({ hoi: cau, dap: t.van });
        if (lichSu.length > 6) lichSu.shift();
        dangCho = false;
        gui.disabled = false;
        nut.classList.remove("f2-nghi");
        cuonXuong();
      });
    }).catch(function (e) {
      /* Ba cham quay mai la loi te nhat: nguoi dung tuong bot dang nghi,
         thuc ra no chet tu lau. Tha bao loi xau con hon treo im lang. */
      oBuoc.remove();
      cho.remove();
      themHang("bot", md(
        "**Trợ lý gặp lỗi nên không trả lời được câu này.**\n\n" +
        "```\n" + String((e && e.message) || e) + "\n```\n\n" +
        "Bấm F12 → Console để xem chi tiết."));
      dangCho = false;
      gui.disabled = false;
      nut.classList.remove("f2-nghi");
      cuonXuong();
    });
  }

  function capNhatConLai() {
    var con = SO_LUOT_TOI_DA - soLuot;
    if (con <= 0) {
      conlai.textContent = "đã hết lượt hỏi — tải lại trang để bắt đầu phiên mới";
      o.disabled = true;
      gui.disabled = true;
    } else if (con <= 10) {
      conlai.textContent = "còn " + con + " lượt hỏi trong phiên này";
    } else {
      conlai.textContent = "";
    }
  }

  /* ───────── mở / thu ───────── */
  var hen_dong = null;
  function mo() {
    tatThoai();
    /* Phai huy hen dong dang cho: bam ra ngoai (bat dau dong) roi bam ngay
       vao nut trong 190ms thi hen cu van no ra va dong panel vua mo. */
    clearTimeout(hen_dong);
    panel.classList.remove("f2-an", "f2-dong");
    nut.classList.add("f2-an");
    nut.classList.remove("f2-hien");
    setTimeout(function () { o.focus(); cuonXuong(); }, 60);
  }
  /* Truoc day thu lai la display:none phut mot cai, trong khi mo thi co
     animation truot len — lech han. Gio panel co ve phia nut tron o goc duoi
     phai, roi nut moi bung ra, thanh mot mach lien tuc. */
  function thuLai() {
    if (panel.classList.contains("f2-an")) return;
    clearTimeout(hen_dong);
    panel.classList.add("f2-dong");
    hen_dong = setTimeout(function () {
      panel.classList.add("f2-an");
      panel.classList.remove("f2-dong");
      nut.classList.remove("f2-an");
      nut.classList.add("f2-hien");
      setTimeout(function () { nut.classList.remove("f2-hien"); }, 320);
    }, 190);
  }

  /* ═══════════ BONG BÓNG THOẠI ═══════════
     Thi thoang noi mot cau cho do vo hon. Ky luat chat, neu khong thanh phien:
       - chi khi panel DANG DONG, va tab dang duoc nhin
       - im 45 giay dau, sau do cach nhau 70-160 giay
       - toi da 4 lan moi phien, tu an sau 9 giay
       - bam vao la mo thang panel; bam ra ngoai thi tat
     Cau co so lieu lay THANG tu bien D cua dashboard, khong qua LLM nen khong
     the bia. Khong co D (ban deploy) thi chi dung cau vu vo. */
  var THOAI_TOI_DA = 4, daThoai = 0, oThoai = null, henThoai = null, henTat = null;

  function cauVuVo() {
    return [
      "Tôi vẫn ở đây, cần gì thì gọi.",
      "Rảnh quá… hỏi tôi câu gì đi.",
      "Đang ngồi canh mấy con số. Yên tâm.",
      "Bạn cứ hỏi tiếng Việt bình thường, tôi hiểu được.",
      "Hỏi \u201Cngày nào bất thường?\u201D thử xem.",
      "Số nào tôi đưa ra cũng có trong dữ liệu, không bịa đâu.",
      "Muốn xem riêng một ngày thì bấm vào ngày trên thanh phía trên nhé."
    ];
  }
  function cauCoSo() {
    var ra = [];
    try {
      if (typeof D === "undefined" || !D || !D.tong) return ra;
      var t = D.tong, f = function (x) { return Number(x).toLocaleString("vi"); };
      var nhan = function (g) { return g.slice(8, 10) + "/" + g.slice(5, 7); };
      ra.push("Kỳ này có <b>" + f(t.alert) + "</b> alert của <b>" +
              f(t.kh) + "</b> khách hàng.");
      if (D.ngay && D.ngay.length) {
        var mx = D.ngay[0];
        D.ngay.forEach(function (x) { if (x.alert > mx.alert) mx = x; });
        ra.push("Ngày cao nhất kỳ là <b>" + nhan(mx.ngay) + "</b> với <b>" +
                f(mx.alert) + "</b> alert.");
        var cuoi = D.ngay[D.ngay.length - 1];
        ra.push("Ngày mới nhất (<b>" + nhan(cuoi.ngay) + "</b>) có <b>" +
                f(cuoi.alert) + "</b> alert.");
      }
      if (t.kb && t.kbCauHinh)
        ra.push("<b>" + (t.kbCauHinh - t.kb) + "</b> kịch bản đã cấu hình mà " +
                "không có alert nào cả kỳ.");
    } catch (e) { }
    return ra;
  }
  function tatThoai() {
    clearTimeout(henTat);
    if (!oThoai) return;
    var q = oThoai; oThoai = null;
    q.classList.add("f2-tat");
    setTimeout(function () { if (q.parentNode) q.parentNode.removeChild(q); }, 280);
  }
  function noiThoai() {
    if (oThoai || daThoai >= THOAI_TOI_DA) return;
    if (!panel.classList.contains("f2-an")) return;   /* dang mo thi thoi */
    if (document.hidden) return;
    var kho = cauVuVo();
    var co = cauCoSo();
    /* Tron: phan lon la cau vu vo, thi thoang chen mot con so that. */
    if (co.length && Math.random() < 0.45) kho = co;
    var cau = kho[Math.floor(Math.random() * kho.length)];
    var b = document.createElement("div");
    b.className = "f2-thoai";
    b.innerHTML = cau + '<span class="f2-thoai-x">bấm để mở trợ lý</span>';
    b.onclick = function () { tatThoai(); mo(); };
    document.body.appendChild(b);
    oThoai = b; daThoai++;
    henTat = setTimeout(tatThoai, 9000);
  }
  function henNoi() {
    clearTimeout(henThoai);
    if (daThoai >= THOAI_TOI_DA) return;
    henThoai = setTimeout(function () {
      noiThoai();
      henNoi();
    }, 70000 + Math.random() * 90000);
  }
  /* Im 45 giay dau: nguoi ta vua vao trang, dang doc dashboard, chua can bi
     lam phien. */
  setTimeout(henNoi, 45000);
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) { clearTimeout(henThoai); tatThoai(); }
    else henNoi();
  });

  nut.onclick = mo;
  thu.onclick = thuLai;

  /* Phong to / thu nho khung chat.
     Bang bay tam cot khong the vua trong panel 412px. Nho lua chon lai:
     ai da phong to mot lan thi lan sau mo chat van thay khung to, khoi phai
     bam lai moi lan. localStorage co the bi chan (che do rieng tu) nen boc
     try -- hong cai nay khong duoc lam hong nut. */
  var KHOA_TO = "f2_chat_to";
  function datTo(to, ghi) {
    panel.classList.toggle("f2-to", to);
    phong.textContent = to ? "⤡" : "⤢";
    phong.title = to ? "Thu nho khung chat" : "Phong to khung chat";
    phong.setAttribute("aria-label", phong.title);
    phong.setAttribute("aria-pressed", to ? "true" : "false");
    if (ghi) { try { localStorage.setItem(KHOA_TO, to ? "1" : "0"); } catch (e) {} }
    /* Doi be ngang xong, cho trinh duyet dan lai roi moi keo xuong day --
       khong thi cuon theo chieu cao cu, hut mat may dong cuoi. */
    setTimeout(cuonXuong, 0);
  }
  phong.onclick = function () {
    datTo(!panel.classList.contains("f2-to"), true);
  };
  try {
    if (localStorage.getItem(KHOA_TO) === "1") datTo(true, false);
  } catch (e) {}

  /* Bam ra ngoai khung chat thi tu thu lai. Panel che han phan phai cua
     dashboard, ma thao tac ke tiep cua nguoi dung gan nhu luon la doc bang
     ben duoi -- bat ho mot cu bam vao dau tru la thua.
     Hai truong hop phai chua: bam vao chinh nut mo (khong thi vua mo da thu),
     va dang boi den chu trong panel roi tha chuot ra ngoai (van tinh la mot
     cu click, thu lai luc do la cuop mat thao tac cua nguoi dung). */
  /* KHONG dung panel.contains(e.target) o day.
     Nut goi y tu xoa chinh minh ngay trong onclick cua no: hoi() goi
     veGoiY([]) -> goiy.innerHTML = "". Den luc su kien noi len den document
     thi e.target da roi khoi cay DOM, contains() tra ve false, va panel bi
     thu lai oan. composedPath() chup duong di TAI LUC PHAT su kien nen van
     con nguyen ke ca khi nut da bi xoa. */
  function trongKhung(e) {
    var duong = e.composedPath ? e.composedPath() : null;
    if (duong && duong.length) {
      for (var i = 0; i < duong.length; i++) {
        if (duong[i] === panel || duong[i] === nut ||
            (oThoai && duong[i] === oThoai)) return true;
      }
      return false;
    }
    return panel.contains(e.target) || nut.contains(e.target) ||
           !!(oThoai && oThoai.contains(e.target));
  }

  document.addEventListener("click", function (e) {
    if (panel.classList.contains("f2-an")) return;
    if (trongKhung(e)) return;
    var sel = window.getSelection && window.getSelection();
    if (sel && sel.rangeCount && !sel.isCollapsed) {
      var nd = sel.getRangeAt(0).commonAncestorContainer;
      if (nd && nd.nodeType !== 1) nd = nd.parentNode;
      if (nd && panel.contains(nd)) return;
    }
    thuLai();
  });
  gui.onclick = function () { hoi(o.value); };

  o.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); hoi(o.value); }
    if (e.key === "Escape") thuLai();
  });
  o.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 104) + "px";
  });

  /* ───────── khởi động ───────── */
  function nhan(d) { return d.slice(8, 10) + "/" + d.slice(5, 7); }

  try {
    var D2 = TT.duLieu();
    phu.textContent = D2.tong.nd + " ngày · " +
      D2.tong.alert.toLocaleString("vi") + " alert · " +
      nhan(D2.tong.d0) + " – " + nhan(D2.tong.d1);
    chip.innerHTML = "nguồn: " + thoat(D2.file);
    chip.classList.remove("f2-an");
  } catch (e) {
    phu.textContent = "chưa đọc được dữ liệu dashboard";
  }

  if (!BN || typeof BN.hoi !== "function") {
    themHang("bot", md(
      "**Bộ não trợ lý không nạp được** (`window.F2BoNao` không tồn tại).\n\n" +
      "Gần như chắc chắn `_chat_bo_nao.js` lỗi cú pháp. Kiểm tra:\n\n" +
      "```\npy -3.13 _build/soat_js.py\n```"));
    o.disabled = true;
    gui.disabled = true;
  } else if (!BN.coKhoa()) {
    themHang("bot", md(
      "**Chưa có khoá API** nên tôi chưa trả lời được.\n\n" +
      "Trên Streamlit: mở **Settings → Secrets** của app rồi dán vào\n\n" +
      "```\nGEMINI_API_KEYS = [\"khoa1\", \"khoa2\"]\n```\n\n" +
      "Tại máy: đặt khoá trong `.streamlit/secrets.toml` rồi chạy lại " +
      "`_build/xem_truoc.py`.\n\n" +
      "Dashboard và giao diện chat vẫn dùng bình thường."));
  } else {
    themHang("bot", md(
      "Chào bạn. Tôi đọc được dữ liệu alert của kỳ này và trả lời bằng số " +
      "lấy thẳng từ đó — không đoán.\n\n" +
      "Hỏi gì cũng được, hoặc bấm một câu gợi ý bên dưới."));
  }
  veGoiY(GOI_Y_DAU);
  capNhatConLai();

  /* Mở ra vài hàm thuần để kiểm thử tự động dựng lại được câu trả lời mà
     không phải gọi model. Chỉ đọc, không đổi trạng thái panel. */
  window.F2Panel = { md: md, noiThamChieu: noiThamChieu,
                     bangThamChieu: bangThamChieu, hoi: hoi };
})();
