import re
from typing import List, Dict
from langchain.docstore.document import Document
from .config import CHUNK_SIZE, CHUNK_OVERLAP

def chunk_documents(docs: List[Document]) -> List[Document]:
    """
    Chunking tài liệu nâng cao:
    - Part → Section → Subsection
    - Extract tables → chunk type 'table'
    - Extract operation blocks → chunk type 'operation'
    - Text còn lại → chunk type 'text', chia theo CHUNK_SIZE + CHUNK_OVERLAP
    """
    chunks = []

    for doc in docs:
        text = doc.page_content.strip()
        if not text:
            continue

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
                subsections = re.split(r'(?m)^\d+\.\d+\.\d+\s+[^\n]+', section)
                subsection_titles = re.findall(r'(?m)^\d+\.\d+\.\d+\s+[^\n]+', section)
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
                                chunks.append(Document(
                                    page_content=table['content'],
                                    metadata={
                                        **doc.metadata,
                                        "part": part_title,
                                        "section": section_title,
                                        "subsection": subsection_title,
                                        "type": "table"
                                    }
                                ))
                                block = block.replace(placeholder, "")

                        # Check if block is operation
                        if re.match(r'^Thao\s+tác\s+\d+[:\.]', block):
                            chunks.append(Document(
                                page_content=block,
                                metadata={
                                    **doc.metadata,
                                    "part": part_title,
                                    "section": section_title,
                                    "subsection": subsection_title,
                                    "type": "operation"
                                }
                            ))
                        elif block.strip():
                            # Text block → cắt nhỏ nếu dài
                            if len(block) > CHUNK_SIZE:
                                sub_blocks = split_long_block(block)
                                for sub_block in sub_blocks:
                                    chunks.append(Document(
                                        page_content=sub_block,
                                        metadata={
                                            **doc.metadata,
                                            "part": part_title,
                                            "section": section_title,
                                            "subsection": subsection_title,
                                            "type": "text"
                                        }
                                    ))
                            else:
                                chunks.append(Document(
                                    page_content=block,
                                    metadata={
                                        **doc.metadata,
                                        "part": part_title,
                                        "section": section_title,
                                        "subsection": subsection_title,
                                        "type": "text"
                                    }
                                ))

    return chunks


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