"""
MCP server expose tool RAG search trên các PDF đã ingest.

Chỉ hỗ trợ HTTP transport (streamable-http) - dùng cho deploy cloud và kết
nối qua Claude Connectors (Settings -> Connectors -> Add custom connector).

Chạy:
    python server.py

Đăng ký remote connector: xem DEPLOY.md
"""
import os

from mcp.server import FastMCP

from config import DEFAULT_TOP_K
from vector_store import embed_texts, get_collection

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

mcp = FastMCP("rag-pdf", host=HOST, port=PORT)


@mcp.tool()
def search_docs(query: str, top_k: int = DEFAULT_TOP_K) -> str:
    """
    Tìm kiếm ngữ nghĩa (semantic search) trong kho tài liệu PDF đã được index.

    Dùng tool này khi cần tra cứu thông tin, trích dẫn, hoặc trả lời câu hỏi
    dựa trên nội dung các file PDF mà người dùng đã nạp vào hệ thống.

    Args:
        query: câu hỏi hoặc từ khóa cần tìm.
        top_k: số đoạn kết quả liên quan nhất cần trả về (mặc định 5).

    Returns:
        Danh sách các đoạn văn bản liên quan nhất, kèm nguồn (tên file + trang).
    """
    collection = get_collection()
    if collection.count() == 0:
        return (
            "Kho tài liệu hiện đang trống. Hãy chạy `python ingest.py` để nạp "
            "PDF từ thư mục documents/ trước khi tìm kiếm."
        )

    query_embedding = embed_texts([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=max(1, min(top_k, 20)),
    )

    docs = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not docs:
        return "Không tìm thấy đoạn nào liên quan đến truy vấn này."

    parts = []
    for i, (doc, meta, dist) in enumerate(zip(docs, metadatas, distances), start=1):
        similarity = round(1 - dist, 3)
        parts.append(
            f"[{i}] Nguồn: {meta.get('source')} (trang {meta.get('page')}) "
            f"- độ liên quan: {similarity}\n{doc}"
        )

    return "\n\n---\n\n".join(parts)


@mcp.tool()
def list_indexed_documents() -> str:
    """
    Liệt kê danh sách các file PDF hiện đã được index trong kho tài liệu,
    kèm số lượng chunk (đoạn văn bản) của mỗi file.

    Dùng tool này khi cần biết kho tài liệu hiện có gì trước khi tìm kiếm.
    """
    collection = get_collection()
    if collection.count() == 0:
        return "Kho tài liệu hiện đang trống. Hãy chạy `python ingest.py` trước."

    all_meta = collection.get()["metadatas"]
    counts: dict[str, int] = {}
    for meta in all_meta:
        source = meta.get("source", "unknown")
        counts[source] = counts.get(source, 0) + 1

    lines = [f"- {name}: {count} chunks" for name, count in sorted(counts.items())]
    return f"Tổng {len(counts)} file, {collection.count()} chunks:\n" + "\n".join(lines)


def _run_http():
    """Chạy server ở chế độ HTTP (streamable-http)."""
    import uvicorn
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    app = mcp.streamable_http_app()
    # Endpoint đơn giản để cloud platform (Railway/Fly.io) kiểm tra health
    app.router.routes.insert(0, Route("/health", lambda request: PlainTextResponse("ok")))

    print(f"[server] Listening on http://{HOST}:{PORT}/mcp")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    _run_http()
