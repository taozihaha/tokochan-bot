import os
import sys
import time
import datetime
import webbrowser
import pyperclip
import requests
import json
import subprocess
import socket
import random
import re
from pathlib import Path
from openai import OpenAI
from PIL import Image
import numpy as np


token = os.environ.get("QQ_BOT_TOKEN")
if not token:
    raise ValueError("请设置环境变量 QQ_BOT_TOKEN")

client_deepseek = OpenAI(api_key=os.environ.get("DEEPSEEK_API_KEY"),base_url="https://api.deepseek.com")
client_gemini = OpenAI(api_key=os.environ.get("GEMINI_API_KEY"),base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
client_qwen = OpenAI(api_key=os.environ.get("QWEN_API_KEY"),base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
deepseek_modle={"chat":"deepseek-chat","think":"deepseek-reasoner"}
gemini_modle={"chat": "gemini-3.1-flash-lite","think": "gemini-3.1-flash","pro": "gemini-3.1-pro","cheap": "gemini-2.5-flash-lite"}
qwen_modle={"see":"qwen3-vl-flash"}

def read_txt_file(file_path):
    if not file_path.endswith('.txt'):
        file_path = file_path + '.txt'
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def read_knowledge(knowledge):
    txt_file=f"/root/tokochan/{knowledge}.txt"
    return read_txt_file(txt_file)
    
def get_bv_from_b23(short_url):
    clean_url = short_url.replace('\\/', '/')
    try:
        response = requests.get(clean_url, allow_redirects=True)
        final_url = response.url
        bv_match = re.search(r'video/(BV[a-zA-Z0-9]+)', final_url)
        if bv_match:
            return bv_match.group(1)
    except Exception as e:
        print(f"获取失败: {e}")
    return None

def get_bilibili_duration(url):
    cmd = f'yt-dlp --proxy http://127.0.0.1:7890 --dump-json --no-download "{url}"'
    result = os.popen(cmd).read()
    place=result.find("duration")
    duration=""
    while(result[place]!=','):
        duration+=result[place]
        place+=1
    duration=duration[11:]
    duration=float(duration)
    return duration


group_list_str = os.environ.get("GROUP_LIST", "")
if group_list_str:
    group_list = [int(x.strip()) for x in group_list_str.split(",")]
else:
    group_list = []
    print("警告: 未设置 GROUP_LIST 环境变量")

nsy_list={}
help_text='''支持的指令有:
/extract_video（空格）网址，可提取b站视频
/add_nsy_picture（空格）女声优名字，可以将回复的图片加入女声优文件夹（没有则建空文件夹）
女声优名字或部分外号，可获得女声优随机图片一张（没有反应可能是外号未收录或未建立文件夹）
/show_nsy_list 可获得已收录的女声优列表
/add_nickname （空格）外号（空格）正式名字，可以添加女声优外号
/delete_nickname （空格）外号，管理员可以删除女声优外号,'''

admin_list_str=os.environ.get("ADMIN_LIST")
if admin_list_str:
    administrator_list = [int(x.strip()) for x in admin_list_str.split(",")]
else:
    administrator_list = []
    print("警告: 未设置 ADMIN_LIST 环境变量")

bot_qq = os.environ.get("BOT_QQ")

face_dic = {
    "惊讶": 0,
    "撇嘴": 1,
    "色": 2,
    "发呆": 3,
    "得意": 4,
    "流泪": 5,
    "害羞": 6,
    "闭嘴": 7,
    "睡": 8,
    "大哭": 9,
    "尴尬": 10,
    "发怒": 11,
    "调皮": 12,
    "呲牙": 13,
    "微笑": 14,
    "难过": 15,
    "酷": 16,
    "抓狂": 18,
    "吐": 19,
    "偷笑": 20,
    "可爱": 21,
    "白眼": 22,
    "傲慢": 23,
    "饥饿": 24,
    "困": 25,
    "惊恐": 26,
    "流汗": 27,
    "憨笑": 28,
    "悠闲": 29,
    "奋斗": 30,
    "咒骂": 31,
    "疑问": 32,
    "嘘": 33,
    "晕": 34,
    "折磨": 35,
    "衰": 36,
    "骷髅": 37,
    "敲打": 38,
    "再见": 39,
    "发抖":41,
    "爱情":42,
    "跳跳":43,
    "猪头":46,
    "拥抱":49,
    "蛋糕":53,
    "刀":56,
    "便便":59,
    "咖啡":60,
    "玫瑰":63,
    "凋谢":64,
    "心":66,
    "心碎":67,
    "太阳":74,
    "月亮":75,
    "强":76,
    "弱":77,
    "握手":78,
    "胜利":79,
    "冷汗":96,
    "擦汗":97,
    "抠鼻":98,
    "鼓掌":99,
    "糗大了":100,
    "委屈":106,
    "快哭了":107,
    "可怜":111,
    "示爱":116,
    "抱拳":118,
    "勾引":119,
    "拳头":120,
    "差劲":121,
    "NO":123,
    "OK":124,
    "挥手":129,
    "茶":171,
    "吐血":177,
    "笑哭":182,
}


def get_beijing_time():
    """获取北京时间（依赖系统时区设置）"""
    # 如果系统是UTC+8时区
    now = datetime.datetime.now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday = weekdays[now.weekday()]
    time_str = now.strftime("%Y年%m月%d日 %H:%M:%S")
    return f"{time_str} {weekday}"

def get_nsy_list(path="/root/女声优/"):
        # 获取路径下所有条目
        items = os.listdir(path)
        # 筛选出文件夹
        folders = [item for item in items 
                  if os.path.isdir(os.path.join(path, item))]
        return folders

def load_nsy_list(file_path="/root/女声优/外号对应.txt"):
    nickname_dict={}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                lines = content.split('\n')
                for line in lines:
                    parts = line.split(',')
                    if len(parts) == 2:
                        nickname_dict[parts[0].strip()] = parts[1].strip()
    return nickname_dict

def add_nickname(nickname,realname):
    file_path="/root/女声优/外号对应.txt"
    nsys=get_nsy_list()
    nickname_dict={}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                lines = content.split('\n')
                for line in lines:
                    parts = line.split(',')
                    if len(parts) == 2:
                        nickname_dict[parts[0].strip()] = parts[1].strip()
    if realname in nsys:
        nickname_dict[nickname]=realname
        nsy_list[nickname]=realname
    with open(file_path, 'w', encoding='utf-8') as f:
        for k,v in nickname_dict.items():
            f.write(f"{k},{v}\n")

def delete_nickname(nickname):
    file_path="/root/女声优/外号对应.txt"
    nickname_dict={}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                lines = content.split('\n')
                for line in lines:
                    parts = line.split(',')
                    if len(parts) == 2:
                        nickname_dict[parts[0].strip()] = parts[1].strip()
    if nickname in nickname_dict:
        del nickname_dict[nickname]
    with open(file_path, 'w', encoding='utf-8') as f:
        for k,v in nickname_dict.items():
            f.write(f"{k},{v}\n")
    if nickname in nsy_list:
        del nsy_list[nickname]

def get_user_file(user_id):
    MEMORY1="/root/tokochan/用户记忆文件"
    return os.path.join(MEMORY1, f"{user_id}.json")

def load_personal_memory(user_id):
    file_path = get_user_file(user_id)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def get_group_file(group_id):
    MEMORY2="/root/tokochan/群记忆文件"
    return os.path.join(MEMORY2, f"{group_id}.json")

def load_group_memory(group_id):
    file_path = get_group_file(group_id)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_replied_message(msg_id):
    file_path="/root/tokochan/已回复信息.txt"
    replied_ids = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                replied_ids = content.split(',')
    if str(msg_id) not in replied_ids:
        replied_ids.append(str(msg_id))
    replied_ids = replied_ids[-60:]
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(','.join(replied_ids))

def get_last_replied_message():
    file_path="/root/tokochan/已回复信息.txt"
    try:
        if not os.path.exists(file_path):
            return 0
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return 0
            msg_ids = content.split(',')
        return msg_ids[-1]
    except Exception as e:
        print(f"读取已回复文件失败: {e}")
        return 0
            
def is_msg_replied(msg_id):
    file_path="/root/tokochan/已回复信息.txt"
    """检查消息是否已回复"""
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:
            return False
        replied_ids = content.split(',')
        return str(msg_id) in replied_ids
        
def save_personal_memory(qq,memory):
    file_path = get_user_file(qq)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)
        
def save_group_memory(group,memory):
    file_path = get_group_file(group)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def download_image(image_url, save_dir,file_name):
    save_path=save_dir+"/"+file_name
    try:
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except:
        return False
    return False

def compress_png_to_jpg(input_path, output_path=None, quality=85, max_size=None):
    # 检查输入文件是否存在
    if not os.path.exists(input_path):
        print(f"错误: 文件 {input_path} 不存在")
        return False
    
    # 生成输出路径
    if output_path is None:
        input_path_obj = Path(input_path)
        output_path = input_path_obj.with_suffix('.jpg')
    
    try:
        # 打开PNG图片
        with Image.open(input_path) as img:
            # 如果是RGBA模式，转换为RGB（去除alpha通道）
            if img.mode == 'RGBA':
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                # 将PNG粘贴到白色背景上
                background.paste(img, mask=img.split()[3])  # 使用alpha通道作为掩码
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 如果需要调整大小
            if max_size:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 保存为JPG
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            
        # 获取文件大小信息
        original_size = os.path.getsize(input_path) / 1024  # KB
        compressed_size = os.path.getsize(output_path) / 1024  # KB
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        return True
        
    except Exception as e:
        print(f"转换过程中出现错误: {e}")
        return False

def check_url(url):     
    if(len(url)==len("https://m.youtube.com/watch?v=OHn0ls9m52c") and "youtube" in url):
        return True
    try:
        host = url.split('//')[1].split('/')[0].split(':')[0]
        port = 443 if url.startswith('https') else 80
        socket.create_connection((host, port), 2)
        return True
    except:
        return False

def open_file_windows(file_path):
    try:
        if not os.path.exists(file_path):
            print(f"错误：文件不存在 - {file_path}")
            return False
        if sys.platform != "win32":
            print("错误：此程序专为Windows系统设计")
            return False
        
        file_path = os.path.normpath(file_path)
        
        # 获取.bat文件所在目录
        bat_dir = os.path.dirname(file_path)
        
        print(f"批处理文件目录：{bat_dir}")
        
        # 检查必需文件是否在.bat文件目录中
        required_files = ['NapCatWinBootMain.exe', 'NapCatWinBootHook.dll']
        missing_files = []
        
        for file in required_files:
            full_path = os.path.join(bat_dir, file)
            if not os.path.exists(full_path):
                missing_files.append(file)
                print(f"警告：{file} 不存在于批处理文件目录")
        
        if missing_files:
            print("\n可能的原因：")
            print("1. 文件被移动到了其他位置")
            print("2. 批处理文件配置错误")
            
            # 尝试在上级目录查找
            print("\n尝试在上级目录查找...")
            parent_dir = os.path.dirname(bat_dir)
            for file in missing_files:
                parent_path = os.path.join(parent_dir, file)
                if os.path.exists(parent_path):
                    print(f"  找到 {file} 在：{parent_dir}")
        
        # 关键步骤：切换到.bat文件所在目录再执行
        original_dir = os.getcwd()  # 保存当前目录
        os.chdir(bat_dir)  # 切换到.bat文件目录
        
        
        # 执行.bat文件
        os.startfile(file_path)
        
        # 切换回原始目录（可选）
        os.chdir(original_dir)
        return True
        
    except Exception as e:
        print(f"打开文件时出错：{e}")
        return False

def image_symmetry_pillow(image_path, output_path, direction='left',quality=65):
    """
    使用Pillow进行图片对称变换（用于Windows测试）
    
    Args:
        image_path: 输入图片路径
        output_path: 输出图片路径
        direction: 对称方向 'left', 'right', 'top', 'bottom'
    
    Returns:
        bool: 是否成功
    """
    try:
        # 检查输入文件是否存在
        if not os.path.exists(image_path):
            print(f"错误：图片不存在 - {image_path}")
            return False
        
        # 打开图片
        img = Image.open(image_path)
        width, height = img.size
        print(f"图片尺寸: {width}x{height}")
        
        # 转换为RGBA模式（如果是调色板模式）
        if img.mode == 'P':
            img = img.convert('RGBA')
        
        # 转换为numpy数组
        img_array = np.array(img)
        
        # 根据方向处理
        if direction == 'left':
            # 左边不变，右边是左边的镜像
            split_point = width // 2
            left_part = img_array[:, :split_point, :]
            right_part = np.fliplr(left_part)
            result = np.hstack((left_part, right_part))
            
        elif direction == 'right':
            # 右边不变，左边是右边的镜像
            split_point = width // 2
            right_part = img_array[:, split_point:, :]
            left_part = np.fliplr(right_part)
            result = np.hstack((left_part, right_part))
            
        elif direction == 'top':
            # 上边不变，下边是上边的镜像
            split_point = height // 2
            top_part = img_array[:split_point, :, :]
            bottom_part = np.flipud(top_part)
            result = np.vstack((top_part, bottom_part))
            
        elif direction == 'bottom':
            # 下边不变，上边是下边的镜像
            split_point = height // 2
            bottom_part = img_array[split_point:, :, :]
            top_part = np.flipud(bottom_part)
            result = np.vstack((top_part, bottom_part))
            
        else:
            print(f"错误：不支持的对称方向 '{direction}'")
            return False
        
        # 保存结果
        result_img = Image.fromarray(result.astype('uint8'))
        # 转换为RGB（如果不需要透明度，可以减小文件大小）
        if result_img.mode == 'RGBA':
            # 创建白色背景
            background = Image.new('RGB', result_img.size, (255, 255, 255))
            background.paste(result_img, mask=result_img.split()[3])  # 使用alpha通道作为mask
            result_img = background
        
        # 保存图片，设置quality来压缩
        result_img.save(output_path, 'JPEG', quality=quality, optimize=True)
        # 保持原图模式
        if img.mode == 'RGBA':
            result_img = result_img.convert('RGBA')
        else:
            result_img = result_img.convert('RGB')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        result_img.save(output_path, quality=quality,optimize=True)
        print(f"图片已保存到: {output_path}")
        return True
        
    except Exception as e:
        print(f"处理图片时出错: {e}")
        return False

def send_group_message(group_id,token,text,name_list,emoji_list):
    url = "http://127.0.0.1:3000/send_group_msg"  
    headers = {
        "Authorization": token
    }
    message = []
    for qq in name_list:
        message.append({
            "type": "at",
            "data": {
                "qq": str(qq) 
            }
        })
        message.append({
            "type": "text",
            "data": {
                "text": " "
            }
        })
    message.append({
        "type": "text",
        "data": {
            "text": text
        }
    })
    for emoji in emoji_list:
        message.append({
            "type": "face",
            "data": {
                "id": int(emoji) 
            }
        })
    payload = {
    "group_id": group_id,
    "message": message
    }
    response = requests.post(url,headers=headers,data=json.dumps(payload),timeout=10)
    result = response.json()
    return result.get("retcode") 

def send_group_rps(group_id,token):
    url = "http://127.0.0.1:3000/send_group_msg"  # API地址
    headers = {
        "Authorization": token
    }
    message =   [
        {
            "type": "rps",
        }
    ]
    payload = {
        "group_id": group_id,
        "message": message
    }
    response = requests.post(url,headers=headers,data=json.dumps(payload),timeout=10)
    result = response.json()
    return result.get("retcode") 

def send_group_dice(group_id,token):
    url = "http://127.0.0.1:3000/send_group_msg"  # API地址
    headers = {
        "Authorization": token
    }
    message =   [
        {
            "type": "dice",
        }
    ]
    payload = {
        "group_id": group_id,
        "message": message
    }
    response = requests.post(url,headers=headers,data=json.dumps(payload),timeout=10)
    result = response.json()
    return result.get("retcode") 

def get_exact_message(message_id,token):
    url = "http://127.0.0.1:3000/get_msg"  # API地址
    headers = {
        "Authorization": token
    }
    payload = {
        "message_id": message_id
    }
    response = requests.post(url,headers=headers,data=json.dumps(payload),timeout=10)
    result = response.json()
    return result

def send_group_image(group_id,token,image_root):
    url = "http://127.0.0.1:3000/send_group_msg"  # API地址
    headers = {
        "Authorization": token
    }
    message =   [
        {
            "type": "image",
            "data": {
                "file": image_root
            }
        }
    ]
    payload = {
        "group_id": group_id,
        "message": message
    }
    response = requests.post(url,headers=headers,data=json.dumps(payload),timeout=10)
    result = response.json()
    return result.get("retcode") 

def send_group_video(group_id,token,video_root):
    url = "http://127.0.0.1:3000/send_group_msg"  # API地址
    headers = {
        "Authorization": token
    }
    message =   [
        {
            "type": "video",
            "data": {
                "file": video_root
            }
        }
    ]
    payload = {
        "group_id": group_id,
        "message": message
    }
    response = requests.post(url,headers=headers,data=json.dumps(payload),timeout=60)
    result = response.json()
    return result.get("retcode") 

def send_group_stream(group_id,token,video_root):
    # 获取视频格式信息（JSON格式）
    # 获取视频格式信息（JSON格式）
    cmd = [
        'yt-dlp',
        '-J',  # 输出JSON信息
        '--format-sort', 'res',  # 按分辨率排序
        video_root
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("获取视频信息失败")
        return None
    
    try:
        data = json.loads(result.stdout)
    except:
        1
        print("解析视频信息失败")
        return None
    data=data.get('formats', [])
    voice=data[0]['format_id']
    for item in data:
        if item['ext']=='mp4' or item['ext']=='mkv' or item['ext']=='webm':
            video=item['format_id']
            break
    cmd = f'yt-dlp --proxy http://127.0.0.1:7890 -f "{video}+{voice}" -o "/root/temp_video.mp4" "{video_root}"'
    exit_code = os.system(cmd)
    if exit_code != 0:
        print("下载失败")
        send_group_message(group_id,token,"下载失败……可能是反爬虫脚本发力了",[],[])
        return
    if os.path.exists("/root/temp_video.mp4"):
        os.system("ffmpeg -i /root/temp_video.mp4 -c:v libx264 -c:a aac /root/temp_video1.mp4")
        retcode=send_group_video(group_id,token,"/root/temp_video1.mp4")
    elif os.path.exists("/root/temp_video.mp4.webm"):
        os.system("ffmpeg -i /root/temp_video.mp4.webm -c:v libx264 -c:a aac /root/temp_video11.mp4")
        retcode=send_group_video(group_id,token,"/root/temp_video11.mp4")
    elif os.path.exists("/root/temp_video.mp4.mkv"):
        os.system("ffmpeg -i /root/temp_video.mp4.mkv -c:v libx264 -c:a aac /root/temp_video12.mp4")
        retcode=send_group_video(group_id,token,"/root/temp_video12.mp4")
    if os.path.exists("/root/temp_video.mp4"):
        os.remove("/root/temp_video.mp4")
        print("已清理临时文件")
    if os.path.exists("/root/temp_video1.mp4"):
        os.remove("/root/temp_video1.mp4")
        print("已清理临时文件")
    elif os.path.exists("/root/temp_video11.mp4"):
        os.remove("/root/temp_video11.mp4")
        print("已清理临时文件")
    elif os.path.exists("/root/temp_video12.mp4"):
        os.remove("/root/temp_video12.mp4")
        print("已清理临时文件")
    return retcode

def get_lastest_msg_time(token):
    url = "http://127.0.0.1:3000/get_recent_contact"
    payload = {"count": 1}
    headers = {
        "Authorization": token
    }
    try:
        response = requests.post(url, headers=headers,json=payload)
        data = response.json()
        if data.get("retcode") == 0 and data.get("status") == "ok":
            ans=data.get("data",[])
            ans=ans[0]['lastestMsg']['time']
            return ans
        else:
            last_msg_id=get_last_replied_message()
            if(last_msg_id!=0):
                ans=get_exact_message(last_msg_id,token)['data']['time']
                return ans
            else:
                return []
    except Exception as e:
        print(f"请求异常: {e}")
        last_msg_id=get_last_replied_message()
        if(last_msg_id!=0):
            ans=get_exact_message(last_msg_id,token)['data']['time']
            return ans
        else:
            return []  

def get_group_msg_history(group_id,count,token):
    payload = {"group_id":group_id,
               "count":count,
               }
    headers = {
        "Authorization": token
    }
    URL="http://127.0.0.1:3000/get_group_msg_history"
    try:
        response = requests.post(URL, headers=headers,json=payload)
        data = response.json()
        if data.get("retcode") == 0 and data.get("status") == "ok":
            return data.get("data", [])
        else:
            print(f"请求失败: {data.get('message')}")
            return []
    except Exception as e:
        print(f"请求异常: {e}")
        return []          

def get_group_message(start_time):
    message_dic={}
    for group in group_list:
        messages=get_group_msg_history(group,5,token)
        messages=messages['messages']
        msg_list=[]
        for dic in messages:
            msg_dic={}
            if(dic['time']<start_time):
                continue
            else:
                msg_dic['sender']=dic['user_id']
                msg_dic['time']=dic['time']
                msg_dic['message']=dic['message']
                msg_dic['nickname']=dic['sender']['nickname']
                msg_dic['message_id']=dic['message_id']
                if(dic['sender']['card']==''):
                    msg_dic['group_nickname']=msg_dic['nickname']
                else:
                    msg_dic['group_nickname']=dic['sender']['card']
                msg_list.append(msg_dic)
        message_dic[group]=msg_list
    return message_dic

def add_nsy_picture(group,sender,message,nsy):
    for part in message:
        if(part['type']=='reply'):
            for part2 in part['data']:
                if(part2['type']=='image'):
                    picture_url=part2['data']['url']
                    nsy_list=load_nsy_list()
                    folder_names=get_nsy_list()
                    for nsys in folder_names:
                        nsy_list[nsys]=nsys
                    if(not(nsy in nsy_list)):
                        nsy_list[nsy]=nsy
                        os.mkdir("/root/女声优/"+nsy)
                        send_group_message(group,token,"未找到该女声优，已创建新文件夹",[sender],[])    
                    nsy=nsy_list[nsy]
                    folder_path="/root/女声优/"+nsy
                    count = len(os.listdir(folder_path))
                    count+=1
                    download_image(picture_url,folder_path,str(count)+".png")
                    send_group_message(group,token,"已添加至文件夹 "+nsy+" 中",[sender],[])    
   
def extract_key_words(user_content):
    try:
        response = client_deepseek.chat.completions.create(
            model=deepseek_modle["chat"],
            messages=[
                {"role": "system", "content": '''你是一个关键词提取器。关键词用逗号分隔，只返回关键词本身，不要其他内容
                 如果你认为用户的输入和《BanG Dream!》中的内容有强相关（例如提到其中的角色例如丰川祥子，户山香澄或者地点商店街，RinG，CiRCLE），则将‘二次元世界’加入关键词列表中。
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
                      
def ai_reply(sender,user_content,group,qq,max_history=39):
    group_history=load_group_memory(group)
    user_content=sender+":"+user_content
    system_prompt=read_txt_file("透子本身")
    current_time = get_beijing_time()
    messages=[{"role": "system", "content": system_prompt}]
    messages.append({"role": "system", "content": "现在是服务器（北京时间）:"+current_time})
    key_words=extract_key_words(user_content)
    if('二次元世界' in key_words):
        print(1)
        messages.append({"role": "system", "content": read_txt_file('二次元世界')})
    group_history = group_history[-max_history:]
    messages.extend(group_history)
    messages.append({"role": "user", "content": user_content})
    response = client_deepseek.chat.completions.create(temperature=1.3,model=deepseek_modle["chat"],messages=messages,stream=False)
    reply=response.choices[0].message.content
    send_group_message(group,token,reply,[],[])
    group_history.append({"role": "user", "content": user_content})
    group_history.append({"role": "assistant", "content": reply})
    save_group_memory(group, group_history)

def rewrite_message(message):
    msg=[]
    for part in message:
        if(part['type']=='face'):
            msg.append({'type':'face','data':{'id':part['data']['id']}})
        elif(part['type']=='reply'):
            q=get_exact_message(part['data']['id'],token)
            q=q['data']
            q=q['message']
            q=rewrite_message(q)
            msg.append({'type':'reply',"data":q})
        elif(part['type']=='image'):
            msg.append({'type':'image','data':{'url':part['data']['url']}})
        elif(part['type']=='video'):
            msg.append({'type':'video','data':{'url':part['data']['url']}})
        elif(part['type']=='record'):
            msg.append({'type':'record','data':{'url':part['data']['url']}})
        elif(part['type']=='json'):
            try:
                q=part['data']['data']
                if((q[q.find("appid"):][8:18]=='1109937557')):
                    position=q.find('qqdocurl')
                    url=""
                    while(q[position]!='?'):
                        url+=q[position]
                        position+=1
                    url=url[11:]
                    bv=get_bv_from_b23(url)
                    BV=f"https://www.bilibili.com/video/{bv}"
                    msg.append({'type':'Bilibili','url':BV})
                elif(q[q.find("appid"):][7:16]=='100951776'):
                        position=q.find('https://b23.tv')
                        url=""
                        while(q[position]!='"'):
                            url+=q[position]
                            position+=1
                        bv=get_bv_from_b23(url)
                        BV=f"https://www.bilibili.com/video/{bv}"
                        msg.append({'type':'Bilibili','url':BV})
                elif(q[q.find("appid"):][7:17]=='1105517988'):
                        position=q.find('https://b23.tv')
                        url=""
                        while(q[position]!='"'):
                            url+=q[position]
                            position+=1
                        bv=get_bv_from_b23(url)
                        BV=f"https://www.bilibili.com/video/{bv}"
                        msg.append({'type':'Bilibili','url':BV})
                        
                else:
                    msg.append(part)
            except:
                try:
                    q=part['data']['data']
                    print(q.type())
                    msg.append(part)  
                except:
                    msg.append(part)  
        else:
            msg.append(part)      
    return msg

def process_message(group,sender,message,user_nickname):
    message=rewrite_message(message)
    print(message)
    nsy_list=load_nsy_list()
    folder_names=get_nsy_list()
    for nsy in folder_names:
        nsy_list[nsy]=nsy
    for part in message:
        if(not 'type' in part):
            continue
        if(part['type']=='forward'):
            break
        if(part['type']=='text'):
            if(part['data']['text']=='' or part['data']['text']==' '):
                continue
            group_history=load_group_memory(group)
            text=part['data']['text']
            user_content=user_nickname+":"+text
            group_history.append({"role": "user", "content": user_content})
            save_group_memory(group, group_history)
            if(text=='/help'):
                send_text=help_text
                send_group_message(group,token,send_text,[sender],[])
            elif(text[:14]=='/extract_video'):
                url=text[15:]
                if(check_url(url)):
                    send_group_message(group,token,"正在提取中，请稍等",[sender],[])
                    send_group_stream(group,token,url)
                else:
                    send_group_message(group,token,"小透子访问不了这个网址呢……",[sender],[5])
            elif(text=='/show_nsy_list'):
                nsy_list_str="已收录的女声优有：\n"
                nsy_page=get_nsy_list()
                for nsy in nsy_page:
                    nsy_list_str+=nsy+","
                send_group_message(group,token,nsy_list_str,[sender],[])
            elif(text[:13]=='/add_nickname'):
                if(sender in administrator_list):
                    try:
                        nickname=text[14:]
                        nickname=nickname.split(" ")[0]
                        realname=text[14:]
                        realname=realname.split(" ")[1]
                        if(realname in nsy_list):
                            add_nickname(nickname,realname)
                            send_group_message(group,token,f"已添加外号 {nickname} 对应 {realname}",[sender],[])
                        else:
                            send_group_message(group,token,f"未找到女声优 {realname}，请先添加女声优或检查名字是否正确",[sender],[5])
                    except:
                        send_group_message(group,token,"指令格式错误，请检查后重试",[sender],[5])
                else:
                    send_group_message(group,token,"您没有权限添加外号",[sender],[5])
            elif(text[:16]=='/delete_nickname'):
                if(sender in administrator_list):
                    try:
                        nickname=text[17:]
                        if(nickname in nsy_list):
                            delete_nickname(nickname)
                            send_group_message(group,token,f"已删除外号 {nickname}",[sender],[])
                        else:
                            send_group_message(group,token,f"未找到外号 {nickname}",[sender],[5])
                    except:
                        send_group_message(group,token,"指令格式错误，请检查后重试",[sender],[5])
                else:
                    send_group_message(group,token,"您没有权限删除外号",[sender],[5])
            elif(text in nsy_list):
                nsy=nsy_list[text] 
                folder_path="/root/女声优/"+nsy
                count = len(os.listdir(folder_path))
                if(count==0):
                    continue
                choose= random.randint(1,count)
                picture_path=folder_path+"/"+str(choose)+".png"
                send_group_image(group,token,picture_path)
            elif(text[:16]=='/add_nsy_picture'):
                if(sender in administrator_list):
                    nsy=text[17:]
                    add_nsy_picture(group,sender,message,nsy)
                else:   
                    send_group_message(group,token,"您没有权限添加女声优图片",[sender],[5])
            elif(text[:3]=='/对称'):
                for part in message:
                    if(part['type']=='reply'):
                        for part2 in part['data']:
                            if(part2['type']=='image'):
                                picture_url=part2['data']['url']
                                download_image(picture_url,"/root","temp.png")
                                image_path="/root/temp.png"
                                output_path="/root/temp_symmetry.png"
                                image_symmetry_pillow(image_path, output_path, direction='left')
                                compress_png_to_jpg(output_path,"/root/temp_symmetry.jpg", quality=85)
                                output_path="/root/temp_symmetry.jpg"
                                send_group_image(group,token,output_path)
                                os.remove("/root/temp.png")
                                os.remove("/root/temp_symmetry.png")
                                os.remove("/root/temp_symmetry.jpg")
            elif(text[:4]=='/左对称'):
                for part in message:
                    if(part['type']=='reply'):
                        for part2 in part['data']:
                            if(part2['type']=='image'):
                                picture_url=part2['data']['url']
                                download_image(picture_url,"/root","temp.png")
                                image_path="/root/temp.png"
                                output_path="/root/temp_symmetry.png"
                                image_symmetry_pillow(image_path, output_path, direction='left')
                                compress_png_to_jpg(output_path,"/root/temp_symmetry.jpg", quality=85)
                                output_path="/root/temp_symmetry.jpg"
                                send_group_image(group,token,output_path)
                                os.remove("/root/temp.png")
                                os.remove("/root/temp_symmetry.png")
                                os.remove("/root/temp_symmetry.jpg")
            elif(text[:4]=='/右对称'):
                for part in message:
                    if(part['type']=='reply'):
                        for part2 in part['data']:
                            if(part2['type']=='image'):
                                picture_url=part2['data']['url']
                                download_image(picture_url,"/root","temp.png")
                                image_path="/root/temp.png"
                                output_path="/root/temp_symmetry.png"
                                image_symmetry_pillow(image_path, output_path, direction='right')
                                compress_png_to_jpg(output_path,"/root/temp_symmetry.jpg", quality=85)
                                output_path="/root/temp_symmetry.jpg"
                                send_group_image(group,token,output_path)
                                os.remove("/root/temp.png")
                                os.remove("/root/temp_symmetry.png")
                                os.remove("/root/temp_symmetry.jpg")   
            elif(text[:4]=='/上对称'):
                for part in message:
                    if(part['type']=='reply'):
                        for part2 in part['data']:
                            if(part2['type']=='image'):
                                picture_url=part2['data']['url']
                                download_image(picture_url,"/root","temp.png")
                                image_path="/root/temp.png"
                                output_path="/root/temp_symmetry.png"
                                image_symmetry_pillow(image_path, output_path, direction='top')
                                compress_png_to_jpg(output_path,"/root/temp_symmetry.jpg", quality=85)
                                output_path="/root/temp_symmetry.jpg"
                                send_group_image(group,token,output_path)
                                os.remove("/root/temp.png")
                                os.remove("/root/temp_symmetry.png")
                                os.remove("/root/temp_symmetry.jpg")
            elif(text[:4]=='/下对称'):
                for part in message:
                    if(part['type']=='reply'):
                        for part2 in part['data']:
                            picture_url=part2['data']['url']
                            download_image(picture_url,"/root","temp.png")
                            image_path="/root/temp.png"
                            output_path="/root/temp_symmetry.png"
                            image_symmetry_pillow(image_path, output_path, direction='bottom')
                            compress_png_to_jpg(output_path,"/root/temp_symmetry.jpg", quality=85)
                            output_path="/root/temp_symmetry.jpg"
                            send_group_image(group,token,output_path)
                            os.remove("/root/temp.png")
                            os.remove("/root/temp_symmetry.png")
                            os.remove("/root/temp_symmetry.jpg")
        elif(part['type']=='at' and part['data']['qq']==bot_qq):
                for part2 in message:
                    if(part2['type']=='text'):
                        if(part2['data']['text']=='' or part2['data']['text']==' '):
                            continue
                        text=part2['data']['text'][1:]
                        if(text=='/help'):
                            send_text=help_text
                            send_group_message(group,token,send_text,[sender],[])
                        elif(text[:14]=='/extract_video'):
                            url=text[15:]
                            if(check_url(url)):
                                send_group_message(group,token,"正在提取中，请稍等",[sender],[])
                                send_group_stream(group,token,url)
                            else:
                                send_group_message(group,token,"小透子访问不了这个网址呢……",[sender],[5])
                        elif(text=='/show_nsy_list'):
                            nsy_list_str="已收录的女声优有：\n"
                            nsy_page=get_nsy_list()
                            for nsy in nsy_page:
                                nsy_list_str+=nsy+","
                            send_group_message(group,token,nsy_list_str,[sender],[])
                        elif(text[:13]=='/add_nickname'):
                            if(sender in administrator_list):
                                try:
                                    nickname=text[14:]
                                    nickname=nickname.split(" ")[0]
                                    realname=text[14:]
                                    realname=realname.split(" ")[1]
                                    if(realname in nsy_list):
                                        add_nickname(nickname,realname)
                                        send_group_message(group,token,f"已添加外号 {nickname} 对应 {realname}",[sender],[])
                                    else:
                                        send_group_message(group,token,f"未找到女声优 {realname}，请先添加女声优或检查名字是否正确",[sender],[5])
                                except:
                                    send_group_message(group,token,"指令格式错误，请检查后重试",[sender],[5])
                            else:
                                send_group_message(group,token,"您没有权限添加外号",[sender],[5])
                        elif(text[:16]=='/delete_nickname'):
                            if(sender in administrator_list):
                                try:
                                    nickname=text[17:]
                                    delete_nickname(nickname)
                                    send_group_message(group,token,f"已删除外号 {nickname}",[sender],[])
                                except:
                                    send_group_message(group,token,"指令格式错误，请检查后重试",[sender],[5])
                            else:
                                send_group_message(group,token,"您没有权限删除外号",[sender],[5])
                        elif(text in nsy_list):
                            nsy=nsy_list[text]
                            folder_path="/root/女声优/"+nsy
                            count = len(os.listdir(folder_path))
                            if(count==0):
                                continue
                            choose= random.randint(1,count)
                            picture_path=folder_path+"/"+str(choose)+".png"
                            send_group_image(group,token,picture_path)
                        elif(text[:16]=='/add_nsy_picture' ):
                            if(sender in administrator_list):
                                nsy=text[17:]
                                add_nsy_picture(group,sender,message,nsy)
                            else:
                                send_group_message(group,token,"您没有权限添加女声优图片",[sender],[5])
                        elif(text[:3]=='/对称'):
                            for part in message:
                                if(part['type']=='reply'):
                                    for part2 in part['data']:
                                        if(part2['type']=='image'):
                                            picture_url=part2['data']['url']
                                            download_image(picture_url,"/root","temp.png")
                                            image_path="/root/temp.png"
                                            output_path="/root/temp_symmetry.png"
                                            image_symmetry_pillow(image_path, output_path, direction='left')
                                            compress_png_to_jpg(output_path,"/root/temp_symmetry.jpg", quality=85)
                                            output_path="/root/temp_symmetry.jpg"
                                            send_group_image(group,token,output_path)
                                            os.remove("/root/temp.png")
                                            os.remove("/root/temp_symmetry.png")
                                            os.remove("/root/temp_symmetry.jpg")
                        elif(text[:4]=='/左对称'):
                            for part in message:
                                if(part['type']=='reply'):
                                    for part2 in part['data']:
                                        if(part2['type']=='image'):
                                            picture_url=part2['data']['url']
                                            download_image(picture_url,"/root","temp.png")
                                            image_path="/root/temp.png"
                                            output_path="/root/temp_symmetry.png"
                                            image_symmetry_pillow(image_path, output_path, direction='left')
                                            compress_png_to_jpg(output_path,"/root/temp_symmetry.jpg", quality=85)
                                            output_path="/root/temp_symmetry.jpg"
                                            send_group_image(group,token,output_path)
                                            os.remove("/root/temp.png")
                                            os.remove("/root/temp_symmetry.png")
                                            os.remove("/root/temp_symmetry.jpg")
                        elif(text[:4]=='/右对称'):
                            for part in message:
                                if(part['type']=='reply'):
                                    for part2 in part['data']:
                                        if(part2['type']=='image'):
                                            picture_url=part2['data']['url']
                                            download_image(picture_url,"/root","temp.png")
                                            image_path="/root/temp.png"
                                            output_path="/root/temp_symmetry.png"
                                            image_symmetry_pillow(image_path, output_path, direction='right')
                                            compress_png_to_jpg(output_path,"/root/temp_symmetry.jpg", quality=85)
                                            output_path="/root/temp_symmetry.jpg"
                                            send_group_image(group,token,output_path)
                                            os.remove("/root/temp.png")
                                            os.remove("/root/temp_symmetry.png")
                                            os.remove("/root/temp_symmetry.jpg")   
                        elif(text[:4]=='/上对称'):
                            for part in message:
                                if(part['type']=='reply'):
                                    for part2 in part['data']:
                                        if(part2['type']=='image'):
                                            picture_url=part2['data']['url']
                                            download_image(picture_url,"/root","temp.png")
                                            image_path="/root/temp.png"
                                            output_path="/root/temp_symmetry.png"
                                            image_symmetry_pillow(image_path, output_path, direction='top')
                                            compress_png_to_jpg(output_path,"/root/temp_symmetry.jpg", quality=85)
                                            output_path="/root/temp_symmetry.jpg"
                                            send_group_image(group,token,output_path)
                                            os.remove("/root/temp.png")
                                            os.remove("/root/temp_symmetry.png")
                                            os.remove("/root/temp_symmetry.jpg")
                        elif(text[:4]=='/下对称'):
                            for part in message:
                                if(part['type']=='reply'):
                                    for part2 in part['data']:
                                        picture_url=part2['data']['url']
                                        download_image(picture_url,"/root","temp.png")
                                        image_path="/root/temp.png"
                                        output_path="/root/temp_symmetry.png"
                                        image_symmetry_pillow(image_path, output_path, direction='bottom')
                                        compress_png_to_jpg(output_path,"/root/temp_symmetry.jpg", quality=85)
                                        output_path="/root/temp_symmetry.jpg"
                                        send_group_image(group,token,output_path)
                                        os.remove("/root/temp.png")
                                        os.remove("/root/temp_symmetry.png")
                                        os.remove("/root/temp_symmetry.jpg")
                        else:
                            ai_reply(user_nickname,text,group,sender)
                        
        elif(part['type']=='Bilibili'):
                url=part['url']
                send_group_message(group,token,"正在提取中，请稍等",[sender],[])
                try:
                    send_group_stream(group,token,url)
                    send_group_message(group,token,"提取成功！",[],[])
                except Exception as e:
                    send_group_message(group,token,"提取失败/(ㄒoㄒ)/~~是不是b站反爬虫发力了",[],[])

def init():
    nsy_list=load_nsy_list()
    folder_names = get_nsy_list()
    for nsy in folder_names:
        nsy_list[nsy]=nsy
    last_time=get_lastest_msg_time(token)-25
    print("后台监控中")
    try:
        while True:
            time.sleep(1)
            messages=get_group_message(last_time)
            for group in messages:
                for message in messages[group]:
                    if(not (is_msg_replied(message['message_id'])) and message['sender']!=int(bot_qq)):
                        process_message(group,message['sender'],message['message'],message['nickname'])
                        save_replied_message(message['message_id'])
            if(get_lastest_msg_time(token)==[]):
                continue
            else:
                last_time=get_lastest_msg_time(token)-25
    except KeyboardInterrupt:
        print("\n监控结束")
        
    
if __name__ == "__main__":  
    
    '''if sys.platform == "win32":
        if file_to_open:
            open_file_windows(file_to_open)
            time.sleep(1)
            pyautogui.hotkey('win', 'down')
            time.sleep(2)
            q=auto_login_with_select("90c4868773a1") 
    if(q):
        while(1):
            os.system("clear")
            cout("请选择你要进行的操作：")
            cout("1.发送群消息")
            cout("2.发送私聊消息")
            cout("0.退出")
            key = msvcrt.getch()
            if(key==b'0'):
                break
            else:
                os.system("clear")    
                if(key==b'1'):
                    print(1)
                    send_group_msg()
                else:
                    break'''
    init()
