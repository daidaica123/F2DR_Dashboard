# SKILL — Dashboard HTML (thiết kế & dựng)

> **Dùng khi:** được yêu cầu tạo hoặc sửa một dashboard bằng HTML/CSS/JS. Đọc
> file này TRƯỚC khi viết dòng CSS đầu tiên.
> (Làm file Excel thì dùng skill `excel-design`, không phải file này.)
>
> Rút ra từ `_build/_van_hanh_template.html` — dashboard vận hành F2DR, ~5 MB,
> một file HTML tự chứa, không phụ thuộc thư viện ngoài. **Mọi con số dưới đây
> trích thẳng từ CSS của file đó** (đã đối chiếu 26/26 mục), không phải guideline
> chung chung.
>
> Mục tiêu: đọc xong tái tạo được gần đúng cùng một ngôn ngữ thiết kế.
>
> Ba loại nhãn dùng xuyên suốt:
> - **[QUY TẮC]** — đang có trong file, làm theo
> - **[KHUYẾN NGHỊ]** — suy ra từ thiết kế hiện có, file chưa quy định rõ
> - **[TRÁNH]** — anti-pattern, gồm cả lỗi đã thật sự mắc trong chính file này

---

## 0. Nguyên tắc lớn nhất

Dashboard này không phải "trang có biểu đồ". Nó là **một lớp kết luận đặt trên số
liệu thô**. Người quản lý mở ra phải biết ngay *hiện đang có vấn đề gì*, không
phải tự đọc bảng rồi tự suy.

Ba điều chi phối mọi quyết định thiết kế bên dưới:

1. **Màu mang nghĩa, không trang trí.** Xanh ngọc = mật độ dữ liệu. Đỏ = rủi ro
   cao. Vàng = cần kiểm chứng. Tím = Very High. Không bao giờ dùng một màu đã có
   nghĩa cho việc khác.
2. **Số phải đọc được ở khoảng cách một sải tay.** KPI chính 34px, đơn điệu
   (monospace), có quầng sáng cùng màu.
3. **Mọi thứ động phải nhanh hơn 0,5 giây.** Dashboard là công cụ làm việc, không
   phải trang giới thiệu. Animation dài hơn thế là cản trở.

---

## 1. Hệ màu

### 1.1. Biến gốc — [QUY TẮC] chép nguyên khối này

```css
:root{
  /* nền — bốn tầng, càng gần người xem càng sáng */
  --bg:#070b14;        /* nền trang, gần như đen xanh */
  --bg2:#0b1120;       /* nền vùng chìm (thanh dính, khối gập) */
  --panel:#0e1628;     /* nền thẻ chính */
  --panel2:#111c33;    /* nền thẻ nổi / ô KPI */

  /* viền */
  --border:#1c2a47;    /* viền thường */
  --border-hi:#2a3f6b; /* viền khi rê chuột / đang chọn */

  /* chữ — ba mức, dùng đúng mức chứ đừng chế thêm */
  --text:#eef3fe;      /* số và tiêu đề */
  --dim:#a8b8da;       /* nội dung thường */
  --faint:#6e80a8;     /* nhãn, chú thích, đơn vị */

  /* màu ngữ nghĩa */
  --accent:#2ee8ff;    /* xanh ngọc — màu chủ, mật độ dữ liệu, tương tác */
  --green:#2ee98a;     /* tốt / giảm / Low */
  --yellow:#ffd84f;    /* cần kiểm chứng / Medium */
  --orange:#ff9550;    /* đỉnh, giá trị cao nhất */
  --red:#ff4d6b;       /* rủi ro / tăng xấu / High */
  --purple:#b98cff;    /* Very High, mức nặng nhất */

  /* alias theo mức độ — LUÔN dùng alias, đừng gọi thẳng màu */
  --low:#2ee98a; --med:#ffd84f; --high:#ff4d6b; --vh:#b98cff;

  --mono:'Consolas','Cascadia Code',monospace;
  --sans:'Segoe UI',system-ui,sans-serif;
}
```

### 1.2. Vì sao dùng alias mức độ

