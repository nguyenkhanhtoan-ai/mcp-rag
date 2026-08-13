# Deploy MCP RAG Server lên Cloud (Railway)

Hướng dẫn deploy `rag-pdf` server thành 1 service chạy 24/7 trên cloud,
truy cập qua URL công khai (HTTPS).

Chọn **Railway**: deploy bằng Dockerfile có sẵn, hỗ trợ persistent volume
(lưu `chroma_db/`), free tier đủ để test. Fly.io/Render tương tự, chỉ khác
thao tác UI.

> **Lưu ý bảo mật**: bản này **không có xác thực** — bất kỳ ai có URL đều
> gọi được `search_docs`/`list_indexed_documents` và tốn OpenAI credit của
> bạn. Phù hợp để test/nội bộ tin cậy. Khi cần dùng thật cho doanh nghiệp,
> nhắn mình để thêm lại lớp xác thực (bearer token hoặc OAuth).

## Kiến trúc sau khi deploy

```
[Claude Desktop / claude.ai / mobile] --HTTPS--> [Railway: rag-pdf service]
                                                        |
                                                  chroma_db (persistent volume)
```

## 1. Chuẩn bị code

Đảm bảo các file này có trong project (đã tạo sẵn): `Dockerfile`,
`.dockerignore`, `server.py` (chỉ chạy HTTP, không còn nhánh stdio).

Đẩy code lên GitHub (Railway deploy từ GitHub repo):

```bash
cd mcp-rag-pdf
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<username>/mcp-rag-pdf.git
git push -u origin main
```

Đừng commit `.env` hay API key — đã có `.gitignore` chặn sẵn.

## 2. Tạo project trên Railway

1. Vào [railway.app](https://railway.app), đăng nhập bằng GitHub.
2. **New Project** → **Deploy from GitHub repo** → chọn repo `mcp-rag-pdf`.
3. Railway tự nhận diện `Dockerfile` và build.

## 3. Thêm Persistent Volume (bắt buộc)

Không có bước này, mỗi lần deploy lại sẽ mất index đã ingest.

1. Vào service → tab **Settings** → **Volumes**.
2. **New Volume** → Mount path: `/app/chroma_db`.
3. Save.

## 4. Cấu hình biến môi trường

Tab **Variables**, thêm:

| Key | Value |
|---|---|
| `OPENAI_API_KEY` | `sk-...` |

## 5. Lấy public URL

Tab **Settings** → **Networking** → **Generate Domain**. Railway cấp URL
dạng `https://rag-pdf-production-xxxx.up.railway.app`.

MCP endpoint: `https://rag-pdf-production-xxxx.up.railway.app/mcp`

## 6. Ingest dữ liệu (khuyên dùng: ingest ngay trong lúc build image)

Cách đơn giản và đáng tin cậy nhất — sửa `Dockerfile`, thêm 2 dòng trước
`CMD`:

```dockerfile
COPY documents/ /app/documents/

ARG OPENAI_API_KEY
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
RUN python ingest.py
```

Trên Railway: **Settings → Variables → Build-time variables**, thêm
`OPENAI_API_KEY` để nó available lúc build. Mỗi lần thêm PDF mới → build
lại image (push code mới hoặc trigger redeploy).

## 7. Kết nối từ Claude (Desktop / claude.ai / mobile)

Server cloud add qua UI, **không sửa `claude_desktop_config.json`**:

1. Mở Claude → **Settings → Connectors**.
2. **Add custom connector** → **Web**.
3. Paste URL: `https://rag-pdf-production-xxxx.up.railway.app/mcp`
4. **Add** → **Connect**.

Sau khi connect, `search_docs` và `list_indexed_documents` xuất hiện trong
tool list — dùng được trên mọi thiết bị đã đăng nhập tài khoản đó.

> Team/Enterprise: chỉ Owner add được connector cho cả tổ chức
> (Organization Settings → Connectors), sau đó từng người tự Connect.

## 8. Kiểm tra server sống

```bash
curl https://rag-pdf-production-xxxx.up.railway.app/health
# → ok
```

## Chi phí ước tính

- Railway: free tier ($5 credit/tháng) đủ cho service nhỏ; vượt quá thì
  tính theo usage (~vài USD/tháng).
- OpenAI embedding: chỉ tốn khi ingest (build image), không đáng kể với
  vài trăm file `text-embedding-3-small`.
