#!/usr/bin/env python3
"""测试GitHub Trends MCP服务器"""

import asyncio
import json
import sys

async def test_server():
    """测试服务器功能"""
    print("🧪 测试GitHub Trends MCP服务器...")
    
    # 测试数据
    test_cases = [
        {
            "name": "获取趋势仓库",
            "method": "tools/call",
            "params": {
                "name": "get_trending_repositories",
                "arguments": {"language": "python", "since": "daily"}
            }
        },
        {
            "name": "搜索仓库",
            "method": "tools/call",
            "params": {
                "name": "search_repositories",
                "arguments": {"query": "machine learning", "language": "python"}
            }
        },
        {
            "name": "获取GitHub统计",
            "method": "tools/call",
            "params": {
                "name": "get_github_stats",
                "arguments": {}
            }
        }
    ]
    
    # 模拟MCP消息
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试 {i}: {test_case['name']}")
        print(f"  方法: {test_case['method']}")
        print(f"  参数: {json.dumps(test_case['params'], indent=2)}")
        
        # 这里可以添加实际的MCP客户端测试代码
        # 目前只显示测试用例
        
    print("\n✅ 测试用例准备完成")
    print("📝 要实际测试，请使用MCP Inspector:")
    print("   npx @anthropics/mcp-inspector python github_trends_mcp.py")

def main():
    """主函数"""
    print("=" * 60)
    print("GitHub Trends MCP 服务器测试")
    print("=" * 60)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return
    
    # 检查依赖
    try:
        import mcp
        import httpx
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("📦 请运行: pip install -r requirements.txt")
        return
    
    # 运行测试
    asyncio.run(test_server())
    
    print("\n" + "=" * 60)
    print("📚 使用说明:")
    print("  1. 启动服务器: python github_trends_mcp.py")
    print("  2. 注册到Claude: 编辑 ~/.claude/mcp.json")
    print("  3. 测试工具: 在Claude中调用工具")
    print("=" * 60)

if __name__ == "__main__":
    main()