`--low/--med/--high/--vh` trỏ tới cùng giá trị với `--green/--yellow/--red/--purple`,
nhưng **luôn gọi qua alias** khi thể hiện mức độ. Sau này đổi thang màu chỉ sửa
một chỗ, và đọc code biết ngay ý nghĩa.

### 1.3. Độ sáng và tương phản — [QUY TẮC]

- Nền tối, chữ sáng. **Không có chế độ sáng** — dashboard này để nhìn lâu trong
  phòng làm việc.
- Chữ trên nền: `--text` trên `--panel` cho tỉ lệ tương phản ~14:1, thừa chuẩn
  AA. `--faint` trên `--panel` ~4,6:1 — **chỉ dùng cho nhãn ≥10px**, đừng dùng cho
  nội dung cần đọc kỹ.
- Nền màu theo mật độ (bảng nhiệt) dùng alpha `0.13 → 1.0`, và **đổi màu chữ khi
  nền sáng quá**:
  ```js
  const o = v => v ? (0.13 + 0.87*Math.sqrt(v/max)) : 0;
  color: o(v) > 0.5 ? '#04121e' : 'var(--dim)'
  ```
  Căn bậc hai chứ không tuyến tính: giá trị nhỏ vẫn phân biệt được với ô rỗng.

### 1.4. Gradient — [QUY TẮC] dùng rất tiết chế

Chỉ ba chỗ, mỗi chỗ một mục đích:

```css
/* 1. Nền thẻ KPI — tạo chiều sâu, góc trên sáng hơn */
background:linear-gradient(160deg,var(--panel2),#0c1526);

/* 2. Vạch sáng trên đỉnh thẻ — "có đèn chiếu" */
background:linear-gradient(90deg,var(--cc),transparent 72%);
box-shadow:0 0 12px var(--cc);

/* 3. Quầng tròn mờ góc phải — cho ô đỡ phẳng */
background:var(--cc); opacity:.07; border-radius:50%;
```

**[TRÁNH]** gradient nhiều màu, gradient nền toàn trang, gradient trên chữ.

---

## 2. Chữ

### 2.1. Hai họ chữ, phân vai rõ — [QUY TẮC]

| Dùng cho | Font |
|---|---|
| **Mọi con số**, mã, ngày, tỉ lệ | `--mono` |
| Tiêu đề, nhãn, câu văn | `--sans` |

Số dùng monospace là quyết định quan trọng nhất về chữ: các hàng trong bảng thẳng
cột, mắt so sánh được theo chiều dọc mà không cần căn phải thủ công.

### 2.2. Thang cỡ chữ — [QUY TẮC]

Trích từ tần suất thật trong file:

| Vai trò | Cỡ | Weight | Ghi chú |
|---|---|---|---|
| KPI chính | **34px** | 700 | mono, `letter-spacing:-1px`, có `text-shadow` quầng |
| KPI phụ (ô nhỏ) | 19px | 700 | mono |
| Tiêu đề mục (h2) | 13–14px | 700 | hoa, `letter-spacing:.5px` |
| Nội dung thẻ | **11–11.5px** | 400 | cỡ dùng nhiều nhất |
| Ô bảng | 11.5px | 400 | mono nếu là số |
| Nhãn / đơn vị | **10–10.5px** | 600 | hoa, `letter-spacing:.5–.9px`, màu `--faint` |
| Chú thích nhỏ nhất | 9–9.5px | 400 | mono, chỉ cho metadata |

**[QUY TẮC]** Không dùng cỡ ngoài thang này. Cần nhấn mạnh thì đổi **màu** hoặc
**weight**, đừng chế cỡ mới.

### 2.3. Chi tiết dễ bỏ sót — [QUY TẮC]

- `line-height` nội dung: **1.5**; số lớn: **1.12** (số cao, cần chặt lại)
- Nhãn hoa luôn kèm `letter-spacing` dương (.5–.9px); **số lớn kèm âm** (-1px)
- Mẫu số trong tỉ lệ ("29/50") nhỏ và mờ hơn hẳn tử số:
  ```css
  font-size:.6em; font-weight:600; color:var(--faint); letter-spacing:0;
  ```

---

## 3. Bố cục

