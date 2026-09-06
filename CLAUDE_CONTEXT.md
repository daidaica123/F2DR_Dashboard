# CLAUDE_CONTEXT.md — bàn giao giữa hai phiên Claude Code

> **Đọc file này TRƯỚC khi sửa bất cứ thứ gì.**
> Đây không phải tài liệu mô tả dashboard. Đây là bộ nhớ bàn giao: ghi lại
> dashboard ban đầu ra sao, đã sửa gì, **tại sao** sửa, quyết định nào đã chốt,
> và thứ gì **tuyệt đối không được làm ngược lại**.
>
> Viết ngày 06/09/2026, sau khi audit toàn bộ source. Mọi con số trong file này
> lấy từ code và dữ liệu thật, không phải trí nhớ.

---

## 0. Đọc nhanh 60 giây

| | |
|---|---|
| **Sản phẩm** | Dashboard HTML một file, theo dõi alert F2DR (Viettel Money), đọc hằng ngày lúc 9h sáng |
| **Nguồn** | `_build/_van_hanh_template.html` (3.199 dòng) — **sửa ở đây**, KHÔNG sửa `F2DR_Van_Hanh.html` |
| **Dựng** | `python _build/build_van_hanh.py` → `F2DR_Van_Hanh.html` |
| **Xem trước có chatbot** | `python _build/xem_truoc.py` → `F2DR_Van_Hanh_xemtruoc.html` (**có khoá API, đã gitignore**) |
| **Deploy** | https://f2drdashboard.streamlit.app/ — auto từ nhánh `main` |
| **Repo** | https://github.com/daidaica123/F2DR_Dashboard — **public**, chủ dự án đã chốt |
| **Chatbot** | JS trong trang, 22 hàm tri thức, gọi Gemini thẳng từ trình duyệt |

**Ba lỗi quy trình đã dính nhiều lần, đừng dính lại:**

1. Chạy `xem_truoc.py` mà **quên** `build_van_hanh.py` → sửa template xong không thấy gì đổi. **Phải chạy cả hai, đúng thứ tự.**
2. Viết nội dung có escape (`\n`, `\b`, `\d`) qua heredoc bash → escape bị nuốt, file JS chết câm. **Dùng công cụ Write/Edit cho nội dung có escape.** Đã giết chatbot 2 lần và làm hỏng 1 bộ kiểm.
3. Máy **không có Node/Deno/Bun**. Kiểm JS bằng Chrome headless. Đường dẫn phải không dấu cách (dùng `C:\Users\YOGA7~1\...`).

---

## 1. Baseline — bản deploy đầu tiên (`a5f4736`)

Template lúc đó **1.524 dòng** (nay 3.199). Bản đó đã có bộ khung tốt, không phải bản nháp:

**Đã có:**

- **KPI lớn** 6 ô: Tổng alert · Khách hàng · **Kịch bản nổ (x/y)** · Alert ngày cuối (kèm ▲▼ so hôm trước) · Tái phạm · Very High
- **⓪ Công thức tính score** — PP-D hai tầng, có thanh kéo `r`, `k`
- **① Ngưỡng impact** — 3 thanh kéo, preset, `cutByTarget` (cắt theo mục tiêu %), `autoGap` (tìm khe trống)
- **② Phân bố score** — histogram theo lượt (KH × ngày)
- **③ Alert theo ngày** — biểu đồ cột + bảng bên phải, chọn N ngày gần nhất
- **④ Theo nhóm nghiệp vụ** — bảng 7 nhóm, có cột `Kịch bản nổ x/y`
- **⑤ Ma trận kịch bản × ngày** — heatmap, ô tìm kiếm, ô "Hiện N ngày" có `−`/`+`
- **⑥ Khách hàng nhiều alert nhất** — bảng top, bấm dòng để mở chi tiết, lọc `all`/`VH`
- **⑦ Kết luận điều tra & tối ưu rule** — ô nháp lưu `localStorage`, xuất JSON
- **⑧ Lưu ý** — cảnh báo phương pháp luận
- ⓪①② gộp trong khối gập, mặc định đóng (`vh_fold` trong localStorage)

**Còn sơ khai / chưa có:**

| Thiếu | Hệ quả thực tế |
|---|---|
| Không có bộ lọc theo ngày | Sếp xem báo cáo mỗi sáng nhưng không có cách xem riêng **hôm nay** |
| Không có bảng nào sắp xếp được | Muốn biết "ngày nào nhiều khách mới nhất" phải dò mắt |
| Không có mục "điều cần chú ý" | Người xem tự phải tìm ra bất thường |
| Histogram gom cột bằng `Math.round` | Cột "80" thực chất là `[79,5 – 80,5)` — sai lệch hàng nghìn lượt |
| Xếp mức làm tròn 1 chữ số trước khi so ngưỡng | Điểm thật 79,96 bị xếp Very High |
| Ngưỡng mặc định `25 / 55 / 80` | Không khớp ngưỡng nghiệp vụ đang dùng |
| Giao diện phẳng, không có ngôn ngữ ánh sáng | — |
| Chatbot là **package Python** riêng (`chatbot/`), chạy widget Streamlit ngoài iframe | Hai con bot lệch nhau; bot deploy không đọc được thanh trượt trong dashboard |

