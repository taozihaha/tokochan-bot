import os
import time
import asyncio
import aiofiles
from PIL import Image
import numpy as np

async def download_image(session, url: str, save_path: str):
    async with session.get(url) as resp:
        if resp.status == 200:
            async with aiofiles.open(save_path, 'wb') as f:
                await f.write(await resp.read())
        else:
            print(f"下载图片失败，状态码: {resp.status}")

async def _delayed_delete(delay: float, *files):
    await asyncio.sleep(delay)
    for f in files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception as e:
                print(f"删除文件失败 {f}: {e}")

async def image_symmetry(session, temp_base: str, delay: float, 
                         group_id: int, direction: str, image_url: str,
                         send_func):
    timestamp = int(time.time())
    temp_png = f"{temp_base}temp_{timestamp}.png"
    temp_sym_png = f"{temp_base}temp_symmetry_{timestamp}.png"
    temp_jpg = f"{temp_base}temp_symmetry_{timestamp}.jpg"
    
    await download_image(session, image_url, temp_png)
    
    img = Image.open(temp_png)
    width, height = img.size
    if img.mode == 'P':
        img = img.convert('RGBA')
    img_array = np.array(img)
    
    if direction == 'left':
        split_point = width // 2
        left_part = img_array[:, :split_point, :]
        right_part = np.fliplr(left_part)
        result = np.hstack((left_part, right_part))
    elif direction == 'right':
        split_point = width // 2
        right_part = img_array[:, split_point:, :]
        left_part = np.fliplr(right_part)
        result = np.hstack((left_part, right_part))
    elif direction == 'top':
        split_point = height // 2
        top_part = img_array[:split_point, :, :]
        bottom_part = np.flipud(top_part)
        result = np.vstack((top_part, bottom_part))
    else:
        split_point = height // 2
        bottom_part = img_array[split_point:, :, :]
        top_part = np.flipud(bottom_part)
        result = np.vstack((top_part, bottom_part))
    
    result_img = Image.fromarray(result.astype('uint8'))
    if result_img.mode == 'RGBA':
        background = Image.new('RGB', result_img.size, (255, 255, 255))
        background.paste(result_img, mask=result_img.split()[3])
        result_img = background
    result_img.save(temp_sym_png)
    
    img = Image.open(temp_sym_png)
    if img.mode == 'RGBA':
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    img.save(temp_jpg, 'JPEG', quality=85, optimize=True)
    
    await send_func(group_id, temp_jpg)
    
    asyncio.create_task(_delayed_delete(delay, temp_png, temp_sym_png, temp_jpg))