### 3.1. Số đo khung — [QUY TẮC]

| Thứ | Giá trị |
|---|---|
| Bề rộng tối đa nội dung | `1560px`, căn giữa |
| Đệm trang | `18px 22px` |
| Khoảng cách giữa các mục | `14px` |
| Đệm trong thẻ | `15px 17px` |
| Bo góc thẻ lớn | `12px` |
| Bo góc ô nhỏ / nút | `8px` |
| Bo góc viên thuốc (pill) | `20px` hoặc `999px` |
| Bo góc vạch / thanh | `2–4px` |

**[KHUYẾN NGHỊ]** Giữ đúng ba mức bo góc: 12 (thẻ) / 8 (ô, nút) / 20+ (pill). Bo
góc lung tung làm giao diện mất nhịp.

### 3.2. Lưới — [QUY TẮC]

```css
/* KPI hàng lớn: 6 cột đều, KHÔNG auto-fit — cần đúng 6 ô ngang */
.kpibig{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:16px}

/* KPI phụ: auto-fit, tự xuống dòng */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:9px}
```

Khác biệt có chủ ý: hàng KPI chính phải **luôn 6 ô một hàng** để so sánh ngang;
KPI phụ thì thoáng hơn.

### 3.3. Mỗi mục là một thẻ có vạch màu — [QUY TẮC]

```css
.card{background:var(--panel);border:1px solid var(--border);
      border-radius:12px;padding:15px 17px;margin-bottom:14px}
.card-head h2::before{                 /* vạch màu chủ của mục */
  content:'';position:absolute;left:0;top:1px;bottom:1px;width:3px;
  border-radius:2px;background:var(--gc,var(--accent));
  box-shadow:0 0 10px var(--gc,var(--accent));
}
```

Vạch 3px có quầng sáng cùng màu — **nhìn màu vạch là biết đang ở mục nào**, không
cần đọc tiêu đề. Đặt màu qua biến `--gc` trên thẻ.

---

## 4. Thẻ KPI

### 4.1. Cấu trúc — [QUY TẮC]

```css
.kb2{
  position:relative;
  background:linear-gradient(160deg,var(--panel2),#0c1526);
  border:1px solid var(--border);
  border-radius:12px;
  padding:17px 19px 15px;
  overflow:hidden;
  transition:border-color .16s,transform .16s,box-shadow .16s;
}
.kb2::before{                          /* vạch trái, mã màu theo ý nghĩa */
  content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--cc);
}
.kb2::after{                           /* quầng mờ góc phải, chống phẳng */
  content:'';position:absolute;right:-38px;top:-38px;width:110px;height:110px;
  border-radius:50%;background:var(--cc);opacity:.07;pointer-events:none;
}
```

### 4.2. Bốn tầng nội dung, đúng thứ tự — [QUY TẮC]

```
k   nhãn      10px hoa, --faint, letter-spacing .9px, padding-right:52px
v   số chính  34px mono 700, màu --cc, text-shadow quầng 26px
u   diễn giải 11px, --dim, line-height 1.5, ÉP ĐÚNG 2 DÒNG
tr  xu hướng  góc trên phải, 11.5px mono 700, pill nhỏ
pg  thanh đáy 3px, nền #0a1020, thanh trong màu --cc opacity .8
```

**Chi tiết quan trọng**: dòng diễn giải bị ép đúng hai dòng để **sáu ô luôn cao
bằng nhau**:

```css
.kb2 .u{
  min-height:33px;display:-webkit-box;-webkit-line-clamp:2;
  -webkit-box-orient:vertical;overflow:hidden;
}
```

Và nhãn chừa `padding-right:52px` để không đè lên pill xu hướng ở góc phải.

### 4.3. Hover — [QUY TẮC]

```css
.kb2:hover{
  border-color:color-mix(in srgb,var(--cc) 40%,var(--border-hi));
  transform:translateY(-2px);
  box-shadow:0 12px 30px rgba(0,0,0,.4),
             0 0 30px color-mix(in srgb,var(--cc) 18%,transparent);
}
```

Nhấc 2px + quầng sáng **cùng màu chủ của ô** — không dùng màu trắng chung chung.