---

## 2. Đã thay đổi những gì, và **tại sao**

### 2.1 Popup báo cáo từng ngày — thay đổi lớn nhất

**Vì sao:** Dashboard là bản tổng hợp cả kỳ, nhưng **nhịp dùng thật là hằng ngày** — data nạp 7h sáng, sếp xem 9h sáng và chỉ quan tâm hôm nay; hôm qua sếp đã xem rồi.

**Vì sao chọn popup chứ không phải tab:** tab sẽ cắt đứt mạch dóng dọc **③ → ⑤ → ⑥** (thấy ngày lạ ở ③ → xuống ⑤ xem kịch bản nào gây ra → xuống ⑥ xem khách nào). Popup phủ lên, đóng lại là mạch cũ còn nguyên.

**Thanh chọn ngày** (`.ngaybar`, hàm `renderNgayBar`) đặt ở khoảng trống trên cùng:

- `CHIP_TOI_DA = 12` chip ngày gần nhất; kỳ dài hơn thì dùng ô `<input type="date">` bên cạnh (đã kẹp `min`/`max` theo kỳ). Thiết kế để chịu được kỳ 100 ngày.
- Trạng thái chip: `.moi` = ngày mới nhất (viền ngọc + nhãn "MỚI NHẤT") · `.dt` = **đã có kết luận điều tra chốt** (✓ xanh lá) · `.nhap` = mới có nháp local (✎ vàng, viền đứt) · trống = chưa xem xét.
- **Vì sao đổi màu theo trạng thái điều tra:** chủ dự án yêu cầu — để sếp liếc là biết ngày nào đã được điều tra, ngày nào chưa.

**Nội dung popup:** 6 ô KPI của ngày → `⚑ ĐIỀU CẦN CHÚ Ý NGÀY NÀY` → `MỨC IMPACT TRONG NGÀY` (kèm dải 7 ngày) → `NHÓM NGHIỆP VỤ TRONG NGÀY` → `KỊCH BẢN NỔ TRONG NGÀY` → `KHÁCH HÀNG BỊ BẮT NHIỀU NHẤT NGÀY NÀY` → `⑦ KẾT LUẬN ĐIỀU TRA — NGÀY <dd/mm>`.

- **Không đưa ⓪①② (công cụ điểm & ngưỡng) vào popup** — chủ dự án chốt: mấy thứ đó thuộc về phân tích cả kỳ, không thuộc báo cáo một ngày.
- **⑦ có mặt trong TỪNG ngày** (không chỉ ở tổng quan) — chủ dự án yêu cầu, vì kết luận điều tra vốn gắn với một ngày cụ thể.

**Ràng buộc bắt buộc:** **chatbot phải hoạt động bình thường khi popup đang mở.** Đây là yêu cầu cứng, đã kiểm bằng `elementFromPoint` và bằng ảnh. Đừng đặt `z-index` hay `overflow` của popup đè lên panel chat.

### 2.2 Sắp xếp bằng cách bấm tên cột

**Vì sao:** chủ dự án yêu cầu bỏ nút filter ở bảng KỊCH BẢN NỔ, thay bằng bấm thẳng vào tiêu đề cột. Kèm chỉ đạo rõ: *"đừng tự động thêm sort vào mọi chỗ một cách máy móc"*.

Cơ chế dùng chung: `SX` (trạng thái) · `SX_VE` (hàm vẽ lại) · `sxMac(tid,k,d)` (mặc định) · `bamSx(tid,k)` · `thS(...)` (sinh `<th>` kèm mũi tên ↑/↓) · `sxSap(arr,tid,lay)`.

**7 bảng có sort** — và chỉ 7:

| id | Bảng | Mặc định |
|---|---|---|
| `sxNgay` | ③ theo ngày | ngày ↓ |
| `sxNhom` | ④ nhóm nghiệp vụ | alert ↓ |
| `sxMat` | ⑤ ma trận (bấm được cả **tên từng cột ngày**) | tổng ↓ |
| `sxKH` | ⑥ khách hàng | alert ↓ |
| `sxNhN` | popup — nhóm | alert ↓ |
| `sxKbN` | popup — kịch bản | alert ↓ |
| `sxKhN` | popup — khách | thứ hạng ↑ |

