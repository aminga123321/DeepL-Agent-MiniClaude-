"""
测试 Qdrant 客户端方法
"""

from qdrant_client import QdrantClient

client = QdrantClient(host='localhost', port=6333)

# 检查客户端方法
print("Qdrant 客户端可用方法:")
methods = [method for method in dir(client) if not method.startswith('_')]
for method in sorted(methods):
    print(f"  - {method}")

# 检查集合
print("\nQdrant 集合:")
try:
    collections = client.list_collections()
    print(f"  集合列表: {collections}")
except Exception as e:
    print(f"  错误: {e}")
