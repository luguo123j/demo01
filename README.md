# 小说爬虫应用 (Novel Crawler)

一个基于 Flask 的多来源小说爬取应用，可以聚合多个站点搜索并下载小说内容。

## 功能特性

- 🔍 **搜索功能**: 输入小说名称进行搜索
- 🌐 **多源聚合**: 支持多来源并发搜索、去重和排序
- 📥 **下载功能**: 一键下载整本小说为 TXT 文件
- 🔁 **自动回退**: 章节下载失败时自动尝试其他来源补齐
- 📊 **进度显示**: 实时显示下载进度
- 📜 **下载历史**: 查看下载历史记录
- 🩺 **可观测性**: 来源健康检查和运行指标接口
- 🎨 **美观界面**: 响应式设计，简洁易用
- ⚠️ **错误处理**: 友好的错误提示

## 技术栈

- **后端**: Python Flask
- **前端**: HTML5 + CSS3 + JavaScript
- **爬虫库**: requests, beautifulsoup4, lxml, fake-useragent

## 安装步骤

1. 克隆或下载项目

2. 安装依赖:
```bash
pip install -r requirements.txt
```

3. 启动应用:
```bash
python app.py
```

4. 在浏览器中访问: http://localhost:5000

## 项目结构

```
demo01/
├── app.py                      # Flask应用主入口
├── config.py                   # 配置文件
├── requirements.txt            # Python依赖清单
├── README.md                   # 项目说明文档
├── logs/                       # 日志目录
│   └── app.log
├── downloads/                  # 下载的小说保存目录
├── templates/                  # Jinja2模板目录
│   └── index.html             # 主页模板
├── static/                     # 静态资源目录
│   ├── css/
│   │   └── style.css          # 样式文件
│   └── js/
│       └── app.js             # 前端逻辑脚本
├── crawler/                    # 爬虫模块目录
│   ├── __init__.py
│   ├── base_crawler.py        # 基础爬虫类
│   ├── novel_crawler.py       # 小说爬虫核心逻辑
│   ├── parser.py              # HTML解析器
│   └── utils.py               # 工具函数
└── services/                   # 业务逻辑层
    ├── __init__.py
    ├── search_service.py      # 搜索服务
    ├── download_service.py     # 下载服务
    └── file_service.py        # 文件处理服务
```

## 使用说明

### 搜索小说

1. 在搜索框中输入小说名称
2. 点击"搜索"按钮或按 Enter 键
3. 查看搜索结果列表

### 下载小说

1. 在搜索结果中找到目标小说
2. 点击"下载"按钮
3. 等待下载完成
4. 点击"下载文件"按钮保存到本地

### 查看下载历史

- 页面底部自动显示下载历史
- 点击"刷新历史"按钮更新历史记录

## 配置说明

在 `config.py` 中可以修改以下配置:

- `BASE_URL`: 爬虫目标网站地址
- `TIMEOUT`: 请求超时时间（秒）
- `MAX_RETRIES`: 最大重试次数
- `REQUEST_DELAY`: 请求间隔时间（秒）
- `DOWNLOAD_DIR`: 小说文件保存目录
- `FL_PORT`: Flask 应用端口

多来源配置示例:

```python
SOURCES = {
    'bqg353': {
        'enabled': True,
        'adapter': 'bqg353_api',
        'display_name': '笔趣阁 353',
        'base_url': 'https://www.bqg353.xyz',
        'weight': 100,
    },
    'bqg356': {
        'enabled': True,
        'adapter': 'bqg353_api',
        'display_name': '笔趣阁 356',
        'base_url': 'https://www.bqg356.cc',
        'weight': 90,
    }
}
```

## 注意事项

1. 请遵守目标网站的 robots.txt 和服务条款
2. 合理设置请求间隔，避免对服务器造成过大压力
3. 本项目仅供学习交流使用
4. 网站结构可能发生变化，需要相应调整解析器代码

## API 接口

### 搜索接口
- **URL**: `GET /api/search`
- **参数**: `keyword` (必填)、`source_id` (可选)、`limit` (可选)、`only_available` (可选)
- **返回**: JSON 格式的搜索结果，包含 `novels`、`sources`、`partial_success`、`degraded_reason`

### 下载接口
- **URL**: `POST /api/download`
- **参数**: JSON 格式，包含 `novel_url`，可选 `source_id`、`start_chapter`、`end_chapter`
- **返回**: JSON 格式，包含 `task_id`

### 状态查询接口
- **URL**: `GET /api/status/<task_id>`
- **返回**: JSON 格式的下载状态，包含来源信息与补齐统计字段

### 来源列表接口
- **URL**: `GET /api/sources`
- **返回**: JSON 格式的来源配置与启用状态

### 来源健康检查接口
- **URL**: `GET /api/health/sources`
- **参数**: `keyword` (可选，默认 `武动`)
- **返回**: JSON 格式的来源可用性检测结果

### 指标接口
- **URL**: `GET /api/metrics`
- **返回**: JSON 格式的搜索/下载成功率与来源时延指标

### 下载历史接口
- **URL**: `GET /api/history`
- **返回**: JSON 格式的历史记录

### 文件下载接口
- **URL**: `GET /api/download/<filename>`
- **返回**: TXT 文件

## 常见问题

### 搜索不到小说
- 确认小说名称拼写正确
- 该小说可能不在目标网站上
- 网站结构可能已变化，需要更新解析器

### 下载失败
- 检查网络连接
- 查看日志文件 `logs/app.log` 获取详细错误信息
- 可能是网站反爬虫机制触发

### 文件乱码
- 检查文件编码是否为 UTF-8
- 可能需要调整解析器的文本清理逻辑

## 许可证

MIT License

## 免责声明

本项目仅供学习交流使用，请勿用于商业用途。使用者需自行承担使用本工具产生的法律后果。