**Mặc định của mỗi bảng cố ý giữ đúng thứ tự nó vẫn hiện từ trước** — mở file lên không thấy gì khác lạ, sắp xếp chỉ xảy ra khi người dùng thật sự bấm.

Bấm lại cùng cột thì đảo chiều ASC ↔ DESC.

### 2.3 Quy ước điểm số — phần dễ làm sai nhất, đọc kỹ

Đây là chuỗi ba sửa đổi liên quan nhau, **đã được chủ dự án cân nhắc và chốt sau khi thảo luận riêng**.

**a) Gom cột histogram: `[a, b)` — nửa mở, đóng ở đầu dưới.**

```js
// _van_hanh_template.html : buildCur()
const s = Math.min(100, Math.max(0, Math.floor(chuanDiem(scoreKH(...)))));
```

Nhãn hiện là `[80-81)`, tooltip ghi *"điểm từ 80 đến dưới 81"*. Quy ước được ghi thẳng ở tiêu đề mục ② để người xem hiểu ngay.

**Vì sao `[a, b)` chứ không phải `(a, b]`:** vì luật xếp mức vốn đã là *"điểm < ngưỡng thì thuộc mức dưới"*. Đo trên dữ liệu thật, 7 bộ ngưỡng: `[a,b)` cho **0 lượt lệch**; `(a,b]` lệch ở 6/7 bộ (tới **2.748 lượt**); làm tròn cũng lệch 6/7. Chọn `(a,b]` là tự tạo mâu thuẫn giữa biểu đồ và bảng mức.

> ⚠️ **LƯU Ý MÂU THUẪN:** prompt bàn giao mô tả quy ước là `a < Score <= b` (tức `(a,b]`). **Code hiện tại là `[a, b)` — ngược lại.** Đây không phải lỗi: chủ dự án ban đầu yêu cầu `(a,b]`, sau đó chủ động dừng lại để thảo luận rồi **chốt đổi sang `[a, b)`** kèm ba việc đi cùng (nhãn `[80-81)`, bỏ làm tròn trước khi so ngưỡng, hiển thị cắt xuống). Nếu ai đó bảo "sửa lại thành `(a,b]`", hãy hỏi lại và nhắc con số 2.748 lượt trước khi làm.

**b) So ngưỡng bằng ĐIỂM THẬT, không làm tròn.**

```js
function chuanDiem(s){ return s; }   // KHÔNG ghim, KHÔNG làm tròn
```

**Vì sao:** trước đây mọi chỗ làm tròn 1 chữ số rồi mới so ngưỡng, nên 79,9525 thành "80,0" và ở ngưỡng 80 bị xếp Very High dù chưa tới 80. **Đo được 40 lượt dính lỗi này ở ngưỡng 80, 33 lượt ở ngưỡng 74.**

**Đã thử và đã bỏ:** có lúc tôi thêm bước ghim những giá trị cách số nguyên dưới `1e-9`, tưởng là bụi số thực. Đo lại thì **không phải bụi**: `79,999999999966` là kết quả THẬT của một kịch bản gốc 70 / trần 80 bị lặp ~75 lần. Nó thật sự chưa chạm 80. **Đừng thêm lại bước ghim đó.**

**c) Hiển thị thì CẮT XUỐNG, không làm tròn.**

```js
function catDiem(s){ return Math.floor(s * 10 + 1e-9) / 10; }
const hienDiem = s => catDiem(s).toFixed(1);
```

`79,952` hiện `79,9`, không phải `80,0`. **Vì sao:** số hiện ra không bao giờ được vượt điểm thật — hết cảnh "nhìn thấy 80 mà chưa tới 80". Epsilon `1e-9` ở đây **chỉ** để gạt bụi của phép nhân 10 (`87,3 × 10 = 872,9999999999999`), không đụng tới việc xếp mức.

**d) Ngưỡng mặc định `25 / 55 / 80` → `30 / 65 / 82`** (`build_van_hanh.py:43`), theo yêu cầu nghiệp vụ.

### 2.4 Mẫu số cho mọi số đếm kịch bản

**Vì sao:** *"ghi nổ 35kb ai biết tổng tất cả bn kịch bản đâu"*. Mọi chỗ đếm kịch bản phải ghi **x / `D.tong.kbCauHinh`** (hiện là **50** — tổng rule đã cấu hình lên F2DR, lấy từ `_build/nhom_kb.json`).

**Không dùng `D.kb.length` làm mẫu số** — nó chỉ đếm kịch bản TỪNG nổ trong kỳ (35), lấy nó thì phụ đề ⑤ ra "35/35", vô nghĩa. Đây là lỗi đã tồn tại và đã sửa.

