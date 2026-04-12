# test_chunking.py
from langchain_text_splitters import MarkdownHeaderTextSplitter
import json

# 读取你的 Markdown 文件
with open("data/markdown/visual_encoder.md", "r", encoding="utf-8") as f:
    md_text = f.read()

# 配置标题层级
headers_to_split_on = [
    ("#", "title"),
    ("##", "section"),
    ("###", "subsection"),
]

splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
chunks = splitter.split_text(md_text)

# 输出统计
print(f"总共切分成 {len(chunks)} 个片段\n")

# 查看前 5 个片段
for i, chunk in enumerate(chunks[:5]):
    print(f"=== Chunk {i+1} ===")
    print(f"标题: {chunk.metadata}")
    print(f"内容长度: {len(chunk.page_content)} 字符")
    print(f"内容预览: {chunk.page_content[:200]}...")
    print("-" * 50)

# 保存结果到 JSON，方便查看
results = []
for i, chunk in enumerate(chunks):
    results.append({
        "index": i,
        "metadata": chunk.metadata,
        "content": chunk.page_content,
        "length": len(chunk.page_content)
    })

with open("data/chunks/chunk_test.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n完整结果已保存到 data/chunks/chunk_test.json")