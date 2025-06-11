import asyncio
import sys
import os

from downloader_concurrent import download_streamed_posts
from kemono import extract_attachments_urls_streamed
from meta_dir import load_status, save_status

async def update_status_func(user_id, post_id, finished=True, extra=None):
    """更新每个作者（user_id）单独的状态文件"""
    status = load_status(user_id)
    entry = {"finished": finished}
    if extra:
        entry.update(extra)
    status[str(post_id)] = entry
    save_status(user_id, status)

async def main():
    if len(sys.argv) < 2:
        print("用法: python main.py <kemono用户主页url> [下载目录] [并发图片数] [并发帖子数] [日期模式]")
        print("例: python main.py https://kemono.su/fanbox/user/123456 ./download 16 2 1")
        print("日期模式: 0=无日期, 1=前缀, 2=后缀")
        return

    url = sys.argv[1]
    save_dir = sys.argv[2] if len(sys.argv) > 2 else "./download"
    concurrency = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    post_concurrency = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    day_mode = int(sys.argv[5]) if len(sys.argv) > 5 else 0

    # 自动创建下载目录
    os.makedirs(save_dir, exist_ok=True)

    # 提取user_id
    # 支持 https://kemono.su/fanbox/user/123456 也支持 https://kemono.su/api/v1/fanbox/user/123456
    import re
    m = re.search(r"/user/(\d+)", url)
    if not m:
        print("URL格式不正确，请用 https://kemono.su/fanbox/user/123456")
        return
    user_id = m.group(1)

    # 跳过已完成帖子
    status = load_status(user_id)
    async def filtered_stream():
        async for post in extract_attachments_urls_streamed(url, day_mode=day_mode):
            # 如果已完成则跳过
            if status.get(str(post["id"]), {}).get("finished"):
                print(f"跳过已完成：{post['title']}")
                continue
            yield post

    async def update_status_callback(post_id, finished=True, extra=None):
        await update_status_func(user_id, post_id, finished, extra)

    await download_streamed_posts(
        filtered_stream(),
        save_dir,
        concurrency=concurrency,
        post_concurrency=post_concurrency,
        update_status=update_status_callback
    )

if __name__ == "__main__":
    asyncio.run(main())
