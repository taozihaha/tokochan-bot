# 桐谷透子QQ机器人

基于 NapCat 的 QQ 机器人，支持多模型切换、视频提取、图片识别等功能。

## 功能特性

- 💬 AI对话（DeepSeek/Gemini 多模型支持）
- 🖼️ 图片识别（千问VL）
- 🎥 B站/YouTube视频提取
- 👩 女声优图片库管理
- 🎨 图片对称处理

## 快速开始

1. 安装依赖
```bash
pip install openai requests Pillow numpy pyperclip yt-dlp
```

2. 配置环境变量
```bash
cp .env.example .env
```

3. 运行
```bash
python linux-version.py
```

注意事项
需要 NapCat 框架支持

视频下载需要 ffmpeg

代理配置（如需）请设置环境变量


## 🎯 上传步骤

### 第一步：整理目录

在你的服务器上，先创建一个干净的临时目录：

```bash
mkdir ~/tokochan_github
cd ~/tokochan_github

# 复制必要文件
cp ~/tokochan/linux-version.py .
cp ~/tokochan/"透子本身.txt" .
cp ~/tokochan/"二次元世界.txt" .

