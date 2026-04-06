# GitHub Trends MCP Server

一个用于实时监控GitHub技术趋势的MCP服务器。

## 功能特性

- 🔍 **实时趋势监控**: 获取GitHub热门仓库趋势
- 📊 **仓库搜索**: 按技术、语言、关键词搜索仓库
- 👤 **用户分析**: 查看用户的仓库和活动
- 📦 **仓库详情**: 获取仓库详细信息、README、语言统计
- 💾 **智能缓存**: 自动缓存API响应，减少请求
- 📈 **统计信息**: 获取GitHub总体状态和统计

## 安装

### 1. 安装依赖

```bash
cd skills/github-trends-monitor
pip install -r requirements.txt
```

### 2. 配置环境变量

复制环境变量示例文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，添加GitHub Token（可选）：

```env
GITHUB_TOKEN=your_github_token_here
```

## 注册到Claude

在 `~/.claude/mcp.json` 中添加以下配置：

```json
{
  "mcpServers": {
    "github-trends-monitor": {
      "command": "python",
      "args": ["D:/agent/DeepL_Agent/backend/skills/github-trends-monitor/github_trends_mcp.py"]
    }
  }
}
```

## 可用工具

### 1. get_trending_repositories
获取GitHub趋势仓库

**参数:**
- `language` (可选): 编程语言过滤 (如: python, javascript, go)
- `since` (可选): 时间范围 (daily, weekly, monthly)，默认: daily
- `spoken_language_code` (可选): 口语语言代码 (如: zh, en)

**示例:**
```
获取Python语言的每日趋势仓库
```

### 2. search_repositories
搜索GitHub仓库

**参数:**
- `query`: 搜索关键词
- `language` (可选): 编程语言过滤
- `sort` (可选): 排序方式 (stars, forks, updated)，默认: stars
- `order` (可选): 排序顺序 (desc, asc)，默认: desc
- `per_page` (可选): 每页结果数 (1-100)，默认: 10

**示例:**
```
搜索包含"machine learning"的Python仓库
```

### 3. get_user_repositories
获取用户的GitHub仓库

**参数:**
- `username`: GitHub用户名
- `sort` (可选): 排序方式 (created, updated, pushed, full_name)，默认: updated
- `per_page` (可选): 每页结果数 (1-100)，默认: 10

**示例:**
```
获取用户"torvalds"的仓库
```

### 4. get_repository_details
获取仓库详细信息

**参数:**
- `owner`: 仓库所有者
- `repo`: 仓库名称

**示例:**
```
获取"facebook/react"仓库的详细信息
```

### 5. get_github_stats
获取GitHub总体统计信息

**示例:**
```
获取GitHub当前状态和统计
```

### 6. clear_cache
清除所有缓存数据

**示例:**
```
清除缓存
```

## 可用资源

### 1. github://trending
获取GitHub趋势仓库资源

### 2. github://stats
获取GitHub统计资源

## 使用示例

### 1. 查看Python趋势
```
获取Python语言的GitHub趋势仓库
```

### 2. 搜索AI相关项目
```
搜索包含"artificial intelligence"的仓库，按星标排序
```

### 3. 查看用户项目
```
获取用户"microsoft"的最新仓库
```

### 4. 分析具体项目
```
获取"openai/gpt-3"仓库的详细信息
```

## 缓存机制

- **仓库搜索**: 5分钟缓存
- **趋势数据**: 1小时缓存
- **用户数据**: 5分钟缓存

使用 `clear_cache` 工具可以手动清除缓存。

## 注意事项

1. **API限制**: 未使用GitHub Token时，API请求限制为60次/小时
2. **网络连接**: 需要稳定的网络连接访问GitHub API
3. **数据延迟**: 趋势数据可能有1-2小时的延迟
4. **缓存策略**: 合理使用缓存避免频繁请求

## 故障排除

### 1. 服务器无法启动
- 检查Python版本 (需要Python 3.8+)
- 检查依赖是否安装完整
- 检查文件路径是否正确

### 2. API请求失败
- 检查网络连接
- 检查GitHub API状态: https://www.githubstatus.com/
- 检查GitHub Token是否有效

### 3. 数据不更新
- 使用 `clear_cache` 清除缓存
- 检查缓存配置时间

## 开发

### 添加新功能
1. 在 `github_trends_mcp.py` 中添加新的工具函数
2. 使用 `@server.tool()` 装饰器注册工具
3. 更新README文档

### 测试
```bash
# 测试服务器启动
python github_trends_mcp.py

# 使用MCP Inspector测试
npx @anthropics/mcp-inspector python github_trends_mcp.py
```

## 许可证

MIT License