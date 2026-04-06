"""GitHub Trends MCP 配置"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# GitHub API配置
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# 缓存配置
CACHE_DURATION = int(os.getenv("CACHE_DURATION", "300"))  # 5分钟
TRENDING_CACHE_DURATION = int(os.getenv("TRENDING_CACHE_DURATION", "3600"))  # 1小时

# 请求限制
MAX_PER_PAGE = 100
REQUEST_TIMEOUT = 30.0

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 服务器配置
SERVER_NAME = "github-trends-monitor"
SERVER_VERSION = "1.0.0"