"""
智能家居对接模块
支持 Home Assistant API
"""

import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SmartHomeIntegration:
    """
    智能家居集成管理器
    
    功能：
    1. 连接 Home Assistant
    2. 控制智能设备（灯光、开关、空调等）
    3. 查询设备状态
    4. 自动化场景触发
    """
    
    def __init__(self, hass_url: str = "http://localhost:8123", api_token: str = None):
        """
        初始化智能家居集成
        
        Args:
            hass_url: Home Assistant URL
            api_token: Long-lived Access Token
        """
        self.hass_url = hass_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}" if api_token else "",
            "Content-Type": "application/json"
        }
        self.devices_cache = {}
        
    def test_connection(self) -> bool:
        """测试连接是否正常"""
        try:
            response = requests.get(
                f"{self.hass_url}/api/",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("✅ Home Assistant 连接成功")
                return True
            else:
                logger.error(f"❌ 连接失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 连接异常: {e}")
            return False
    
    def get_all_devices(self) -> List[Dict]:
        """获取所有设备列表"""
        try:
            response = requests.get(
                f"{self.hass_url}/api/states",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                devices = response.json()
                self.devices_cache = {d['entity_id']: d for d in devices}
                logger.info(f"获取到 {len(devices)} 个设备")
                return devices
            else:
                logger.error(f"获取设备失败: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"获取设备异常: {e}")
            return []
    
    def get_device_status(self, entity_id: str) -> Optional[Dict]:
        """
        获取指定设备状态
        
        Args:
            entity_id: 设备ID，如 light.living_room
        
        Returns:
            设备状态信息
        """
        try:
            response = requests.get(
                f"{self.hass_url}/api/states/{entity_id}",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取设备状态失败: {entity_id}")
                return None
                
        except Exception as e:
            logger.error(f"获取设备状态异常: {e}")
            return None
    
    def turn_on(self, entity_id: str) -> bool:
        """
        打开设备
        
        Args:
            entity_id: 设备ID
        
        Returns:
            是否成功
        """
        return self._control_device(entity_id, "turn_on")
    
    def turn_off(self, entity_id: str) -> bool:
        """
        关闭设备
        
        Args:
            entity_id: 设备ID
        
        Returns:
            是否成功
        """
        return self._control_device(entity_id, "turn_off")
    
    def set_light_brightness(self, entity_id: str, brightness: int) -> bool:
        """
        设置灯光亮度
        
        Args:
            entity_id: 灯光设备ID
            brightness: 亮度 (0-255)
        
        Returns:
            是否成功
        """
        try:
            response = requests.post(
                f"{self.hass_url}/api/services/light/turn_on",
                headers=self.headers,
                json={
                    "entity_id": entity_id,
                    "brightness": brightness
                },
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"✅ 设置亮度成功: {entity_id} -> {brightness}")
                return True
            else:
                logger.error(f"设置亮度失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"设置亮度异常: {e}")
            return False
    
    def set_temperature(self, entity_id: str, temperature: float) -> bool:
        """
        设置温度（空调/暖气）
        
        Args:
            entity_id: 温控设备ID
            temperature: 目标温度
        
        Returns:
            是否成功
        """
        try:
            response = requests.post(
                f"{self.hass_url}/api/services/climate/set_temperature",
                headers=self.headers,
                json={
                    "entity_id": entity_id,
                    "temperature": temperature
                },
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"✅ 设置温度成功: {entity_id} -> {temperature}°C")
                return True
            else:
                logger.error(f"设置温度失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"设置温度异常: {e}")
            return False
    
    def trigger_scene(self, scene_id: str) -> bool:
        """
        触发场景
        
        Args:
            scene_id: 场景ID，如 scene.movie_night
        
        Returns:
            是否成功
        """
        try:
            response = requests.post(
                f"{self.hass_url}/api/services/scene/turn_on",
                headers=self.headers,
                json={"entity_id": scene_id},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"✅ 场景触发成功: {scene_id}")
                return True
            else:
                logger.error(f"场景触发失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"场景触发异常: {e}")
            return False
    
    def _control_device(self, entity_id: str, service: str) -> bool:
        """通用设备控制"""
        try:
            # 确定服务类型
            domain = entity_id.split('.')[0]
            
            response = requests.post(
                f"{self.hass_url}/api/services/{domain}/{service}",
                headers=self.headers,
                json={"entity_id": entity_id},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"✅ 控制成功: {entity_id} -> {service}")
                return True
            else:
                logger.error(f"控制失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"控制异常: {e}")
            return False
    
    def get_devices_by_type(self, device_type: str) -> List[Dict]:
        """
        按类型获取设备
        
        Args:
            device_type: 设备类型 (light, switch, climate, etc.)
        
        Returns:
            设备列表
        """
        if not self.devices_cache:
            self.get_all_devices()
        
        return [
            device for device in self.devices_cache.values()
            if device['entity_id'].startswith(f"{device_type}.")
        ]
    
    def execute_command(self, command: str) -> str:
        """
        执行自然语言命令
        
        Args:
            command: 自然语言命令，如"打开客厅灯"
        
        Returns:
            执行结果
        """
        command_lower = command.lower()
        
        # 简单的命令解析（实际应该用LLM）
        if "打开" in command_lower or "开" in command_lower:
            if "灯" in command_lower:
                lights = self.get_devices_by_type("light")
                if lights:
                    self.turn_on(lights[0]['entity_id'])
                    return f"✅ 已打开 {lights[0]['attributes'].get('friendly_name', '灯')}"
            
            elif "空调" in command_lower or "暖气" in command_lower:
                climates = self.get_devices_by_type("climate")
                if climates:
                    self.turn_on(climates[0]['entity_id'])
                    return f"✅ 已打开 {climates[0]['attributes'].get('friendly_name', '空调')}"
        
        elif "关闭" in command_lower or "关" in command_lower:
            if "灯" in command_lower:
                lights = self.get_devices_by_type("light")
                if lights:
                    self.turn_off(lights[0]['entity_id'])
                    return f"✅ 已关闭 {lights[0]['attributes'].get('friendly_name', '灯')}"
        
        elif "温度" in command_lower:
            # 提取温度数字
            import re
            temps = re.findall(r'(\d+)', command)
            if temps:
                temp = int(temps[0])
                climates = self.get_devices_by_type("climate")
                if climates:
                    self.set_temperature(climates[0]['entity_id'], temp)
                    return f"✅ 已设置温度为 {temp}°C"
        
        return "❌ 无法理解命令，请尝试更具体的指令"
