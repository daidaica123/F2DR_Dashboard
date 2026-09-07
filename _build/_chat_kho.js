/* ══════════════════════════════════════════════════════════════════════
   KHO HỘI THOẠI  —  lưu lại các cuộc chat, còn nguyên sau khi tải lại trang

   Vì sao localStorage chứ không phải SQLite/database:
     Dashboard này là một trang HTML tĩnh, mọi thứ chạy trong trình duyệt.
     Không có backend nào lúc chạy để mà cắm database vào:
       · bản HTML       — mở bằng file://, không có máy chủ
       · bản Streamlit   — filesystem bị xoá sạch mỗi lần app ngủ dậy
       · bản Cloudflare  — Pages không có đĩa ghi được
     localStorage bền qua reload, qua tắt trình duyệt, và chạy giống nhau
     ở cả ba bản. Đúng nhu cầu mà không phải dựng thêm hạ tầng.

   Giới hạn cần biết: localStorage gắn với MỘT trình duyệt trên MỘT máy.
   Đổi máy hay xoá dữ liệu duyệt web là mất. Với sổ tay hỏi đáp cá nhân thì
   chấp nhận được; muốn đồng bộ nhiều máy mới cần tới máy chủ thật.
   ══════════════════════════════════════════════════════════════════════ */
window.F2Kho = (function () {
  "use strict";

  var KHOA = "f2dr_chat_v1";
  var SO_CUOC_TOI_DA = 30;      // giữ 30 cuộc gần nhất, cũ hơn thì bỏ
  var SO_TIN_MOI_CUOC = 60;     // một cuộc dài quá thì cắt bớt đầu

  /* localStorage bị chặn ở chế độ riêng tư trên vài trình duyệt, và cũng
     đầy được (thường ~5 MB). Hỏng chỗ này TUYỆT ĐỐI không được làm hỏng
     chat — nên mọi lối vào đều bọc try và ngã về bộ nhớ tạm. */
  var TAM = null;               // dùng khi localStorage không xài được

  function doc() {
    if (TAM) return TAM;
    try {
      var s = localStorage.getItem(KHOA);
      if (!s) return { ds: [], hienTai: null };
      var j = JSON.parse(s);
      return j && j.ds ? j : { ds: [], hienTai: null };
    } catch (e) {
      TAM = { ds: [], hienTai: null };
      return TAM;
    }
  }

  function ghi(kho) {
    if (TAM) { TAM = kho; return; }
    try {
      localStorage.setItem(KHOA, JSON.stringify(kho));
    } catch (e) {
      /* Đầy kho: bỏ dần cuộc cũ nhất rồi thử lại. Vẫn không được thì
         chuyển hẳn sang bộ nhớ tạm — phiên này vẫn chat bình thường,
         chỉ không giữ được sau khi tải lại. */
      for (var i = 0; i < 6 && kho.ds.length > 1; i++) {
        kho.ds.pop();
        try { localStorage.setItem(KHOA, JSON.stringify(kho)); return; }
        catch (e2) { /* thử tiếp */ }
      }
      TAM = kho;
    }
  }

  function ma() {
    return String(Date.now()) + "-" + Math.random().toString(36).slice(2, 7);
  }

  /* Tên cuộc chat lấy từ câu hỏi ĐẦU TIÊN — đó là thứ người ta nhớ khi
     tìm lại. Cắt ngắn cho vừa danh sách bên cạnh. */
  function datTen(cau) {
    var s = String(cau || "").replace(/\s+/g, " ").trim();
    if (s.length > 42) s = s.slice(0, 42).replace(/\s\S*$/, "") + "…";
    return s || "Cuộc trò chuyện";
  }

  return {
    /* Danh sách cuộc chat, mới nhất lên đầu. Chỉ trả phần tóm lược để vẽ
       danh sách, không kéo cả nội dung ra cho nhẹ. */
    danhSach: function () {
      var k = doc();
      return k.ds.map(function (c) {
        return { ma: c.ma, ten: c.ten, luc: c.luc, soTin: (c.tin || []).length };
      });
    },

    maHienTai: function () { return doc().hienTai; },

    layCuoc: function (m) {
      var k = doc(), i;
      for (i = 0; i < k.ds.length; i++) if (k.ds[i].ma === m) return k.ds[i];
      return null;
    },

    /* Mở một cuộc cũ: chỉ đánh dấu đang xem cuộc nào, nội dung do bên
       giao diện tự đọc bằng layCuoc(). */
    chon: function (m) {
      var k = doc();
      k.hienTai = m;
      ghi(k);
    },

    /* Cuộc mới chỉ được tạo THẬT khi có câu hỏi đầu tiên (xem themTin).
       Bấm "New Chat" mà tạo ngay thì danh sách đầy những cuộc rỗng. */
    moiCuoc: function () {
      var k = doc();
      k.hienTai = null;
      ghi(k);
    },

    /* Thêm một lượt hỏi–đáp. Trả về mã cuộc đang ghi vào, vì lượt đầu
       tiên là lúc cuộc được sinh ra. */
    themTin: function (hoiCau, dapVan, kem) {
      var k = doc(), c = null, i;
      for (i = 0; i < k.ds.length; i++) {
        if (k.ds[i].ma === k.hienTai) { c = k.ds[i]; break; }
      }
      if (!c) {
        c = { ma: ma(), ten: datTen(hoiCau), luc: Date.now(), tin: [] };
        k.ds.unshift(c);
        k.hienTai = c.ma;
      }
      c.luc = Date.now();
      c.tin.push({ vai: "toi", van: hoiCau, luc: Date.now() });
      c.tin.push({
        vai: "bot", van: dapVan, luc: Date.now(),
        /* Giữ nhãn kiểm chứng và nguồn số liệu: mở lại cuộc cũ mà mất
           dấu "✓ n số đã đối chiếu" thì không còn biết câu trả lời đó
           có được soát hay không. */
        kem: kem || null
      });
      if (c.tin.length > SO_TIN_MOI_CUOC) {
        c.tin = c.tin.slice(c.tin.length - SO_TIN_MOI_CUOC);
      }
      /* Cuộc vừa động phải lên đầu danh sách. */
      k.ds = [c].concat(k.ds.filter(function (x) { return x.ma !== c.ma; }));
      if (k.ds.length > SO_CUOC_TOI_DA) k.ds = k.ds.slice(0, SO_CUOC_TOI_DA);
      ghi(k);
      return c.ma;
    },

    xoa: function (m) {
      var k = doc();
      k.ds = k.ds.filter(function (x) { return x.ma !== m; });
      if (k.hienTai === m) k.hienTai = null;
      ghi(k);
    },

    xoaHet: function () {
      ghi({ ds: [], hienTai: null });
    },

    /* Ngữ cảnh cho câu hỏi nối tiếp: vài lượt gần nhất của cuộc đang mở,
       đúng dạng mà bộ não đang nhận ({hoi, dap}). Không gửi cả cuộc —
       vừa tốn hạn mức vừa dễ vượt giới hạn. */
    nganhCanh: function (soLuot) {
      var c = this.layCuoc(doc().hienTai);
      if (!c) return [];
      var ra = [], t = c.tin, i;
      for (i = 0; i + 1 < t.length; i += 2) {
        if (t[i].vai === "toi" && t[i + 1].vai === "bot") {
          ra.push({ hoi: t[i].van, dap: t[i + 1].van });
        }
      }
      return ra.slice(-(soLuot || 6));
    },

    /* Có dùng được localStorage không — để giao diện nói thật với người
       dùng thay vì hứa suông là đã lưu. */
    ben: function () { return !TAM; }
  };
})();