Đã áp dụng: phụ đề ⑤ · dòng ngăn nhóm khi bật "Gom theo nhóm" (dùng `nhom.kbTong`) · cột `KB nổ` ở ③ (từng ngày + dòng TB/TỔNG) · tooltip cột biểu đồ ③ · ô KPI "Kịch bản nổ" trong popup · dòng đếm bảng KỊCH BẢN NỔ · header trang · ④ (vốn đã có).

Chênh lệch 50 − 35 = **15 rule chưa nổ lần nào cả kỳ** — nói thẳng ra ở phụ đề ⑤, vì rule không nổ có thể là **rule chết** chứ không phải rủi ro bằng 0.

**Cố ý KHÔNG thêm mẫu số ở ⑥**: cột số kịch bản ở đó là "khách này dính mấy kịch bản" — thêm `/50` chỉ là nhiễu.

Trong ô KPI, mẫu số để nhỏ (`0.6em`) và mờ (`--faint`) qua `.kpi .v .dv`; trong ô bảng dùng `.mso` (`0.86em`). Để mắt đọc tử số trước.

### 2.5 Mục ⚑ ĐIỀU CẦN CHÚ Ý (mới hoàn toàn)

`renderChuY()` ở tổng quan, `chuYNgay(j,S)` trong popup. Tự rút ra 4–6 điều: ngày cao nhất · kịch bản tăng mạnh nhất · **im lặng bất thường** (bắn đều cả kỳ rồi tắt hẳn ngày cuối — thường là hỏng luồng dữ liệu chứ không phải rủi ro giảm) · nhóm chuyển biến mạnh · **nghi lặp rule** (nhiều alert dồn vào rất ít khách) · tái phạm nặng.

**Vì sao:** người xem không nên phải tự tìm ra bất thường.

### 2.6 Rút gọn tên nhóm

`nhomNgan()` cắt tên nhóm ở dấu hai chấm đầu tiên, **chỉ khi** dạng rút gọn vẫn là duy nhất.

- `KÊNH: NẠP, RÚT, NGHIỆP VỤ HỖ TRỢ` → hiển thị **`KÊNH`**
- Tên đầy đủ vẫn giữ trong thuộc tính `title` và trong dữ liệu gốc — không mất thông tin.
- Rào chắn: nếu có hai nhóm cùng tiền tố (`X: một`, `X: hai`) thì **giữ nguyên tên dài cả hai**, tránh hai dòng trùng tên.

### 2.7 Dải 7 ngày trong MỨC IMPACT (xem mục 5, phần cần đặc biệt lưu ý)

### 2.8 Ngôn ngữ ánh sáng

Popup được thiết kế trước, tổng quan làm sau nên hai nửa từng trông như hai sản phẩm khác nhau. Đã kéo về cùng ngôn ngữ:

- `.card` có nền dốc + gờ sáng đỉnh + bóng đổ, thay vì khối màu phẳng
- Tiêu đề mỗi mục có **vạch màu chủ phát sáng**, đặt qua biến `--gc` theo id: `#fxCard` `#m2c` `#m3` `#m4` `#m5` `#m6` `#m7` `#m8` `.chuy-card`
- Số KPI tự phát sáng (`text-shadow` theo `--cc`) + vạch gradient trên đỉnh ô
- Hàng bảng sáng lên khi rê chuột — **đáng nhất ở ma trận ⑤** (35 dòng × 7 cột, không có gợi ý dòng thì rất dễ đọc nhầm sang dòng bên cạnh)
- Hiệu ứng vào trang chạy **đúng một lần**: `body.classList.add('vao')` rồi gỡ sau 1400ms — không gỡ thì mỗi lần kéo thanh trượt cả trang nháy lại

**Nguyên tắc đã chốt: KHÔNG NHẤP NHÁY.** Đây là dashboard đọc mỗi sáng. Mọi nhịp lặp ≥ **2,6 giây**. Chỉ chấm "live" ở góc phải là đập chậm.

### 2.9 Chatbot: từ hai con còn một con

**Trước:** bot JS trong file HTML (bản dùng hằng ngày) **và** bot Python `chatbot/` chạy widget Streamlit (bản deploy). Hai bản lệch thật sự — bot Python thiếu hàm phân tích cụm điểm, ngưỡng còn 25/55/80, `muc_diem()` còn làm tròn trước khi so ngưỡng, và nằm ngoài iframe nên không đọc được thanh trượt.

**Nay:** xoá hẳn `chatbot/` (13 file) và `_build/may_chu_xem_truoc.py`. `app.py` gọi `xem_truoc.ghep()` để ghép panel chat vào dashboard **ngay lúc chạy** — dùng chung đúng hàm với bản xem trước, nên hai bản **không thể lệch nhau**.

