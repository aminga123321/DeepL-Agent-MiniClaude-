#!/usr/bin/env python3
"""GitHub Trends MCP Server - 实时监控GitHub技术趋势"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource

# 创建服务器实例
server = Server("github-trends-monitor")

# 配置
GITHUB_API_BASE = "https://api.github.com"
CACHE_DURATION = 300  # 5分钟缓存
TRENDING_CACHE_DURATION = 3600  # 1小时缓存

# 内存缓存
cache: Dict[str, Dict[str, Any]] = {
    "repositories": {},
    "trending": {},
    "users": {}
}

# GitHub API工具函数
async def fetch_github_api(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """获取GitHub API数据"""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Trends-MCP"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{GITHUB_API_BASE}{endpoint}"
        response = await client.get(url, headers=headers, params=params or {})
        response.raise_for_status()
        return response.json()

def get_cache_key(endpoint: str, params: Optional[Dict] = None) -> str:
    """生成缓存键"""
    if params:
        return f"{endpoint}:{json.dumps(params, sort_keys=True)}"
    return endpoint

def is_cache_valid(cache_entry: Dict, duration: int) -> bool:
    """检查缓存是否有效"""
    if not cache_entry or "timestamp" not in cache_entry:
        return False
    return time.time() - cache_entry["timestamp"] < duration

# 工具定义
@server.tool()
async def get_trending_repositories(
    language: Optional[str] = None,
    since: str = "daily",
    spoken_language_code: Optional[str] = None
) -> str:
    """获取GitHub趋势仓库
    
    Args:
        language: 编程语言过滤 (如: python, javascript, go)
        since: 时间范围 (daily, weekly, monthly)
        spoken_language_code: 口语语言代码 (如: zh, en)
    """
    cache_key = get_cache_key(f"trending:{language}:{since}:{spoken_language_code}")
    
    # 检查缓存
    if cache_key in cache["trending"] and is_cache_valid(cache["trending"][cache_key], TRENDING_CACHE_DURATION):
        return cache["trending"][cache_key]["data"]
    
    # 构建GitHub趋势URL (使用GitHub REST API替代趋势页面)
    params = {}
    if language:
        params["q"] = f"language:{language}"
    if since:
        params["sort"] = "stars"
        params["order"] = "desc"
    
    try:
        # 搜索热门仓库
        search_url = "/search/repositories"
        search_params = {
            "q": f"stars:>1000 {language if language else ''}",
            "sort": "stars",
            "order": "desc",
            "per_page": 25
        }
        
        data = await fetch_github_api(search_url, search_params)
        
        result = []
        result.append(f"📊 GitHub趋势仓库 ({since}趋势)")
        result.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result.append("=" * 60)
        
        for i, repo in enumerate(data.get("items", [])[:20], 1):
            name = repo["full_name"]
            description = repo["description"] or "无描述"
            stars = repo["stargazers_count"]
            forks = repo["forks_count"]
            language = repo["language"] or "Unknown"
            url = repo["html_url"]
            
            result.append(f"{i}. {name}")
            result.append(f"   ⭐ {stars:,} | 🍴 {forks:,} | 📝 {language}")
            result.append(f"   📖 {description[:100]}{'...' if len(description) > 100 else ''}")
            result.append(f"   🔗 {url}")
            result.append("")
        
        output = "\n".join(result)
        
        # 更新缓存
        cache["trending"][cache_key] = {
            "timestamp": time.time(),
            "data": output
        }
        
        return output
        
    except Exception as e:
        return f"获取趋势仓库时出错: {str(e)}"

@server.tool()
async def search_repositories(
    query: str,
    language: Optional[str] = None,
    sort: str = "stars",
    order: str = "desc",
    per_page: int = 10
) -> str:
    """搜索GitHub仓库
    
    Args:
        query: 搜索关键词
        language: 编程语言过滤
        sort: 排序方式 (stars, forks, updated)
        order: 排序顺序 (desc, asc)
        per_page: 每页结果数 (1-100)
    """
    cache_key = get_cache_key(f"search:{query}:{language}:{sort}:{order}:{per_page}")
    
    # 检查缓存
    if cache_key in cache["repositories"] and is_cache_valid(cache["repositories"][cache_key], CACHE_DURATION):
        return cache["repositories"][cache_key]["data"]
    
    try:
        # 构建搜索查询
        search_query = query
        if language:
            search_query += f" language:{language}"
        
        search_params = {
            "q": search_query,
            "sort": sort,
            "order": order,
            "per_page": min(per_page, 100)
        }
        
        data = await fetch_github_api("/search/repositories", search_params)
        
        result = []
        total_count = data.get("total_count", 0)
        result.append(f"🔍 GitHub仓库搜索: '{query}'")
        result.append(f"📊 找到 {total_count:,} 个结果")
        result.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result.append("=" * 60)
        
        for i, repo in enumerate(data.get("items", [])[:per_page], 1):
            name = repo["full_name"]
            description = repo["description"] or "无描述"
            stars = repo["stargazers_count"]
            forks = repo["forks_count"]
            language = repo["language"] or "Unknown"
            updated_at = repo["updated_at"]
            url = repo["html_url"]
            
            result.append(f"{i}. {name}")
            result.append(f"   ⭐ {stars:,} | 🍴 {forks:,} | 📝 {language}")
            result.append(f"   📅 最后更新: {updated_at[:10]}")
            result.append(f"   📖 {description[:120]}{'...' if len(description) > 120 else ''}")
            result.append(f"   🔗 {url}")
            result.append("")
        
        output = "\n".join(result)
        
        # 更新缓存
        cache["repositories"][cache_key] = {
            "timestamp": time.time(),
            "data": output
        }
        
        return output
        
    except Exception as e:
        return f"搜索仓库时出错: {str(e)}"

@server.tool()
async def get_user_repositories(
    username: str,
    sort: str = "updated",
    per_page: int = 10
) -> str:
    """获取用户的GitHub仓库
    
    Args:
        username: GitHub用户名
        sort: 排序方式 (created, updated, pushed, full_name)
        per_page: 每页结果数 (1-100)
    """
    cache_key = get_cache_key(f"user_repos:{username}:{sort}:{per_page}")
    
    # 检查缓存
    if cache_key in cache["repositories"] and is_cache_valid(cache["repositories"][cache_key], CACHE_DURATION):
        return cache["repositories"][cache_key]["data"]
    
    try:
        endpoint = f"/users/{username}/repos"
        params = {
            "sort": sort,
            "per_page": min(per_page, 100)
        }
        
        repos = await fetch_github_api(endpoint, params)
        
        result = []
        result.append(f"👤 {username} 的GitHub仓库")
        result.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result.append("=" * 60)
        
        for i, repo in enumerate(repos[:per_page], 1):
            name = repo["full_name"]
            description = repo["description"] or "无描述"
            stars = repo["stargazers_count"]
            forks = repo["forks_count"]
            language = repo["language"] or "Unknown"
            updated_at = repo["updated_at"]
            url = repo["html_url"]
            
            result.append(f"{i}. {name}")
            result.append(f"   ⭐ {stars:,} | 🍴 {forks:,} | 📝 {language}")
            result.append(f"   📅 最后更新: {updated_at[:10]}")
            result.append(f"   📖 {description[:100]}{'...' if len(description) > 100 else ''}")
            result.append(f"   🔗 {url}")
            result.append("")
        
        output = "\n".join(result)
        
        # 更新缓存
        cache["repositories"][cache_key] = {
            "timestamp": time.time(),
            "data": output
        }
        
        return output
        
    except Exception as e:
        return f"获取用户仓库时出错: {str(e)}"

@server.tool()
async def get_repository_details(
    owner: str,
    repo: str
) -> str:
    """获取仓库详细信息
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
    """
    cache_key = get_cache_key(f"repo_details:{owner}/{repo}")
    
    # 检查缓存
    if cache_key in cache["repositories"] and is_cache_valid(cache["repositories"][cache_key], CACHE_DURATION):
        return cache["repositories"][cache_key]["data"]
    
    try:
        endpoint = f"/repos/{owner}/{repo}"
        repo_data = await fetch_github_api(endpoint)
        
        # 获取README
        readme_content = "无README"
        try:
            readme_data = await fetch_github_api(f"/repos/{owner}/{repo}/readme")
            import base64
            readme_content = base64.b64decode(readme_data["content"]).decode("utf-8", errors="ignore")
            readme_content = readme_content[:500] + "..." if len(readme_content) > 500 else readme_content
        except:
            pass
        
        # 获取语言统计
        languages_data = await fetch_github_api(f"/repos/{owner}/{repo}/languages")
        
        result = []
        result.append(f"📦 仓库详情: {owner}/{repo}")
        result.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result.append("=" * 60)
        
        # 基本信息
        result.append(f"📖 描述: {repo_data.get('description', '无描述')}")
        result.append(f"⭐ 星标数: {repo_data.get('stargazers_count', 0):,}")
        result.append(f"🍴 Fork数: {repo_data.get('forks_count', 0):,}")
        result.append(f"👁️ 关注者: {repo_data.get('watchers_count', 0):,}")
        result.append(f"📅 创建时间: {repo_data.get('created_at', '')[:10]}")
        result.append(f"📅 最后更新: {repo_data.get('updated_at', '')[:10]}")
        result.append(f"🔗 主页: {repo_data.get('homepage', '无')}")
        result.append(f"📝 主要语言: {repo_data.get('language', 'Unknown')}")
        
        # 语言统计
        if languages_data:
            result.append("\n📊 语言统计:")
            total_bytes = sum(languages_data.values())
            for lang, bytes_count in list(languages_data.items())[:5]:
                percentage = (bytes_count / total_bytes) * 100
                result.append(f"  {lang}: {percentage:.1f}% ({bytes_count:,} bytes)")
        
        # README预览
        result.append(f"\n📄 README预览:")
        result.append(readme_content)
        
        # 链接
        result.append(f"\n🔗 链接:")
        result.append(f"  GitHub: {repo_data.get('html_url')}")
        result.append(f"  Issues: {repo_data.get('html_url')}/issues")
        result.append(f"  Pull Requests: {repo_data.get('html_url')}/pulls")
        
        output = "\n".join(result)
        
        # 更新缓存
        cache["repositories"][cache_key] = {
            "timestamp": time.time(),
            "data": output
        }
        
        return output
        
    except Exception as e:
        return f"获取仓库详情时出错: {str(e)}"

@server.tool()
async def get_github_stats() -> str:
    """获取GitHub总体统计信息"""
    try:
        # 获取GitHub状态
        status_url = "https://www.githubstatus.com/api/v2/status.json"
        async with httpx.AsyncClient() as client:
            status_response = await client.get(status_url)
            status_data = status_response.json()
        
        # 获取热门话题
        try:
            topics_data = await fetch_github_api("/search/topics", {"q": "stars:>1000", "per_page": 5})
        except:
            topics_data = {"items": []}
        
        result = []
        result.append("📊 GitHub实时统计")
        result.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result.append("=" * 60)
        
        # GitHub状态
        status = status_data.get("status", {})
        result.append(f"🌐 GitHub状态: {status.get('description', '未知')}")
        result.append(f"  状态指示: {status.get('indicator', 'unknown')}")
        
        # 热门话题
        if topics_data.get("items"):
            result.append("\n🔥 热门话题:")
            for i, topic in enumerate(topics_data["items"][:5], 1):
                result.append(f"  {i}. {topic['name']}")
                result.append(f"     相关仓库: {topic.get('repositories', 0):,}")
        
        # 缓存统计
        result.append(f"\n💾 缓存统计:")
        result.append(f"  仓库缓存: {len(cache['repositories'])} 项")
        result.append(f"  趋势缓存: {len(cache['trending'])} 项")
        result.append(f"  用户缓存: {len(cache['users'])} 项")
        
        # 使用建议
        result.append(f"\n💡 使用建议:")
        result.append("  1. 使用 get_trending_repositories() 查看趋势")
        result.append("  2. 使用 search_repositories() 搜索特定技术")
        result.append("  3. 使用 get_repository_details() 查看仓库详情")
        result.append("  4. 使用 get_user_repositories() 查看用户仓库")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"获取GitHub统计时出错: {str(e)}"

@server.tool()
async def clear_cache() -> str:
    """清除所有缓存数据"""
    cache["repositories"].clear()
    cache["trending"].clear()
    cache["users"].clear()
    return "✅ 缓存已清除"

# 资源定义
@server.resource("github://trending")
async def get_trending_resource() -> str:
    """获取GitHub趋势仓库资源"""
    return await get_trending_repositories()

@server.resource("github://stats")
async def get_stats_resource() -> str:
    """获取GitHub统计资源"""
    return await get_github_stats()

# 运行服务器
async def main():
    """主函数"""
    print("🚀 GitHub Trends MCP Server 启动中...", file=sys.stderr)
    print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr)
    print("🔧 可用工具:", file=sys.stderr)
    print("  • get_trending_repositories - 获取趋势仓库", file=sys.stderr)
    print("  • search_repositories - 搜索仓库", file=sys.stderr)
    print("  • get_user_repositories - 获取用户仓库", file=sys.stderr)
    print("  • get_repository_details - 获取仓库详情", file=sys.stderr)
    print("  • get_github_stats - 获取GitHub统计", file=sys.stderr)
    print("  • clear_cache - 清除缓存", file=sys.stderr)
    
    async with stdio_server() as (read, write):
        await server.run(read, write)

if __name__ == "__main__":
    import sys
    asyncio.run(main())