"""
步骤 1：将 PDF 转换为 Markdown
"""

import pymupdf4llm
from pathlib import Path
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from config import RAW_DIR, MARKDOWN_DIR, IMAGES_DIR


def convert_pdf_to_markdown(pdf_path: Path, output_path: Path) -> str:
    """
    将 PDF 转换为 Markdown
    - 提取图片并保存到 images 目录
    - 保留表格、公式等结构
    """
    print(f"正在转换: {pdf_path.name}")
    
    # 转换 PDF 为 Markdown
    md_text = pymupdf4llm.to_markdown(
        str(pdf_path),
        # page_chunks=True,           # 分页处理
        write_images=True,          # 提取图片
        image_path=str(IMAGES_DIR), # 图片保存目录
        image_format="png",         # 图片格式
        dpi=150,                    # 图片分辨率
    )
    
    # 保存 Markdown 文件
    output_path.write_text(md_text, encoding="utf-8")
    print(f"✅ 已保存: {output_path}")
    print(f"   大小: {len(md_text)} 字符")
    
    return md_text


def main():
    """转换所有 PDF 文件"""
    # 获取所有 PDF 文件
    pdf_files = list(RAW_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ 没有找到 PDF 文件，请把 PDF 放到 {RAW_DIR}")
        return
    
    print(f"找到 {len(pdf_files)} 个 PDF 文件\n")
    
    for pdf_path in pdf_files:
        # 输出 Markdown 文件名
        md_name = pdf_path.stem + ".md"
        md_path = MARKDOWN_DIR / md_name
        
        try:
            convert_pdf_to_markdown(pdf_path, md_path)
            print()
        except Exception as e:
            print(f"❌ 转换失败: {pdf_path.name}, 错误: {e}\n")


if __name__ == "__main__":
    main()