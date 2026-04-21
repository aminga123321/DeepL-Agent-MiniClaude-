import sqlite3
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
import math

class BM25Index:
    """
    BM25 关键词库索引类
    """
    
    def __init__(self, db_path: str = "bm25_index.db"):
        """
        初始化 BM25 索引
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.k1 = 1.5  # BM25 参数
        self.b = 0.75   # BM25 参数
        self._init_db()
    
    def _init_db(self):
        """
        初始化数据库表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建文档表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            doc_id INTEGER PRIMARY KEY,
            doc_name TEXT UNIQUE,
            doc_path TEXT,
            doc_len INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建切分块表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id INTEGER PRIMARY KEY,
            doc_id INTEGER,
            chunk_content TEXT,
            chunk_len INTEGER,
            breadcrumbs TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
        )
        ''')
        
        # 创建关键词表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
            keyword_id INTEGER PRIMARY KEY,
            keyword TEXT UNIQUE
        )
        ''')
        
        # 创建倒排索引表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS inverted_index (
            id INTEGER PRIMARY KEY,
            keyword_id INTEGER,
            chunk_id INTEGER,
            tf REAL,
            FOREIGN KEY (keyword_id) REFERENCES keywords (keyword_id),
            FOREIGN KEY (chunk_id) REFERENCES chunks (chunk_id),
            UNIQUE (keyword_id, chunk_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 文本内容
            top_k: 返回前 K 个关键词
            
        Returns:
            关键词列表
        """
        # 简单的关键词提取：分词 + 频率统计
        # 实际应用中可以使用更复杂的方法，如 TF-IDF、TextRank 等
        
        # 去除标点符号，转换为小写
        text = re.sub(r'[\W_]', ' ', text)
        text = text.lower()
        
        # 分词
        words = text.split()
        
        # 过滤停用词
        stop_words = set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall', 'should',
            'can', 'could', 'may', 'might', 'must', 'ought', 'i', 'you', 'he', 'she',
            'it', 'we', 'they', 'this', 'that', 'these', 'those', 'there', 'here',
            'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few',
            'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will',
            'don', 'should', 'now'
        ])
        
        # 计算词频
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按词频排序，返回前 K 个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:top_k]]
    
    def add_document(self, doc_name: str, doc_path: str, chunks: List[Dict]):
        """
        添加文档到索引
        
        Args:
            doc_name: 文档名称
            doc_path: 文档路径
            chunks: 切分块列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 插入文档
            cursor.execute('''
            INSERT OR IGNORE INTO documents (doc_name, doc_path, doc_len) 
            VALUES (?, ?, ?)
            ''', (doc_name, doc_path, sum(len(chunk['content']) for chunk in chunks)))
            
            # 获取文档 ID
            cursor.execute('SELECT doc_id FROM documents WHERE doc_name = ?', (doc_name,))
            doc_id = cursor.fetchone()[0]
            
            # 插入切分块
            for chunk in chunks:
                breadcrumbs = ' > '.join(chunk.get('breadcrumbs', []))
                cursor.execute('''
                INSERT INTO chunks (doc_id, chunk_content, chunk_len, breadcrumbs) 
                VALUES (?, ?, ?, ?)
                ''', (doc_id, chunk['content'], len(chunk['content']), breadcrumbs))
                
                # 获取 chunk ID
                chunk_id = cursor.lastrowid
                
                # 提取关键词
                keywords = self._extract_keywords(chunk['content'], top_k=10)
                
                # 插入关键词和倒排索引
                for keyword in keywords:
                    # 插入关键词
                    cursor.execute('''
                    INSERT OR IGNORE INTO keywords (keyword) 
                    VALUES (?)
                    ''', (keyword,))
                    
                    # 获取关键词 ID
                    cursor.execute('SELECT keyword_id FROM keywords WHERE keyword = ?', (keyword,))
                    keyword_id = cursor.fetchone()[0]
                    
                    # 计算 TF（词频）
                    tf = chunk['content'].lower().count(keyword.lower()) / len(chunk['content'].split())
                    
                    # 插入倒排索引
                    cursor.execute('''
                    INSERT OR IGNORE INTO inverted_index (keyword_id, chunk_id, tf) 
                    VALUES (?, ?, ?)
                    ''', (keyword_id, chunk_id, tf))
            
            conn.commit()
            print(f"✅ 文档 {doc_name} 已添加到索引")
        except Exception as e:
            print(f"❌ 添加文档失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def build_index(self, chunks_dir: str):
        """
        从切分块目录构建索引
        
        Args:
            chunks_dir: 切分块目录
        """
        # 这里可以实现从切分块目录读取数据并构建索引的逻辑
        # 由于我们的切分块是在内存中生成的，这里暂时留空
        pass
    
    def search(self, query: str, top_n: int = 5) -> List[Dict]:
        """
        使用 BM25 搜索
        
        Args:
            query: 查询字符串
            top_n: 返回前 N 个结果
            
        Returns:
            搜索结果列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 提取查询关键词
            query_keywords = self._extract_keywords(query, top_k=10)
            if not query_keywords:
                return []
            
            # 获取平均文档长度
            cursor.execute('SELECT AVG(chunk_len) FROM chunks')
            avg_doc_len = cursor.fetchone()[0] or 1
            
            # 计算每个 chunk 的 BM25 分数
            chunk_scores = {}
            
            for keyword in query_keywords:
                # 获取关键词 ID
                cursor.execute('SELECT keyword_id FROM keywords WHERE keyword = ?', (keyword,))
                result = cursor.fetchone()
                if not result:
                    continue
                keyword_id = result[0]
                
                # 获取包含该关键词的 chunk
                cursor.execute('''
                SELECT chunk_id, tf FROM inverted_index WHERE keyword_id = ?
                ''', (keyword_id,))
                inverted_results = cursor.fetchall()
                
                # 计算 IDF
                cursor.execute('''
                SELECT COUNT(DISTINCT chunk_id) FROM inverted_index WHERE keyword_id = ?
                ''', (keyword_id,))
                df = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM chunks')
                total_docs = cursor.fetchone()[0]
                
                idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1)
                
                # 计算每个 chunk 的分数
                for chunk_id, tf in inverted_results:
                    # 获取 chunk 长度
                    cursor.execute('SELECT chunk_len FROM chunks WHERE chunk_id = ?', (chunk_id,))
                    chunk_len = cursor.fetchone()[0]
                    
                    # 计算 BM25 分数
                    score = idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * (chunk_len / avg_doc_len)))
                    
                    # 累加分数
                    if chunk_id in chunk_scores:
                        chunk_scores[chunk_id] += score
                    else:
                        chunk_scores[chunk_id] = score
            
            # 按分数排序
            sorted_chunks = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
            
            # 获取 chunk 详情
            results = []
            for chunk_id, score in sorted_chunks:
                cursor.execute('''
                SELECT c.chunk_content, c.breadcrumbs, d.doc_name 
                FROM chunks c 
                JOIN documents d ON c.doc_id = d.doc_id 
                WHERE c.chunk_id = ?
                ''', (chunk_id,))
                chunk_info = cursor.fetchone()
                if chunk_info:
                    results.append({
                        "content": chunk_info[0],
                        "breadcrumbs": chunk_info[1].split(' > ') if chunk_info[1] else [],
                        "source": chunk_info[2],
                        "score": score
                    })
            
            return results
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []
        finally:
            conn.close()
    
    def clear_index(self):
        """
        清空索引
        """
        conn = sqlite3.connect(self.db_path)
        
        try:
            # 清空所有表（不使用事务）
            conn.execute('DELETE FROM inverted_index')
            conn.execute('DELETE FROM keywords')
            conn.execute('DELETE FROM chunks')
            conn.execute('DELETE FROM documents')
            conn.commit()
            
            # 重置自增 ID（使用单独的连接）
            conn.close()
            conn = sqlite3.connect(self.db_path)
            conn.execute('VACUUM')
            conn.commit()
            
            print("✅ 索引已清空")
        except Exception as e:
            print(f"❌ 清空索引失败: {e}")
        finally:
            conn.close()
    
    def get_stats(self) -> Dict:
        """
        获取索引统计信息
        
        Returns:
            统计信息
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 文档数
            cursor.execute('SELECT COUNT(*) FROM documents')
            doc_count = cursor.fetchone()[0]
            
            # 切分块数
            cursor.execute('SELECT COUNT(*) FROM chunks')
            chunk_count = cursor.fetchone()[0]
            
            # 关键词数
            cursor.execute('SELECT COUNT(*) FROM keywords')
            keyword_count = cursor.fetchone()[0]
            
            # 倒排索引数
            cursor.execute('SELECT COUNT(*) FROM inverted_index')
            index_count = cursor.fetchone()[0]
            
            return {
                "doc_count": doc_count,
                "chunk_count": chunk_count,
                "keyword_count": keyword_count,
                "index_count": index_count
            }
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {}
        finally:
            conn.close()

# 创建 BM25 索引实例
bm25_index = BM25Index()
