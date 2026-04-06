# GitHub Trends MCP 快速开始

## 1. 安装

```bash
# 进入目录
cd skills/github-trends-monitor

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件，添加GitHub Token
```

## 2. 启动服务器

```bash
# 方法1: 直接运行
python github_trends_mcp.py

# 方法2: 使用批处理文件（Windows）
start_server.bat
```

## 3. 注册到Claude

编辑 `~/.claude/mcp.json` 文件，添加：

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

## 4. 重启Claude

重启Claude桌面应用，使配置生效。

## 5. 开始使用

在Claude中，您现在可以使用以下命令：

### 查看趋势
```
获取GitHub上Python语言的趋势仓库
```

### 搜索项目
```
搜索包含"deep learning"的Python项目
```

### 查看用户
```
获取用户"google"的GitHub仓库
```

### 查看详情
```
获取"microsoft/vscode"仓库的详细信息
```

### 获取统计
```
获取GitHub的当前状态和统计信息
```

## 6. 常见问题

### Q: 服务器无法启动？
A: 检查Python版本（需要3.8+），检查依赖是否安装。

### Q: Claude无法连接？
A: 检查MCP配置文件路径是否正确，重启Claude。

### Q: API请求失败？
A: 检查网络连接，或添加GitHub Token提高限制。

## 7. 高级功能

### 使用GitHub Token
1. 在GitHub设置中创建Token
2. 在 `.env` 文件中设置 `GITHUB_TOKEN`
3. 重启服务器

### 调整缓存时间
编辑 `.env` 文件：
```env
CACHE_DURATION=600  # 10分钟
TRENDING_CACHE_DURATION=7200  # 2小时
```

## 8. 获取帮助

查看完整文档：
```bash
cat README.md
```

测试服务器：
```bash
python test_mcp.py
```