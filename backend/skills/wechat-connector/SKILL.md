---
name: wechat-connector
description: |
  微信消息处理和自动回复系统。使用场景：
  (1) 需要处理微信消息，自动回复特定联系人
  (2) 需要监控微信消息，根据关键词触发回复
  (3) 需要设置微信消息自动转发或通知
  (4) 需要创建微信机器人或自动化助手
  (5) 需要集成微信消息到其他系统
  关键词：微信、wechat、消息处理、自动回复、机器人、自动化、联系人、关键词
---

# 微信连接器 - 消息处理与自动回复

专业的微信消息处理和自动回复系统，支持特定联系人、关键词触发、定时回复等功能。

## 核心功能

### 1. 消息监听与处理
- 实时监听微信消息
- 支持文本、图片、语音、文件等多种消息类型
- 消息内容解析和格式化

### 2. 联系人管理
- 特定联系人识别
- 联系人分组管理
- 黑白名单设置

### 3. 自动回复规则
- 基于联系人的自动回复
- 基于关键词的触发回复
- 定时自动回复
- 智能回复模板

### 4. 消息转发与通知
- 重要消息转发到其他平台
- 消息通知到邮箱、钉钉等
- 消息归档和备份

## 技术实现方案

### 方案一：基于itchat（推荐）
```python
import itchat
from itchat.content import TEXT

# 登录微信
itchat.auto_login(hotReload=True)

# 消息处理函数
@itchat.msg_register(TEXT)
def text_reply(msg):
    # 获取发送者信息
    sender = msg['FromUserName']
    content = msg['Text']
    
    # 检查是否为特定联系人
    if is_specific_contact(sender):
        # 自动回复逻辑
        reply = generate_reply(content)
        return reply
    
    return None

# 运行
itchat.run()
```

### 方案二：基于wxauto（Windows桌面版）
```python
from wxauto import WeChat

# 初始化微信
wx = WeChat()

# 获取最近聊天窗口
chats = wx.GetSessionList()

# 监听特定联系人的消息
def monitor_specific_contact(contact_name):
    while True:
        # 获取最新消息
        msgs = wx.GetLastMessage()
        
        for msg in msgs:
            if msg.sender == contact_name:
                # 处理消息并回复
                reply = process_message(msg.content)
                wx.SendMsg(reply, contact_name)
        
        time.sleep(1)
```

### 方案三：基于企业微信API（更稳定）
```python
import requests

class WeComBot:
    def __init__(self, corp_id, corp_secret, agent_id):
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.agent_id = agent_id
        self.access_token = self.get_access_token()
    
    def get_access_token(self):
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.corp_secret
        }
        response = requests.get(url, params=params)
        return response.json()["access_token"]
    
    def send_message(self, user_id, content):
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send"
        params = {"access_token": self.access_token}
        data = {
            "touser": user_id,
            "msgtype": "text",
            "agentid": self.agent_id,
            "text": {"content": content}
        }
        response = requests.post(url, params=params, json=data)
        return response.json()
```

## 配置管理

### 配置文件示例（config.yaml）
```yaml
wechat:
  # 登录配置
  auto_login: true
  hot_reload: true
  login_callback: "qr_callback.png"
  
  # 联系人配置
  specific_contacts:
    - name: "张三"
      id: "@zhangsan123"
      reply_rules:
        - keywords: ["你好", "hi", "hello"]
          reply: "您好！有什么可以帮您？"
        - keywords: ["报价", "价格"]
          reply: "请稍等，我为您查询价格信息..."
    
    - name: "李四"
      id: "@lisi456"
      reply_rules:
        - keywords: ["紧急", "urgent"]
          reply: "收到紧急消息，正在处理..."
          forward_to: ["email@example.com"]
  
  # 全局回复规则
  global_rules:
    - keywords: ["帮助", "help"]
      reply: "请输入以下关键词获取帮助：\n1. 报价\n2. 订单\n3. 客服"
    
    - time_based:
        start: "09:00"
        end: "18:00"
        reply: "工作时间自动回复：请留言，稍后回复您"
  
  # 消息转发配置
  forwarding:
    enabled: true
    targets:
      - type: "email"
        address: "admin@example.com"
        triggers: ["紧急", "重要"]
      
      - type: "webhook"
        url: "https://hooks.slack.com/services/xxx"
        triggers: ["错误", "异常"]
```

## 使用示例

### 示例1：特定联系人自动回复
```python
from wechat_connector import WeChatBot

# 初始化机器人
bot = WeChatBot(config_path="config.yaml")

# 添加特定联系人规则
bot.add_contact_rule(
    contact_name="老板",
    rules=[
        {
            "condition": "always",  # 总是回复
            "reply": "收到，马上处理！",
            "delay": 0  # 立即回复
        },
        {
            "condition": "keyword",
            "keywords": ["报告", "报表"],
            "reply": "报告正在生成中，请稍候...",
            "delay": 2  # 2秒后回复
        }
    ]
)

# 启动机器人
bot.start()
```

### 示例2：关键词触发回复
```python
# 添加关键词规则
bot.add_keyword_rule(
    keywords=["价格", "报价", "cost"],
    reply="我们的价格信息如下：\n1. 基础版：¥1000\n2. 专业版：¥3000\n3. 企业版：¥8000",
    match_type="contains"  # 包含关键词即触发
)

# 添加正则表达式规则
bot.add_regex_rule(
    pattern=r"订单号\s*(\d+)",
    reply=lambda match: f"正在查询订单 {match.group(1)} 的状态...",
    action="query_order"  # 可以关联自定义动作
)
```