Khoá API lấy từ `st.secrets` (`GEMINI_API_KEYS` mảng, hoặc `GEMINI_API_KEY` đơn), **không bao giờ nằm trong repo**.

Chatbot cũng được làm cho sống động: robot thở (3,6s) / chớp mắt (5,4s) / ăng-ten (2,6s) / nghiêng đầu khi đang nghĩ (`f2-nghi`); thu gọn có animation co về phía nút tròn; **bong bóng thoại** thi thoảng nói một câu.

---

## 3. Business logic đã chốt

### 3.1 Công thức điểm PP-D hai tầng

```
Tầng 1 — một kịch bản nổ n lần:   eᵢ = cap − (cap − base) · r^(n−1)
Tầng 2 — dính nhiều kịch bản:     score = M + (100 − M) · k · (1 − ∏(1 − eⱼ/100))
                                   M = điểm của kịch bản nặng nhất
```

- `cap` theo Level: `Low 25 · Medium 50 · High 80 · Very High 100`
- `r = k = 0,70` mặc định
- **Trần điểm là TIỆM CẬN, KHÔNG BAO GIỜ CHẠM.** Kịch bản gốc 70 / trần 80: lặp 10 lần được **79,5965**, lặp 30 lần được **79,99968**, lặp 75 lần được **79,999999999966** — vẫn dưới 80. Muốn chạm Very High **bắt buộc phải dính nhiều kịch bản**, lặp một kịch bản mãi cũng không tới.
- Đã đo: **82,4% số lượt có điểm đúng bằng số nguyên** (64 điểm: 2.681 lượt · 12 điểm: 1.343 · 67 điểm: 1.317) vì một kịch bản nổ đúng 1 lần thì `r^0 = 1`, `e = base` chính xác. Chính vì vậy quy ước khoảng `[a,b)` vs `(a,b]` dịch chuyển hàng nghìn dòng chứ không phải chuyện thẩm mỹ.

### 3.2 Đếm alert

**Đếm bằng SỐ DÒNG, cấm `DISTINCT`.** `AlertID` không duy nhất — dùng `DISTINCT` lệch **6,7%**.

### 3.3 Đơn vị "lượt"

Một **lượt** = một (khách hàng × ngày). Kỳ hiện tại: 15.581 alert · 7.636 khách · **9.174 lượt** · 7 ngày.

- `D.picks` / `D.luotKh` / `D.luotNg` / `D.luotAl` / `D.luotNkb` = **toàn bộ 9.174 lượt**, chi tiết đầy đủ
- `D.topkh` chỉ là **top 100 cả kỳ** — đừng dùng nó để tính thống kê toàn kỳ
- Điểm chấm **theo từng ngày, không cộng dồn**

### 3.4 Tổng kịch bản

`D.tong.kbCauHinh = 50` (tổng rule đã cấu hình, từ `_build/nhom_kb.json`) — khác `D.tong.kb = 35` (số kịch bản có alert trong kỳ). 7 nhóm nghiệp vụ, mỗi nhóm có `kbTong` riêng. Nhóm `SÀN FRESO` có 4 rule và **0 alert** — vẫn hiện, làm mờ đi, để thấy nhóm nào đang im lặng hoàn toàn.

### 3.5 Ghi chép điều tra (⑦)

Hai nguồn, phân biệt rõ:

- **Chốt** — từ `_build/ghi_chep_dieu_tra.json`, nạp lúc dựng. `_khop_ngay()` nhận `2026-08-28`, `28/08/2026`, `28/08`. Chip ngày hiện ✓ xanh lá.
- **Nháp** — `localStorage`, khoá `vh_gc_<YYYY-MM-DD>`. Chip hiện ✎ vàng viền đứt. Nút xuất ra `ghi_chep_dieu_tra.json` để chuyển nháp thành chốt.

### 3.6 Dữ liệu và PII

- CSV đã ẩn danh **hai bước** — file mới **phải chạy CẢ HAI** script (`an_danh_sdt.py` rồi `an_danh_bo_sung.py`). Bước 1 bỏ lọt PII; regex số bỏ sót **họ tên người** (22,7% dòng còn PII nếu chỉ chạy bước 1).
- Chatbot chặn PII bằng **ba tầng luật** (không qua model, nên không bị thuyết phục vòng vo). Câu từ chối **phải đúng nguyên văn**:
  > `Tôi không cung cấp thông tin nhân thân của khách hàng — số điện thoại, căn cước, số tài khoản, tên hay địa chỉ.`
- Thông tin **alert** thì trả lời bình thường; chỉ chặn thông tin nhân thân.

### 3.7 Không hardcode