---

## 5. Bảng

### 5.1. Nền tảng — [QUY TẮC]

```css
table{width:100%;border-collapse:collapse;font-size:11.5px}
.heat{table-layout:fixed}              /* bảng nhiều cột: PHẢI fixed */
```

`table-layout:fixed` bắt buộc khi bảng có nhiều cột ngày — không có nó, trình
duyệt tự chia theo nội dung và cột nhảy loạn mỗi lần lọc lại.

### 5.2. Số đo — [QUY TẮC]

| Thứ | Giá trị |
|---|---|
| Chiều cao hàng | **28–30px** (`padding:6px 9px`) |
| Đệm ô | `6px 9px`; ô số `0 8px` |
| Cỡ chữ | 11.5px; ô số 11px mono |
| Tiêu đề cột | 9–10px hoa, `--faint`, `letter-spacing:.04em` |
| Cột tên | 34% hoặc 320px cố định |
| Cột số | 64–96px |

### 5.3. Tiêu đề và hover — [QUY TẮC]

```css
thead th{
  border-bottom:1px solid rgba(70,110,175,.4);
  background:linear-gradient(180deg,rgba(24,40,70,.55),transparent);
}
tbody tr:hover{background:rgba(46,232,255,.05)}
tbody tr:hover td.nm{color:var(--accent)}
tbody tr:hover{box-shadow:inset 3px 0 0 var(--accent)}
```

Hover nhạt (alpha .05) vì bảng nhiệt đã có màu nền theo mật độ — hover đậm sẽ đè
mất dữ liệu.

### 5.4. Cột sắp xếp được — [QUY TẮC]

```css
th.sx{cursor:pointer;transition:color .12s}
th.sx:hover{color:var(--accent)}
th.sx::after{content:'↕';opacity:.35;margin-left:3px}
```

### 5.5. Số phải căn phải và không ngắt dòng — [QUY TẮC]

```css
td.num{
  text-align:right;
  font-variant-numeric:tabular-nums;
  white-space:nowrap;
}
td.num *{white-space:nowrap}   /* CẢ THẺ CON */
```

**[TRÁNH]** — lỗi đã mắc trong chính file này: đặt `nowrap` ở ô nhưng quên thẻ
con, số `11.362` bọc trong `<strong>` bị bẻ thành `11.36` / `2` — **đọc ra số
khác hẳn**. Luôn đặt cả `td.num *`.

---

## 6. Đánh dấu mức độ

### 6.1. Pill — [QUY TẮC]

```css
.pill{
  display:inline-block;padding:1.5px 7px;border-radius:20px;
  font-size:9.5px;font-weight:700;white-space:nowrap;
  border:1px solid color-mix(in srgb,var(--pc) 34%,transparent);
  background:color-mix(in srgb,var(--pc) 14%,transparent);
  color:var(--pc);
}
```

Công thức ba mức alpha dùng lại khắp nơi: **viền 34%, nền 14%, chữ 100%**.

### 6.2. Xu hướng — [QUY TẮC]

```
tăng xấu:  ▲ + --red      giảm tốt:  ▼ + --green      đi ngang: ≈ + --faint
```

**[QUY TẮC]** Luôn kèm ký hiệu mũi tên, không chỉ dựa vào màu — người mù màu đỏ
lục chiếm ~8% nam giới.

### 6.3. Tô sáng dòng được chỉ tới — [QUY TẮC]

```css
tr.f2-sang > td{
  box-shadow:inset 0 1.5px 0 var(--green), inset 0 -1.5px 0 var(--green);
}
tr.f2-sang > td:first-child{
  box-shadow:inset 4px 0 0 var(--green), /* vạch trái dày — thứ nhìn thấy đầu tiên */
             inset 0 1.5px 0 var(--green), inset 0 -1.5px 0 var(--green);
}
tr.f2-sang{filter:drop-shadow(0 0 4px rgba(46,233,138,.6));
           animation:f2nhay 1.6s ease-in-out 3}
```

