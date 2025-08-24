# KemonoDownloader CLI

高并发 Kemono 批量下载器

## 快速开始

### 1. **依赖安装**
```bash
pip install aiohttp aiofiles
```
### 2. 运行下载器
```bash
python main.py <kemono主页url> [下载目录] [并发图片数] [并发帖子数] [日期模式] [代理]
```
参数说明：
```
<kemono主页url>
示例：https://kemono.su/fanbox/user/123456

[下载目录]
默认：./download

[并发图片数]
每个帖子内同时下载图片的最大数量（如 16）

[并发帖子数]
同时下载的帖子数量（如 2）

[日期模式]
0 = 不加日期, 1 = 日期前缀, 2 = 日期后缀

[代理]
请求时使用的网络代理
```
使用示例：
```bash
python main.py https://kemono.su/fanbox/user/123456 ./download 16 2 1 http://127.0.0.1:7890
```
### 3. 元数据与断点续传
状态文件会自动写入跨平台目录，无需手动管理

再次运行不会重复下载已完成的帖子

