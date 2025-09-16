import re
from typing import List, Dict
from langchain.docstore.document import Document
from .config import CHUNK_SIZE, CHUNK_OVERLAP


from typing import List
from langchain.docstore.document import Document

import re
from typing import List
from langchain.docstore.document import Document

def chunk_documents(docs: List[Document], CHUNK_SIZE=CHUNK_SIZE, CHUNK_OVERLAP=CHUNK_OVERLAP) -> List[Document]:
    """
    Chunk theo từng trang:
    - Mỗi trang được xử lý độc lập
    - Trong mỗi trang:
        + Table => chunk type 'table'
        + Operation => chunk type 'operation'
        + Text còn lại => chunk type 'text' (chia nhỏ nếu dài hơn CHUNK_SIZE)
    - Mỗi chunk có chunk_id duy nhất, metadata giữ source_file + page_number + chunk_type
    """
    chunks = []
    global_idx = 0

    for doc in docs:
        # --- Tách thành các trang ---
        pages = re.split(r'\f', doc.page_content)
        if len(pages) == 1:
            # fallback: giả sử mỗi 50 dòng = 1 trang
            lines = doc.page_content.splitlines()
            page_size = 50
            pages = ['\n'.join(lines[i:i + page_size]) for i in range(0, len(lines), page_size)]

        source_file = doc.metadata.get("source_file", "unknown_file")

        # --- Duyệt từng trang ---
        for page_number, page_text in enumerate(pages, start=1):
            page_text = page_text.strip()
            if not page_text:
                continue

            # 1. Extract tables
            tables = extract_tables(page_text)
            table_placeholders = {}
            page_remaining = page_text
            for tidx, table in enumerate(tables):
                placeholder = f"__TABLE_{tidx}__"
                table_placeholders[placeholder] = table
                page_remaining = page_remaining.replace(table['content'], placeholder)

            # 2. Split theo operation hoặc text
            blocks = re.split(r'(?m)^(?=Thao\s+tác\s+\d+[:\.])', page_remaining)

            # 3. Xử lý từng block trong trang
            for block in blocks:
                block = block.strip()
                if not block:
                    continue

                # Restore tables trước
                for placeholder, table in table_placeholders.items():
                    if placeholder in block:
                        global_idx += 1
                        chunks.append(Document(
                            page_content=table['content'],
                            metadata={
                                **doc.metadata,
                                "source_file": source_file,
                                "page_number": page_number,
                                "chunk_type": "table",
                                "chunk_id": f"{source_file}__{page_number:03d}__{global_idx:05d}"
                            }
                        ))
                        block = block.replace(placeholder, "")

                if not block.strip():
                    continue

                # Operation block
                if re.match(r'^Thao\s+tác\s+\d+[:\.]', block):
                    global_idx += 1
                    chunks.append(Document(
                        page_content=block,
                        metadata={
                            **doc.metadata,
                            "source_file": source_file,
                            "page_number": page_number,
                            "chunk_type": "operation",
                            "chunk_id": f"{source_file}__{page_number:03d}__{global_idx:05d}"
                        }
                    ))

                # Text block
                else:
                    if len(block) > CHUNK_SIZE:
                        sub_blocks = split_long_block(block)
                        for sub_block in sub_blocks:
                            global_idx += 1
                            chunks.append(Document(
                                page_content=sub_block,
                                metadata={
                                    **doc.metadata,
                                    "source_file": source_file,
                                    "page_number": page_number,
                                    "chunk_type": "text",
                                    "chunk_id": f"{source_file}__{page_number:03d}__{global_idx:05d}"
                                }
                            ))
                    else:
                        global_idx += 1
                        chunks.append(Document(
                            page_content=block,
                            metadata={
                                **doc.metadata,
                                "source_file": source_file,
                                "page_number": page_number,
                                "chunk_type": "text",
                                "chunk_id": f"{source_file}__{page_number:03d}__{global_idx:05d}"
                            }
                        ))

    return chunks
6

def build_payload(base_meta: Dict, part: str, section: str, subsection: str,
                  chunk_type: str, source_file: str, idx: int) -> Dict:
    """
    Chuẩn hóa payload (metadata) cho Qdrant.
    Thêm chunk_id duy nhất.
    """
    return {
        **base_meta,  # giữ metadata gốc (author, etc.)
        "part": part,
        "section": section,
        "subsection": subsection,
        "type": chunk_type,
        "chunk_id": f"{source_file}__{idx:05d}"  # ví dụ: doc1.pdf__00042
    }


def extract_tables(text: str) -> List[Dict[str, str]]:
    """
    Trích xuất bảng: giả định bảng có ký tự '|' trong nhiều dòng liên tiếp.
    """
    tables = []
    current_table = []
    in_table = False

    for line in text.splitlines():
        if "|" in line:
            in_table = True
            current_table.append(line)
        else:
            if in_table:
                tables.append({"content": "\n".join(current_table)})
                current_table = []
                in_table = False

    if current_table:
        tables.append({"content": "\n".join(current_table)})

    return tables


def split_long_block(block: str) -> List[str]:
    """
    Chia nhỏ block dài thành nhiều sub-block theo CHUNK_SIZE + CHUNK_OVERLAP
    """
    sub_blocks = []
    start = 0
    while start < len(block):
        end = start + CHUNK_SIZE
        sub_blocks.append(block[start:end])
        start = end - CHUNK_OVERLAP
    return sub_blocks