**[TRÁNH]** — lỗi đã mắc: bản đầu tô **nền vàng đè lên cả dòng**. Các ô đó vốn
mang màu xanh theo mật độ alert, vàng đè lên thành nâu xỉn — dữ liệu vừa mờ vừa
bẩn, mà chính mật độ màu mới là thứ cần đọc.

> **Nguyên tắc rút ra: đánh dấu bằng VIỀN và QUẦNG SÁNG, không đụng vào nền ô.**
> Nền ô đã mang thông tin.

---

## 7. Nút, bộ lọc, tab

### 7.1. Nút thường — [QUY TẮC]

```css
button{
  background:var(--panel2);border:1px solid var(--border);color:var(--dim);
  font-size:11px;padding:5px 12px;border-radius:8px;cursor:pointer;
  font-family:var(--sans);transition:.13s;
}
button:hover{border-color:var(--accent);color:var(--accent)}
button.on{background:rgba(46,232,255,.12);border-color:var(--accent);color:var(--accent)}
button:disabled{opacity:.5;cursor:default}
```

### 7.2. Nút phụ / hành động lùi — [QUY TẮC]

```css
button.mo{background:none;border-color:var(--border);color:var(--faint);
          font-size:10px;padding:4px 10px}
```

### 7.3. Nút mở rộng danh sách — [QUY TẮC]

```css
.cy-more button{border:1px dashed var(--border-hi)}
.cy-more button:hover{border-style:solid;border-color:var(--accent)}
```

Viền **đứt nét** cho hành động "còn nữa" — khác hẳn nút hành động thật.

---

## 8. Biểu đồ

### 8.1. Số đo — [QUY TẮC]

| Thứ | Giá trị |
|---|---|
| Chiều cao cột | `170–200px` |
| Khe giữa cột | `2–3px` |
| Bo góc đỉnh cột | `3px 3px 0 0` |
| Đường lưới | `1px dashed rgba(110,128,168,.22)` |
| Nhãn trục | 9–9.5px mono, `--faint` |

**[KHUYẾN NGHỊ]** Chiều cao vùng vẽ ≈ **⅓ bề rộng**, tối thiểu 150px, tối đa 260px.

### 8.2. Quy ước màu — [QUY TẮC]

- Cột thường: `--accent`
- Cột cao nhất: `--orange` (một cột duy nhất được nhấn)
- Vạch trung bình: nét đứt `--orange`, mảnh 1px
- Cột hover: `filter:brightness(1.4)` — sáng lên, không đổi màu

### 8.3. Nhãn số — [QUY TẮC]

Đặt **ngay trên đỉnh cột**, không dùng trục Y có số. Trục Y chỉ còn đường lưới
mờ. Ít mực hơn, đọc nhanh hơn.

**[TRÁNH]** legend rời cho biểu đồ dưới 4 chuỗi — dán nhãn thẳng vào cột.

---

## 9. Animation

### 9.1. Danh sách đầy đủ đang dùng — [QUY TẮC]

```css
@keyframes theVao{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes modalvao{from{opacity:0;transform:translateY(14px) scale(.985)}to{opacity:1;transform:none}}
@keyframes maskvao{from{opacity:0}to{opacity:1}}
@keyframes bl{0%,100%{opacity:1}50%{opacity:.35}}
@keyframes f2nhay{0%,100%{filter:drop-shadow(0 0 4px rgba(46,233,138,.6))}
                  50%{filter:drop-shadow(0 0 9px rgba(46,233,138,1))}}
```

### 9.2. Thời lượng và nhịp — [QUY TẮC]

| Loại | Thời lượng | Easing |
|---|---|---|
| Đổi màu, viền | **.12–.13s** | mặc định |
| Biến hình (transform) | **.15–.16s** | mặc định |
| Thẻ vào trang | **.42s** | `cubic-bezier(.22,1,.36,1)` |
| Hộp thoại mở | **.22s** | `cubic-bezier(.2,.8,.3,1)` |
| Lớp phủ | **.18s** | `ease-out` |
| Nhấp chú ý | 1.6s × **3 lần rồi dừng** | `ease-in-out` |

**[QUY TẮC]** Không có animation nào vượt **0,45s**, trừ hiệu ứng nhấp chú ý —
mà cái đó cũng chỉ chạy 3 nhịp rồi đứng yên hẳn.

