# Edge Bookmark Organizer

一个用于整理 Edge/Chrome 浏览器导出书签的命令行工具。支持 **去重**、**失效链接检测**、**AI 智能分类**，并生成可直接导入浏览器的书签文件和 Markdown 分析报告。

## 功能

- **解析** Netscape Bookmark HTML 格式（Edge / Chrome / Firefox 导出格式）
- **URL 去重** — 自动归一化 URL（统一 http/https、去除 www、清理追踪参数），按最新日期保留
- **失效检测** — 异步并发 HTTP GET 检测，快速标记不可访问的链接
- **AI 智能分类** — 调用 DeepSeek API，根据书签标题和 URL 自动分配到 17 个预定义类别
- **输出** — 生成可导入浏览器的 HTML 书签文件 + Markdown 分析报告

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

如果需要 AI 分类功能，将 DeepSeek API Key 配置到 `.env` 文件：

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

或者通过命令行参数传入：

```bash
python main.py --api-key sk-your-key
```

### 3. 导出书签

从 Edge 浏览器导出书签：**设置** → **导入或导出** → **导出收藏夹**，得到 HTML 文件。

### 4. 运行

```bash
# 完整流程：去重 + 链接检测 + AI 分类
python main.py -i favorites.html

# 仅去重和分类，跳过链接检测（更快）
python main.py -i favorites.html --skip-link-check

# 仅去重，跳过链接检测和分类
python main.py -i favorites.html --skip-link-check --skip-classify

# 自动检测当前目录下的书签文件
python main.py
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `-i` / `--input` | 输入的 HTML 书签文件路径（省略则自动检测） |
| `-o` / `--output` | 输出 HTML 文件路径（默认 `organized_bookmarks.html`） |
| `--report` | 输出 Markdown 报告路径（默认 `report.md`） |
| `--skip-link-check` | 跳过链接失效检测 |
| `--skip-classify` | 跳过 AI 分类，保留原始文件夹结构 |
| `--keep-broken` | 在输出 HTML 中保留失效链接 |
| `--concurrency` | 链接检测的最大并发数（默认 20） |
| `--api-key` | DeepSeek API Key（覆盖环境变量） |

## 输出文件

### organized_bookmarks.html

去重、分类后的书签文件，可直接导入 Edge / Chrome / Firefox：

```
收藏夹栏/
├── AI/
│   ├── ComputerVision/
│   ├── MachineLearning/
│   ├── NLP/
│   └── Tools/
├── Programming/
│   ├── C++/
│   ├── Go/
│   ├── Python/
│   ├── Web/
│   └── General/
├── DevTools/
├── Academic/
│   └── Research/
├── Algorithms/
│   └── DataStructures/
├── Finance/
│   └── Investing/
├── Career/
│   └── Jobs/
├── Utilities/
│   └── OnlineTools/
├── News/
│   └── Media/
└── Other/
```

### report.md

Markdown 格式的分析报告，包含：

- **概览** — 总数、去重数、失效数、分类数
- **重复书签** — 列出每组重复 URL 的详情
- **失效链接** — 列出所有不可访问的 URL 及错误原因
- **分类分布** — 各类别的书签数量统计
- **分类变更** — 书签从原始文件夹到新分类的映射

## 预定义分类

| 类别 | 说明 |
|------|------|
| Programming/C++ | C++ 相关 |
| Programming/Go | Go 相关 |
| Programming/Python | Python 相关 |
| Programming/Web | 前端 / Web 开发 |
| Programming/General | 通用编程 |
| AI/MachineLearning | 机器学习 |
| AI/ComputerVision | 计算机视觉 |
| AI/NLP | 自然语言处理 |
| AI/Tools | AI 工具和平台 |
| DevTools | 开发工具（编辑器、Git、CI/CD） |
| Algorithms/DataStructures | 算法与数据结构 |
| Academic/Research | 学术研究 |
| Finance/Investing | 金融投资 |
| Career/Jobs | 职业发展 |
| News/Media | 新闻媒体 |
| Utilities/OnlineTools | 在线工具 |
| Other | 其他 |

分类列表可在 `config.py` 中自定义。

## 项目结构

```
main.py              # CLI 入口 / 流程编排
models.py            # Bookmark 数据模型
parser.py            # Netscape Bookmark HTML 解析器
dedup.py             # URL 归一化与去重
link_checker.py      # 异步 HTTP 链接检测（aiohttp）
classifier.py        # DeepSeek API 批量分类
html_generator.py    # 生成浏览器可导入的 HTML
report_generator.py  # 生成 Markdown 分析报告
config.py            # 配置常量（超时、分类、API 设置）
requirements.txt     # Python 依赖
```

## 技术细节

- **解析**: 使用 Python 标准库 `html.parser` 解析 Netscape Bookmark 格式
- **去重**: URL 归一化（统一协议、去除 www、清理 utm 追踪参数、去除尾部斜杠）
- **链接检测**: `aiohttp` 异步并发请求，支持可配置的并发数和超时
- **AI 分类**: DeepSeek API（OpenAI 兼容），每批 20 个书签，JSON 结构化输出
- **输出 HTML**: 带 `PERSONAL_TOOLBAR_FOLDER` 属性，导入后直接进入收藏夹栏

## License

[MIT](LICENSE)
