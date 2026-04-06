#!/usr/bin/env python3
"""
微信自动回复机器人 - 基础示例
功能：自动回复特定联系人的消息
"""

import itchat
from itchat.content import TEXT
import time
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeChatAutoReplyBot:
    def __init__(self):
        """初始化机器人"""
        self.specific_contacts = {
            # 格式：微信ID: 联系人信息
            "@zhangsan123": {
                "name": "张三",
                "rules": [
                    {
                        "keywords": ["你好", "hi", "hello"],
                        "reply": "您好！我是自动回复助手，有什么可以帮您？",
                        "delay": 1  # 1秒后回复
                    },
                    {
                        "keywords": ["报价", "价格", "多少钱"],
                        "reply": "请稍等，正在为您查询价格信息...",
                        "delay": 2
                    },
                    {
                        "keywords": ["订单", "查询订单"],
                        "reply": "请输入订单号，我为您查询订单状态。",
                        "delay": 1
                    }
                ]
            },
            "@lisi456": {
                "name": "李四",
                "rules": [
                    {
                        "keywords": ["报告", "报表"],
                        "reply": "报告正在生成中，预计需要5分钟。",
                        "delay": 3
                    },
                    {
                        "keywords": ["紧急", "urgent", "急"],
                        "reply": "收到紧急消息！已通知相关人员处理。",
                        "delay": 0  # 立即回复
                    }
                ]
            }
        }
        
        # 全局回复规则
        self.global_rules = [
            {
                "keywords": ["帮助", "help", "功能"],
                "reply": """可用功能：
1. 查询价格 - 发送"报价"或"价格"
2. 订单查询 - 发送"订单"加订单号
3. 联系客服 - 发送"客服"
4. 工作时间 - 发送"时间"
                """,
                "delay": 1
            },
            {
                "keywords": ["时间", "几点", "工作时间"],
                "reply": "工作时间：周一至周五 9:00-18:00",
                "delay": 1
            }
        ]
        
        self.message_log = []
    
    def is_specific_contact(self, user_id):
        """检查是否为特定联系人"""
        return user_id in self.specific_contacts
    
    def get_contact_name(self, user_id):
        """获取联系人名称"""
        if user_id in self.specific_contacts:
            return self.specific_contacts[user_id]["name"]
        return "未知联系人"
    
    def match_keywords(self, content, keywords):
        """检查消息是否包含关键词"""
        content_lower = content.lower()
        for keyword in keywords:
            if keyword.lower() in content_lower:
                return True
        return False
    
    def generate_reply(self, user_id, content):
        """生成回复消息"""
        reply = None
        delay = 0
        
        # 1. 检查特定联系人规则
        if user_id in self.specific_contacts:
            contact_rules = self.specific_contacts[user_id]["rules"]
            for rule in contact_rules:
                if self.match_keywords(content, rule["keywords"]):
                    reply = rule["reply"]
                    delay = rule["delay"]
                    break
        
        # 2. 检查全局规则
        if not reply:
            for rule in self.global_rules:
                if self.match_keywords(content, rule["keywords"]):
                    reply = rule["reply"]
                    delay = rule["delay"]
                    break
        
        # 3. 默认回复
        if not reply:
            # 智能回复：根据消息长度和内容决定
            if len(content) < 5:
                reply = "收到您的消息。"
            elif "?" in content or "？" in content:
                reply = "您的问题已收到，稍后回复您。"
            else:
                reply = "消息已收到，谢谢！"
            delay = 2
        
        return reply, delay
    
    def log_message(self, user_id, content, reply=None):
        """记录消息日志"""
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_id,
            "contact_name": self.get_contact_name(user_id),
            "content": content,
            "reply": reply
        }
        self.message_log.append(log_entry)
        
        # 打印日志
        logger.info(f"收到消息 - 来自: {log_entry['contact_name']}, 内容: {content}")
        if reply:
            logger.info(f"发送回复 - 内容: {reply}")
    
    def text_message_handler(self, msg):
        """文本消息处理函数"""
        user_id = msg['FromUserName']
        content = msg['Text']
        
        # 记录收到的消息
        self.log_message(user_id, content)
        
        # 生成回复
        reply, delay = self.generate_reply(user_id, content)
        
        if reply:
            # 添加延迟
            if delay > 0:
                logger.info(f"等待 {delay} 秒后回复...")
                time.sleep(delay)
            
            # 发送回复
            msg.user.send(reply)
            
            # 记录发送的回复
            self.log_message(user_id, content, reply)
        
        return reply
    
    def run(self):
        """运行机器人"""
        logger.info("正在启动微信自动回复机器人...")
        
        # 登录微信（热登录，避免每次扫码）
        itchat.auto_login(
            hotReload=True,
            enableCmdQR=False,  # 在GUI环境中使用
            statusStorageDir='itchat.pkl'
        )
        
        logger.info("微信登录成功！")
        
        # 注册消息处理器
        @itchat.msg_register(TEXT)
        def handle_text_message(msg):
            return self.text_message_handler(msg)
        
        # 显示机器人信息
        print("\n" + "="*50)
        print("微信自动回复机器人已启动")
        print("="*50)
        print(f"监控的特定联系人：")
        for user_id, info in self.specific_contacts.items():
            print(f"  - {info['name']} ({user_id})")
        print("\n机器人正在运行中...")
        print("按 Ctrl+C 停止")
        print("="*50 + "\n")
        
        # 运行机器人
        try:
            itchat.run()
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在退出...")
        finally:
            # 退出前保存日志
            self.save_logs()
            itchat.logout()
            logger.info("机器人已停止")
    
    def save_logs(self):
        """保存消息日志到文件"""
        if not self.message_log:
            return
        
        filename = f"message_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("微信消息处理日志\n")
            f.write("="*50 + "\n\n")
            
            for log in self.message_log:
                f.write(f"时间: {log['timestamp']}\n")
                f.write(f"联系人: {log['contact_name']}\n")
                f.write(f"收到消息: {log['content']}\n")
                if log['reply']:
                    f.write(f"发送回复: {log['reply']}\n")
                f.write("-"*30 + "\n")
        
        logger.info(f"消息日志已保存到: {filename}")

def main():
    """主函数"""
    print("微信自动回复机器人")
    print("功能：自动回复特定联系人的消息")
    print("-" * 40)
    
    # 创建机器人实例
    bot = WeChatAutoReplyBot()
    
    # 运行机器人
    bot.run()

if __name__ == "__main__":
    main()