### 9.3. Thẻ vào trang so le — [QUY TẮC]

```css
body.vao .kb2{animation:theVao .42s cubic-bezier(.22,1,.36,1) backwards}
body.vao .kb2:nth-child(2){animation-delay:.04s}
body.vao .kb2:nth-child(3){animation-delay:.08s}
/* … mỗi ô +.04s, tới ô thứ 6 là .2s */
```

Lệch **.04s** mỗi ô. Toàn hàng vào xong trong 0,62s.

**[QUY TẮC]** Gắn hiệu ứng vào class `body.vao`, gỡ class sau khi chạy xong — để
mỗi lần vẽ lại nội dung không animation lại từ đầu.

### 9.4. Tôn trọng thiết lập hệ thống — [QUY TẮC] bắt buộc

```css
@media (prefers-reduced-motion:reduce){
  body.vao .card, body.vao .kb2, body.vao .dieuhuong{animation:none}
  tr.f2-sang{animation:none}
}
```

### 9.5. [TRÁNH]

- Animation lặp vô hạn ở nhiều chỗ (nhấp nháy liên tục gây mỏi mắt). Cả file chỉ
  có **một** chỗ lặp vô hạn: chấm trạng thái `bl 2s infinite`.
- Chuyển động trên thứ đang đọc (bảng số, nội dung văn bản).
- `transition:all` — luôn liệt kê đúng thuộc tính cần đổi.

---

## 10. Tương tác nhỏ

### 10.1. Ba trạng thái bắt buộc — [QUY TẮC]

Mọi thứ bấm được phải có: **thường → hover → đang chọn**. Thiếu trạng thái "đang
chọn" là lỗi hay gặp nhất.

### 10.2. Mở rộng / thu gọn — [QUY TẮC]

```css
.fold .cv{transition:transform .15s}       /* mũi tên ▶ */
.fold.open .cv{transform:rotate(90deg)}
```

Xoay mũi tên, **không** đổi ký tự — xoay mượt hơn và không giật khung.

### 10.3. Hàng bảng bấm được — [QUY TẮC]

```css
tr.co-the-mo{cursor:pointer}
tr.co-the-mo:hover{background:rgba(46,232,255,.07)}
```

Đặt `cursor:pointer` cho mọi thứ bấm được, kể cả hàng bảng.

### 10.4. Tooltip — [QUY TẮC]

Dùng `title=` gốc của trình duyệt cho chú thích ngắn. **Không dựng tooltip tự
chế** trừ khi cần HTML bên trong — tooltip tự chế phải xử lý tràn màn hình, bàn
phím, cảm ứng, rất dễ hỏng.

---

## 11. Đáp ứng màn hình

### 11.1. Các mốc đang dùng — [QUY TẮC]

```css
@media (max-width:1450px){ /* KPI 6 cột → 3 cột */ }
@media (max-width:1250px){ /* bảng phụ ẩn cột ít quan trọng */ }
@media (max-width:1240px){ /* hộp thoại ngày thu hẹp */ }
@media (max-width:1150px){ /* lưới 2 cột → 1 cột */ }
@media (max-width:1000px){ /* thu nhỏ đệm */ }
@media (max-width:900px) { /* thanh dính xuống dòng */ }
@media (max-width:820px) { /* bố cục dọc hoàn toàn */ }
@media (max-width:430px) { /* điện thoại: ẩn phần phụ */ }
@media print             { /* bỏ mọi animation, đổ bóng, nút */ }
```

**[KHUYẾN NGHỊ]** Bảy mốc là nhiều. Với dashboard mới nên bắt đầu bằng **ba mốc**
(1450 / 1150 / 820) rồi thêm khi thật sự thấy vỡ — mỗi mốc là một tổ hợp phải
kiểm lại bằng mắt.

### 11.2. Nguyên tắc — [QUY TẮC]

- Bảng nhiều cột: **cuộn ngang**, đừng xé chữ. `overflow-x:auto` trên khung bọc.
- Cột ngày ẩn dần từ **cũ nhất** trở đi, luôn giữ ngày mới nhất.
- KPI xuống 3 cột trước, rồi mới 2 rồi 1 — đừng nhảy thẳng 6 → 1.

