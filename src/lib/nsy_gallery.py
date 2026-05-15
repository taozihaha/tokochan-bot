import os
import random
import asyncio
import aiohttp
import aiofiles
from typing import Optional, Callable, Awaitable


class NSYGallery:
    """女声优图库模块 - 支持公共图库 + 群私有图库"""
    
    def __init__(self, base_path: str = "D:/女声优/"):
        """
        初始化女声优图库
        
        Args:
            base_path: 图库根目录，默认 D:/女声优/
        """
        self.base_path = base_path
        self.nickname_file = os.path.join(base_path, "外号对应.txt")
        self._nickname_cache = None
        self._nickname_lock = asyncio.Lock()
    
    # ==================== 路径工具 ====================
    
    def get_public_path(self) -> str:
        """公共图库根目录"""
        return os.path.join(self.base_path, "公用照片/")
    
    def get_private_path(self, group_id: int) -> str:
        """某群私有图库根目录"""
        return os.path.join(self.base_path, f"{group_id}/")
    
    def get_folder_path(self, group_id: int, realname: str, is_public: bool = False) -> str:
        """获取某个女声优的文件夹路径"""
        if is_public:
            return os.path.join(self.get_public_path(), realname)
        return os.path.join(self.get_private_path(group_id), realname)
    
    # ==================== 外号映射（带缓存） ====================
    
    async def load_nickname_dict(self, force_refresh: bool = False) -> dict:
        """加载外号映射（带缓存，60秒有效期）"""
        if not force_refresh and self._nickname_cache:
            return self._nickname_cache
        
        nickname_dict = {}
        if os.path.exists(self.nickname_file):
            async with aiofiles.open(self.nickname_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                for line in content.strip().split('\n'):
                    if line and ',' in line:
                        parts = line.split(',')
                        nickname_dict[parts[0].strip()] = parts[1].strip()
        
        self._nickname_cache = nickname_dict
        return nickname_dict
    
    async def add_nickname(self, nickname: str, realname: str) -> bool:
        """添加外号映射"""
        async with self._nickname_lock:
            nickname_dict = await self.load_nickname_dict(force_refresh=True)
            
            if realname not in await self.get_all_folders():
                return False
            
            nickname_dict[nickname] = realname
            
            async with aiofiles.open(self.nickname_file, 'w', encoding='utf-8') as f:
                for k, v in nickname_dict.items():
                    await f.write(f"{k},{v}\n")
            
            self._nickname_cache = nickname_dict
            return True
    
    async def delete_nickname(self, nickname: str) -> bool:
        """删除外号映射"""
        async with self._nickname_lock:
            nickname_dict = await self.load_nickname_dict(force_refresh=True)
            
            if nickname not in nickname_dict:
                return False
            
            del nickname_dict[nickname]
            
            async with aiofiles.open(self.nickname_file, 'w', encoding='utf-8') as f:
                for k, v in nickname_dict.items():
                    await f.write(f"{k},{v}\n")
            
            self._nickname_cache = nickname_dict
            return True
    
    async def get_nicknames_by_realname(self, realname: str) -> list:
        """根据真实名字查询所有外号"""
        nickname_dict = await self.load_nickname_dict()
        return [nick for nick, target in nickname_dict.items() if target == realname]
    
    # ==================== 文件夹列表 ====================
    
    async def get_all_folders(self, group_id: Optional[int] = None) -> list:
        """获取所有女声优文件夹（公共 + 私有）"""
        all_folders = set()
        
        # 公共图库
        public_path = self.get_public_path()
        if os.path.exists(public_path):
            for item in os.listdir(public_path):
                if os.path.isdir(os.path.join(public_path, item)):
                    all_folders.add(item)
        
        # 私有图库
        if group_id:
            private_path = self.get_private_path(group_id)
            if os.path.exists(private_path):
                for item in os.listdir(private_path):
                    if os.path.isdir(os.path.join(private_path, item)):
                        all_folders.add(item)
        
        return list(all_folders)
    
    async def get_public_folders(self) -> list:
        """获取公共图库文件夹列表"""
        public_path = self.get_public_path()
        if not os.path.exists(public_path):
            return []
        return [item for item in os.listdir(public_path) 
                if os.path.isdir(os.path.join(public_path, item))]
    
    async def get_private_folders(self, group_id: int) -> list:
        """获取某群私有图库文件夹列表"""
        private_path = self.get_private_path(group_id)
        if not os.path.exists(private_path):
            return []
        return [item for item in os.listdir(private_path) 
                if os.path.isdir(os.path.join(private_path, item))]
    
    # ==================== 图片操作 ====================
    
    async def get_random_image(self, group_id: int, name: str) -> Optional[str]:
        """
        获取随机图片路径（优先私有，再公共）
        
        Returns:
            图片完整路径，找不到返回 None
        """
        nickname_dict = await self.load_nickname_dict()
        realname = nickname_dict.get(name, name)
        
        # 私有优先
        private_path = self.get_folder_path(group_id, realname)
        if os.path.exists(private_path):
            files = [f for f in os.listdir(private_path) 
                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if files:
                return os.path.join(private_path, random.choice(files))
        
        # 公共兜底
        public_path = self.get_folder_path(group_id, realname, is_public=True)
        if os.path.exists(public_path):
            files = [f for f in os.listdir(public_path) 
                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if files:
                return os.path.join(public_path, random.choice(files))
        
        return None
    
    async def add_image(self, group_id: int, realname: str, image_url: str, 
                        is_public: bool = False) -> bool:
        """
        添加图片到图库
        
        Args:
            group_id: 群号（is_public=True 时可不传）
            realname: 女声优真实名字
            image_url: 图片 URL
            is_public: 是否添加到公共图库
        """
        folder_path = self.get_folder_path(group_id, realname, is_public=is_public)
        os.makedirs(folder_path, exist_ok=True)
        
        # 计算下一个序号
        existing = [f for f in os.listdir(folder_path) if f.endswith('.png')]
        count = len(existing) + 1
        
        # 下载图片
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    return False
                save_path = os.path.join(folder_path, f"{count}.png")
                async with aiofiles.open(save_path, 'wb') as f:
                    await f.write(await resp.read())
                return True
    
    async def publish_folder(self, group_id: int, realname: str) -> bool:
        """将本群私有文件夹转为公共图库（移动）"""
        private_path = self.get_folder_path(group_id, realname)
        public_path = self.get_folder_path(group_id, realname, is_public=True)
        
        if not os.path.exists(private_path):
            return False
        
        if os.path.exists(public_path):
            return False
        
        import shutil
        shutil.move(private_path, public_path)
        return True
    
