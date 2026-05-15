# TokoBot - 小透子 QQ 机器人

基于 NapCat 框架的 QQ 机器人，支持 AI 对话、女声优图库管理、视频下载等功能。

## ✨ 功能特性

| 功能模块 | 说明 |
|---------|------|
| 🤖 AI 对话 | 接入 DeepSeek API，支持群聊记忆和关键词触发知识库 |
| 📸 女声优图库 | 公共/私有图库分离，外号映射，随机图片发送 |
| 🎬 视频下载 | 支持 B站、YouTube 等平台视频提取和转码 |
| 🖼️ 图片处理 | 图片对称变换（左/右/上/下对称） |
| 👥 群管理 | 多级权限系统（所有者、管理员） |

## 📋 指令列表

| 指令 | 说明 | 权限 |
|------|------|------|
| `/help` | 显示帮助信息 | 所有人 |
| `女声优名字/外号` | 获取随机图片 | 所有人 |
| `/show_nsy_list` | 显示已收录的女声优列表 | 所有人 |
| `/extract_video <url>` | 提取视频并发送 | 所有人 |
| `/add_nsy_picture <名字>` | 添加回复中的图片到图库 | 管理员 |
| `/add_nickname <外号> <真名>` | 添加外号映射 | 管理员 |
| `/delete_nickname <外号>` | 删除外号映射 | 管理员 |
| `/get_nickname <真名>` | 查询真名的所有外号 | 所有人 |
| `/publish_nsy <真名>` | 公开私有图库 | 所有者 |
| `/set_admin <QQ号>` | 设置管理员 | 所有者 |
| `/del_admin <QQ号>` | 移除管理员 | 所有者 |
| `/左对称` `/右对称` `/上对称` `/下对称` | 对回复的图片做对称处理 | 所有人 |

**特殊功能：**
- `@机器人 + 消息`：触发 AI 回复
- `戳一戳`：随机回复卖萌

## 🚀 快速开始

### 环境要求
- Python 3.8+
- NapCat 框架（已配置并运行）
- FFmpeg（视频转码）
- yt-dlp（视频下载）

### 安装依赖

```bash
pip install aiohttp aiofiles pillow numpy openai yt-dlp
配置文件
复制配置模板：

bash
cp data/config_toko.json.example data/config_toko.json
编辑 data/config_toko.json，填入你的配置：

NapCat 的 HTTP/WebSocket Token

DeepSeek API Key

文件路径（根据实际情况修改）

目录结构
text
tokochan/
├── src/
│   ├── napcat_bot.py      # NapCat 基类
│   └── tokobot.py          # 主机器人
├── lib/
│   ├── nsy_gallery.py      # 女声优图库模块
│   └── image_symmetry.py   # 图片对称模块
├── data/
│   ├── config_toko.json    # 配置文件（不提交）
│   ├── admin.txt           # 管理员列表
│   ├── inventor.txt        # 所有者列表
│   ├── 透子本身.txt        # AI 系统提示词
│   ├── 二次元世界.txt      # 二次元世界知识库
│   ├── 外号对应.txt        # 外号映射表
│   └── 群记忆文件/         # 各群对话历史
├── D:/女声优/              # 图库目录（不提交）
│   ├── 公用照片/           # 公共图库
│   └── {群号}/             # 私有图库
└── README.md
运行
bash
python src/tokobot.py
🏗️ 项目架构
text
NapCatBot (基类)
├── WebSocket 连接管理
├── HTTP API 封装
├── 事件分发机制
└── 消息解析工具

TokoBot (子类)
├── AI 对话模块
├── 女声优图库模块
├── 视频下载模块
├── 群管理模块
└── 指令处理系统

NSYGallery (图库模块)
├── 公共/私有图库分离
├── 外号映射缓存
├── 随机图片获取
└── 图片添加/发布
📝 提示词文件示例
data/透子本身.txt
text
你是小透子，一个可爱的 QQ 机器人助手。
你的性格：活泼、友善、有点傲娇
回复要求：保持简短，适当使用表情符号
data/二次元世界.txt
text
这是关于《BanG Dream!》的世界观知识：
主要乐队：Poppin'Party、Roselia、RAISE A SUILEN、Morfonica、MyGO!!!!!
🔧 常见问题
Q: 机器人不回复 AI 消息？

检查 features.ai_enabled 是否为 true

检查 DeepSeek API Key 是否有效

需要 @机器人 才会触发 AI

Q: 图库图片找不到？

检查文件夹路径是否正确

图片格式是否为 .png/.jpg/.jpeg

Q: 视频下载失败？

检查 yt-dlp 和 FFmpeg 是否已安装

检查是否添加到 PATH 环境变量

🛡️ 安全提醒
不要提交 config_toko.json 到版本控制

定期更换 API Key

图库目录建议不要上传到 GitHub

📄 许可证
MIT License

🙏 致谢
NapCat - QQ 机器人框架

DeepSeek - AI 对话服务

yt-dlp - 视频下载工具
