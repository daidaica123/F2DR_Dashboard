# F2DR Vận hành

Công cụ theo dõi alert định kỳ hằng tuần — xem mỗi kịch bản bắn bao nhiêu alert
mỗi ngày, ngày nào bất thường là do kịch bản nào, khách hàng nào bị bắn nhiều nhất.

Dashboard là **một file HTML tĩnh** đã nhúng sẵn dữ liệu. Mọi thao tác lọc, kéo
ngưỡng, tính điểm đều chạy bằng JavaScript trong trình duyệt — không gọi về server.
App Streamlit chỉ bọc file đó lại để có link chia sẻ và chỗ upload dữ liệu mới.

## Xem nhanh

Không cần cài gì: mở thẳng `F2DR_Van_Hanh.html` bằng trình duyệt.

## Phiên bản Python

| Chạy ở đâu | Python | Ghi chú |
|---|---|---|
| Máy (Windows) | **3.10** | Bản duy nhất đã cài đủ pandas, numpy, streamlit, openpyxl |
| Streamlit Cloud | **3.11** | Khai trong `runtime.txt`, Cloud tự dựng môi trường |

Trên máy phải gọi rõ `py -3.10`. Bản 3.13 và venv trong `D:\Project F2DR\.venv`
đều **thiếu thư viện** — chạy vào đó sẽ lỗi `ModuleNotFoundError`.

## Chạy app tại máy

```bash
py -3.10 -m pip install -r requirements.txt
py -3.10 -m streamlit run app.py
```

## Đổ dữ liệu mới

**Cách 1 — trên web:** upload file CSV ở thanh bên rồi bấm *Dựng lại dashboard*.

**Cách 2 — tại máy:**

```bash
py -3.10 _build/build_van_hanh.py --csv data/<file>.csv
```

Tham số chỉnh được:

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--csv` | `data/score_clean_2608_0109.csv` | File alert đã clean |
| `--dotbien` | `2.0` | Đánh dấu đột biến khi ngày cao nhất ≥ N lần mức thường |
| `--apk` | `3.0` | Đánh dấu bắn dày khi ≥ N alert mỗi khách |
| `--topkh` | `80` | Số khách đưa vào bảng ⑥ |
| `--ghichep` | `_build/ghi_chep_dieu_tra.json` | Nội dung mục ⑦ |

## Cấu trúc trang

Luồng đọc đi thẳng từ tổng quan tới kết luận:

| Mục | Trả lời câu hỏi |
|---|---|
| KPI | Kỳ này có gì đáng chú ý? |
| ⓪①② *(gập lại)* | Đặt điểm và ngưỡng thế này thì phải xử lý bao nhiêu? |
| ③ Alert theo ngày | Ngày nào bất thường? |
| ④ Nhóm nghiệp vụ | Nhóm nào đang tạo nhiều alert nhất? |
| ⑤ Ma trận KB × ngày | **Ngày đó bất thường là do kịch bản nào?** |
| ⑥ Khách hàng | **Ai bị bắn? Dính kịch bản gì, điểm bao nhiêu?** |
| ⑦ Kết luận điều tra | Đã điều tra ra gì, sửa rule nào? |
| ⑧ Lưu ý dữ liệu | Những chỗ dễ đọc nhầm |

## Ghi chép điều tra (mục ⑦)

Tạo `_build/ghi_chep_dieu_tra.json` rồi build lại:

```json
[
  {
    "ngay": "01/09/2026",
    "tieude": "QR code bùng alert ngày 28/08",
    "noidung": "Điều tra <b>42 khách</b>. Nguyên nhân: chống lặp theo merchant chưa chặn được cùng một mã QR quét lại. <b>Đã sửa:</b> thêm gom theo mã QR trong ngày.",
    "tag": ["TT_QR code", "đã sửa"]
  }
]
```

`noidung` nhận thẻ HTML đơn giản (`<b>`, `<br>`, `<i>`).

## Trợ lý hỏi đáp

Panel chat nổi ở góc phải dưới dashboard. Hỏi bằng tiếng Việt, trả lời bằng
số lấy thẳng từ dữ liệu kỳ hiện tại.

### Cách hoạt động

```
Câu hỏi → lập kế hoạch → chạy hàm pandas → kiểm chứng số → trả lời
              ↑______________________|
                  tối đa 4 vòng
