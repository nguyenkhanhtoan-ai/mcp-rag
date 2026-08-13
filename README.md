# MCP RAG Server cho PDF

MCP server (HTTP) cho phép Claude tìm kiếm ngữ nghĩa (semantic search) trên
các file PDF của bạn thông qua RAG (Retrieval-Augmented Generation).

- **Transport**: HTTP (streamable-http) — kết nối qua Claude Connectors,
  dùng được trên Claude Desktop, claude.ai, và mobile
- **Vector DB**: ChromaDB (embedded, lưu trên đĩa)
- **Embedding**: OpenAI `text-embedding-3-small`
- **PDF**: chỉ hỗ trợ PDF dạng text (không OCR)
- **Xác thực**: không có (xem lưu ý bảo mật trong `DEPLOY.md`)

## Cấu trúc project

```
mcp-rag-pdf/
├── documents/          # Bỏ file PDF cần index vào đây
├── chroma_db/           # Chroma tự tạo, lưu vector index (không sửa tay)
├── config.py             # Cấu hình chung
├── pdf_utils.py          # Đọc PDF + chia chunk
├── vector_store.py       # Wrapper Chroma + OpenAI embedding
├── ingest.py             # Script chạy thủ công để nạp/refresh dữ liệu
├── server.py              # MCP server (HTTP)
├── Dockerfile
├── requirements.txt
└── DEPLOY.md              # Hướng dẫn deploy lên cloud (Railway)
```

## 1. Cài đặt (chạy dev trên máy)

```bash
cd mcp-rag-pdf
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Cấu hình OpenAI API key

Tạo file `.env` (copy từ `.env.example`):

```
OPENAI_API_KEY=sk-...
```

## 3. Ingest PDF

Bỏ file `.pdf` vào `documents/`, sau đó chạy:

```bash
python ingest.py
```

Các lệnh hữu ích khác:

```bash
python ingest.py --reset          # xoá index cũ, ingest lại từ đầu
python ingest.py --force          # ingest lại tất cả kể cả file không đổi
python ingest.py --dir /path/khac # ingest từ thư mục khác
```

Chạy lại `python ingest.py` bất cứ khi nào thêm/sửa file PDF — script tự
động bỏ qua file không đổi (dựa trên hash nội dung), chỉ re-index file mới
hoặc đã thay đổi.

**Lưu ý chi phí**: mỗi lần ingest gọi OpenAI Embedding API. Với vài trăm
file PDF, chi phí `text-embedding-3-small` thường dưới $1.

## 4. Chạy thử server local

```bash
python server.py
```

Mặc định lắng nghe tại `http://0.0.0.0:8000/mcp`, có endpoint kiểm tra
sống tại `http://localhost:8000/health`.

Đổi port bằng biến môi trường: `PORT=8080 python server.py`

Test bằng [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector):

```bash
npx @modelcontextprotocol/inspector http://localhost:8000/mcp
```

## 5. Deploy lên cloud + kết nối vào Claude

Xem hướng dẫn chi tiết trong [`DEPLOY.md`](./DEPLOY.md) — deploy lên
Railway, lấy public URL, rồi add qua **Claude → Settings → Connectors →
Add custom connector**.

## Quy trình cập nhật dữ liệu

Local: chạy lại `python ingest.py` sau khi thêm/sửa PDF trong `documents/`.

Cloud (Railway): ingest được thực hiện trong lúc build Docker image —
push code/PDF mới rồi redeploy (chi tiết trong `DEPLOY.md`).

## Giới hạn hiện tại

- Chỉ đọc PDF dạng text; PDF scan (ảnh) sẽ bị bỏ qua với cảnh báo.
- Xoá file khỏi `documents/` không tự động xoá khỏi index — cần chạy
  `python ingest.py --reset` để làm sạch hoàn toàn.
- Không có xác thực — chỉ nên deploy cho môi trường nội bộ tin cậy, hoặc
  đặt sau 1 lớp bảo vệ khác (VPN, IP allowlist...).