### 11.3. In ra giấy — [KHUYẾN NGHỊ] đừng bỏ qua

```css
@media print{
  .card,.kb2,.mkpi .kpi{box-shadow:none;animation:none}
  .md-x,.md-nav,button{display:none}
}
```

Dashboard vận hành hay bị in ra để họp.

---

## 12. Thứ tự ưu tiên thông tin

Từ trên xuống, thứ tự này **không được đảo**:

```
1. Tiêu đề + nguồn dữ liệu + kỳ           ← biết đang xem cái gì
2. Thanh chọn ngày                        ← đổi phạm vi
3. Hàng KPI lớn (6 ô)                     ← số tổng quan
4. ĐIỀU CẦN CHÚ Ý                         ← lớp kết luận, thứ quan trọng nhất
5. Công cụ (gập lại mặc định)             ← ít dùng thì giấu
6. Các mục số liệu ③④⑤⑥                   ← bảng chi tiết
7. Ghi chép, lưu ý                        ← ngữ cảnh
```

**[QUY TẮC]** Mục "Điều cần chú ý" đặt **ngay dưới KPI**, trước mọi bảng. Đó là
lớp trả lời câu "vậy thì sao?" — để cuối trang là vô nghĩa.

**[QUY TẮC]** Công cụ ít dùng thì gập mặc định (`<div class="fold">`), đừng xoá —
người cần vẫn mở được.

---

## 13. Nhất quán giữa các tab

Bắt buộc giống nhau ở mọi trang/tab:

| Thứ | Ràng buộc |
|---|---|
| Bảng màu | dùng chung `:root`, không định nghĩa lại |
| Ý nghĩa màu | xanh ngọc = dữ liệu, đỏ = rủi ro, tím = Very High — **không đổi vai** |
| Cỡ chữ | theo thang mục 2.2 |
| Bo góc | 12 / 8 / 20 |
| Thời lượng animation | theo bảng mục 9.2 |
| Cách hiển thị số | mono, `tabular-nums`, phân cách nghìn bằng dấu chấm (vi-VN) |
| Cấu trúc thẻ | `.card` + `.card-head` + vạch màu 3px |

---

## 14. Nên / Không nên

### Nên

- Đặt vạch màu 3px cho mỗi mục — điều hướng bằng màu nhanh hơn bằng chữ
- Ép chiều cao đồng đều cho thẻ cùng hàng (`-webkit-line-clamp`)
- Số dùng monospace + `tabular-nums`
- Nhãn đơn vị/mẫu số nhỏ và mờ hơn con số chính
- Giải thích ngưỡng ngay tại chỗ (`title=` hoặc dòng `.card-sub`)
- Hover đổi **viền và độ sáng**, không đổi kích thước chữ

### Không nên

- **Tô nền đè lên ô đã mang màu dữ liệu** (mục 6.3)
- **Quên `white-space:nowrap` cho thẻ con của ô số** (mục 5.5)
- Dùng `table-layout:auto` cho bảng nhiều cột
- Animation quá 0,45s, hoặc lặp vô hạn ở nhiều chỗ
- Thêm cỡ chữ ngoài thang
- Dùng màu ngữ nghĩa cho trang trí (đỏ cho tiêu đề chẳng hạn)
- Legend rời cho biểu đồ dưới 4 chuỗi
- Trạng thái "đang chọn" trông giống hover

---

## 15. Khuôn mẫu dùng lại

### 15.1. Thẻ mục

```html
<div class="card" id="mX" style="--gc:var(--accent)">
  <div class="card-head">
    <div><h2>③ TIÊU ĐỀ MỤC</h2>
      <span class="card-sub">giải thích ngắn · ngưỡng đang dùng</span></div>
    <div class="card-tools"><!-- nút lọc --></div>
  </div>
  <!-- nội dung -->
</div>
```

### 15.2. Thẻ KPI

