"""
微信集成模块
使用 itchat-uos 实现微信机器人
"""

import logging
from typing import Callable, Optional
import threading
import time

logger = logging.getLogger(__name__)


class WeChatIntegration:
    """
    微信集成管理器
    
    功能：
    1. 微信登录和消息接收
    2. 自动回复家庭相关消息
    3. 发送家庭提醒到微信
    4. 支持群聊管理
    """
    
    def __init__(self, agent_core=None):
        self.agent_core = agent_core
        self.is_running = False
        self.bot = None
        self.friends_cache = {}
        self.groups_cache = {}
        
    def start(self, auto_reply: bool = True) -> bool:
        """
        启动微信机器人
        
        Args:
            auto_reply: 是否自动回复
        
        Returns:
            是否启动成功
        """
        try:
            import itchat
            from itchat.content import TEXT
            
            self.bot = itchat
            
            # 注册消息处理器
            @self.bot.msg_register(TEXT)
            def handle_text_message(msg):
                if not auto_reply:
                    return
                
                # 获取发送者
                user = msg['User']
                content = msg['Text']
                
                logger.info(f"收到微信消息: {user.get('NickName', 'Unknown')}: {content}")
                
                # 调用Agent处理
                if self.agent_core:
                    response = self.agent_core.chat(content, user_id=user.get('UserName'))
                    
                    # 回复消息
                    self.bot.send(response, msg['FromUserName'])
                    logger.info(f"已回复: {response[:50]}...")
            
            # 启动登录
            logger.info("正在启动微信机器人...")
            self.bot.auto_login(hotReload=True, statusStorageDir='wechat_login.pkl')
            
            self.is_running = True
            logger.info("✅ 微信机器人启动成功")
            
            # 在后台线程运行
            thread = threading.Thread(target=self.bot.run, daemon=True)
            thread.start()
            
            return True
            
        except ImportError:
            logger.error("❌ itchat-uos 未安装，请运行: pip install itchat-uos")
            return False
        except Exception as e:
            logger.error(f"❌ 微信启动失败: {e}")
            return False
    
    def stop(self):
        """停止微信机器人"""
        if self.bot and self.is_running:
            try:
                self.bot.logout()
                self.is_running = False
                logger.info("微信机器人已停止")
            except Exception as e:
                logger.error(f"停止失败: {e}")
    
    def send_reminder(self, user_name: str, message: str) -> bool:
        """
        发送提醒到指定用户
        
        Args:
            user_name: 用户昵称或备注名
            message: 提醒内容
        
        Returns:
            是否发送成功
        """
        if not self.bot or not self.is_running:
            logger.warning("微信机器人未运行")
            return False
        
        try:
            # 查找用户
            users = self.bot.search_friends(name=user_name)
            
            if not users:
                logger.warning(f"未找到用户: {user_name}")
                return False
            
            # 发送给第一个匹配的用户
            target_user = users[0]
            self.bot.send(f"🔔 家庭提醒:\n{message}", target_user['UserName'])
            
            logger.info(f"提醒已发送给 {user_name}")
            return True
            
        except Exception as e:
            logger.error(f"发送提醒失败: {e}")
            return False
    
    def send_to_group(self, group_name: str, message: str) -> bool:
        """
        发送消息到微信群
        
        Args:
            group_name: 群名称
            message: 消息内容
        
        Returns:
            是否发送成功
        """
        if not self.bot or not self.is_running:
            logger.warning("微信机器人未运行")
            return False
        
        try:
            # 查找群聊
            groups = self.bot.search_chatrooms(name=group_name)
            
            if not groups:
                logger.warning(f"未找到群聊: {group_name}")
                return False
            
            # 发送到第一个匹配的群
            target_group = groups[0]
            self.bot.send(f"🏡 家庭管家:\n{message}", target_group['UserName'])
            
            logger.info(f"消息已发送到群: {group_name}")
            return True
            
        except Exception as e:
            logger.error(f"发送群消息失败: {e}")
            return False
    
    def get_status(self) -> dict:
        """获取微信状态"""
        return {
            "is_running": self.is_running,
            "friends_count": len(self.friends_cache),
            "groups_count": len(self.groups_cache)
        }