```

Ba ranh giới không bao giờ phá:

| Nguyên tắc | Vì sao |
|---|---|
| LLM chọn **hàm nào** và **tham số gì**, code chạy phép tính | LLM tự tính sẽ sai mà không ai biết |
| Mọi con số trong câu trả lời phải truy được về dữ kiện | Chặn bịa số; số lạ thì viết lại, vẫn hỏng thì trả bảng thô |
| Không suy luận nhân quả, không dự báo | Được nói "A giảm cùng lúc B ngừng bắn", không được nói "A giảm **vì** B" |

Khi 26 hàm đóng sẵn không phủ được câu hỏi, trợ lý tự viết code pandas và
chạy trong hộp cát: cấm `import`/`open`/`eval`, cấm cột `chi_tiet_alert`,
giới hạn thời gian chạy. Code tự viết luôn hiện ra trong mục *nguồn số liệu*
để kiểm chứng.

### Khoá API

Trợ lý dùng Gemini. Khoá đặt ở **server**, không bao giờ xuống trình duyệt:

| Chạy ở đâu | Đặt khoá thế nào |
|---|---|
| Máy | Tạo `.streamlit/secrets.toml`: `GEMINI_API_KEY = "..."` |
| Streamlit Cloud | Settings → Secrets, dán cùng nội dung |

File `secrets.toml` đã nằm trong `.gitignore`. **Không bao giờ commit khoá.**

Thiếu khoá thì dashboard vẫn chạy bình thường, chỉ mất ô chat.

### Kiểm thử

```bash
py -3.13 -m chatbot.kiem_thu
```

Bộ kiểm thử **không** so với số cố định — vì dữ liệu đổi hằng ngày. Nó so
**hai đường tính độc lập**: kết quả hàm phải khớp với kết quả tính lại từ
CSV bằng cách khác, và điểm Python phải khớp từng lượt với JS trong
dashboard. Kiểu kiểm tra này vẫn đúng sau mỗi lần nạp dữ liệu mới.

## Cấu trúc thư mục

```
app.py                          app Streamlit bọc HTML
F2DR_Van_Hanh.html              dashboard đã nhúng dữ liệu
data/score_clean_2608_0109.csv  dữ liệu alert nguồn
_build/
  build_van_hanh.py             script dựng dashboard
  _van_hanh_template.html       khung giao diện
  nhom_kb.json                  số KB mỗi nhóm (chốt từ sheet FINAL)
  clean_2608_0109.py            script làm sạch alert thô → CSV
  an_danh_sdt.py                ẩn danh bước 1 — quét theo dạng số
  an_danh_bo_sung.py            ẩn danh bước 2 — quét theo tên khoá JSON
  tra_nguoc.py                  tra mã băm ↔ số thật (cần muối)
chatbot/
  nap.py                        nạp CSV + dựng bảng kiến thức (tự nhận file mới)
  diem.py                       công thức PP-D — bản Python, khớp JS từng lượt
  truy_van.py                   26 hàm truy vấn đóng sẵn
  hop_cat.py                    chạy code LLM tự viết, có kiểm soát
  kiem_chung.py                 đối chiếu từng con số, chặn bịa
  tro_ly.py                     vòng lặp suy luận nhiều bước
  llm.py                        gọi Gemini, tự thử lại khi quá tải
  khung_chat.py                 ghép giao diện với trợ lý
  giao_dien.py                  CSS panel chat nổi
  phien.py                      trạng thái phiên + cache theo mtime
  kiem_thu.py                   bộ kiểm thử
```

## Dữ liệu đã ẩn danh

Repo này công khai nên **mọi thông tin định danh đều đã được băm** trước khi
đẩy lên. Việc ẩn danh làm hai bước, phải chạy **cả hai** cho file mới:

```bash
py -3.10 _build/an_danh_sdt.py    <file.csv> --out data/<file.csv>   # bước 1
py -3.10 _build/an_danh_bo_sung.py data/<file.csv>                   # bước 2
```

| Bước | Quét theo | Xử lý |
|---|---|---|
| 1 · `an_danh_sdt.py` | dạng số | `object_value` là SĐT, và SĐT `0xxxxxxxxx` nằm trong `chi_tiet_alert` |
| 2 · `an_danh_bo_sung.py` | **tên khoá JSON** | 14 khoá định danh trong `chi_tiet_alert` |

Bước 2 quét theo tên khoá chứ không theo dạng số, nên không phụ thuộc vào
việc giá trị trông như thế nào — an toàn hơn hẳn cách dùng regex.

Các khoá bước 2 xử lý: `tb_duoc_nap`, `cccd`, `so_gttt`, `sdt_kenh`,
`tk_thu_huong`, `dau_moi`, `doi_tac_stk`, `doi_tac`, `merchant_code`,
`ma_kenh`, `nguoi_gui`, `kh_duoc_nap`, `doi_tac_sdt`, `ds_dich_nhan`.

Giá trị đã là mã băm 20 ký tự hoặc chuỗi `enc:...` thì **giữ nguyên**, không
băm chồng — băm lại sẽ làm mã đổi và mất liên kết với các kỳ trước.

Cách băm: `sha256(muối + giá trị)[:20]`, cùng định dạng với mã băm sẵn có nên
dashboard không phải sửa gì.

Cả hai script tự kiểm lại toàn bộ file sau khi xử lý; còn sót số nào là báo
lỗi và dừng, không cho ghi ra.

### Muối (salt)

Đặt trước khi chạy, nếu không script sinh ngẫu nhiên và in ra màn hình:

```powershell
$env:F2DR_SALT = "chuỗi-bí-mật-của-bạn"
```

**Muối không bao giờ được commit lên repo.** Mất muối là mất khả năng tra
ngược vĩnh viễn.

**Tra ngược:**

```bash
py -3.10 _build/tra_nguoc.py --sdt 09xxxxxxxx           # số → mã
py -3.10 _build/tra_nguoc.py --ma <mã> --goc <file gốc> # mã → số
```

## Lưu ý

Điểm trong file tính theo công thức PP-D hai tầng với `r = k = 0,70`. Ba mục
⓪①② dùng để ước lượng khối lượng phải xử lý, **không phải nơi chốt ngưỡng
Impact chính thức**.
