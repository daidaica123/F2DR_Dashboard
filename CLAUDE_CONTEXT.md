# CLAUDE_CONTEXT.md — bàn giao tri thức giữa hai phiên Claude Code

> **Đọc file này TRƯỚC khi sửa bất cứ thứ gì.**
>
> Đây không phải tài liệu mô tả dashboard. Đây là **toàn bộ tri thức** tích luỹ
> trong quá trình phát triển trên laptop: dashboard ban đầu ra sao, đã sửa gì,
> **tại sao** sửa, quyết định nào đã chốt, cạm bẫy nào đã trả giá, và thứ gì
> **tuyệt đối không được làm ngược lại**.
>
> Phần lớn nội dung dưới đây trước nay nằm trong bộ nhớ riêng của Claude trên
> laptop (`~/.claude/projects/.../memory/`) — **không có trong repo**, nên máy
> khác sẽ không biết. Đã gộp hết vào đây.
>
> Viết 06/09/2026 sau khi audit toàn bộ source + 17 file bộ nhớ. Mọi con số lấy
> từ code và dữ liệu thật, không phải trí nhớ.

## Mục lục

1. [Đọc nhanh 60 giây](#1-đọc-nhanh-60-giây)
2. [Baseline — bản deploy đầu tiên](#2-baseline--bản-deploy-đầu-tiên-a5f4736)
3. [Đã thay đổi gì, và tại sao](#3-đã-thay-đổi-gì-và-tại-sao)
4. [Business logic đã chốt](#4-business-logic-đã-chốt)
5. [UX / interaction đã chốt](#5-ux--interaction-đã-chốt)
6. [Thay đổi gần đây cần ĐẶC BIỆT lưu ý](#6-thay-đổi-gần-đây-cần-đặc-biệt-lưu-ý)
7. [Chatbot — kiến trúc và tri thức đầy đủ](#7-chatbot--kiến-trúc-và-tri-thức-đầy-đủ)
8. [Gemini API — hạn mức, model, lỗi](#8-gemini-api--hạn-mức-model-lỗi)
9. [Quy trình & công cụ](#9-quy-trình--công-cụ)
10. [Cạm bẫy đã trả giá](#10-cạm-bẫy-đã-trả-giá)
11. [Những thứ GIỮ NGUYÊN](#11-những-thứ-giữ-nguyên--đừng-tự-ý-đổi)
12. [Future Improvements](#12-future-improvements--chưa-làm-đừng-tự-ý-làm)
12b. [**Phiên 07/09/2026** — 67 ngày, bản Cloudflare, chatbot nâng cấp](#12b-phiên-07092026--dữ-liệu-67-ngày-bản-cloudflare-chatbot-nâng-cấp)
13. [Current State](#13-current-state--dashboard-đang-ở-đâu)

---

## 1. Đọc nhanh 60 giây

| | |
|---|---|
| **Sản phẩm** | Dashboard HTML một file, theo dõi alert F2DR (Viettel Money), đọc hằng ngày lúc 9h sáng |
| **Nguồn** | `_build/_van_hanh_template.html` (3.199 dòng) — **sửa ở đây**, KHÔNG sửa `F2DR_Van_Hanh.html` |
| **Dựng** | `python _build/build_van_hanh.py` → `F2DR_Van_Hanh.html` |
| **Xem trước có chatbot** | `python _build/xem_truoc.py` → `F2DR_Van_Hanh_xemtruoc.html` (**có khoá API, đã gitignore**) |
| **Deploy** | https://f2drdashboard.streamlit.app/ — auto từ nhánh `main` |
| **Deploy 2** | https://f2dr-dashboard-pages.pages.dev — Cloudflare Pages, repo riêng, xem [§12b](#12b-phiên-07092026--dữ-liệu-67-ngày-bản-cloudflare-chatbot-nâng-cấp) |
| **Repo** | https://github.com/daidaica123/F2DR_Dashboard — **public**, chủ dự án đã chốt |
| **Chatbot** | JS chạy trong trang, **26 hàm** tri thức, lưu lịch sử qua localStorage |

> **Phiên gần nhất (07/09/2026) đổi nhiều thứ lớn: dữ liệu 67 ngày, thêm bản Cloudflare, chatbot 26 hàm + lưu lịch sử. Đọc [§12b](#12b-phiên-07092026--dữ-liệu-67-ngày-bản-cloudflare-chatbot-nâng-cấp) trước khi sửa gì liên quan.**

**Ba lỗi quy trình đã dính nhiều lần, đừng dính lại:**

1. Chạy `xem_truoc.py` mà **quên** `build_van_hanh.py` → sửa template xong không thấy gì đổi. **Phải chạy cả hai, đúng thứ tự.**
2. Viết nội dung có escape (`\n`, `\b`, `\d`) qua heredoc bash → escape bị nuốt, cả file JS chết câm. **Dùng Write/Edit cho nội dung có escape.** Đã giết chatbot 3 lần. Chi tiết ở [§9.3](#93-lỗi-heredoc--đã-tái-diễn-ba-lần).
3. Máy **không có Node/Deno/Bun**. Kiểm JS bằng Chrome headless, đường dẫn phải không dấu cách. Chi tiết ở [§9.2](#92-kiểm-js-bằng-chrome-headless).

**Cách làm việc chủ dự án đã yêu cầu:**

- Trả lời bằng **tiếng Việt**.
- **Nêu đánh giá trước khi sửa**, nhất là với thay đổi lớn hoặc khi thấy yêu cầu có vấn đề. Chủ dự án nhiều lần nói rõ: *"m phải đánh giá feedback của t trước nhé, xem có nên sửa hay ko"*.
- **Sửa nhỏ thì đừng kiểm quá kỹ** — dựng lại + chụp một ảnh là đủ. Nguyên văn: *"mấy cái sửa nhỏ này thì ko cần kiểm tra kĩ quá đâu nhé, lâu quá"*. Giữ kiểm đầy đủ cho: logic điểm/phân cụm, chatbot, và thứ nhiều chỗ dùng chung.

---

## 2. Baseline — bản deploy đầu tiên (`a5f4736`)

Template lúc đó **1.524 dòng** (nay 3.199). Bản đó đã có bộ khung tốt, không phải bản nháp:

**Đã có:**

- **KPI lớn** 6 ô: Tổng alert · Khách hàng · **Kịch bản nổ (x/y)** · Alert ngày cuối (kèm ▲▼ so hôm trước) · Tái phạm · Very High
- **⓪ Công thức tính score** — PP-D hai tầng, thanh kéo `r`, `k`
- **① Ngưỡng impact** — 3 thanh kéo, preset, `cutByTarget` (cắt theo mục tiêu %), `autoGap` (tìm khe trống)
- **② Phân bố score** — histogram theo lượt (KH × ngày)
- **③ Alert theo ngày** — biểu đồ cột + bảng bên phải, chọn N ngày gần nhất
- **④ Theo nhóm nghiệp vụ** — bảng 7 nhóm, có cột `Kịch bản nổ x/y`
- **⑤ Ma trận kịch bản × ngày** — heatmap, ô tìm kiếm, ô "Hiện N ngày" có `−`/`+`
- **⑥ Khách hàng nhiều alert nhất** — bảng top, bấm dòng mở chi tiết, lọc `all`/`VH`
- **⑦ Kết luận điều tra & tối ưu rule** — ô nháp `localStorage`, xuất JSON
- **⑧ Lưu ý** — cảnh báo phương pháp luận
- ⓪①② gộp trong khối gập, mặc định đóng (`vh_fold`)

**Còn sơ khai / chưa có:**

| Thiếu | Hệ quả thực tế |
|---|---|
| Không có bộ lọc theo ngày | Sếp xem báo cáo mỗi sáng nhưng không có cách xem riêng **hôm nay** |
| Không bảng nào sắp xếp được | Muốn biết "ngày nào nhiều khách mới nhất" phải dò mắt |
| Không có mục "điều cần chú ý" | Người xem tự phải tìm ra bất thường |
| Histogram gom cột bằng `Math.round` | Cột "80" thực chất là `[79,5 – 80,5)` — lệch hàng nghìn lượt |
| Xếp mức làm tròn 1 chữ số trước khi so ngưỡng | Điểm thật 79,96 bị xếp Very High |
| Ngưỡng mặc định `25 / 55 / 80` | Không khớp ngưỡng nghiệp vụ |
| Giao diện phẳng, chưa có ngôn ngữ ánh sáng | — |
| Chatbot là **package Python** (`chatbot/`), widget Streamlit ngoài iframe | Hai con bot lệch nhau; bot deploy không đọc được thanh trượt |

---

## 3. Đã thay đổi gì, và **tại sao**

### 3.1 Popup báo cáo từng ngày — thay đổi lớn nhất

**Vì sao:** Dashboard là bản tổng hợp cả **kỳ**, nhưng **nhịp dùng thật là hằng ngày** — data đổ 7h sáng, sếp xem 9h và chỉ quan tâm hôm nay; hôm qua sếp xem hôm qua rồi.

**Vì sao popup chứ không phải tab hay khối cố định:** tab cắt đứt mạch dóng dọc **③ → ⑤ → ⑥** (thấy ngày lạ ở ③ → xuống ⑤ xem kịch bản nào gây ra → xuống ⑥ xem khách nào). Khối cố định thì trùng nội dung với ③ và kéo dài trang. Popup phủ lên, đóng lại là tổng quan còn nguyên 100%.

**Thanh chọn ngày** (`.ngaybar`, `renderNgayBar`) đặt ở khoảng trống trên cùng:

- `CHIP_TOI_DA = 12` chip ngày gần nhất; ngày cũ hơn qua ô `<input type="date">` (đã kẹp `min`/`max` theo kỳ). Thiết kế để chịu kỳ 100 ngày.
- Trạng thái chip: `.moi` = ngày mới nhất (viền ngọc + nhãn "MỚI NHẤT") · `.dt` = **đã có kết luận điều tra chốt** (✓ xanh lá) · `.nhap` = mới có nháp local (✎ vàng, viền đứt) · trống = chưa xem xét.
- **Vì sao đổi màu theo trạng thái điều tra:** chủ dự án yêu cầu — để sếp liếc là biết ngày nào đã điều tra, ngày nào chưa.

**Nội dung popup:** 6 ô KPI của ngày → `⚑ ĐIỀU CẦN CHÚ Ý NGÀY NÀY` → `MỨC IMPACT TRONG NGÀY` (kèm dải 7 ngày) → `NHÓM NGHIỆP VỤ TRONG NGÀY` → `KỊCH BẢN NỔ TRONG NGÀY` → `KHÁCH HÀNG BỊ BẮT NHIỀU NHẤT NGÀY NÀY` → `⑦ KẾT LUẬN ĐIỀU TRA — NGÀY <dd/mm>`.

- **Không đưa ⓪①② (công cụ điểm & ngưỡng) vào popup** — đó là công cụ hiệu chỉnh làm một lần mỗi kỳ. Nhưng **giữ kết quả** phân bố 4 mức, chỉ bỏ thanh trượt: câu đầu tiên người xem hỏi là "hôm nay mấy ca nặng".
- **⑦ có mặt trong TỪNG ngày** (không chỉ ở tổng quan) — chủ dự án yêu cầu, vì kết luận điều tra vốn gắn với một ngày cụ thể.

**Số liệu popup dựng từ mảng LƯỢT** (`D.picks` / `luotKh` / `luotNg` / `luotAl` / `luotNkb`) chứ **không** từ `D.topkh`. Nhờ vậy "khách nhiều alert nhất ngày 28/08" là thật trên cả 7.636 khách — ông đứng đầu cả kỳ ở mục ⑥ có thể hôm nay im lặng.

**Ba ràng buộc BẮT BUỘC, đừng phá:**

1. **Chatbot phải dùng được khi popup đang mở.** Panel chat `z-index: 2147483000`, lớp phủ `.mask` chỉ `90` — **đừng nâng `.mask` lên**. Kiểm bằng `elementFromPoint`, đừng chỉ nhìn z-index.
2. **Mặc định là TỔNG QUAN**, không tự mở ngày nào. Ngày mới nhất chỉ được đánh dấu nổi.
3. **Ngày cũ luôn xem được** — chip mọi ngày, nút `‹` `›`, ô lịch.

**Đường tắt bookmark:** `#ngay-moi-nhat` luôn mở ngày mới nhất (file build lại hằng ngày, bookmark cũ vẫn trỏ đúng). `#ngay=YYYY-MM-DD` mở ngày cụ thể.

### 3.2 Sắp xếp bằng cách bấm tên cột

**Vì sao:** chủ dự án yêu cầu bỏ nút filter ở bảng KỊCH BẢN NỔ, thay bằng bấm thẳng vào tiêu đề cột. Kèm chỉ đạo rõ: *"đừng tự động thêm sort vào mọi chỗ một cách máy móc"*.

Cơ chế dùng chung: `SX` (trạng thái) · `SX_VE` (hàm vẽ lại) · `sxMac(tid,k,d)` (mặc định) · `bamSx(tid,k)` · `thS(...)` (sinh `<th>` kèm ↑/↓) · `sxSap(arr,tid,lay)`. Bấm lần đầu = chiều đáng chú ý trước (số: lớn→nhỏ, chữ: A→Z); bấm lại đảo chiều.

**7 bảng có sort — và chỉ 7:**

| id | Bảng | Mặc định |
|---|---|---|
| `sxNgay` | ③ theo ngày | ngày ↓ |
| `sxNhom` | ④ nhóm nghiệp vụ | alert ↓ |
| `sxMat` | ⑤ ma trận (bấm được cả **tên từng cột ngày**) | tổng ↓ |
| `sxKH` | ⑥ khách hàng | alert ↓ |
| `sxNhN` | popup — nhóm | alert ↓ |
| `sxKbN` | popup — kịch bản | alert ↓ |
| `sxKhN` | popup — khách | thứ hạng ↑ |

Bấm **tên cột ngày ở ⑤** là thủ phạm của ngày đó nhảy lên đầu — đúng mạch điều tra ③→⑤.

**Mặc định của mỗi bảng cố ý giữ đúng thứ tự nó vẫn hiện từ trước** — mở file lên không thấy gì khác lạ, sắp xếp chỉ xảy ra khi người dùng thật sự bấm.

**Cố ý KHÔNG có sort ở:** ⓪ ① (bảng điều khiển, không phải dữ liệu) · ② histogram · ⚑ điều cần chú ý (đã xếp theo mức quan trọng) · KPI · **dải 4 mức Impact** — `Low → Medium → High → Very High` là thứ tự mức độ, sắp lại là phá mất nghĩa.

### 3.3 Quy ước điểm số — phần dễ làm sai nhất, đọc kỹ

Chuỗi ba sửa đổi liên quan nhau, **chủ dự án đã cân nhắc và chốt sau khi thảo luận riêng**.

**a) Gom cột histogram: `[a, b)` — nửa mở, đóng ở đầu dưới.**

```js
// _van_hanh_template.html : buildCur()
const s = Math.min(100, Math.max(0, Math.floor(chuanDiem(scoreKH(...)))));
```

Nhãn hiện `[80-81)`, tooltip ghi *"điểm từ 80 đến dưới 81"*. Quy ước ghi thẳng ở tiêu đề mục ② để người xem hiểu ngay từ đầu.

**Vì sao `[a, b)` chứ không `(a, b]`:** vì luật xếp mức vốn đã là *"điểm < ngưỡng thì thuộc mức dưới"*, tức cũng là `[a, b)`. Đo trên dữ liệu thật, 7 bộ ngưỡng: `[a,b)` lệch **0 lượt**; `(a,b]` lệch ở 6/7 bộ (có bộ **2.748 lượt**); làm tròn cũng lệch 6/7. Chọn `(a,b]` là tự tạo mâu thuẫn giữa biểu đồ và bảng mức.

> ✅ **ĐÃ CHỐT VÀ ĐÃ XÁC NHẬN LẠI — `[a, b)` là quy ước chính thức.**
>
> Chuyện đã xảy ra, ghi lại để khỏi lặp: chủ dự án ban đầu yêu cầu `(a, b]`, sau đó chủ động dừng lại (*"dừng lại 1 chút t muốn bàn vs m nên quy ước thi như nào cho lợp hí"*), nghe số đo, rồi **chốt `[a, b)`** kèm ba việc đi cùng (nhãn `[80-81)`, bỏ làm tròn trước khi so ngưỡng, hiển thị cắt xuống).
>
> Trong yêu cầu bàn giao có nhắc lại nhầm thành `a < Score <= b` — đó là nhắc theo trí nhớ bản cũ. Chủ dự án đã **xác nhận lại ngày 06/09/2026: giữ `[a, b)`**. Code đang đúng, **không phải sửa gì**.
>
> Nếu sau này có ai bảo đổi sang `(a, b]`: đó là thay đổi làm dịch chuyển tới **2.748 lượt** và tạo mâu thuẫn giữa biểu đồ ② với bảng xếp mức. Hỏi lại cho chắc trước khi làm.

**b) So ngưỡng bằng ĐIỂM THẬT, không làm tròn.**

```js
function chuanDiem(s){ return s; }   // KHÔNG ghim, KHÔNG làm tròn
```

**Vì sao:** trước đây làm tròn 1 chữ số rồi mới so ngưỡng, nên 79,9525 thành "80,0" và ở ngưỡng 80 bị xếp Very High dù chưa tới 80. **Đo được 40 lượt dính lỗi ở ngưỡng 80, 33 lượt ở ngưỡng 74.** Ngưỡng 82 hiện tại thì 0 lượt — **may, không phải đúng**.

**Đã thử và đã bỏ:** có lúc tôi thêm bước ghim giá trị cách số nguyên dưới `1e-9`, tưởng là bụi số thực. Đo lại thì **không phải bụi**: `79,999999999966` là kết quả THẬT của kịch bản gốc 70 / trần 80 lặp ~75 lần. **Đừng thêm lại bước ghim đó.**

**c) Hiển thị thì CẮT XUỐNG, không làm tròn.**

```js
function catDiem(s){ return Math.floor(s * 10 + 1e-9) / 10; }
const hienDiem = s => catDiem(s).toFixed(1);
```

`79,952` hiện `79,9`, không phải `80,0`. **Vì sao:** số hiện ra không bao giờ được vượt điểm thật. Đây cũng là cách giải đúng cho lý do cũ của việc làm tròn ("hai dòng cùng hiện 80,0 mà khác mức") — cắt xuống thì hai dòng khác mức đã hiện hai con số khác nhau rồi.

Epsilon `1e-9` ở đây **chỉ** để gạt bụi của phép nhân 10 (`87,3 × 10 = 872,9999999999999`, không có nó sẽ hiện `87,2`), không đụng tới việc xếp mức.

**d) Ngưỡng mặc định `25 / 55 / 80` → `30 / 65 / 82`** (`build_van_hanh.py:43` **và** thuộc tính `value=` trong markup ba thanh trượt — phải sửa cả hai chỗ).

**Hệ quả số liệu sau ba thay đổi:** cột `[80-81)` từ 43 lượt còn **3**; khối gần-80 dồn về `[79-80)` (**102 lượt**). Các mức Impact ở ngưỡng 82 không đổi: Low 1.597 · Medium 3.728 · High 3.390 · Very High 459.

### 3.4 Mẫu số cho mọi số đếm kịch bản

**Vì sao:** *"ghi nổ 35kb ai biết tổng tất cả bn kịch bản đâu"*. Mọi chỗ đếm kịch bản phải ghi **x / `D.tong.kbCauHinh`** (hiện **50** — tổng rule đã cấu hình lên F2DR, lấy từ `_build/nhom_kb.json`).

**Không dùng `D.kb.length` làm mẫu số** — nó chỉ đếm kịch bản TỪNG nổ trong kỳ (35), lấy nó thì phụ đề ⑤ ra "35/35", vô nghĩa. Đây là lỗi đã tồn tại và đã sửa.

Đã áp dụng: phụ đề ⑤ · dòng ngăn nhóm khi bật "Gom theo nhóm" (dùng `nhom.kbTong`) · cột `KB nổ` ở ③ (từng ngày + dòng TB/TỔNG) · tooltip cột biểu đồ ③ · ô KPI "Kịch bản nổ" trong popup · dòng đếm bảng KỊCH BẢN NỔ · header trang · ④ (vốn đã có).

Chênh lệch 50 − 35 = **15 rule chưa nổ lần nào cả kỳ** — nói thẳng ở phụ đề ⑤, vì rule không nổ có thể là **rule chết** chứ không phải rủi ro bằng 0.

**Cố ý KHÔNG thêm mẫu số ở ⑥**: cột số kịch bản ở đó là "khách này dính mấy kịch bản" — thêm `/50` chỉ là nhiễu.

Mẫu số trong ô KPI để nhỏ (`0.6em`) và mờ (`--faint`) qua `.kpi .v .dv`; trong ô bảng dùng `.mso` (`0.86em`). Để mắt đọc tử số trước.

### 3.5 Mục ⚑ ĐIỀU CẦN CHÚ Ý (mới hoàn toàn)

`renderChuY()` ở tổng quan, `chuYNgay(j,S)` trong popup. Mọi mục khác đều là bảng số thô; **đây là lớp "so what" duy nhất**. Tự rút ra tối đa 4–6 điều:

- ngày vọt cao · kịch bản tăng mạnh nhất
- **im lặng bất thường** — bắn đều cả kỳ rồi tắt hẳn ngày cuối; thường là **hỏng luồng dữ liệu** chứ không phải rủi ro giảm
- nhóm chuyển biến mạnh
- **nghi lặp rule** — nhiều alert dồn vào rất ít khách
- tái phạm nặng

**Mọi ngưỡng so tương đối với chính kỳ đó**, không viết cứng con số nào. Trong dải ⚑ của popup ngày, **đừng kể lại con số đã nằm ở hàng KPI ngay trên** — mỗi phát hiện phải so với **các ngày còn lại trong kỳ**.

### 3.6 Những thứ đã BỎ vì trùng lặp

Nguyên tắc rà soát: **mỗi ô phải trả lời một câu hỏi mà ô khác chưa trả lời.**

- **KPI "Kịch bản nổ 35/50"** → con số đã nằm ở dòng TỔNG mục ④. Thay bằng **"Tập trung"** = bao nhiêu % alert dồn vào 20% kịch bản nặng nhất — trả lời "sửa cái gì trước thì đỡ nhất". Số kịch bản tính theo tỉ lệ `max(3, round(kb*0.2))`, không cắm cứng "top 5".
- **Cột "Tỉ trọng alert"** ở ④ → chỉ vẽ lại đúng cột "% tổng" ngay bên cạnh. Thay bằng **"Cơ cấu theo mức kịch bản"**: thanh xếp lớp Low/Medium/High/VH + số "% nặng". Trả lời câu quan trọng hơn: khối lượng này nguy hiểm hay chỉ là nhiễu. Ví dụ thật: **AML 100% nặng**, còn **THANH TOÁN 1.642 alert nhưng chỉ 11% nặng** → ứng viên tối ưu rule.
- **Cột "Đã cấu hình"** (chấm tròn) ở ④ → trùng với cột "7/9" ngay bên cạnh.

**Đã thêm:** cột **Xu hướng** ở ④ và ⑤ (`xuHuong` + `spark`) — so **nửa sau kỳ với nửa đầu**, không so ngày cuối với ngày kề, vì một ngày trồi sụt là chuyện thường.

### 3.7 Rút gọn tên nhóm

`nhomNgan()` cắt tên nhóm ở dấu hai chấm đầu tiên, **chỉ khi** dạng rút gọn vẫn là duy nhất.

- `KÊNH: NẠP, RÚT, NGHIỆP VỤ HỖ TRỢ` → hiển thị **`KÊNH`**
- Tên đầy đủ vẫn giữ trong `title` và trong `D.nhom[].ten` — **chatbot vẫn dùng tên gốc**
- Rào chắn: hai nhóm cùng tiền tố (`AML: X`, `AML: Y`) thì **giữ nguyên tên dài cả hai**
- **Không viết cứng tên nào** — tên nhóm lấy từ sheet FINAL, đổi theo dữ liệu

### 3.8 Ngôn ngữ ánh sáng

Popup được làm ánh sáng trước, tổng quan để nguyên — mở popup rồi đóng lại thấy như hai sản phẩm khác nhau. Đã kéo về cùng ngôn ngữ:

- `.card` nền dốc + gờ sáng đỉnh + bóng đổ, thay vì khối màu phẳng
- Tiêu đề mỗi mục có **vạch màu chủ phát sáng**, gán qua biến `--gc` theo id: `#fxCard` `#m2c` `#m3` `#m4` `#m5` `#m6` `#m7` `#m8` `.chuy-card`
- Số KPI tự phát sáng (`text-shadow` theo `--cc`) + vạch gradient trên đỉnh ô
- Hàng bảng sáng lên khi rê chuột — **đáng nhất ở ma trận ⑤** (35 dòng × 7 cột, không có gợi ý dòng thì rất dễ đọc nhầm sang dòng bên cạnh)
- Hiệu ứng vào trang chạy **đúng một lần**: thêm `body.vao` rồi gỡ sau 1400ms — không gỡ thì mỗi lần kéo thanh trượt cả trang nháy lại

**Nguyên tắc đã chốt: KHÔNG NHẤP NHÁY.** Đây là dashboard đọc mỗi sáng, chữ số nhấp nháy là tra tấn mắt. Ánh sáng = quầng tĩnh + chuyển động chậm khi có tương tác. Mọi nhịp lặp **≥ 2,6 giây**. Chỉ chấm "live" ở góc phải là đập chậm.

### 3.9 Chatbot: từ hai con còn một con

**Trước:** bot JS trong file HTML (bản dùng hằng ngày) **và** bot Python `chatbot/` chạy widget Streamlit (bản deploy). Hai bản lệch thật sự — bot Python thiếu hàm phân tích cụm điểm, ngưỡng còn 25/55/80, `muc_diem()` còn làm tròn trước khi so ngưỡng, và nằm ngoài iframe nên không đọc được thanh trượt.

**Nay:** xoá hẳn `chatbot/` (13 file) và `_build/may_chu_xem_truoc.py`. `app.py` gọi `xem_truoc.ghep()` để ghép panel chat vào dashboard **ngay lúc chạy** — dùng chung đúng hàm với bản xem trước, nên hai bản **không thể lệch nhau**.

Khoá API lấy từ `st.secrets` (`GEMINI_API_KEYS` mảng, hoặc `GEMINI_API_KEY` đơn), **không bao giờ nằm trong repo**.

---

## 4. Business logic đã chốt

### 4.1 Công thức điểm PP-D hai tầng

```
Tầng 1 — một kịch bản nổ n lần:   eᵢ = cap − (cap − base) · r^(n−1)
Tầng 2 — dính nhiều kịch bản:     score = M + (100 − M) · k · (1 − ∏(1 − eⱼ/100))
                                   M = điểm của kịch bản nặng nhất
```

- `cap` theo Level: `Low 25 · Medium 50 · High 80 · Very High 100`
- `r = k = 0,70` mặc định
- **Trần điểm là TIỆM CẬN, KHÔNG BAO GIỜ CHẠM.** Kịch bản gốc 70 / trần 80: lặp 10 lần → **79,5965** · 30 lần → **79,99968** · 75 lần → **79,999999999966**. Một kịch bản High lặp bao nhiêu lần cũng **không tự lên nổi 80** — muốn vượt Very High **bắt buộc phải kết hợp nhiều kịch bản**.
- Đã đo: **82,4% số lượt có điểm đúng bằng số nguyên** (64 điểm: 2.681 lượt · 12 điểm: 1.343 · 67 điểm: 1.317) vì một kịch bản nổ đúng 1 lần thì `r^0 = 1`, `e = base` chính xác. Chính vì vậy chọn mép nào đóng (`[a,b)` hay `(a,b]`) **dịch chuyển hàng nghìn lượt**, không phải chuyện thẩm mỹ.

### 4.2 ⚠️ Hai giá trị r,k trong dự án — KHÔNG khớp nhau

- `_build/clean_2608_0109.py` dùng **`R0 = K0 = 0.5`** → ghi ra cột `last_risk_score` và `Level` trong CSV
- `_build/build_van_hanh.py` dùng **`R0 = K0 = 0.7`** → dashboard tính lại điểm ngay trên trình duyệt

Ngưỡng r,k được chỉnh **sau khi** script clean đã chạy. Dashboard không đọc hai cột đó nên không mâu thuẫn trong thực tế, nhưng **ai mở CSV ra đối chiếu sẽ thấy lệch**.

**Quy tắc:** chatbot và mọi công cụ mới phải **tính lại điểm bằng công thức PP-D 2 tầng** với r,k hiện hành. **Tuyệt đối không đọc `last_risk_score` hay `Level` từ CSV.**

### 4.3 ⚠️ Đếm alert bằng SỐ DÒNG, cấm `DISTINCT`

Trong `data/score_clean_*.csv` **không có tổ hợp cột nào là khoá duy nhất**. Đo trên kỳ 26/08–01/09/2026 (15.581 dòng):

| Cách gom | Số nhóm |
|---|---|
| `AlertID` | 14.533 (còn trùng) |
| `AlertID` + `usecase_clean` | 15.264 (còn trùng) |
| `object_value` + `ngay_alert` + `usecase_clean` | 9.937 (còn trùng) |

**Vì sao:** `AlertID = PARTITION_DATE + "_" + request_id`, và với kịch bản Blacklist thì `request_id` chính là `object_value`. Một khách có thể bị cùng một kịch bản bắn nhiều lần trong cùng ngày — mỗi lần là một giao dịch khác. **Trùng là bản chất dữ liệu, không phải lỗi.**

**Dùng `DISTINCT` ra 14.533 thay vì 15.581 — lệch 6,7% mà trông vẫn hợp lý nên không ai phát hiện.**

### 4.4 Đơn vị "lượt"

Một **lượt** = một (khách hàng × ngày). Kỳ hiện tại: 15.581 alert · 7.636 khách · **9.174 lượt** · 7 ngày.

- `D.picks` / `D.luotKh` / `D.luotNg` / `D.luotAl` / `D.luotNkb` = **toàn bộ 9.174 lượt**, chi tiết đầy đủ
- `D.topkh` chỉ là **top 100 cả kỳ** — đừng dùng để tính thống kê toàn kỳ
- Điểm chấm **theo từng ngày, không cộng dồn**

### 4.5 Tổng kịch bản và nhóm nghiệp vụ

`D.tong.kbCauHinh = 50` (tổng rule đã cấu hình, từ `_build/nhom_kb.json`) — khác `D.tong.kb = 35` (số kịch bản có alert trong kỳ).

| Nhóm | Rule cấu hình | Có alert |
|---|---|---|
| THUÊ BAO | 9 | 7 |
| AML | 8 | 8 |
| VAY | 12 | 9 |
| THANH TOÁN | 7 | 5 |
| CHUYỂN/NHẬN TIỀN | 2 | 2 |
| KÊNH: NẠP, RÚT, NGHIỆP VỤ HỖ TRỢ | 8 | 4 |
| SÀN FRESO | 4 | **0** |

Nhóm **0 alert vẫn hiện, làm mờ đi** — để thấy ngay nhóm nào đang im lặng hoàn toàn, cần kiểm tra xem kịch bản có chạy không.

### 4.6 Dữ liệu cập nhật HẰNG NGÀY — không hardcode

File CSV trong `data/` được cập nhật hằng ngày, không cố định. Mọi con số, danh sách kịch bản, dải ngày, tên nhóm đều có thể đổi giữa các lần nạp.

- **Không hardcode bất kỳ con số nào** (15.581 alert, 35 kịch bản, 7 ngày…) vào code hay prompt
- Cẩn thận `@st.cache_data`: **phải cho file mtime vào khoá cache**, không thì app phục vụ dữ liệu cũ sau khi nạp file mới
- Kỳ dữ liệu có thể dài ra (>7 ngày) → hàm so sánh MoM/WoW dần dùng được, nhưng phải kiểm đủ ngày trước khi tính

**Đã kiểm chứng 06/09/2026 — bản HTML tự thích ứng, không cần dạy lại.** Cách kiểm: chèn thêm một ngày, một kịch bản chưa từng có và một nhóm mới vào biến `D` ngay lúc chạy, rồi hỏi lại. Kết quả **9/9**: số ngày, tổng alert, danh sách kịch bản, `top_kich_ban`, và **bảng kiến thức gửi cho model** (`moTaKy`) đều đổi ngay lập tức. Lý do: `duLieu()` đọc thẳng biến `D` mỗi lần gọi, không cache.

→ Quy trình khi có dữ liệu mới chỉ là: **dựng lại dashboard → chạy `xem_truoc.py`**. Không sửa prompt, không huấn luyện.

### 4.7 Ghi chép điều tra (⑦) — hai nguồn, cố ý khác độ tin cậy

- **CHỐT** — `_build/ghi_chep_dieu_tra.json`, build nhúng vào file, ai mở cũng thấy → chip **✓ xanh lá**. `_khop_ngay()` nhận `2026-08-28`, `28/08/2026`, `28/08` rồi ghi trường `_ngay`.
- **NHÁP** — gõ trong popup, `localStorage` khoá `vh_gc_<YYYY-MM-DD>` → chip **✎ vàng nét đứt**. Có nút xuất JSON đúng định dạng để dán vào file rồi build lại.

### 4.8 ⚠️ Ẩn danh dữ liệu — PHẢI chạy CẢ HAI script

```bash
py -3.13 _build/an_danh_sdt.py     <file.csv> --out data/<file.csv>
py -3.13 _build/an_danh_bo_sung.py data/<file.csv>
```

**Vì sao bước 2 tồn tại:** `an_danh_sdt.py` chỉ bắt số điện thoại dạng `0[35789]xxxxxxxx` bằng regex. Ngày 05/09/2026 phát hiện nó **bỏ lọt** trong `chi_tiet_alert`: **1.569 số điện thoại dạng `84xxxxxxxxx`, 321 số CCCD, 137 số giấy tờ tuỳ thân** — tất cả đang nằm trong repo GitHub public. `an_danh_bo_sung.py` quét theo **tên khoá JSON** (14 khoá) thay vì theo dạng số.

**Bài học lớn hơn — quét theo dạng SỐ là không đủ.** Cùng ngày, một đánh giá độc lập tìm ra **3.530 dòng (22,7%) vẫn còn họ tên thật, ngày sinh, và cả tên nhân viên Viettel**. Regex số chỉ thấy cái nó được viết để tìm.

**Ẩn danh phải quét hai chiều:**
1. Theo **tên khoá** — danh sách khoá đã biết là định danh
2. Theo **giá trị** — regex bắt tên người `^[A-ZÀ-Ỹ][a-zà-ỹ]*(\s+[A-ZÀ-Ỹ][a-zà-ỹ]*){1,5}$`, ngày sinh — để bắt cả khoá mới chưa biết

`an_danh_bo_sung.py` làm cả hai và **dừng hẳn** nếu phát hiện trường nghi ngờ chưa xử lý.

**Hai quy tắc phụ:**
- Giá trị đã là hash 20 ký tự hex hoặc `enc:...` thì **giữ nguyên, không băm chồng** — băm lại làm mất liên kết với các kỳ trước.
- Luôn có **danh sách loại trừ** cho tên sản phẩm/trạng thái (`process_name`, `trang_thai`, `ten_goi`) — băm nhầm chúng là mất ý nghĩa nghiệp vụ.

Salt sinh ngày 05/09/2026 nằm ở **password manager của chủ dự án**, không có trong repo.

---

## 5. UX / interaction đã chốt

### 5.1 Đang có

| Chỗ | Tương tác |
|---|---|
| Thanh chọn ngày | Bấm chip → popup ngày · ô lịch cho ngày cũ · `‹` `›` chuyển ngày trong popup |
| ⑤ ma trận | Bấm **tên cột ngày** để xếp kịch bản theo ngày đó · `⊞ Gom theo nhóm` · ô tìm tên · `−`/`+` số ngày |
| ⑥ khách hàng | Bấm dòng mở chi tiết từng ngày · `−`/`+` số dòng · lọc `Tất cả` / `Very High` |
| Popup — dải 7 ngày | Bấm cột để nhảy sang ngày khác |
| Popup — khách hàng | `−`/`+` số dòng hiện |
| 7 bảng | Bấm tên cột để sort ASC ↔ DESC |
| Thanh điều hướng | Nhảy tới mục, mục đang xem có quầng sáng |
| ⓪①② | Khối gập, nhớ trạng thái trong `localStorage` |
| URL | `#ngay=YYYY-MM-DD` · `#ngay-moi-nhat` |
| Chatbot | Bấm ra ngoài tự thu · `Esc` thu · bong bóng thoại bấm được để mở · nút tham chiếu trong câu trả lời |

### 5.2 Đã chốt KHÔNG làm

- **Không thêm nút filter vào bảng KỊCH BẢN NỔ.** Chủ dự án đã bỏ nút filter để thay bằng sort theo tên cột. Đừng thêm lại.
- **Không thêm sort vào mọi bảng một cách máy móc.** Nguyên văn: *"đừng tự động thêm sort vào mọi chỗ một cách máy móc"*. 7 bảng hiện có là kết quả rà soát từng bảng một; danh sách "cố ý không có sort" ở [§3.2](#32-sắp-xếp-bằng-cách-bấm-tên-cột).
- **Không đưa ⓪①② vào popup ngày.**
- **Không cắt bớt danh sách kịch bản trong popup.** Từng hiện top rồi ghi "Còn 16 kịch bản nữa" — chủ dự án bỏ, vì cắt thì đúng cái đuôi dài mới nổi lần đầu lại bị giấu. **Đông quá thì lọc, đừng giấu.** Cột `#` giữ **thứ hạng gốc** trong ngày; lọc bớt dòng vẫn không đánh số lại.
- **Không ghi chữ hành động** (Không làm gì / Cảnh báo VÀNG / ĐỎ / PENDING) trong MỨC IMPACT của popup — chủ dự án yêu cầu bỏ để lấy diện tích tăng chiều cao cột.
- **Không nhấp nháy.** Mọi nhịp lặp ≥ 2,6 giây.
- **Không dùng sticky `<thead>` trong popup, không cuộn lồng.** Chi tiết ở [§10.2](#102-cạm-bẫy-trong-popup).

### 5.3 Bảng khách trong popup — quy ước riêng

**Mỗi kịch bản một dòng**, ô của khách gộp dọc bằng `rowspan` (cùng thủ pháp với phần xổ xuống của ⑥). Nhờ tách dòng mới nhét được Level KB + Score KB của **từng** kịch bản.

**Phép tự kiểm:** cột "Lần" cộng lại **phải** bằng cột "Alert" của khách. Đã có trong bộ kiểm tự động.

---

## 6. Thay đổi gần đây cần ĐẶC BIỆT lưu ý

### 6.1 Dải ngày trong `MỨC IMPACT TRONG NGÀY`

```js
const NM_SO = 7;
const nmTu  = Math.max(0, j - NM_SO + 1);   // j = chỉ số ngày đang xem
const nmDs  = D.ngay.slice(nmTu, j + 1);
const mxN   = Math.max(...nmDs.map(x => x.alert), 1);
```

Quy tắc đã chốt:

- **7 ngày LIÊN TIẾP tính đến ngày đang chọn.** Chọn 10/10 → 04/10 … 10/10. Chọn 08/10 → 02/10 … 08/10. ✔ đúng như mô tả bàn giao.
- **Ngày được chọn LUÔN là cột cuối cùng bên phải.**
- **Có data label ngay phía trên mỗi cột.** Cột trần **82%** chiều cao vùng vẽ, 18% còn lại dành cho nhãn số.
- Thang cao thấp so **trong đúng cửa sổ đang hiện**, không so đỉnh cả kỳ — một tuần yên ả mà lấy đỉnh cả kỳ làm mốc thì bảy cột đều lùn tịt. Mức so cả kỳ đã có ở ô KPI "So TB cả kỳ".
- Bấm cột để nhảy sang ngày khác.

**Vì sao có tính năng này:** bản đầu vẽ **toàn bộ** `D.ngay`. Kỳ 7 ngày trông đúng nên không lộ, nhưng đổ thêm dữ liệu thành 30 hay 100 ngày là thành 100 sợi tăm.

> ⚠️ **KHÁC với mô tả bàn giao:** prompt ghi *"luôn hiển thị đúng 7 cột"*. Code **không** làm vậy ở **đầu kỳ**: nếu ngày đang xem chưa có đủ 6 ngày trước nó, dải hiện **đúng số ngày có thật** kèm ghi chú *"(đầu kỳ, chưa đủ 7 ngày)"*, **không đệm cột giả**.
> Đây là chủ ý — cột giá trị 0 giả sẽ nói dối rằng hôm đó không có alert. Dải **dồn về phải** (`.r{justify-content:flex-end}`) + `max-width:104px` mỗi cột, nên chỗ trống bên trái tự nói lên "những ngày đó chưa có".

Muốn đổi sang 30/100 ngày: đổi `NM_SO`, phần còn lại tự co giãn.

### 6.2 `KÊNH: NẠP, RÚT, NGHIỆP VỤ HỖ TRỢ` → `KÊNH`

Làm bằng `nhomNgan()`, **không sửa dữ liệu gốc**. ✔ đúng như mô tả bàn giao. Nếu thấy tên dài xuất hiện trong `<script>` thì đó là **đúng** — dữ liệu gốc phải giữ nguyên để chatbot dùng.

### 6.3 Quy ước cụm Score — `[a, b)`, đã xác nhận lại

Cụm `80–81` nghĩa là **`80 ≤ điểm < 81`**. Nhãn cột ghi thẳng `[80-81)`.

Chủ dự án đã xác nhận lại quy ước này ngày 06/09/2026. **Code đang đúng, không phải sửa.** Lý do đầy đủ và số đo ở [§3.3](#33-quy-ước-điểm-số--phần-dễ-làm-sai-nhất-đọc-kỹ) — đọc trước nếu định đụng vào.

### 6.4 Deploy (`5d49487` + `bc73cf9`)

- `F2DR_Van_Hanh.html` trong repo là dashboard **thuần** — không chatbot, không khoá.
- `app.py` ghép chat lúc chạy qua `xem_truoc.ghep()`.
- **iframe phải cao `calc(100vh - 3.2rem)`**, không được đặt số pixel cố định. Nút chat dùng `position:fixed` mà mốc là khung nhìn của **chính iframe** — để `3400px` thì nút rơi xuống tận đáy 3400px.
- Chat tự phát hiện đang bị nhúng (`window.self !== window.top`) → gắn lớp `f2-nhung` → CSS nâng nút lên 82px để thoát huy hiệu Streamlit. `app.py` cũng ẩn huy hiệu, nhưng **không được dựa vào lớp đó** vì tên `data-testid` của Streamlit đổi theo phiên bản.
- Đã đo trong iframe `data:text/html;base64` + `sandbox="allow-scripts allow-same-origin"`: panel mở được, `F2BoNao`/`F2TriThuc`/`D` đều nạp, khoá tới nơi. Origin là opaque (`null`) giống hệt khi mở bằng `file://` nên fetch sang Gemini vẫn qua CORS. `localStorage` ném lỗi ở origin opaque — chỗ dùng đã có `try/catch` sẵn.

---

## 7. Chatbot — kiến trúc và tri thức đầy đủ

### 7.1 Kiến trúc (plan đã duyệt 05/09/2026)

```
User → Intent Router → Data/Web/Hybrid → Validation → LLM → Answer
```

**Ba quyết định cốt lõi, đừng đảo:**

1. **Hàm đóng sẵn, KHÔNG cho LLM sinh SQL.** LLM chỉ chọn tên hàm + tham số. Tránh việc LLM âm thầm viết truy vấn sai mà kết quả trông vẫn hợp lý.
2. **Đối chiếu từng con số bằng regex.** Mọi số trong câu trả lời phải truy được về bảng dữ kiện; không khớp thì không trả ra.
3. **Router hai lớp: luật trước, LLM sau.** ~70% câu hỏi bắt bằng luật, không tốn lượt gọi API.

Không dùng RAG/vector DB (dữ liệu ~7MB, đủ nhanh). Ưu tiên số 1 của chủ dự án là **độ chính xác**, sau đó mới tới tốc độ.

### 7.2 Bốn file, mỗi file một việc

```
_build/_chat_ui.html      ← NGUỒN THIẾT KẾ DUY NHẤT (CSS + markup panel)
_build/_chat_tri_thuc.js  ← 22 hàm truy vấn, đọc thẳng biến D của dashboard
_build/_chat_bo_nao.js    ← vòng lặp suy luận, chặn PII, kiểm chứng số, gọi LLM
_build/_chat_ui.js        ← chỉ vẽ
        │
        └─ xem_truoc.ghep()  → bản xem trước (có khoá) VÀ bản deploy (khoá từ Secrets)
```

**Thứ tự nạp QUAN TRỌNG: tri thức → bộ não → giao diện.** Giao diện gọi bộ não, bộ não gọi tri thức, tri thức đọc biến `D`. Nạp sai thứ tự là `undefined`.

Sửa giao diện → `_chat_ui.html`; sửa cách nghĩ → `_chat_bo_nao.js`; sửa truy vấn → `_chat_tri_thuc.js`. Rồi chạy `xem_truoc.py`.

### 7.3 22 hàm tri thức

`alert_theo_ngay` · `chi_tiet_kich_ban` · `ghi_chep_dieu_tra` · **`hanh_vi_theo_cum_diem`** · `ho_so_khach` · `khach_nhieu_kich_ban` · `khach_tai_pham` · `kich_ban_ban_day` · `kich_ban_dot_bien` · `kich_ban_im_lang` · `kich_ban_im_lang_trong_ngay` · `ma_tran_kich_ban_ngay` · `ngay_bat_thuong` · `nhom_im_lang` · `nhom_theo_ngay` · `so_sanh_ngay` · `thong_ke_nhom` · `tim_khach` · `tong_quan` · `top_khach_hang` · `top_kich_ban` · `xu_huong_kich_ban`

### 7.4 Các lớp trả lời KHÔNG cần model (0 lượt gọi API)

| Lớp | Ví dụ | Hàm |
|---|---|---|
| Xã giao | "hello", "cảm ơn", "ê", "ok", "bye" | `xaGiao()` |
| Hỏi về bot | "m là ai", "làm được gì" | `RX_HOI_VE_BOT` → `GIOI_THIEU` |
| Phép tính | "1+1 bằng mấy", "(5+3)*2" | `tinhBieuThuc()` |
| Chặn PII | "cho tôi sđt khách" | `kiemCauHoi()` |

**Vì sao xã giao phải tách khỏi hỏi-về-bot:** trước đây `RX_HOI_VE_BOT` gộp cả "hello", nên chào một tiếng là bị dội lại bản giới thiệu 5 gạch đầu dòng. Chủ dự án phàn nàn đúng: *"t chào chat bot thì chat bot chào lại ấy, chứ đừng nêu ra 1 đống dữ liệu, chưa ai hỏi j mà"*. Xã giao chỉ nhận câu **≤ 6 từ**, để "chào bạn, kịch bản nào nhiều alert nhất?" vẫn là câu hỏi thật.

**Vì sao phép tính phải tự tính:** để model tính rồi đi qua lớp kiểm chứng số thì kết quả không truy được về dữ liệu → bị kết luận là bịa. Tự phân tích biểu thức (**không dùng `eval`**, chuỗi do người dùng gõ) rồi trả thẳng.

### 7.5 Hành động trong vòng lặp suy luận (`promptKeHoach`)

- **`tra_thuong`** — câu chung vô hại (thủ đô nước Pháp). Trả lời ≤ 2 câu, bỏ qua lớp kiểm chứng số, prompt cấm nêu số liệu F2DR. Trước đây từ chối thẳng thừng, rất ngớ ngẩn.
- **`hoi_lai`** — câu thiếu dữ kiện ("so sánh hai ngày"). Bot hỏi ngược kèm `lua_chon`, đi qua `GOI_Y` nên giao diện vẽ thành chip bấm được.
- **`ngoai_chu_de`** — giờ chỉ dành cho việc nhờ làm hộ / dụ lách quy tắc.

**Nút tham chiếu trong câu trả lời** (`noiThamChieu` ở `_chat_ui.js`): quét câu trả lời, tên nào **có thật trong `D`** thì bọc thành `button.f2-ref`. **Phải dùng HÀNG ĐỢI** chứ không duyệt một lượt — cắt xong còn phần đuôi, trong đuôi vẫn còn tên khác. Nhận cả `2026-09-01` lẫn `01/09` vì model viết cả hai kiểu.

**Khi bí thì đừng bỏ giữa đường** (`khongLayDuoc`): nêu đã thử gì, vướng ở đâu, rồi chỉ ra thứ có thật trong kỳ để đi tiếp. Gợi ý lấy từ `D` chứ **không viết cứng** — kỳ sau đổi kịch bản thì gợi ý cũ trỏ vào thứ không còn tồn tại.

### 7.6 Chặn thông tin nhân thân — ràng buộc cứng

Ba tầng luật, **chạy bằng luật chứ không qua model**, nên không thể bị thuyết phục hay đánh lừa bằng cách diễn đạt vòng vo.

Yêu cầu nguyên văn của chủ dự án: *"chặn mọi prompt có ý đồ khai thác thông tin sđt hay thông tin khách hàng nhé, còn thông tin alert thì k sao, chứ tt nhân thân nhạy cảm là ko đc, đừng để nó đánh lừa chat bot"*.

Câu từ chối **phải đúng nguyên văn**:

> `Tôi không cung cấp thông tin nhân thân của khách hàng — số điện thoại, căn cước, số tài khoản, tên hay địa chỉ.`

Thông tin **alert** thì trả lời bình thường; chỉ chặn thông tin nhân thân.

### 7.7 Lớp chống bịa số — đo được bao nhiêu, đánh đổi ở đâu

Mọi con số trong câu trả lời phải truy được về dữ kiện (`kiemSo`, `soTrongDuKien` trong `_chat_bo_nao.js`). Số đo 06/09/2026:

| | trước khi cho phép phép trừ | sau |
|---|---|---|
| số LỚN bịa (100–20.000) lọt | 0,0% | **0,0%** |
| số NHỎ bịa (2–100) lọt | 50,8% | 57,0% |
| số thật qua được | 4/4 | 4/4 |
| phép trừ suy ra qua được | 0/7 | **7/7** |

**Vì sao cho phép phép trừ:** bot trả lời "nhóm VAY có 9/12 kịch bản có alert, còn **3** kịch bản chưa có" — số 3 đúng nhưng không nằm nguyên văn trong dữ kiện nên bị kết luận là bịa, rồi **vứt cả câu trả lời để đổ JSON thô ra màn hình**. Hình phạt nặng hơn lỗi rất nhiều.

**Chỉ trừ trong CÙNG một bản ghi** (`dsGhep`), không ghép mọi số nhỏ với nhau: ghép tự do thì **94% số nhỏ bịa cũng lọt**.

**Hình phạt phải tương xứng:** viết lại một lần; nếu vẫn còn ≤ 2 con số và đều **nhỏ hơn 100** thì GIỮ câu trả lời và ghi chú rõ số nào chưa truy được. Chỉ đổ bảng số thô khi có số ≥ 100 hoặc quá 2 số — **số bịa nguy hiểm là số lớn** (alert, khách), không phải phép đếm lặt vặt.

**Điểm yếu còn lại, biết mà chấp nhận:** số nhỏ bịa lọt ~57%, số thập phân bịa lọt ~38%. Nguyên nhân: tập dữ kiện vốn chứa sẵn nhiều số nguyên nhỏ (điểm gốc, ngưỡng, số kịch bản) và phần mở rộng tỉ lệ sinh ra nhiều số một chữ số thập phân. Muốn siết phải kiểm theo **ngữ nghĩa từng mệnh đề** chứ không chỉ đối chiếu tập số — việc lớn, chưa làm.

### 7.8 Phân tích hành vi theo CỤM ĐIỂM và ba cái bẫy đã trả giá

Chủ dự án hỏi "khách 80–82 điểm thì gồm hành vi gì", bot trả lời về **điểm gốc của KỊCH BẢN** — sai hẳn đối tượng. Nguyên nhân: trong 21 hàm tri thức **không có hàm nào nhận khoảng điểm của khách**, nên model vơ lấy thứ "điểm" duy nhất nó nhìn thấy rồi trả lời trôi chảy về sai chuyện. **Đây là kiểu hỏng tệ nhất: sai mà nghe rất chắc.**

Đã thêm `hanh_vi_theo_cum_diem({tu, den} | {muc}, ngay)` — tính thẳng trên **toàn bộ 9.174 lượt** (`D.picks`), không phải `D.topkh`. Trả về: cách hình thành (1 kịch bản / kết hợp 2 / kết hợp 3+), tổ hợp phổ biến, và **kịch bản đặc trưng** = dày hơn mặt bằng toàn kỳ bao nhiêu lần (chứ không phải kịch bản đông nhất — đông nhất chỉ phản ánh kịch bản to).

**Lỗ hổng đi kèm đã vá:** bot trước đây đọc `d.r` / `d.k` / `d.nguong` — giá trị **chốt lúc build** — và còn nói với model là "CỐ ĐỊNH". Người dùng kéo thanh trượt sang 82 rồi hỏi "ai Very High", bot trả lời theo 80 mà không ai biết. Giờ `thamSoDiem()` đọc `pR/pK/tLM/tMH/tHV` **đang đặt trên trang**, tự lùi về giá trị build khi không có thanh trượt.

**Trả lời câu "đổi ngưỡng thì bot có tự học không":** nó **không học, nó tính lại** mỗi lần hỏi — nên không có gì để cũ đi. Kiểm thật: kéo Very High 82 → 90 thì số lượt trong cụm tự đổi **459 → 9**.

**Ba cái bẫy đã trả giá:**

**① Biểu đồ ② GOM CỘT SAI, không chỉ gắn nhãn sai.** `buildCur()` dùng `Math.round` nên 79,9 điểm rơi vào cột 80 — cột "80" hoá ra chứa 79,5–80,4. Người dùng đọc cột 80+81 ra **68 lượt**, bot đếm đúng khoảng ra **43**.

Lần đầu tôi sửa bằng cách **đổi nhãn cho đúng với quy ước sai** ("Làm tròn về 80 điểm, điểm thật 79,5–80,5"). Chủ dự án bác lại: *"sao 79.9 điểm lại thuộc cột 80-81 nó phải thuộc cột 79-80 chứ"*. Đúng — **sửa gốc, đừng dán nhãn giải thích cho cái sai**.

Vá này còn chặn một lỗi tiềm ẩn: `bandCount()` xếp mức trên **chỉ số cột**, nên với cách làm tròn cũ, ở ngưỡng 80 thì **27 lượt điểm 79,5–79,9 bị đếm thành Very High**.

**② Cảnh báo suy từ HAI ĐẦU KHOẢNG chứ không từ dữ liệu.** Bản đầu so `tu`/`den` với vạch ngưỡng rồi kết luận "nửa trên là Very High" — trong khi điểm cao nhất thật chỉ 80,6, **không lượt nào chạm tới**. Đúng về số học, sai về dữ liệu. **Mọi cảnh báo phải đếm trên bản ghi có thật.**

**③ Bội số lớn trên nền vài lượt bị đọc thành "đặc điểm chính".** Một kịch bản 3/43 lượt nhưng dày gấp **160×** mặt bằng leo lên đầu danh sách "đặc trưng", model biến nó thành câu mở đầu "đặc điểm chính là tần suất giao dịch cao" — trong khi chỉ **19%** số lượt liên quan tần suất. Đã nâng sàn "đặc trưng" lên `max(5, 10% số lượt)`, tách phần còn lại thành `tin_hieu_hiem` gọi đúng tên, thêm `kich_ban_chiem_da_so`, và cấm thẳng trong prompt: **không tự rút ra "đặc điểm chung" nếu dữ kiện không nói thẳng.**

> **Lớp chống bịa số KHÔNG bắt được ba lỗi này** — 58,1% / 14% / 11,6% / 43 / 37 đều có thật trong dữ kiện. Cái sai nằm ở **diễn giải định tính**, không ở con số.

### 7.9 Chatbot cử động

- Robot **thở** (3,6s) · **chớp mắt** (5,4s, hai mắt lệch pha 0,08s — lệch hơn thành lác) · **ăng-ten** (2,6s, so le) · **nghiêng đầu khi đang nghĩ** (`f2-nghi`, ăng-ten nhấp nhanh gấp 4)
- Thu gọn có animation co về phía nút tròn, rồi nút mới bung ra — thay vì `display:none` phựt một cái
- **Bong bóng thoại** (`f2-thoai`): chỉ khi panel **đang đóng** và tab đang được nhìn · im **45 giây** đầu · cách nhau **70–160 giây** · tối đa **4 lần/phiên** · tự ẩn sau **9 giây**. Nội dung trộn câu vu vơ với vài con số lấy **THẲNG từ `D`** — không qua LLM nên không thể bịa. Nền **phải đặc**: để bán trong suốt thì chữ chìm hẳn vào bảng số phía dưới.
- Tất cả tắt dưới `prefers-reduced-motion`.

---

## 8. Gemini API — hạn mức, model, lỗi

### 8.1 Hạn mức

**20 lượt mỗi NGÀY cho mỗi cặp (KHOÁ, MODEL)** — không phải mỗi phút. Lỗi trả về: `quotaId GenerateRequestsPerDayPerProjectPerModel-FreeTier`, `quotaValue 20`. Một câu hỏi của bot tốn **2–4 lượt** (đo được 1,8 lượt/câu).

Vì hạn mức tính theo từng khoá, **nhiều khoá = nhiều sức chứa**. Dự án dùng **5 khoá** (đo 05/09/2026: chúng độc lập thật). Khoá ở `.streamlit/secrets.toml` (`GEMINI_API_KEYS`, đã gitignore) và ở ô Secrets của Streamlit Cloud — **không chép khoá vào file tài liệu nào**.

Đặt lại lúc **nửa đêm giờ Thái Bình Dương** (~14h chiều giờ Việt Nam).

**Hạn mức tính theo SỐ LƯỢT GỌI, không theo token.** Nên cắt prompt cho gọn **không** làm tăng số câu hỏi mỗi ngày; giảm số lượt gọi mới có tác dụng. Bảng kiến thức tuy dài (~1.500 token) nhưng thường giúp model trả lời ngay ở vòng 1 mà không phải gọi hàm — tức là **tiết kiệm** một lượt.

### 8.2 Xoay KHOÁ trước, MODEL sau

Đổi khoá mà giữ nguyên model thì vẫn được model flash tốt nhất; đổi model trước thì tụt xuống model kém trong khi các khoá kia còn nguyên hạn mức. Code: `_chat_bo_nao.js` → `goiLLM`. Nhớ cặp đã cạn trong phiên (`DA_CAN`, lưu `localStorage` khoá `f2dr_can`, tự bỏ khi sang ngày mới theo giờ Thái Bình Dương).

### 8.3 Thứ tự model — NHANH và NHẸ trước (chủ dự án chốt 06/09/2026)

```
gemini-3.1-flash-lite → 3.8-flash → 3.5-flash → 3-flash-preview
→ flash-latest → 3.7-flash → 2.5-flash
```

Đo trên cả 5 khoá ngày 05/09/2026:

| model | số khoá còn hạn mức | giây |
|---|---|---|
| gemini-3.1-flash-lite | 5/5 | 0,88 |
| gemini-3.8-flash | 5/5 | 0,93 |
| gemini-3.5-flash | 5/5 | 1,08 |
| gemini-3-flash-preview | 1/5 | 1,23 |
| gemini-flash-latest | 2/5 | 3,83 |
| gemini-3.7-flash | **0/5** | — |
| gemini-2.5-flash | **0/5** | — |

Hai model cuối hết trên **mọi** khoá — 5 project độc lập không thể cùng cạn đúng bằng nhau, nên nhiều khả năng chúng **không có suất miễn phí**. Để chúng ở đầu danh sách thì mỗi câu hỏi phí một lượt gọi chỉ để nhận 429 (`gemini-3.7-flash` từng là model chính).

`flash-lite` làm model chính chạy tốt: xử lý đúng cả câu gõ sai chính tả, câu mơ hồ, câu hỏi thứ dữ liệu không có — kiểm 6/6.

### 8.4 ⚠️ Phải tách HAI loại lỗi, gộp lại là hỏng

- **Hết hạn mức** (`429` / `quota` / `RESOURCE_EXHAUSTED`): cặp chết tới nửa đêm giờ Thái Bình Dương → ghi sổ loại bỏ, **đổi khoá ngay**.
- **Quá tải nhất thời**: chuỗi `"This model is currently experiencing high demand"` — **không kèm mã số nào**. Thiếu nó trong bộ nhận diện thì bot coi là lỗi vĩnh viễn và bỏ cuộc; còn ghi sổ loại bỏ thì **vứt oan một cặp còn tốt suốt cả phiên**. Đúng cách: chờ ~1,2s thử lại, rồi đổi khoá mà **KHÔNG** ghi sổ.

### 8.5 `thinking_budget` — luôn đặt hạn mức cụ thể

Đo 05/09/2026 trên prompt lập kế hoạch ~11.500 ký tự:

| thinking_budget | thời gian |
|---|---|
| `-1` ("model tự quyết") | **143–150 giây** |
| `1024` | 6,6–11,8 giây |
| `0` (tắt) | 4,2 giây |

`-1` để model tự chọn ngân sách, và với prompt phức tạp nó chọn rất lớn. **Không có cách nào biết trước độ trễ.** Luôn đặt hạn mức cụ thể — `1024` đủ để vạch đường đi 2–3 bước. Trong `_chat_bo_nao.js`: `NGAN_SACH_NGHI = 1024`.

### 8.6 Hai điều về gói cước

- **Google Search grounding KHÔNG dùng được với bậc miễn phí.** Khoá mới hoàn toàn vẫn 429 khi bật `google_search`, và lỗi grounding không kèm `quotaId`/`quotaValue` nào. Muốn dùng tuyến WEB phải **bật thanh toán**.
- **Google AI Pro (gói thuê bao ứng dụng Gemini) KHÔNG nâng hạn mức Gemini API** — hai thứ khác nhau. Muốn vượt bậc miễn phí phải bật thanh toán cho từng project trên Google Cloud.

---

## 9. Quy trình & công cụ

### 9.1 Dựng dashboard

```bash
python _build/build_van_hanh.py        # template → F2DR_Van_Hanh.html   ← BẮT BUỘC TRƯỚC
python _build/xem_truoc.py             # + chatbot → F2DR_Van_Hanh_xemtruoc.html
```

**Chạy `xem_truoc.py` mà quên `build_van_hanh.py` là sửa template xong không thấy gì đổi.** Đã dính, mất thời gian tưởng code hỏng.

`xem_truoc.py` tự chạy `soat_js.py` trước khi gộp và **dừng lại** nếu có lỗi cú pháp JS.

### 9.2 Kiểm JS bằng Chrome headless

Máy **không có Node/Deno/Bun**, nhưng có Chrome ở `C:\Program Files\Google\Chrome\Application\chrome.exe`. Đó là cách duy nhất chạy thật `_chat_*.js` và toàn bộ JS của dashboard.

```
chrome.exe --headless=new --disable-gpu --no-sandbox \
  --virtual-time-budget=180000 --dump-dom "file:///C:/f2kiem/kiem.html" > dom.html
```

**Hai cạm bẫy khiến lệnh trên im lặng trả về rỗng:**

- **Đường dẫn có dấu cách** (`C:\Users\YOGA 7\...`) làm Chrome tách thành nhiều tham số rồi báo `Multiple targets are not supported in headless mode`. Dùng dạng ngắn `C:\Users\YOGA7~1\...` hoặc copy sang thư mục không dấu cách.
- Chạy từ **PowerShell** thì stdout của Chrome không được nối vào file (Chrome là GUI app trên Windows). Chạy qua **Bash** thì `>` hoạt động bình thường.
- Với `--screenshot`, **đường dẫn ra phải là tuyệt đối kiểu Windows**, không thì báo `Access is denied`.

**Cách dựng bài kiểm:** một trang gồm biến `D` (tách từ `F2DR_Van_Hanh.html`) + markup panel + ba file JS + kịch bản ghi kết quả vào `<pre id="KQ">`. **Chèn `window.onerror` và `unhandledrejection` TRƯỚC các script** — không có nó thì lỗi cú pháp trong một file chỉ biểu hiện gián tiếp (panel thiếu lời chào) chứ không nói cho biết file nào hỏng.

Gọi Gemini thật vẫn chạy được dưới `--virtual-time-budget`. Nhưng khi kiểm giao diện, **hãy chặn lượt gọi thật** bằng cách thay `window.F2BoNao.hoi` bằng một promise treo — vừa nhanh vừa không đốt hạn mức.

**Streamlit thì khác:** app Streamlit render qua websocket nên `--virtual-time-budget` + `--dump-dom` trả về gần như rỗng. Chụp ảnh (`--screenshot`) với `--virtual-time-budget=25000` thì được.

`_build/soat_js.py` là bộ soát tĩnh — bắt được chuỗi bị xuống dòng thật, **nhưng không bắt được** token lạ kiểu `"```" + \n" + x`. Chrome headless mới là lưới cuối.

### 9.3 Lỗi heredoc — đã tái diễn BA lần

Ghi file có escape **qua heredoc/shell là hỏng**: `\n` biến thành xuống dòng THẬT, `\b` thành ký tự backspace `0x08`, `\d` trong regex bị nuốt thành `d`.

**Hậu quả trong JS nặng hơn Python nhiều:** một chuỗi bị đứt làm **cả file lỗi cú pháp**, `window.F2BoNao` không bao giờ được tạo, `BN.hoi()` ném lỗi ngay — và vì `_chat_ui.js` lúc đó chưa có `.catch`, dấu ba chấm quay **vĩnh viễn** mà không báo gì. Người dùng chỉ thấy "bot không trả lời được".

**Vì sao khó tìm:** dấu hiệu bên ngoài (bot im lặng) cách rất xa nguyên nhân (một dấu `\n` trong câu thông báo lỗi).

**Quy tắc:**
- Nội dung có `\n`, `\b`, `\t`, regex → dùng **Write/Edit**, không heredoc. Bắt buộc, kể cả khi heredoc có vẻ tiện hơn.
- Sau mỗi lần sửa: `python _build/soat_js.py`.
- Mọi `.then()` gọi ra ngoài **phải** có `.catch` — treo im lặng tệ hơn báo lỗi xấu.

### 9.4 Mức độ kiểm theo việc

**Sửa nhỏ** (đổi nhãn, thêm mẫu số, sửa câu chữ, chỉnh màu): dựng lại + chụp **một** ảnh đúng chỗ vừa sửa. **Không** viết bộ kiểm riêng, **không** chạy lại toàn bộ. Chủ dự án nói thẳng: *"mấy cái sửa nhỏ này thì ko cần kiểm tra kĩ quá đâu nhé, lâu quá"*.

**Giữ kiểm đầy đủ** khi: (1) đụng logic tính điểm hay phân cụm, (2) đụng chatbot, (3) sửa thứ nhiều chỗ dùng chung (hàm sắp xếp, hàm định dạng, CSS gốc).

**Bài kiểm phải hỏi lại DOM sau mỗi cú bấm** — bảng vẽ lại nên node `<th>` cũ đã rời khỏi tài liệu, kiểm trên nó luôn sai.

### 9.5 Bảo mật

- `.streamlit/secrets.toml` và `F2DR_Van_Hanh_xemtruoc.html` **đã gitignore**, đã soát sạch cả lịch sử commit.
- Khoá API **không bao giờ** vào repo. Trên web lấy từ Streamlit Secrets, tại máy lấy từ `secrets.toml`.
- **Đánh đổi đã biết:** khoá vẫn đi xuống trình duyệt người xem (mở source là đọc được). Repo public + app public là **quyết định đã chốt của chủ dự án** sau khi đã nêu rủi ro. Đừng bàn lại nếu không có yêu cầu mới.

---

## 10. Cạm bẫy đã trả giá

### 10.1 CSS toàn trang

- Trang có luật chung `svg{display:flex}` cho biểu đồ → đường sparkline bị thành khối, đẩy % xuống dòng, mọi hàng cao gấp đôi. Phải `.spark{display:inline-block !important}`.
- `table-layout:fixed` chia phần dư **ĐỀU** cho mọi cột → cột nào cũng phình và hở toang ở giữa. Thêm một **cột đệm không đặt `width`** để hút hết phần dư.
- Bảng trong trang mặc định **căn phải**; cột nào cần trái phải gắn class `.l`. Quên là chữ trôi hết sang mép phải.
- **Đừng chặn `max-width` cho toàn bộ `.card table`**: sửa được chỗ này thì tạo khoảng trống chết bên phải mọi thẻ khác.
- Icon lịch của Chrome mặc định màu đen, trên nền tối gần như tàng hình — phải `filter: invert(...)`.
- `color-mix(in srgb, var(--kc) 26%, ...)` chạy tốt trên Chrome hiện tại — **đã kiểm bằng `getComputedStyle`**, không đoán.

### 10.2 Cạm bẫy trong popup

- **Vùng cuộn là CẢ popup, không phải từng bảng.** `position:sticky` cho `thead` sẽ làm tiêu đề đỗ lơ lửng **đè lên hàng thứ hai của chính bảng đó**. Và `max-height` trên bảng tạo cuộn-trong-cuộn, chuột lăn vào là kẹt. Bảng ở đây 6–15 dòng: **đừng dính, đừng giới hạn chiều cao**.
- **Thay cả khối CSS thì dễ đánh rơi luật cũ** — lần này rơi `.mgrid`, hai thẻ tuột xuống toàn chiều rộng và bảng nhóm hở một khoảng chết to ở giữa.

### 10.3 Sắp xếp và cắt danh sách

- Hai cột dẫn xuất từ nhau (`Alert` và `% tổng`) mà dùng **CHUNG khoá** thì bấm một cái sáng cả hai tiêu đề. Phải cho **khoá riêng**, cùng trỏ về một accessor.
- Bảng bị cắt top (⑥, khách trong popup): **cắt theo alert TRƯỚC, sắp SAU**. Sắp trước rồi cắt là đổi cả danh sách ai được vào bảng.
- `aMax` cho thanh so sánh **không được** lấy `rows[0]` — bảng có thể đang xếp theo cột khác. Phải `Math.max`.

### 10.4 Chatbot

- **Panel chat mặc định phải ĐÓNG.** Có lúc nó mặc định mở, che hẳn phần phải dashboard. Phải để sẵn class `f2-an` trên `.f2-panel` trong `_chat_ui.html`.
- Bộ bắt "bấm ra ngoài" **không được** dùng `panel.contains(e.target)`: nút gợi ý tự xoá chính mình trong `onclick` (`veGoiY([])`), đến lúc sự kiện nổi lên `document` thì `e.target` đã mồ côi → panel bị thu oan. Phải dùng **`e.composedPath()`** (đường đi được chụp tại lúc phát sự kiện).
- `thuLai()` là **bất đồng bộ** (đợi 190ms) nên `mo()` **phải** `clearTimeout(hen_dong)` — không thì bấm ra ngoài rồi bấm lại nút trong 190ms là panel vừa mở đã tự đóng.
- Hai trường hợp phải chừa khi tự thu: bấm vào **chính nút mở**, và **đang bôi đen chữ** trong panel rồi thả chuột ra ngoài.
- Bong bóng thoại **phải có nền đặc**.

---

## 11. Những thứ GIỮ NGUYÊN — đừng tự ý đổi

1. **`chuanDiem()` trả về nguyên `s`.** Không thêm làm tròn, không thêm ghim epsilon. Đã đo, đã bỏ, có lý do.
2. **Gom cột bằng `Math.floor`, quy ước `[a, b)`, nhãn `[80-81)`.**
3. **Hiển thị điểm bằng `catDiem` (cắt xuống), không `toFixed` thẳng.**
4. **Ngưỡng mặc định `[30, 65, 82]`** — sửa cả `NG_MAC_DINH` lẫn `value=` của ba thanh trượt.
5. **Mẫu số kịch bản luôn là `D.tong.kbCauHinh`**, không phải `D.kb.length`.
6. **`nhomNgan()` giữ rào chắn trùng tiền tố.** Đừng đơn giản hoá thành `split(':')[0]`.
7. **Đếm alert bằng số dòng, cấm `DISTINCT`.**
8. **Không đọc `last_risk_score` / `Level` từ CSV** — chúng tính theo r=k=0,5, khác dashboard.
9. **Mặc định sort của 7 bảng** — đúng thứ tự vốn có.
10. **Chatbot phải chạy được khi popup ngày đang mở.** `.mask` giữ `z-index: 90`.
11. **Câu từ chối PII đúng nguyên văn.**
12. **Không commit `F2DR_Van_Hanh_xemtruoc.html` và `.streamlit/secrets.toml`.**
13. **Popup không sticky header, không cuộn lồng.**
14. **Hiệu ứng vào trang chạy đúng một lần** (thêm rồi gỡ `body.vao`).
15. **`app.py` và `xem_truoc.py` dùng CHUNG `ghep()`.** Đừng chép lại logic ghép sang `app.py` — chép là mở đường cho hai bản lệch nhau.
16. **Xoay khoá trước, model sau.** Và giữ nguyên thứ tự model đã đo.
17. **`thinking_budget` luôn là số cụ thể**, không bao giờ `-1`.
18. **Ẩn danh phải chạy cả hai script** trước khi commit dữ liệu mới.

---

## 12. Future Improvements — **chưa làm, đừng tự ý làm**

Ghi lại từ đợt audit, để lần sau có việc thì biết bắt đầu từ đâu.

1. **Bộ kiểm không nằm trong repo.** Toàn bộ bộ kiểm JS (178 phép kiểm trong 8 bộ, cộng các bộ mới) nằm ở thư mục tạm của phiên làm việc trên laptop, **sẽ không có trên máy khác**. Nên đưa vào `_build/kiem/` kèm script chạy tất cả. **Đây là khoảng trống lớn nhất hiện nay.**
2. **`README.md` đã lỗi thời.** Vẫn mô tả package `chatbot/` (đã xoá ở `5d49487`), vẫn ghi "26 hàm truy vấn" của bản Python.
3. **Bot chưa tự biết người dùng vừa đổi ngưỡng.** Nó đọc đúng giá trị live, nhưng không chủ động nhắc lại kết luận cũ đã lỗi thời.
4. **Lớp kiểm chứng số còn yếu với số nhỏ** (~57% số nhỏ bịa lọt). Muốn siết phải kiểm theo ngữ nghĩa từng mệnh đề — việc lớn.
5. **`CHIP_TOI_DA = 12` và `NM_SO = 7` chưa chạy thử với kỳ dài thật.** Code đã thiết kế co giãn nhưng dữ liệu hiện chỉ có 7 ngày.
6. **Khoá API vẫn đi xuống trình duyệt.** Nếu sau này cần siết: dựng proxy ngoài (Cloudflare Worker / Vercel) giữ khoá. Streamlit không cho mở route riêng nên không làm proxy trong app được.
7. **Dữ liệu alert nằm trong repo public.** SĐT đã ẩn danh đúng, nhưng cột `chi_tiet_alert` lộ ngưỡng phát hiện thật (`dk1_VTT_100tr`, `dk2_MM_thang_200tr`, `gia_tri_gd`…) cùng tên và điểm gốc của 50 kịch bản. **Đã nêu rủi ro, chủ dự án đã chốt để public.** Ghi lại để không phải bàn lại từ đầu.
8. **`.devcontainer/` còn sót** từ commit `4aa5694`, hiện không dùng.

---

## 12b. Phiên 07/09/2026 — dữ liệu 67 ngày, bản Cloudflare, chatbot nâng cấp

> Phiên dài nhất từ trước tới nay. Ghi lại đủ để phiên sau không phải dò lại.

### 12b.1. Dữ liệu: 7 ngày → 67 ngày

| | Trước | Sau |
|---|---|---|
| Kỳ | 26/08 – 01/09 (7 ngày) | **01/07 – 05/09 (67 ngày)** |
| Alert | 15.785 | **210.713** |
| Khách | — | **88.910** (126.616 lượt) |
| Kịch bản có alert | 35/50 | **38/50** |
| File dữ liệu | CSV 76 MB | **`score_clean_full.csv.gz` 6,2 MB** |

**gzip chứ không cắt cột:** đo từng cột thấy `usecase_name`+`usecase_clean` chiếm 34%, nhưng bỏ cột nào cũng mất thông tin. pandas đọc `.csv.gz` trực tiếp nên không phải đổi code — 76 → 6,2 MB, giữ nguyên mọi cột.

**Luồng nạp hằng ngày:** `_build/nap_alert_ngay.py`. Người dùng gõ "nạp file này: `<đường dẫn>`".
**BẪY NGÀY — đã sai một lần, người dùng phải nhắc lại:** file alert ghi **ngày lên alert**, không phải ngày diễn ra. **Phải trừ 2 ngày**: file ghi 07/09 = ngày 05/09 trên dashboard. Script tự trừ, đừng sửa.

### 12b.2. BA bản chạy song song — cùng một bộ mã nguồn

| Bản | Ở đâu | Khoá API nằm đâu |
|---|---|---|
| HTML | `F2DR_Van_Hanh_xemtruoc.html` | nhúng thẳng trong file (đã gitignore) |
| Streamlit | f2drdashboard.streamlit.app | Secrets, ghép lúc chạy |
| **Cloudflare** | **f2dr-dashboard-pages.pages.dev** | **biến môi trường, trang KHÔNG có khoá** |

Cả ba dùng chung `_build/*` và hàm `xem_truoc.ghep()`. **Sửa một chỗ, dựng lại là cả ba cùng đổi** — đừng chép code sang thư mục Pages.

Thư mục bản Pages: `D:\Project F2DR\F2DR Van Hanh Pages\` (repo riêng: `daidaica123/f2dr-dashboard-pages`).
Dựng: `python _build/dung_pages.py --so-khoa 1` · Thử tại máy: `py -3.10 _build/chay_thu.py` (cổng 8910).

### 12b.3. Cloudflare: hai chuyện phải biết trước khi đụng vào

**(a) Pages là trang TĨNH — không có "lúc chạy" để ghép khoá.**
Giải pháp: `functions/api/gemini.js` chạy phía Cloudflare, giữ khoá ở biến môi trường. Trình duyệt gửi lên **số thứ tự khoá** (`{model, khoa: 2, than}`), hàm tra ra khoá thật. Nhờ vậy cơ chế xoay khoá 5 khoá × 5 model **giữ nguyên** — vẫn nhớ "khoá 3 + model X hết lượt" — mà trang không bao giờ chứa khoá.

**(b) Google CHẶN Gemini API gọi từ Hồng Kông.**
Cloudflare phục vụ Việt Nam từ colo **HKG** (đã đo `cdn-cgi/trace`). Gọi thẳng Gemini từ đó trả `User location is not supported for the API use`. Máy người dùng ở VN nên bản HTML/Streamlit **không dính**.
→ Bản Pages đi qua **OpenRouter** (`OPENROUTER_API_KEY`). Hàm tự chọn: có khoá OpenRouter thì dùng, không thì quay về Gemini.

**Model miễn phí OpenRouter hay nghẽn/từ chối — đã đo 07/09:**
- `google/gemma-4-26b-a4b-it:free` → 429 `temporarily rate-limited upstream`
- `inclusionai/ling-3.0-flash-sante:free` → chạy, NHƯNG **không nhận `response_format`** (400 `does not support feature: structured-outputs`)
- `minimax/minimax-m2.7:free`, `nvidia/nemotron-3.5-lightning:free` → nhận `response_format`

→ Hàm tự nhảy model khi gặp 400/429, và model nào không nhận `response_format` thì **dặn trả JSON bằng lời** thay vì gửi tham số đó.

**Tên model Gemini đang dùng** (đừng viết theo trí nhớ — tôi từng bịa 6 tên đều 404):
`gemini-3.1-flash-lite` · `gemini-3.8-flash` · `gemini-3.5-flash` · `gemini-3-flash-preview` · `gemini-flash-latest` · `gemini-3.7-flash` · `gemini-2.5-flash`

**Khoá Gemini hiện tại dạng `AQ.Ab8RN6…`, KHÔNG phải `AIza…`.** Bộ chặn trong `dung_pages.py` quét cả hai mẫu — đừng bỏ mẫu `AQ.`.

### 12b.4. Chatbot: 23 → 26 hàm + lưu lịch sử

**Ba hàm mới** (khai thác 126.616 lượt trước nay bỏ không):

| Hàm | Dùng khi |
|---|---|
| `kich_ban_di_cung_nhau` | hai rule có trùng nhau không, tổ hợp nào là thủ đoạn có cấu trúc |
| `do_tap_trung_kich_ban` | rule bắn vào vài đối tượng hay quét rộng |
| `so_sanh_hai_ky` | "tháng 8 so tháng 7" — so theo **trung bình mỗi ngày** nên lệch số ngày vẫn đúng |

Đo bằng **lift**, không đếm thô: hai rule đông alert đương nhiên hay gặp nhau. Sàn tối thiểu 20 lượt — lift cao trên nền vài lượt là nhiễu (đúng bẫy đã mắc ở `hanh_vi_theo_cum_diem`).

**Kết quả đáng chú ý:** cặp `VAY_CCCD không hợp lệ` ↔ `VAY_CCCD cấp quá gần ngày vay` có **lift 110,9**, có B thì **98,1%** có A → hai rule gần như trùng nhau, đáng rà lại. `AML_TK nhận tiền rồi chuyển/rút ngay`: **511 alert chỉ từ 3 khách**.

**Lưu lịch sử chat — `_build/_chat_kho.js`, localStorage.**
**KHÔNG dùng SQLite** dù prompt tham khảo có nói: dashboard chạy trong trình duyệt, không có backend lúc chạy; Streamlit Cloud xoá filesystem mỗi lần ngủ dậy; Pages không có đĩa. localStorage bền qua reload và chạy giống nhau ở cả ba bản.
Nút `✚` (New Chat) và `☰` (danh sách cuộc) trên thanh tiêu đề. Mở lại trang thì vào đúng cuộc đang dở; ngữ cảnh câu hỏi nối tiếp đọc từ cuộc đang mở nên **mở lại cuộc cũ vẫn hỏi tiếp được**.

**Hai sửa nhỏ nhưng quan trọng:**
- `coKhoa()` giờ tính cả chế độ proxy — trước đó bản Pages luôn báo "chưa có khoá" dù chat chạy tốt.
- `chiSoNgay()` phân biệt **"chưa có dữ liệu"** với **"bằng 0"**. Với dashboard rủi ro hai thứ này khác hẳn: 0 alert = hệ sạch, chưa có data = chưa biết gì. Thông báo lỗi dặn thẳng model *"TUYỆT ĐỐI không trả lời là 0 alert"*.

### 12b.5. Giao diện

- **Bảng markdown trong chat**: `md()` trước không dựng `<table>`, model trả bảng thì đổ ra một mớ dấu `|`. Đã thêm. **Bẫy**: số bọc `**đậm**` bị bẻ dòng (`11.362` → `11.36`/`2`) vì `nowrap` trên ô không chặn được ngắt bên trong `<strong>` — phải đặt cho cả thẻ con.
- **Nút phóng to chat** `⤢`: 412px → ~52% màn hình. Nhớ lựa chọn qua localStorage.
- **Ma trận thu gọn**: giấu 67 cột ngày thì thừa cả nghìn pixel. Thêm 5 cột — Tỉ trọng (thanh) · % tổng · Ngày nổ · TB/ngày nổ · Ngày đỉnh. **TB chia cho số ngày CÓ nổ**, không chia cả kỳ (kịch bản nổ 2/67 ngày mà chia 67 ra số vô nghĩa). Thanh so với kịch bản nặng nhất, không so tổng (so tổng thì mọi thanh đều tí xíu).
- **Mục ⑤ chọn khoảng**: thêm chọn theo tháng và full ngày.
- Thanh chọn ngày chỉ hiện tổng quan + 7 ngày gần nhất + lịch. Bảng mục ③ 7 ngày, biểu đồ vẫn 30.

### 12b.6. Bài học phiên này

**Bịa rồi phải đo lại — ba lần:**
1. Tưởng Streamlit đen vì iframe sập chiều cao → thật ra `data:` URL vượt ~2 MB.
2. Tưởng lỗi OpenRouter là 429 nghẽn → bắt request thật thấy **400** `does not support structured-outputs`.
3. Viết bảng tên model OpenRouter theo trí nhớ → **cả 6 tên đều 404**.
→ **Bắt thẳng request/response thật, đừng suy đoán.** Playwright `pg.on('request'/'response')` là cách nhanh nhất.

**Báo động giả đã kiểm và loại:** quét `public/index.html` ra 54 chuỗi giống SĐT + 1.402 số 12 chữ số. Soi ngữ cảnh: **54/54 và 1400/1402 nằm gọn trong mã băm hex 20 ký tự** (mã băm toàn `[0-9a-f]` nên ngẫu nhiên có 10 chữ số liền là thường); 2 cái còn lại là `79,999999999966` trong chú thích. **Không có định danh thật.** Repo Pages để public an toàn.

**Bẫy cũ tái diễn:** heredoc bash nuốt `\` trong đường dẫn Windows (`r'D:\Project...'`) → `SyntaxError`. Dùng Write tool. Đây là §9.3 lặp lại lần thứ tư.

**Playwright:** `FrameLocator` **không có** `.evaluate()`. Muốn chạy JS trong iframe phải lấy `Frame` thật từ `pg.frames`.

---

## 13. Current State — dashboard đang ở đâu

**Ổn định, đã deploy cả ba bản, không có việc dở dang.**

- Kỳ dữ liệu: `2026-07-01 → 2026-09-05` (**67 ngày**) · **210.713** alert · **88.910** khách · **126.616** lượt · **38/50** kịch bản có alert
- Nguồn: `data/score_clean_full.csv.gz` (6,2 MB)
- Dựng ra HTML ~4,97 MB; ghép chatbot thành ~5,15 MB
- Ba bản đang chạy: [HTML](#12b2-ba-bản-chạy-song-song--cùng-một-bộ-mã-nguồn) · Streamlit · Cloudflare Pages
- Chatbot: **26 hàm** tri thức, có lưu lịch sử hội thoại
- Lần kiểm gần nhất: bảng markdown · nút phóng to · 5 cột thu gọn (đối chiếu CSV tháng 7 khớp tuyệt đối) · lưu chat qua reload · 4 nâng cấp trí tuệ — **0 lỗi JS**

**Việc gần nhất đã làm:** nạp dữ liệu 67 ngày; dựng bản Cloudflare Pages với proxy giữ khoá; sửa chatbot trả lời được theo khoảng ngày; bảng markdown + nút phóng to; 5 cột lấp chỗ trống khi thu gọn ma trận; lưu lịch sử chat; thêm 3 hàm phân tích.

**Trước khi sửa tiếp, đọc lại [§11 (giữ nguyên)](#11-những-thứ-giữ-nguyên--đừng-tự-ý-đổi) và [§5.2 (chốt không làm)](#52-đã-chốt-không-làm).** Nhiều quyết định trong đó trông như thiếu sót nhưng thực ra là kết quả của một vòng thảo luận và đo đạc — **sửa "cho đúng" mà không đọc lý do là làm hỏng.**
