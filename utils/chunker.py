import re
from typing import List, Dict
from langchain.docstore.document import Document
from .config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_documents(docs: List[Document]) -> List[Document]:
    """
    Chunking tài liệu nâng cao + Payload:
    - Part → Section → Subsection
    - Extract tables → chunk type 'table'
    - Extract operation blocks → chunk type 'operation'
    - Text còn lại → chunk type 'text'
    - Mỗi chunk có ID duy nhất để tránh trùng lặp
    """
    chunks = []
    global_idx = 0  # tăng dần cho mỗi chunk

    for doc in docs:
        text = doc.page_content.strip()
        if not text:
            continue

        source_file = doc.metadata.get("source_file", "unknown_file")

        # 1. Split by Part
        parts = re.split(r'(?m)^PART\s+\d+[:\-]?\s+[^\n]+', text)
        part_titles = re.findall(r'(?m)^PART\s+\d+[:\-]?\s+[^\n]+', text)
        if not part_titles:
            part_titles = ["Unknown Part"]

        for idx, part in enumerate(parts):
            part_title = part_titles[idx] if idx < len(part_titles) else "Unknown Part"
            part = part.strip()
            if not part:
                continue

            # 2. Split by Section
            sections = re.split(r'(?m)^\d+\.\d+\s+[^\n]+', part)
            section_titles = re.findall(r'(?m)^\d+\.\d+\s+[^\n]+', part)
            if not section_titles:
                section_titles = ["Unknown Section"]

            for sidx, section in enumerate(sections):
                section_title = section_titles[sidx] if sidx < len(section_titles) else "Unknown Section"
                section = section.strip()
                if not section:
                    continue

                # 3. Split by Subsection
                subsections = re.split(r'(?m)^\d+(?:\.\d+){2,}\s+[^\n]+', section)
                subsection_titles = re.findall(r'(?m)^\d+(?:\.\d+){2,}\s+[^\n]+', section)
                if not subsection_titles:
                    subsection_titles = ["Unknown Subsection"]

                for subidx, subsection in enumerate(subsections):
                    subsection_title = subsection_titles[subidx] if subidx < len(subsection_titles) else "Unknown Subsection"
                    subsection = subsection.strip()
                    if not subsection:
                        continue

                    # --- 4. Extract Tables ---
                    tables = extract_tables(subsection)
                    table_placeholders = {}
                    section_text = subsection
                    for tidx, table in enumerate(tables):
                        placeholder = f"__TABLE_{tidx}__"
                        table_placeholders[placeholder] = table
                        section_text = section_text.replace(table['content'], placeholder)

                    # --- 5. Split operation blocks ---
                    blocks = re.split(r'(?m)^(?=Thao\s+tác\s+\d+[:\.])', section_text)

                    for block in blocks:
                        block = block.strip()
                        if not block:
                            continue

                        # Restore tables inside block
                        for placeholder, table in table_placeholders.items():
                            if placeholder in block:
                                global_idx += 1
                                chunks.append(Document(
                                    page_content=table['content'],
                                    metadata=build_payload(
                                        doc.metadata,
                                        part_title,
                                        section_title,
                                        subsection_title,
                                        "table",
                                        source_file,
                                        global_idx
                                    )
                                ))
                                block = block.replace(placeholder, "")

                        # Check if block is operation
                        if re.match(r'^Thao\s+tác\s+\d+[:\.]', block):
                            global_idx += 1
                            chunks.append(Document(
                                page_content=block,
                                metadata=build_payload(
                                    doc.metadata,
                                    part_title,
                                    section_title,
                                    subsection_title,
                                    "operation",
                                    source_file,
                                    global_idx
                                )
                            ))
                        elif block.strip():
                            # Text block → cắt nhỏ nếu dài
                            if len(block) > CHUNK_SIZE:
                                sub_blocks = split_long_block(block)
                                for sub_block in sub_blocks:
                                    global_idx += 1
                                    chunks.append(Document(
                                        page_content=sub_block,
                                        metadata=build_payload(
                                            doc.metadata,
                                            part_title,
                                            section_title,
                                            subsection_title,
                                            "text",
                                            source_file,
                                            global_idx
                                        )
                                    ))
                            else:
                                global_idx += 1
                                chunks.append(Document(
                                    page_content=block,
                                    metadata=build_payload(
                                        doc.metadata,
                                        part_title,
                                        section_title,
                                        subsection_title,
                                        "text",
                                        source_file,
                                        global_idx
                                    )
                                ))

    return chunks


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