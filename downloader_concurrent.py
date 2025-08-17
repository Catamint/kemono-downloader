import os
import aiohttp
import aiofiles
import asyncio
from file import set_hidden_windows
from cilent_session import create_session

# ---- 1. 文件夹命名 & .post_id 管理 ----

def get_unique_folder(base_path, title, post_id):
    sanitized_title = title
    count = 1
    while True:
        folder_name = sanitized_title if count == 1 else f"{sanitized_title}-{count}"
        folder_path = os.path.join(base_path, folder_name)
        post_id_file = os.path.join(folder_path, ".post_id")
        if os.path.exists(folder_path):
            if os.path.exists(post_id_file):
                with open(post_id_file, "r", encoding="utf-8") as f:
                    existing_id = f.read().strip()
                if existing_id == str(post_id):
                    return folder_path
            count += 1
        else:
            os.makedirs(folder_path)
            with open(post_id_file, "w", encoding="utf-8") as f:
                f.write(str(post_id))
            set_hidden_windows(post_id_file)
            return folder_path


# ---- 2. 图片下载（.temp后缀，完毕重命名） ----

async def download_image(session, url, save_path, sem):
    temp_path = save_path + ".temp"
    async with sem:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(temp_path, "wb") as f:
                        await f.write(await resp.read())
                    os.replace(temp_path, save_path)
                    print(f"✅ 图片下载完成: {save_path}")
                else:
                    print(f"❌ 图片下载失败: {url} ({resp.status})")
        except Exception as e:
            print(f"❌ 图片下载异常: {url} - {e}")


# ---- 3. 大文件断点续传（.temp后缀，完毕重命名） ----

async def download_with_resume(session, url, save_path, sem, chunk_size=1024 * 1024):
    temp_path = save_path + ".temp"
    async with sem:
        try:
            file_size = 0
            if os.path.exists(temp_path):
                file_size = os.path.getsize(temp_path)
            headers = {"Range": f"bytes={file_size}-"} if file_size else {}

            async with session.get(url, headers=headers) as resp:
                if resp.status in (200, 206):  # 支持断点
                    mode = "ab" if file_size else "wb"
                    async with aiofiles.open(temp_path, mode) as f:
                        async for chunk in resp.content.iter_chunked(chunk_size):
                            await f.write(chunk)
                    # 完整性校验
                    content_length = resp.headers.get("Content-Range") or resp.headers.get("Content-Length")
                    try:
                        total = int(content_length.split("/")[-1]) if content_length and "/" in content_length else int(
                            content_length or 0)
                        final_size = os.path.getsize(temp_path)
                        if total and final_size >= total:
                            os.replace(temp_path, save_path)
                            print(f"✅ 大文件下载完成: {save_path}")
                        else:
                            print(f"⚠️ 断点续传未完成，文件已部分保存: {temp_path}")
                    except:
                        # 没有总长度时直接重命名
                        os.replace(temp_path, save_path)
                        print(f"✅ 大文件下载完成: {save_path}")
                else:
                    print(f"❌ 大文件下载失败: {url} ({resp.status})")
        except Exception as e:
            print(f"❌ 大文件下载异常: {url} - {e}")


# ---- 4. 主保存调度 ----

async def save_post_concurrent(post, base_path, session, sem, update_status=None):
    folder_path = get_unique_folder(base_path, post["title"], post["id"])
    image_exts = {"jpg", "jpeg", "png", "gif", "webp"}

    download_tasks = []
    for img in post["images"]:
        save_path = os.path.join(folder_path, img["name"])
        ext = img["name"].rsplit(".", 1)[-1].lower()
        if ext in image_exts:
            download_tasks.append(download_image(session, img["url"], save_path, sem))
        else:
            download_tasks.append(download_with_resume(session, img["url"], save_path, sem))
    if download_tasks:
        await asyncio.gather(*download_tasks)

    for f in post.get("files", []):
        save_path = os.path.join(folder_path, f["name"])
        await download_with_resume(session, f["url"], save_path, sem)

    if post.get("external_links"):
        links_path = os.path.join(folder_path, "external_links.txt")
        async with aiofiles.open(links_path, "w", encoding="utf-8") as f:
            await f.write("\n".join(post["external_links"]))
        print(f"📝 外链已保存：{links_path}")

    if update_status:
        await update_status(post["id"], finished=True)


async def download_streamed_posts(post_stream, base_path, concurrency=10, post_concurrency=2, update_status=None):
    """
    post_stream: 异步生成器
    base_path: 保存目录
    concurrency: 每个帖子内部最大下载并发
    post_concurrency: 同时处理的帖子数量
    """
    sem = asyncio.Semaphore(concurrency)
    post_sem = asyncio.Semaphore(post_concurrency)
    async with create_session() as session:
        download_post_tasks = []
        async for post in post_stream:
            await post_sem.acquire()
            t = asyncio.create_task(
                save_post_concurrent(post, base_path, session, sem, update_status)
            )
            t.add_done_callback(lambda fut: post_sem.release())
            download_post_tasks.append(t)
        if download_post_tasks:
            await asyncio.gather(*download_post_tasks)