Dữ liệu cập nhật hằng ngày. **Không cắm cứng con số nào** (số ngày, số kịch bản, số khách). Ví dụ: "độ tập trung" lấy `Math.max(3, round(D.tong.kb * 0.2))` chứ không phải "top 5"; ô "Hiện N ngày" chạy từ 1 đến `ndMax()`.

---

## 4. UX / interaction đã chốt

### 4.1 Đang có

| Chỗ | Tương tác |
|---|---|
| Thanh chọn ngày | Bấm chip → popup ngày · ô lịch cho ngày cũ · `‹` `›` chuyển ngày trong popup |
| ⑤ ma trận | Bấm **tên cột ngày** để xếp kịch bản theo đúng ngày đó · `⊞ Gom theo nhóm` · ô tìm tên · `−`/`+` số ngày |
| ⑥ khách hàng | Bấm dòng để mở chi tiết từng ngày · `−`/`+` số dòng hiện · lọc `Tất cả` / `Very High` |
| Popup — dải 7 ngày | Bấm cột để nhảy sang ngày khác |
| Popup — khách hàng | `−`/`+` số dòng hiện |
| 7 bảng | Bấm tên cột để sort ASC ↔ DESC |
| Thanh điều hướng | Nhảy tới mục, mục đang xem có quầng sáng |
| ⓪①② | Khối gập, nhớ trạng thái trong `localStorage` |
| URL | `#ngay=YYYY-MM-DD` mở thẳng popup ngày đó · `#ngay-moi-nhat` |
| Chatbot | Bấm ra ngoài tự thu · Esc thu · bong bóng thoại bấm được để mở |

### 4.2 Đã chốt KHÔNG làm

- **Không thêm nút filter vào bảng KỊCH BẢN NỔ.** Chủ dự án đã bỏ nút filter để thay bằng sort theo tên cột. Đừng thêm lại.
- **Không thêm sort vào mọi bảng một cách máy móc.** Chỉ đạo nguyên văn: *"đừng tự động thêm sort vào mọi chỗ một cách máy móc"*. 7 bảng hiện có là kết quả rà soát từng bảng một.
- **Không đưa ⓪①② vào popup ngày** — công cụ điểm & ngưỡng thuộc phân tích cả kỳ.
- **Không cắt bớt danh sách kịch bản trong popup.** Từng hiện top rồi ghi "Còn 16 kịch bản nữa" — chủ dự án bỏ, vì cắt thì đúng cái đuôi dài mới nổi lần đầu lại bị giấu. **Đông quá thì lọc, đừng giấu.**
- **Không ghi chữ hành động** (Không làm gì / Cảnh báo VÀNG / ĐỎ / PENDING) trong MỨC IMPACT của popup — chủ dự án yêu cầu bỏ để lấy diện tích tăng chiều cao cột.
- **Không nhấp nháy.** Mọi nhịp lặp ≥ 2,6 giây.
- **Không dùng sticky `<thead>` trong popup.** Đã thử: vùng cuộn là cả popup chứ không phải riêng bảng, nên header dính đè lên dòng 2 của mọi bảng. Cũng **không** cuộn lồng (`max-height` bên trong popup).

### 4.3 Cạm bẫy CSS/JS đã dính

- Thay cả khối CSS của popup từng làm **mất `.mgrid`** → hai thẻ giãn full-width, bảng nhóm hở một mảng trống lớn.
- Hai cột dùng chung khoá sort (`Alert` và `% tổng`) → bấm một cột sáng cả hai. Phải cho mỗi cột khoá riêng, dù cùng trỏ về một accessor.
- `aMax` từng lấy `rows[0].alert` với giả định "rows đã sắp giảm dần" — sai ngay khi người dùng sort theo cột khác. Dùng `Math.max`.
- Bộ bắt "bấm ra ngoài" của chat **không được** dùng `panel.contains(e.target)`: nút gợi ý tự xoá chính mình trong `onclick` (`veGoiY([])`), đến lúc sự kiện nổi lên `document` thì `e.target` đã mồ côi → panel bị thu oan. Phải dùng `e.composedPath()`.
- `thuLai()` là bất đồng bộ (đợi 190ms) nên `mo()` **phải** `clearTimeout(hen_dong)` — không thì bấm ra ngoài rồi bấm lại nút trong 190ms là panel vừa mở đã tự đóng.
- Bong bóng thoại **phải có nền đặc**. Để bán trong suốt thì chữ chìm hẳn vào bảng số phía dưới.

---

## 5. Các thay đổi gần đây cần ĐẶC BIỆT lưu ý

### 5.1 Dải ngày trong `MỨC IMPACT TRONG NGÀY`

```js
const NM_SO = 7;
const nmTu  = Math.max(0, j - NM_SO + 1);   // j = chỉ số ngày đang xem
const nmDs  = D.ngay.slice(nmTu, j + 1);
const mxN   = Math.max(...nmDs.map(x => x.alert), 1);
```

