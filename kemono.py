import re

import aiohttp
from cilent_session import session_manager
import json

from file import sanitize_filename, rename_list

async def extract_attachments_urls(user_url: str) -> list[dict]:
    user = user_url.split('https://kemono.cr/')[-1]
    try:
        session = session_manager.create_session(headers={'Accept': 'text/css'})
        posts = await GetPosts(user, session)
        detailed_posts = await GetPostsAttachments(posts, session)
    finally:
        await session.close()

    result = []

    for post in detailed_posts:
        image_raw = []
        other_files = []
        external_links = extract_external_links(post["html_content"])
        title = sanitize_filename(post["title"])
        day = post["day"]
        id = post["id"]
        base_url = "https://kemono.cr/data"

        for att in post["attachments"]:
            name = att.get("name", "")
            path = att.get("path", "")
            if not name or not path:
                continue

            ext = name.lower().split('.')[-1]
            url = base_url + path
            if ext in ("jpg", "jpeg", "png", "gif", "webp"):
                image_raw.append({"url": url, "name": name})
            else:
                other_files.append({"url": url, "name": name})

        # 重命名图片
        images = rename_list(image_raw)

        result.append({
            "title": title,
            "url": post["url"],
            "id": id,
            "day": day,
            "images": images,
            "files": other_files,
            "external_links": external_links
        })

    return result


async def GetPosts(user: str, session: aiohttp.ClientSession) -> list[dict]:
    n = 0
    getPostsUrl = f"https://kemono.cr/api/v1/{user}/posts"
    posts = []

    while True:
        url = f"{getPostsUrl}?o={n}"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    temp_text = await response.text()
                    temp_list = json.loads(temp_text)
                    if temp_list:
                        posts.extend(temp_list)
                        n += 50
                    else:
                        break
                else:
                    print(f"GetPosts HTTP error {response}")
                    break
        except Exception as e:
            print("GetPosts error", e)
            break

    return posts


async def GetPostsAttachments(posts: list[dict], session: aiohttp.ClientSession) -> list[dict]:
    all_attachments = []

    for post in posts:
        post_id = post["id"]
        day = post["published"].split("T")[0]
        title = post["title"]
        user = post["user"]
        service = post["service"]

        post_url = f'https://kemono.cr/api/v1/{service}/user/{user}/post/{post_id}'
        attachments = []
        html_content = ""

        try:
            async with session.get(post_url) as response:
                if response.status == 200:
                    temp_text = await response.text()
                    data = json.loads(temp_text)
                    html_content = data['post'].get('content', '')
                    file = data["post"].get("file")
                    attachments = [file] + data["post"]["attachments"] if file else data["post"]["attachments"]

                    all_attachments.append({
                        "title": title,
                        "url": f'https://kemono.cr/{service}/user/{user}/post/{post_id}',
                        "id": post_id,
                        "day":day,
                        "html_content": html_content,
                        "attachments": attachments
                    })
                else:
                    print(f"GetPostsAttachments HTTP error {response.status}")
        except Exception as e:
            print("GetPostsAttachments error", e)

    return all_attachments

async def extract_attachments_urls_streamed(
    user_url: str,
    day_mode: int = 0  # 0: 不加日期, 1: 前缀, 2: 后缀
):
    """
    边拉边产出单个帖子资源
    :param user_url: 用户主页链接
    :param day_mode: 日期模式（0=无，1=前缀，2=后缀）
    """
    user = user_url.split('https://kemono.cr/')[-1]
    try:
        session = session_manager.create_session(headers={'Accept': 'text/css'})
        posts = await GetPosts(user, session)
        for post in posts:
            post_id = post["id"]
            day = post["published"].split("T")[0]
            title = post["title"]
            user_id = post["user"]
            service = post["service"]
            post_url = f'https://kemono.cr/api/v1/{service}/user/{user_id}/post/{post_id}'
            url_out = f'https://kemono.cr/{service}/user/{user_id}/post/{post_id}'

            async with session.get(post_url) as response:
                if response.status == 200:
                    temp_text = await response.text()
                    data = json.loads(temp_text)
                    html_content = data['post'].get('content', '')
                    file = data["post"].get("file")
                    attachments = [file] + data["post"]["attachments"] if file else data["post"]["attachments"]

                    # --- 处理文件夹title ---
                    cleaned_title = sanitize_filename(title)
                    if day_mode == 1:
                        folder_title = f"{day}_{cleaned_title}"
                    elif day_mode == 2:
                        folder_title = f"{cleaned_title}_{day}"
                    else:
                        folder_title = cleaned_title

                    # 资源分类
                    image_raw, other_files = [], []
                    base_url = "https://kemono.cr/data"
                    for att in attachments:
                        name = att.get("name", "")
                        path = att.get("path", "")
                        if not name or not path:
                            continue
                        ext = name.lower().split('.')[-1]
                        url = base_url + path
                        if ext in ("jpg", "jpeg", "png", "gif", "webp"):
                            image_raw.append({"url": url, "name": name})
                        else:
                            other_files.append({"url": url, "name": name})

                    images = rename_list(image_raw)
                    external_links = extract_external_links(html_content)

                    yield {
                        "title": folder_title,
                        "url": url_out,
                        "id": post_id,
                        "day": day,
                        "images": images,
                        "files": other_files,
                        "external_links": external_links
                    }

    except Exception as e:
        print("GetPostsAttachments error", e)

    finally:
        await session.close()

def extract_external_links(html: str) -> list[str]:
    if not html:
        return []
    return re.findall(r'https?://(?:mega|drive|dropbox|puu\\.sh)[^\\s\"<>]+', html)

