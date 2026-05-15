import asyncio
import json
import re
import aiohttp
from typing import Optional


class NapCatBot:
    """NapCat 机器人基类 - 所有机器人共用的能力"""
    
    def __init__(self, session: aiohttp.ClientSession, config_path: str = "config.json"):
        """
        初始化基类
        
        Args:
            session: aiohttp ClientSession，用于 HTTP 请求
            config_path: 配置文件路径
        """
        self.session = session
        self.config_path = config_path
        
        # 加载配置
        self.config = self._load_config()
        
        # 应用配置
        self._apply_config()
        
        # WebSocket 连接对象，run() 时会赋值
        self.ws = None
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"配置文件 {self.config_path} 不存在，使用默认配置")
            return {}
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
    def _apply_config(self):
        """应用配置到实例变量"""
        # NapCat 连接配置
        napcat = self.config.get("napcat", {})
        self.http_token = napcat.get("http_token", "")
        self.ws_token = napcat.get("ws_token", "")
        self.http_host = napcat.get("http_host", "127.0.0.1")
        self.http_port = napcat.get("http_port", 3000)
        self.ws_host = napcat.get("ws_host", "127.0.0.1")
        self.ws_port = napcat.get("ws_port", 3001)
        
        # 构建 URL
        self.http_base_url = f"http://{self.http_host}:{self.http_port}"
        self.ws_url = f"ws://{self.ws_host}:{self.ws_port}?access_token={self.ws_token}"
        
        # 路径配置
        paths = self.config.get("paths", {})
        self.nsy_path = paths.get("nsy_base", "D:/女声优/")
        self.data_path = paths.get("data_base", "D:/tokochan/")
        self.temp_base = paths.get("temp_base", "D:/")
        
        # 子路径配置
        self.memory_dir = paths.get("memory_dir", "群记忆文件")
        self.admin_file = paths.get("admin_file", "admin.txt")
        self.inventor_file = paths.get("inventor_file", "inventor.txt")
        self.system_prompt = paths.get("system_prompt", "透子本身.txt")
        self.world_prompt = paths.get("world_prompt", "二次元世界.txt")
        self.nickname_map = paths.get("nickname_map", "外号对应.txt")
        
        # 临时文件配置
        temp = self.config.get("temp", {})
        self.video_temp = temp.get("video_temp", "temp_video.mp4")
        self.video_output = temp.get("video_output", "temp_video1.mp4")
        self.image_cleanup_delay = temp.get("image_cleanup_delay", 30)
        
        # 完整路径
        self.admin_file_path = f"{self.data_path}{self.admin_file}"
        self.inventor_file_path = f"{self.data_path}{self.inventor_file}"
        self.nickname_file_path = f"{self.nsy_path}{self.nickname_map}"
        self.system_prompt_path = f"{self.data_path}{self.system_prompt}"
        self.world_prompt_path = f"{self.data_path}{self.world_prompt}"
        self.memory_dir_path = f"{self.data_path}{self.memory_dir}"
        
        # 视频临时完整路径
        self.video_temp_path = f"{self.temp_base}{self.video_temp}"
        self.video_output_path = f"{self.temp_base}{self.video_output}"
    
    # ==================== 子类可重写的钩子方法 ====================
    
    async def on_message(self, group_id: int, sender: int, 
                         message: list, nickname: str, raw_event: dict) -> None:
        """收到消息时调用，子类重写"""
        pass
    
    async def on_poke(self, group_id: int, user_id: int, target_id: int) -> None:
        """收到戳一戳时调用"""
        pass
    
    async def on_emoji_like(self, group_id: int, user_id: int, 
                            message_id: int, is_add: bool, likes: list) -> None:
        """收到贴表情时调用"""
        pass
    
    async def on_group_increase(self, group_id: int, user_id: int, operator_id: int) -> None:
        """群成员增加时调用（包括机器人自己被拉入）"""
        pass
    
    async def on_group_decrease(self, group_id: int, user_id: int, operator_id: int) -> None:
        """群成员减少时调用"""
        pass
    
    async def on_kick_me(self, group_id: int, operator_id: int) -> None:
        """机器人自己被踢出群时调用"""
        pass
    
    # ==================== 基础通信 API ====================
    
    async def send_group_message(self, group_id: int, text: str,
                                  name_list: Optional[list[int]] = None,
                                  emoji_list: Optional[list[int]] = None) -> None:
        """发送群消息"""
        message = []
        for qq in (name_list or []):
            message.append({"type": "at", "data": {"qq": str(qq)}})
            message.append({"type": "text", "data": {"text": " "}})
        message.append({"type": "text", "data": {"text": text}})
        for emoji in (emoji_list or []):
            message.append({"type": "face", "data": {"id": emoji}})
        
        await self.ws.send_json({
            "action": "send_group_msg",
            "params": {
                "group_id": group_id,
                "message": message
            }
        })
    
    async def send_group_image(self, group_id: int, image_root: str) -> None:
        """发送群图片（本地路径或URL）"""
        message = [{"type": "image", "data": {"file": image_root}}]
        await self.ws.send_json({
            "action": "send_group_msg",
            "params": {
                "group_id": group_id,
                "message": message
            }
        })
    
    async def send_group_video(self, group_id: int, video_root: str) -> None:
        """发送群视频"""
        message = [{"type": "video", "data": {"file": video_root}}]
        await self.ws.send_json({
            "action": "send_group_msg",
            "params": {
                "group_id": group_id,
                "message": message
            }
        })
    
    async def get_group_list(self, no_cache: bool = False) -> list[int]:
        """获取当前所有群号列表（HTTP API）"""
        try:
            async with self.session.post(
                f"{self.http_base_url}/get_group_list",
                json={"no_cache": no_cache},
                headers={"Authorization": f"Bearer {self.http_token}"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                result = await resp.json()
                if result.get('status') == 'ok' and result.get('data'):
                    return [group['group_id'] for group in result['data']]
        except Exception as e:
            print(f"获取群列表异常: {e}")
        return []
    
    async def get_msg(self, message_id: int) -> dict:
        """获取单条消息内容（HTTP API）"""
        try:
            async with self.session.post(
                f"{self.http_base_url}/get_msg",
                json={"message_id": message_id},
                headers={"Authorization": f"Bearer {self.http_token}"},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                result = await resp.json()
                return result.get('data', {})
        except Exception as e:
            print(f"获取消息失败: {e}")
            return {}
    
    # ==================== 消息解析工具 ====================
    
    async def get_bv_from_b23(self, short_url: str) -> Optional[str]:
        """从 b23.tv 短链接获取 BV 号"""
        try:
            async with self.session.get(short_url.replace('\\/', '/'), allow_redirects=True) as resp:
                final_url = str(resp.url)
                bv_match = re.search(r'video/(BV[a-zA-Z0-9]+)', final_url)
                if bv_match:
                    return bv_match.group(1)
        except Exception as e:
            print(f"获取BV号失败: {e}")
        return None
    
    async def rewrite_message(self, message: list) -> list:
        """解析消息结构（处理回复、表情、B站卡片等）"""
        msg = []
        for part in message:
            if 'type' not in part:
                continue
            
            if part['type'] == 'face':
                msg.append({'type': 'face', 'data': {'id': part['data']['id']}})
            
            elif part['type'] == 'reply':
                try:
                    data = await self.get_msg(int(part['data']['id']))
                    q = data.get('message', [])
                    q = await self.rewrite_message(q)
                    msg.append({'type': 'reply', "data": q})
                except Exception as e:
                    print(f"获取回复消息失败: {e}")
                    msg.append(part)
            
            elif part['type'] in ('image', 'video', 'record'):
                msg.append({'type': part['type'], 'data': {'url': part['data']['url']}})
            
            elif part['type'] == 'json':
                try:
                    q = part['data']['data']
                    appid_start = q.find("appid")
                    if appid_start != -1:
                        appid_segment = q[appid_start:appid_start+18]
                        if any(x in appid_segment for x in ['1109937557', '100951776', '1105517988']):
                            position = q.find('https://b23.tv')
                            if position != -1:
                                url = ""
                                while q[position] != '"':
                                    url += q[position]
                                    position += 1
                                bv = await self.get_bv_from_b23(url)
                                if bv:
                                    msg.append({'type': 'Bilibili', 'url': f"https://www.bilibili.com/video/{bv}"})
                                    continue
                    msg.append(part)
                except:
                    msg.append(part)
            
            else:
                msg.append(part)
        
        return msg
    
    # ==================== 事件分发与主循环 ====================
    
    async def _dispatch_event(self, event: dict, group_list: list[int]):
        """内部事件分发，子类不需要调用"""
        post_type = event.get('post_type')
        
        if post_type == 'message':
            group_id = event.get('group_id')
            if group_id not in group_list:
                return
            sender = event['user_id']
            if sender == event.get('self_id'):
                return
            nickname = event['sender'].get('card') or event['sender'].get('nickname', '')
            await self.on_message(group_id, sender, event['message'], nickname, event)
        
        elif post_type == 'notice':
            notice_type = event.get('notice_type')
            
            if notice_type == 'notify' and event.get('sub_type') == 'poke':
                await self.on_poke(
                    event.get('group_id'),
                    event.get('user_id'),
                    event.get('target_id')
                )
            
            elif notice_type == 'group_msg_emoji_like':
                await self.on_emoji_like(
                    event.get('group_id'),
                    event.get('user_id'),
                    event.get('message_id'),
                    event.get('is_add', True),
                    event.get('likes', [])
                )
            
            elif notice_type == 'group_increase':
                await self.on_group_increase(
                    event.get('group_id'),
                    event.get('user_id'),
                    event.get('operator_id')
                )
            
            elif notice_type == 'group_decrease':
                if event.get('sub_type') == 'kick_me':
                    await self.on_kick_me(
                        event.get('group_id'),
                        event.get('operator_id')
                    )
                else:
                    await self.on_group_decrease(
                        event.get('group_id'),
                        event.get('user_id'),
                        event.get('operator_id')
                    )
    
    async def run(self, group_list: list[int]):
        """
        主循环 - 连接 WebSocket 并持续处理事件
        
        Args:
            group_list: 需要监听的群号列表
        """
        print(f"NapCatBot 启动，连接 {self.ws_url}")
        
        async with self.session.ws_connect(self.ws_url) as ws:
            self.ws = ws
            print("✅ WebSocket 已连接")
            
            try:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        event = json.loads(msg.data)
                        await self._dispatch_event(event, group_list)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print("WebSocket 连接出错")
                        break
            except asyncio.CancelledError:
                print("任务被取消")
            except Exception as e:
                print(f"WebSocket 异常: {e}")