```html
<div class="kb2" style="--cc:var(--accent)">
  <span class="k">NHÃN</span>
  <span class="tr tr-up">▲ 12%</span>
  <div class="v">210.713</div>
  <div class="u">67 ngày · trung bình <b>3.145</b>/ngày</div>
  <div class="pg"><i style="width:64%"></i></div>
</div>
```

### 15.3. Nền theo mật độ

```js
const o = v => v ? (0.13 + 0.87*Math.sqrt(v/mx)) : 0;
const cell = v => v
  ? `<td style="background:rgba(46,232,255,${o(v).toFixed(2)});
       color:${o(v)>0.5?'#04121e':'var(--dim)'}">${v}</td>`
  : `<td style="background:#0a1020;color:#2a3f6b">·</td>`;
```

### 15.4. Chấm điểm rủi ro để xếp hạng

Khi cần chọn "vài điều đáng chú ý nhất" từ nhiều loại phát hiện khác nhau,
**đừng dùng khe cố định rồi cắt theo thứ tự viết code**. Chấm điểm chung rồi xếp:

```js
function diemRuiRo(o){
  const qm = Math.min(100, Math.log10(Math.max(1,o.quyMo))/4*100);  // thang loga
  if(o.quyMo < (o.sanQuyMo ?? 20)) return 0;   // chặn nhiễu số bé
  return Math.round(o.nghiemTrong*0.35 + o.dauHieu*0.28
                  + o.doLech*0.22 + qm*0.15);
}
ds.sort((a,b)=>b.diem-a.diem);
```

**[TRÁNH]** — lỗi đã mắc: sáu khe cố định, mỗi khe lấy cái đầu loại của nó, rồi
`slice(0,4)`. Kết quả: một mục có **1 alert của 1 khách** lọt vào vì "tập trung
100%", trong khi rủi ro thật (dồn 3 khách, tăng 1219%) không có khe nào để lọt.

Thang **loga** cho quy mô là chi tiết quan trọng: 10 với 100 khác nhau rất nhiều,
nhưng 10.000 với 20.000 thì gần như nhau về mức đáng chú ý.

### 15.5. Định dạng số Việt Nam

```js
const fmt = n => n.toLocaleString('vi');     // 210713 → "210.713"
const pc  = (a,b) => b ? a/b*100 : 0;
```

---

## 16. Khi giá trị chưa có trong file

Nếu cần một số đo mà file chưa quy định, suy theo thứ tự:

1. **Tìm thành phần gần nhất về vai trò** rồi dùng lại số của nó
2. Bám thang có sẵn: cỡ chữ mục 2.2, bo góc 12/8/20, animation .12–.16s
3. Khoảng cách: bội của **3px** (3, 6, 9, 12, 14, 18, 22)
4. Ghi rõ **[KHUYẾN NGHỊ]** trong chú thích để người sau biết đây là suy ra

---

## 17. Tự kiểm trước khi giao

Mở file bằng trình duyệt và kiểm bằng mắt — **không tin vào việc "code đúng là
giao diện đúng"**. Lỗi tô nền vàng ở mục 6.3 lọt qua vì tôi chỉ đếm "có đủ 5 dòng
được đánh dấu không", không nhìn ảnh.

Danh sách kiểm:

- [ ] Số nào bị bẻ dòng không (`11.36` / `2`)
- [ ] Thẻ cùng hàng có cao bằng nhau không
- [ ] Chữ có bị cắt (`scrollHeight > clientHeight`) không
- [ ] Bảng có tràn ngang ngoài khung không
- [ ] Hover có phản hồi ở mọi thứ bấm được không
- [ ] Thu cửa sổ xuống 1200px / 900px có vỡ không
- [ ] Console có lỗi JS không
- [ ] Màu đánh dấu có đè mất màu dữ liệu không

Cách kiểm tự động:

```js
// chữ bị cắt
[...document.querySelectorAll('.cyt,.u')]
  .filter(x => x.scrollHeight > x.clientHeight + 3);

// ô số bị bẻ dòng
[...document.querySelectorAll('td.num')]
  .filter(x => x.innerText.includes('\n'));

// bảng tràn khung
[...document.querySelectorAll('table')]
  .filter(t => t.scrollWidth > t.parentElement.clientWidth + 4);
```