Quy tắc đã chốt:

- **7 ngày LIÊN TIẾP tính đến ngày đang chọn.** Chọn 10/10 → hiện 04/10 … 10/10. Chọn 08/10 → hiện 02/10 … 08/10. ✔ đúng như mô tả bàn giao.
- **Ngày được chọn LUÔN là cột cuối cùng bên phải.**
- **Có data label ngay phía trên mỗi cột.** Cột cao tối đa 82% để chừa chỗ cho nhãn.
- Thang cao thấp so **trong đúng cửa sổ đang hiện**, không so với đỉnh cả kỳ — một tuần yên ả mà lấy đỉnh cả kỳ làm mốc thì bảy cột đều lùn tịt. Mức so với cả kỳ đã có ở ô KPI "So TB cả kỳ".
- Bấm cột để nhảy sang ngày khác.

> ⚠️ **KHÁC với mô tả bàn giao:** prompt ghi *"luôn hiển thị đúng 7 cột"*. Code **không** làm vậy ở **đầu kỳ**: nếu ngày đang xem chưa có đủ 6 ngày trước nó, dải hiện **đúng số ngày có thật** kèm ghi chú *"(đầu kỳ, chưa đủ 7 ngày)"*, **không đệm cột giả**. Đây là chủ ý — cột giá trị 0 giả sẽ nói dối rằng hôm đó không có alert. Nếu muốn đổi thành luôn 7 cột thì phải quyết định hiển thị gì ở cột không có dữ liệu.

Thiết kế để chịu kỳ 30 hay 100 ngày: đổi `NM_SO` là xong, phần còn lại tự co giãn (`.r{justify-content:flex-end}` + `.b{max-width:104px}` để cửa sổ ngắn vẫn dồn phải).

### 5.2 `KÊNH: NẠP, RÚT, NGHIỆP VỤ HỖ TRỢ` → `KÊNH`

Làm bằng `nhomNgan()`, **không sửa dữ liệu gốc**. Tên đầy đủ vẫn nằm trong `title` và trong `D.nhom[].ten`. ✔ đúng như mô tả bàn giao. Nếu thấy tên dài xuất hiện trong `<script>` thì đó là **đúng** — dữ liệu gốc phải giữ nguyên.

### 5.3 Quy ước cụm Score

Xem **2.3**. Nhắc lại vì đây là chỗ dễ bị sửa ngược nhất: **code là `[a, b)`**, prompt bàn giao ghi `(a, b]`. Đừng đổi nếu không có yêu cầu mới và không đọc lại lý do.

### 5.4 Deploy (mới nhất, `5d49487` + `bc73cf9`)

- `F2DR_Van_Hanh.html` trong repo là dashboard **thuần** — không chatbot, không khoá.
- `app.py` ghép chat lúc chạy qua `xem_truoc.ghep()`.
- **iframe phải cao `calc(100vh - 3.2rem)`**, không được đặt số pixel cố định. Nút chat dùng `position:fixed` mà mốc là khung nhìn của chính iframe — để `3400px` thì nút rơi xuống tận đáy 3400px.
- Chat tự phát hiện đang bị nhúng (`window.self !== window.top`) → gắn lớp `f2-nhung` → CSS nâng nút lên 82px để thoát huy hiệu Streamlit. `app.py` cũng ẩn huy hiệu, nhưng **không được dựa vào lớp đó** vì tên `data-testid` của Streamlit đổi theo phiên bản.

---

## 6. Những thứ GIỮ NGUYÊN — đừng tự ý đổi

1. **`chuanDiem()` trả về nguyên `s`.** Không thêm làm tròn, không thêm ghim epsilon. Đã đo, đã bỏ, có lý do.
2. **Gom cột bằng `Math.floor`, quy ước `[a, b)`, nhãn `[80-81)`.**
3. **Hiển thị điểm bằng `catDiem` (cắt xuống), không `toFixed` thẳng.**
4. **Ngưỡng mặc định `[30, 65, 82]`.**
5. **Mẫu số kịch bản luôn là `D.tong.kbCauHinh`**, không phải `D.kb.length`.
6. **`nhomNgan()` giữ rào chắn trùng tiền tố.** Đừng đơn giản hoá thành `split(':')[0]`.
7. **Đếm alert bằng số dòng, cấm `DISTINCT`.**
8. **Mặc định sort của 7 bảng** — đúng thứ tự vốn có, không đổi.
9. **Chatbot phải chạy được khi popup ngày đang mở.** Ràng buộc cứng.
10. **Câu từ chối PII đúng nguyên văn.**
11. **Không commit `F2DR_Van_Hanh_xemtruoc.html` và `.streamlit/secrets.toml`** — đã gitignore, đã soát sạch cả lịch sử.
12. **Popup không sticky header, không cuộn lồng.**
13. **Hiệu ứng vào trang chạy đúng một lần** (thêm rồi gỡ `body.vao`).
14. **`app.py` và `xem_truoc.py` dùng CHUNG `ghep()`.** Đừng chép lại logic ghép sang `app.py` — chép là mở đường cho hai bản lệch nhau.

