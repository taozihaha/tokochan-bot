import os
import random
import asyncio
import aiohttp
import json
import aiofiles
import datetime
import time
from napcat_bot import NapCatBot
import threading
from lib.nsy_gallery import NSYGallery
from lib.image_symmetry import image_symmetry

class TokoBot(NapCatBot):
    """小透子机器人 - 女声优图库 + AI 对话 + 群管理"""
    
    def __init__(self, session: aiohttp.ClientSession, config_path: str = "data/config_toko.json"):
        # 调用父类初始化（父类会加载配置）
        super().__init__(session, config_path)
        self.nsy = NSYGallery(self.nsy_path)
        # ========== AI 客户端 ==========
        from openai import AsyncOpenAI
        
        ai_cfg = self.config.get("ai", {})
        self.client_deepseek = AsyncOpenAI(
            api_key=ai_cfg.get("deepseek_api_key", ""),
            base_url=ai_cfg.get("deepseek_base_url", "https://api.deepseek.com")
        )
        self.deepseek_model = {
            "chat": ai_cfg.get("chat_model", "deepseek-v4-flash"),
            "think": ai_cfg.get("think_model", "deepseek-v4-pro")
        }
        self.ai_max_history = ai_cfg.get("max_history", 5)
        self.ai_temperature = ai_cfg.get("temperature", 1.216)
        
        # ========== 特色模块的数据 ==========
        self.admin_list = []
        self.inventor_list = []
        self._save_locks = {}
        # ========== Bot 配置 ==========
        bot_cfg = self.config.get("bot", {})
        self.self_qq = bot_cfg.get("self_qq", 3227188710)
        self.poke_replies = bot_cfg.get("poke_replies", [
            "你戳我干嘛！", 
            "别戳我，rui会生气的啦！", 
            "好疼啊，别戳了", 
            "再戳我报警了", 
            "🥺"
        ])
        self.help_text = bot_cfg.get("help_text", '''支持的指令有:
/extract_video（空格）网址，可提取b站视频
/add_nsy_picture（空格）女声优名字，可以将回复的图片加入女声优文件夹
女声优名字或部分外号，可获得女声优随机图片一张
/show_nsy_list 可获得已收录的女声优列表
/add_nickname （空格）外号（空格）正式名字，管理员可以添加女声优外号
/delete_nickname （空格）外号，管理员可以删除女声优外号
/get_nickname(空格)女声优，可以查询女声优当前外号''')
        
        # ========== 功能开关 ==========
        features = self.config.get("features", {})
        self.ai_enabled = features.get("ai_enabled", True)
        self.nsy_enabled = features.get("nsy_enabled", True)
        self.video_enabled = features.get("video_enabled", True)
        self.admin_enabled = features.get("admin_enabled", True)
    
    # ==================== 配置读取 ====================
    
    async def read_admin_list(self) -> list[int]:
        """读取管理员列表"""
        admin_list = []
        try:
            async with aiofiles.open(self.admin_file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                for line in content.strip().split('\n'):
                    line = line.strip()
                    if line and line.isdigit():
                        admin_list.append(int(line))
        except FileNotFoundError:
            print(f"管理员文件不存在: {self.admin_file_path}")
        except Exception as e:
            print(f"读取管理员文件失败: {e}")
        return admin_list
    
    async def read_inventor_list(self) -> list[int]:
        """读取所有者列表"""
        inventor_list = []
        try:
            async with aiofiles.open(self.inventor_file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                for line in content.strip().split('\n'):
                    line = line.strip()
                    if line and line.isdigit():
                        inventor_list.append(int(line))
        except FileNotFoundError:
            print(f"所有者文件不存在: {self.inventor_file_path}")
        except Exception as e:
            print(f"读取所有者文件失败: {e}")
        return inventor_list
    
    async def write_admin_list(self):
        """写入管理员列表到文件"""
        async with aiofiles.open(self.admin_file_path, 'w', encoding='utf-8') as f:
            for admin in self.admin_list:
                await f.write(f"{admin}\n")
    
    # ==================== AI 对话 ====================
    
    async def get_beijing_time(self) -> str:
        """获取北京时间"""
        now = datetime.datetime.now()
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday = weekdays[now.weekday()]
        time_str = now.strftime("%Y年%m月%d日 %H:%M:%S")
        return f"{time_str} {weekday}"
    
    async def load_group_memory(self, group_id: int) -> list:
        """加载群聊记忆"""
        file_path = f"{self.memory_dir_path}/{group_id}.json"
        
        if group_id not in self._save_locks:
            self._save_locks[group_id] = asyncio.Lock()
        
        async with self._save_locks[group_id]:
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                return json.loads(content) if content else []
            except:
                return []
    
    async def save_group_memory(self, group_id: int, memory: list):
        """保存群聊记忆"""
        file_path = f"{self.memory_dir_path}/{group_id}.json"
        
        if group_id not in self._save_locks:
            self._save_locks[group_id] = asyncio.Lock()
        
        async with self._save_locks[group_id]:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(memory, ensure_ascii=False, indent=2))
    
    async def read_txt_file(self, file_path: str) -> str:
        """读取文本文件（完整路径）"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except:
            return ""
    
    async def extract_key_words(self, user_content: str) -> list[str]:
        """关键词提取"""
        try:
            response = await self.client_deepseek.chat.completions.create(
                model=self.deepseek_model["chat"],
                messages=[
                    {"role": "system", "content": '''你是一个关键词提取器。关键词用逗号分隔，只返回关键词本身，不要其他内容
                     如果你认为用户的输入和《BanG Dream!》中的内容有强相关，则将'二次元世界'加入关键词列表中。
                     如果未能提取我所给予的关键词，则只返回空字符串'''},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                max_tokens=50
            )
            keywords = response.choices[0].message.content.strip()
            return [k.strip() for k in keywords.split(",")]
        except Exception as e:
            print(f"关键词提取失败: {e}")
            return []
    
    async def ai_reply(self, group_id: int, sender: int, nickname: str, text: str):
        """AI 回复"""
        if not self.ai_enabled:
            return
        
        group_history, system_prompt = await asyncio.gather(
            self.load_group_memory(group_id),
            self.read_txt_file(self.system_prompt_path)
        )
        
        user_content = f"{nickname}:{text}"
        current_time = await self.get_beijing_time()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"现在是服务器（北京时间）:{current_time}"}
        ]
        
        key_words = await self.extract_key_words(user_content)
        if '二次元世界' in key_words:
            sekai = await self.read_txt_file(self.world_prompt_path)
            messages.append({"role": "system", "content": sekai})
        
        group_history = group_history[-self.ai_max_history:]
        messages.append({"role": "system", "content": "以下是与用户的对话历史，请你仅提取这些信息中的一些事实，但是不要回答这些内容"})
        messages.extend(group_history)
        messages.append({"role": "user", "content": user_content})
        
        response = await self.client_deepseek.chat.completions.create(
            temperature=self.ai_temperature,
            model=self.deepseek_model["chat"],
            messages=messages,
            stream=False
        )
        
        reply = response.choices[0].message.content
        
        await asyncio.gather(
            self.send_group_message(group_id, reply, [], []),
            self.save_group_memory(group_id, group_history + [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": reply}
            ])
        )
    
    # ==================== 视频下载 ====================
    
    def check_url(self, url: str) -> bool:
        """检查 URL 是否可访问"""
        if "youtube" in url and len(url) >= 40:
            return True
        try:
            import socket
            host = url.split('//')[1].split('/')[0].split(':')[0]
            port = 443 if url.startswith('https') else 80
            socket.create_connection((host, port), 2)
            return True
        except:
            return False
    
    async def download_video(self, url: str, output_path: str) -> int:
        """下载视频（yt-dlp）"""
        cmd = ['yt-dlp', '-f', 'bestvideo+bestaudio', '-o', output_path, url]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        return proc.returncode
    
    async def transcode_video(self, input_path: str, output_path: str) -> int:
        """视频转码（ffmpeg）"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'h264_nvenc', '-preset', 'p4',
            '-cq', '23', '-c:a', 'aac', output_path
        ]
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.wait()
        return proc.returncode
    
    async def handle_video_download(self, group_id: int, url: str):
        """后台下载并发送视频"""
        if not self.video_enabled:
            return
        
        await self.send_group_message(group_id, "正在提取中，请稍等", [], [])
        
        ret = await self.download_video(url, self.video_temp_path)
        if ret != 0:
            await self.send_group_message(group_id, "下载失败……可能是反爬虫脚本发力了", [], [])
            return
        
        if os.path.exists(self.video_temp_path):
            await self.transcode_video(self.video_temp_path, self.video_output_path)
            await self.send_group_video(group_id, self.video_output_path)
            os.remove(self.video_temp_path)
            if os.path.exists(self.video_output_path):
                os.remove(self.video_output_path)

    # ==================== 事件处理（重写钩子） ====================
    
    async def on_message(self, group_id: int, sender: int, 
                         message: list, nickname: str, raw_event: dict):
        """处理消息"""
        # 解析消息
        message = await self.rewrite_message(message)
        print(message)
        
        # 加载女声优映射
        nsy_dict = await self.nsy.load_nickname_dict()
        
        for nsy in await self.nsy.get_all_folders(group_id):
            nsy_dict[nsy] = nsy
        
        have_added_message = False
        
        for part in message:
            if part.get('type') == 'forward':
                break
            
            if part.get('type') == 'text':
                text = part['data']['text']
                if text in ('', ' '):
                    continue
                
                # 保存到群记忆
                group_history = await self.load_group_memory(group_id)
                user_content = f"{nickname}:{text}"
                if not have_added_message:
                    group_history.append({"role": "user", "content": user_content})
                    await self.save_group_memory(group_id, group_history)
                    have_added_message = True
                
                # ===== 指令处理 =====
                if text == '/help':
                    await self.send_group_message(group_id, self.help_text, [sender], [])
                
                elif self.video_enabled and text.startswith('/extract_video'):
                    url = text[15:].strip()
                    if self.check_url(url):
                        asyncio.create_task(self.handle_video_download(group_id, url))
                        await self.send_group_message(group_id, "正在提取中，请稍等", [sender], [])
                    else:
                        await self.send_group_message(group_id, "小透子访问不了这个网址呢……", [sender], [5])
                
                elif text == '/show_nsy_list':
                    public_list = await self.nsy.get_all_folders()  # 只公共
                    private_list = await self.nsy.get_all_folders(group_id)  # 公共+私有
                    msg = f"公共：{', '.join(public_list) if public_list else '无'}\n"
                    msg += f"本群：{', '.join([f for f in private_list if f not in public_list]) if private_list else '无'}"
                    await self.send_group_message(group_id, msg, [sender], [])
                
                elif self.admin_enabled and text.startswith('/add_nickname'):
                    if sender in self.admin_list or sender in self.inventor_list:
                        try:
                            parts = text[14:].split()
                            nick_name, real_name = parts[0], parts[1]
                            if real_name in nsy_dict:
                                await self.nsy.add_nickname(nick_name, real_name)
                                await self.send_group_message(group_id, f"已添加外号 {nick_name} 对应 {real_name}", [sender], [])
                            else:
                                await self.send_group_message(group_id, f"未找到女声优 {real_name}", [sender], [5])
                        except:
                            await self.send_group_message(group_id, "指令格式错误", [sender], [5])
                    else:
                        await self.send_group_message(group_id, "您没有权限添加外号", [sender], [5])
                
                elif self.admin_enabled and text.startswith('/delete_nickname'):
                    if sender in self.admin_list or sender in self.inventor_list:
                        nick_name = text[17:].strip()
                        if nick_name in nsy_dict:
                            await self.nsy.delete_nickname(nick_name)
                            await self.send_group_message(group_id, f"已删除外号 {nick_name}", [sender], [])
                        else:
                            await self.send_group_message(group_id, f"未找到外号 {nick_name}", [sender], [5])
                    else:
                        await self.send_group_message(group_id, "您没有权限删除外号", [sender], [5])
                
                elif self.admin_enabled and text.startswith('/set_admin'):
                    if sender in self.inventor_list:
                        try:
                            qq = int(text[11:].strip())
                            if qq in self.admin_list or qq in self.inventor_list:
                                await self.send_group_message(group_id, "该用户已经是管理员了", [sender], [5])
                            else:
                                self.admin_list.append(qq)
                                await self.write_admin_list()
                                await self.send_group_message(group_id, "已将该用户设为管理员", [sender], [])
                        except:
                            await self.send_group_message(group_id, "指令格式错误", [sender], [5])
                    else:
                        await self.send_group_message(group_id, "您没有权限设置管理员", [sender], [5])
                
                elif self.admin_enabled and text.startswith('/del_admin'):
                    if sender in self.inventor_list:
                        try:
                            qq = int(text[11:].strip())
                            if qq in self.admin_list:
                                self.admin_list.remove(qq)
                                await self.write_admin_list()
                                await self.send_group_message(group_id, "已将该用户移除管理员", [sender], [])
                            else:
                                await self.send_group_message(group_id, "该用户不是管理员", [sender], [5])
                        except:
                            await self.send_group_message(group_id, "指令格式错误", [sender], [5])
                    else:
                        await self.send_group_message(group_id, "您没有权限移除管理员", [sender], [5])
                
                elif self.nsy_enabled and text.startswith('/add_nsy_picture'):
                    if sender in self.admin_list or sender in self.inventor_list:
                        name = text[17:].strip()
                        for p in message:
                            if p.get('type') == 'reply':
                                for p2 in p.get('data', []):
                                    if p2.get('type') == 'image':
                                        if await self.nsy.add_image(group_id, name, p2['data']['url']):
                                            await self.send_group_message(group_id, f"已添加图片至{name}中", [sender], [])
                                        else:
                                            await self.send_group_message(group_id, f"添加失败", [sender], [5])
                                        break
                    else:
                        await self.send_group_message(group_id, "您没有权限添加女声优图片", [sender], [5])
                elif self.admin_enabled and text.startswith('/get_nickname'):
                    try:
                        realname = text[14:].strip()
                        nicknames = await self.nsy.get_nicknames_by_realname(realname)
                        if nicknames:
                            await self.send_group_message(group_id, f"「{realname}」的外号有：{', '.join(nicknames)}", [sender], [])
                        else:
                            await self.send_group_message(group_id, f"「{realname}」暂无外号", [sender], [5])
                    except:
                        await self.send_group_message(group_id, "指令格式错误", [sender], [5])
                elif self.admin_enabled and text.startswith('/publish_nsy'):
                    if sender in self.inventor_list:
                        try:
                            realname = text[14:].strip()
                            if not realname:
                                await self.send_group_message(group_id, "请指定要公开的文件夹名", [sender], [5])
                            else:
                                await self.nsy.publish_folder(group_id, realname)
                                await self.send_group_message(group_id, f"已公开图库 {realname}", [sender], [])
                        except Exception as e:
                            await self.send_group_message(group_id, "指令格式错误", [sender], [5])
                    else:
                        await self.send_group_message(group_id, "您没有权限公开图库", [sender], [5])
                elif self.nsy_enabled and text in nsy_dict:
                    image_path = await self.nsy.get_random_image(group_id, text)
                    if image_path:
                        await self.send_group_image(group_id, image_path)
                    else:
                        await self.send_group_message(group_id, f"没有找到 {text} 的图片", [], [5])
                
                elif "对称" in text:
                    direction = 'left'
                    if text[:4] in ['/左对称', '/右对称', '/上对称', '/下对称']:
                        direction_map = {'/左对称': 'left', '/右对称': 'right', '/上对称': 'top', '/下对称': 'bottom'}
                        direction = direction_map.get(text[:4], 'left')
                    for p in message:
                        if p.get('type') == 'reply':
                            for p2 in p.get('data', []):
                                if p2.get('type') == 'image':
                                    await image_symmetry(self.session, self.temp_base, self.image_cleanup_delay,group_id, direction, p2['data']['url'],self.send_group_image)
                                    break
            elif part.get('type') == 'at' and part['data']['qq'] == str(self.self_qq):
                for part2 in message:
                    if part2.get('type') == 'text':
                        text = part2['data']['text'].strip()
                        if text.startswith('@'):
                            text = text[1:]
                        if text and text not in ('', ' ') and self.ai_enabled:
                            await self.ai_reply(group_id, sender, nickname, text)
                            break
            
            elif part.get('type') == 'Bilibili':
                await self.send_group_message(group_id, "b站功能正在修复中", [], [5, 5, 5])
    
    async def on_poke(self, group_id: int, user_id: int, target_id: int):
        """处理戳一戳"""
        if target_id == self.self_qq:
            await self.send_group_message(group_id, random.choice(self.poke_replies), [], [])
    
    async def on_group_increase(self, group_id: int, user_id: int, operator_id: int):
        """处理入群事件"""
        if user_id == self.self_qq:
            print(f"✅ 机器人被 {operator_id} 拉入群 {group_id}")
            await self.send_group_message(group_id, "哦哈哟", [], [])
    async def on_kick_me(self, group_id: int, operator_id: int):
        """处理被踢"""
        print(f"❌ 机器人被 {operator_id} 踢出群 {group_id}")
    async def on_emoji_like(self, group_id: int, user_id: int, message_id: int, is_add: bool, likes: list) -> None:
        """处理贴表情"""
        action = "添加了" if is_add else "取消了"
        for like in likes:
            emoji_id = like.get('emoji_id')
            count = like.get('count')
            print(f"🎭 {user_id} 在群 {group_id} 中对消息 {message_id} {action} 表情 {emoji_id}，共 {count} 人使用")


# ==================== 主程序 ====================

async def main():
    import aiohttp
    import asyncio
    
    async with aiohttp.ClientSession() as session:
        # 创建机器人（配置文件路径作为参数）
        bot = TokoBot(session, config_path="data/config_toko.json")
        
        # 加载配置
        bot.admin_list = await bot.read_admin_list()
        bot.inventor_list = await bot.read_inventor_list()
        
        print(f"👑 所有者: {bot.inventor_list}")
        print(f"👥 管理员: {bot.admin_list}")
        
        # 获取群列表
        group_list = await bot.get_group_list()
        print(f"📋 监控群: {group_list}")
        
        # 运行（不再需要传 ws_url，父类自己构建）
        await bot.run(group_list)


if __name__ == "__main__":
    asyncio.run(main())
