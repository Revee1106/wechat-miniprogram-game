# CloudBase Deploy Design

## Goal
让 [wechat-miniprogram-game](/E:/game/wechat-miniprogram-game) 可以直接作为微信云托管的 GitHub 绑定仓库发布，使用根目录 `Dockerfile` 完成后端服务和管理后台静态资源的统一部署。

## Context
- 运行中的 Python 服务入口是 `uvicorn app.main:app`。
- FastAPI 已经挂载后台静态入口，默认从 `admin-console/dist` 提供 `/admin`。
- 微信云托管控制台当前适合的填写方式是：
  - `目标目录` 留空
  - `Dockerfile` 名称填 `Dockerfile`

## Options

### Option 1: 单容器多阶段构建
- 第一阶段使用 Node 构建 `admin-console/dist`
- 第二阶段使用 Python 安装依赖并启动 FastAPI
- 最终镜像同时包含后端代码和后台静态资源

优点：
- 最贴合当前仓库结构
- 一个服务即可同时提供 API 和 `/admin`
- 云托管配置最简单

缺点：
- 构建时间比纯后端镜像更长

### Option 2: 只部署后端容器
- 容器内只跑 Python
- 不构建 `admin-console`

优点：
- Dockerfile 更简单

缺点：
- `/admin` 会因缺少 `dist` 返回 `503`
- 还需要额外找地方托管管理后台

### Option 3: 拆成两个云托管服务
- 一个 Python API 服务
- 一个静态管理台服务

优点：
- 职责拆分清晰

缺点：
- 对当前项目是过度设计
- 增加部署和配置复杂度

## Decision
采用 **Option 1: 单容器多阶段构建**。

## Deployment Shape
- 在仓库根目录新增 `Dockerfile`
- 在仓库根目录新增 `.dockerignore`
- Docker 构建阶段：
  - `node:20-alpine` 负责 `admin-console` 构建
  - `python:3.12-slim` 负责运行 FastAPI
- 运行阶段镜像保留：
  - `app/`
  - `config/`
  - `requirements.txt`
  - `admin-console/dist`

## Runtime Contract
- 启动命令：
  - `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-80}`
- 工作目录：
  - `/app`
- FastAPI 中 `app/admin/static.py` 的默认静态目录解析到：
  - `/app/admin-console/dist`

## Docker Ignore Rules
排除不需要进入构建上下文的大目录和临时文件：
- `.git`
- `.pytest_tmp`
- `.pytest_cache`
- `tests`
- `docs`
- `admin-console/node_modules`
- `admin-console/dist`
- `__pycache__`
- `*.pyc`

## Verification
- 至少验证一次 Docker 构建能通过
- 若本机有 Docker，则执行：
  - `docker build -t wendao-cloudbase .`
- 若本机无 Docker，则至少完成文件级检查并明确说明未做镜像构建验证