---

## 7. Future Improvements — **chưa làm, đừng tự ý làm**

Ghi lại từ đợt audit, để lần sau có việc thì biết bắt đầu từ đâu.

1. **`README.md` đã lỗi thời.** Vẫn mô tả package `chatbot/` (đã xoá ở `5d49487`), vẫn ghi "26 hàm truy vấn" của bản Python. Cần viết lại theo kiến trúc mới.
2. **Bộ kiểm không nằm trong repo.** Toàn bộ 8 bộ kiểm JS (178 phép kiểm) + các bộ mới đang ở thư mục tạm của phiên làm việc trên laptop, **sẽ không có trên máy PC công ty**. Nên đưa vào `_build/kiem/` và viết một script chạy tất cả. Đây là khoảng trống lớn nhất hiện nay.
3. **Chatbot không đọc được thanh trượt khi bị nhúng?** — Không: bản JS nằm *trong* trang nên vẫn đọc được `pR`/`pK`/ngưỡng live. Điều **chưa có** là bot không tự biết người dùng vừa đổi ngưỡng để chủ động nhắc lại kết luận cũ.
4. **Khoá API vẫn đi xuống trình duyệt người xem.** Repo public + app public là quyết định đã chốt của chủ dự án. Nếu sau này cần siết: dựng proxy ngoài (Cloudflare Worker / Vercel) giữ khoá, JS gọi qua đó. Streamlit không cho mở route riêng nên không làm proxy trong app được.
5. **Dữ liệu alert nằm trong repo public.** `data/score_clean_2608_0109.csv` — SĐT đã ẩn danh đúng, nhưng cột `chi_tiet_alert` lộ ngưỡng phát hiện thật (`dk1_VTT_100tr`, `dk2_MM_thang_200tr`, `gia_tri_gd`…) cùng tên và điểm gốc của 50 kịch bản. Đã nêu rủi ro, **chủ dự án đã chốt để public**. Ghi lại để không phải bàn lại từ đầu.
6. **`CHIP_TOI_DA = 12` và `NM_SO = 7` chưa chạy thử với kỳ dài thật.** Code đã thiết kế để co giãn nhưng dữ liệu hiện chỉ có 7 ngày — chưa có dịp kiểm với 30/100 ngày thật.
7. **`.devcontainer/` còn sót** từ commit `4aa5694`, hiện không dùng.

---

## 8. Current State — dashboard đang ở đâu

**Ổn định, đã deploy, không có việc dở dang.**

- Kỳ dữ liệu: `2026-08-26 → 2026-09-01` (7 ngày) · 15.581 alert · 7.636 khách · 9.174 lượt · 35/50 kịch bản có alert
- Template 3.199 dòng, dựng ra HTML ~531 KB
- Commit mới nhất `bc73cf9`, đã đẩy lên `main`
- Lần kiểm gần nhất: **178/178** (8 bộ cũ) + 28 (mẫu số) + 8 (bấm gợi ý) — **0 lỗi, không lỗi JS**
- Đã kiểm bằng ảnh dựng thật: tổng quan · popup ngày · Streamlit local · iframe `data:` + `sandbox`

**Việc gần nhất đã làm:** thêm mẫu số `/50` cho mọi số đếm kịch bản; sửa lỗi bấm câu gợi ý làm thu panel chat; sửa huy hiệu Streamlit che nút chat; xoá bot Python và chuyển sang ghép bot JS lúc chạy.

**Trước khi sửa tiếp, đọc lại mục 6 (giữ nguyên) và mục 4.2 (chốt không làm).** Nhiều quyết định trong đó trông có vẻ như thiếu sót nhưng thực ra là kết quả của một vòng thảo luận và đo đạc — sửa "cho đúng" mà không đọc lý do là làm hỏng.

**Cách làm việc chủ dự án đã yêu cầu:**

- Trả lời bằng **tiếng Việt**.
- **Nêu đánh giá trước khi sửa**, đặc biệt với thay đổi lớn hoặc khi thấy yêu cầu có vấn đề.
- **Sửa nhỏ thì đừng kiểm quá kỹ** — dựng lại + chụp một ảnh là đủ; đừng viết bộ kiểm riêng và đừng chạy lại toàn bộ. Giữ kiểm đầy đủ cho: logic điểm/phân cụm, chatbot, và thứ nhiều chỗ dùng chung.
