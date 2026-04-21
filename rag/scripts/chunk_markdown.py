"""
步骤 2：将 Markdown 按标题结构智能切分
"""

import json
from pathlib import Path
from typing import List, Dict
import sys

sys.path.insert(0, str(Path(__file__).parent))
from config import MARKDOWN_DIR, CHUNKS_DIR, CHUNK_SIZE, MIN_CHUNK_SIZE


def chunk_by_headers(md_text: str) -> List[Dict]:
    """
    按标题层级切分 Markdown
    使用 LangChain 的 MarkdownHeaderTextSplitter
    """
    from langchain_text_splitters import MarkdownHeaderTextSplitter
    
    # 定义要切分的标题层级
    headers_to_split_on = [
        ("#", "title"),
        ("##", "section"),
        ("###", "subsection"),
    ]
    
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
    splits = splitter.split_text(md_text)
    
    chunks = []
    for i, split in enumerate(splits):
        # 构建面包屑路径
        breadcrumbs = []
        if split.metadata.get("title"):
            breadcrumbs.append(split.metadata["title"])
        if split.metadata.get("section"):
            breadcrumbs.append(split.metadata["section"])
        if split.metadata.get("subsection"):
            breadcrumbs.append(split.metadata["subsection"])
        
        chunk = {
            "id": f"chunk_{i:04d}",
            "content": split.page_content.strip(),
            "metadata": {
                "breadcrumbs": breadcrumbs,
                "title": split.metadata.get("title", ""),
                "section": split.metadata.get("section", ""),
                "subsection": split.metadata.get("subsection", ""),
                "source": "",
                "page": None,
                "chunk_type": "section",
                "length": len(split.page_content)
            }
        }
        chunks.append(chunk)
    
    return chunks


def merge_small_chunks(chunks: List[Dict], min_size: int = MIN_CHUNK_SIZE) -> List[Dict]:
    """合并太小的 chunk 到前一个"""
    if not chunks:
        return chunks
    
    merged = []
    current = chunks[0].copy()
    
    for chunk in chunks[1:]:
        if len(current["content"]) < min_size:
            # 合并到当前 chunk
            current["content"] += "\n\n" + chunk["content"]
            current["metadata"]["length"] = len(current["content"])
            current["metadata"]["chunk_type"] = "merged"
        else:
            merged.append(current)
            current = chunk.copy()
    
    merged.append(current)
    return merged


def add_prefix_to_chunks(chunks: List[Dict]) -> List[Dict]:
    """为每个 chunk 添加面包屑前缀"""
    for chunk in chunks:
        breadcrumbs = chunk["metadata"]["breadcrumbs"]
        if breadcrumbs:
            prefix = " > ".join(breadcrumbs)
            chunk["content"] = f"[{prefix}]\n\n{chunk['content']}"
            chunk["metadata"]["has_prefix"] = True
    return chunks


def main():
    """处理所有 Markdown 文件"""
    md_files = list(MARKDOWN_DIR.glob("*.md"))
    
    if not md_files:
        print(f"❌ 没有找到 Markdown 文件，请先运行 1_convert_pdf_to_md.py")
        return
    
    all_chunks = []
    
    for md_path in md_files:
        print(f"正在切分: {md_path.name}")
        
        # 读取 Markdown
        md_text = md_path.read_text(encoding="utf-8")
        
        # 按标题切分
        chunks = chunk_by_headers(md_text)
        print(f"  初始切分: {len(chunks)} 个片段")
        
        # 合并小片段
        chunks = merge_small_chunks(chunks)
        print(f"  合并后: {len(chunks)} 个片段")
        
        # 添加前缀
        chunks = add_prefix_to_chunks(chunks)
        
        # 添加 source 信息
        for chunk in chunks:
            chunk["metadata"]["source"] = md_path.name
        
        all_chunks.extend(chunks)
    
    # 保存结果
    output_path = CHUNKS_DIR / "all_chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    
    # 统计信息
    lengths = [c["metadata"]["length"] for c in all_chunks]
    
    print(f"\n{'='*50}")
    print(f"✅ 切分完成！")
    print(f"   总片段数: {len(all_chunks)}")
    print(f"   平均长度: {sum(lengths)//len(lengths) if lengths else 0} 字符")
    print(f"   最短: {min(lengths) if lengths else 0} 字符")
    print(f"   最长: {max(lengths) if lengths else 0} 字符")
    print(f"   保存位置: {output_path}")


if __name__ == "__main__":
    main()