### 示例3：智能回复模板
```python
# 使用模板引擎
from jinja2 import Template

reply_templates = {
    "greeting": Template("{{name}}，您好！{{time}}，有什么可以帮您？"),
    "order_status": Template("订单 {{order_id}} 当前状态：{{status}}\n预计完成时间：{{eta}}"),
    "price_quote": Template("""
根据您的要求，报价如下：
- 服务：{{service}}
- 周期：{{period}}
- 总价：{{price}}
- 备注：{{notes}}
    """)
}

# 使用模板回复
context = {"name": "张先生", "time": "下午好"}
reply = reply_templates["greeting"].render(context)
```

## 高级功能

### 1. 消息队列处理
```python
from queue import Queue
from threading import Thread

class MessageQueue:
    def __init__(self):
        self.queue = Queue()
        self.workers = []
    
    def add_message(self, msg):
        self.queue.put(msg)
    
    def start_workers(self, num_workers=3):
        for i in range(num_workers):
            worker = Thread(target=self.process_messages)
            worker.start()
            self.workers.append(worker)
    
    def process_messages(self):
        while True:
            msg = self.queue.get()
            # 处理消息
            self.handle_message(msg)
            self.queue.task_done()
```

### 2. 消息持久化
```python
import sqlite3
from datetime import datetime

class MessageLogger:
    def __init__(self, db_path="messages.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                content TEXT,
                timestamp DATETIME,
                replied BOOLEAN,
                reply_content TEXT
            )
        """)
        self.conn.commit()
    
    def log_message(self, sender, content, replied=False, reply_content=None):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO messages (sender, content, timestamp, replied, reply_content)
            VALUES (?, ?, ?, ?, ?)
        """, (sender, content, datetime.now(), replied, reply_content))
        self.conn.commit()
```

### 3. 智能回复引擎
```python
from openai import OpenAI

class SmartReplyEngine:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.context_history = {}
    
    def generate_reply(self, contact_id, message, context=None):
        # 构建对话历史
        history = self.context_history.get(contact_id, [])
        history.append({"role": "user", "content": message})
        
        # 调用AI生成回复
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的微信助手，回复要简洁友好。"},
                *history[-5:],  # 最近5条消息作为上下文
                {"role": "user", "content": message}
            ],
            max_tokens=100
        )
        
        reply = response.choices[0].message.content
        
        # 更新历史
        history.append({"role": "assistant", "content": reply})
        self.context_history[contact_id] = history[-10:]  # 保留最近10条
        
        return reply
```

## 部署与运维

### 1. Docker部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 创建数据目录
RUN mkdir -p /data/logs /data/db

CMD ["python", "main.py"]
```

### 2. 系统服务（systemd）
```ini
# /etc/systemd/system/wechat-bot.service
[Unit]
Description=WeChat Auto Reply Bot
After=network.target

[Service]
Type=simple
User=wechat
WorkingDirectory=/opt/wechat-bot
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. 监控与日志
```python
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('wechat_bot.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

## 安全注意事项

1. **账号安全**
   - 不要硬编码微信凭证
   - 使用环境变量或配置文件
   - 定期更换登录状态

2. **消息隐私**
   - 加密存储敏感消息
   - 遵守数据保护法规
   - 提供消息删除功能

3. **频率限制**
   - 控制消息发送频率
   - 避免被微信限制
   - 添加延迟和退避机制

4. **错误处理**
   - 完善的异常捕获
   - 网络中断重连
   - 消息重试机制

## 故障排除

### 常见问题

1. **无法登录**
   - 检查网络连接
   - 验证账号密码
   - 尝试网页版登录

2. **消息发送失败**
   - 检查联系人是否存在
   - 验证消息内容格式
   - 检查发送频率限制

3. **自动回复不触发**
   - 检查规则配置
   - 验证关键词匹配
   - 查看日志输出

### 调试模式
```python
# 启用调试
import logging
logging.basicConfig(level=logging.DEBUG)

# 或使用itchat的调试
itchat.auto_login(enableCmdQR=True, hotReload=True)
```

## 最佳实践

1. **渐进式部署**
   - 先测试少数联系人
   - 逐步扩大范围
   - 监控效果调整规则

2. **规则维护**
   - 定期审查回复规则
   - 更新关键词列表
   - 优化回复内容

3. **性能优化**
   - 使用消息队列
   - 异步处理消息
   - 缓存常用数据

4. **用户体验**
   - 回复要自然友好
   - 提供人工转接选项
   - 明确告知是自动回复

## 扩展功能

### 1. 集成其他服务
```python
# 集成日历
def check_calendar_events():
    # 查询日历事件
    events = calendar_service.get_events()
    return events

# 集成任务管理
def create_task_from_message(message):
    # 从消息创建任务
    task = task_service.create_task(
        title=f"微信消息处理 - {message.sender}",
        description=message.content
    )
    return task
```

### 2. 数据分析
```python
import pandas as pd
from datetime import datetime, timedelta

class MessageAnalytics:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_daily_stats(self, days=7):
        # 获取最近7天的消息统计
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 查询数据库
        query = """
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as message_count,
                SUM(CASE WHEN replied THEN 1 ELSE 0 END) as replied_count
            FROM messages
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        """
        
        # 返回统计结果
        return pd.read_sql_query(query, self.db_path, 
                                params=(start_date, end_date))
```

---

**开始使用**：
1. 安装依赖：`pip install itchat`
2. 配置联系人规则
3. 启动机器人
4. 监控运行状态

**提示**：建议先在测试环境运行，确认无误后再部署到生产环境。