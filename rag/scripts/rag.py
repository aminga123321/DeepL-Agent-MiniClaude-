import os
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Any

# 导入现有模块
from scripts.config import (
    RAW_DIR, MARKDOWN_DIR, COLLECTION_NAME,
    EMBEDDING_MODEL, DASHSCOPE_API_KEY, DEEPSEEK_API_KEY, DEEPSEEK_MODEL
)
from scripts.convert_pdf_to_md import convert_pdf_to_markdown
from scripts.chunk_markdown import chunk_by_headers
from scripts.store_to_qdrant import store_chunks_to_qdrant
from scripts.fusion import multi_channel_recall
from scripts.rerank import rerank_results, generate_answer

class RAG:
    """
    RAG 系统类，封装了知识库构建和智能检索的功能
    """
    
    def __init__(self):
        """
        初始化 RAG 系统
        """
        # 确保目录存在
        Path(MARKDOWN_DIR).mkdir(parents=True, exist_ok=True)
    
    def build_knowledge_base(self, pdf_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        构建知识库
        
        Args:
            pdf_paths: PDF 文件路径列表，如果为 None，则处理 PDF_DIR 目录下的所有 PDF 文件
            
        Returns:
            构建结果
        """
        result = {
            "conversion": {},
            "chunking": {},
            "storage": {},
            "bm25_index": {}
        }
        
        # 确定要处理的 PDF 文件
        if pdf_paths:
            pdf_files = pdf_paths
        else:
            pdf_files = list(Path(RAW_DIR).glob("*.pdf"))
        
        # 转换 PDF 到 Markdown
        for pdf_file in pdf_files:
            pdf_path = str(pdf_file)
            md_path = os.path.join(MARKDOWN_DIR, f"{os.path.basename(pdf_file).replace('.pdf', '.md')}")
            
            try:
                convert_pdf_to_markdown(Path(pdf_path), Path(md_path))
                result["conversion"][pdf_path] = "success"
            except Exception as e:
                result["conversion"][pdf_path] = f"error: {str(e)}"
        
        # 切分 Markdown 并存储到 Qdrant
        all_chunks = []
        for md_file in Path(MARKDOWN_DIR).glob("*.md"):
            md_path = str(md_file)
            
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
                
                chunks = chunk_by_headers(md_content)
                all_chunks.extend(chunks)
                result["chunking"][md_path] = f"success: {len(chunks)} chunks"
            except Exception as e:
                result["chunking"][md_path] = f"error: {str(e)}"
        
        # 存储到 Qdrant
        if all_chunks:
            try:
                store_result = store_chunks_to_qdrant(all_chunks)
                result["storage"] = store_result
            except Exception as e:
                result["storage"] = f"error: {str(e)}"
        
        # 构建 BM25 索引
        try:
            from scripts.bm25_index import bm25_index
            
            # 清空旧索引
            bm25_index.clear_index()
            
            # 按文档分组 chunks
            docs = {}
            for chunk in all_chunks:
                source = chunk["metadata"].get("source", "unknown.md")
                if source not in docs:
                    docs[source] = []
                docs[source].append(chunk)
            
            # 添加每个文档到 BM25 索引
            for doc_name, doc_chunks in docs.items():
                doc_path = str(Path(MARKDOWN_DIR) / doc_name)
                bm25_index.add_document(doc_name, doc_path, doc_chunks)
            
            # 打印索引统计信息
            stats = bm25_index.get_stats()
            result["bm25_index"] = stats
            print(f"\n📊 BM25 索引统计: {stats}")
        except Exception as e:
            result["bm25_index"] = f"error: {str(e)}"
            print(f"❌ BM25 索引构建失败: {e}")
        
        return result
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        执行多路召回
        
        Args:
            query: 查询字符串
            top_k: 检索返回的文档数
            
        Returns:
            检索到的文档列表
        """
        return multi_channel_recall(query, top_n=top_k)
    
    def rag_pipeline(self, query: str, top_k: int = 5, rerank_top_k: int = 3) -> Dict[str, Any]:
        """
        完整 RAG 流程
        
        Args:
            query: 查询字符串
            top_k: 检索返回的文档数
            rerank_top_k: 重排后保留的文档数
            
        Returns:
            RAG 流程结果
        """
        print("🔍 执行 RAG 流程")
        
        # 执行多路召回
        retrieved_docs = self.retrieve(query, top_k=top_k)
        
        # 重排
        reranked_docs = rerank_results(query, retrieved_docs, top_k=rerank_top_k)
        
        # 生成回答
        answer = generate_answer(query, reranked_docs)
        
        # 构建结果
        result = {
            "query": query,
            "retrieved_docs": reranked_docs,
            "answer": answer,
            "timestamp": time.time()
        }
        
        return result

# 创建 RAG 实例
rag_system = RAG()
