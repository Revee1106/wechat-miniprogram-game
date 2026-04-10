# CloudBase Deploy Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a root-level Docker deployment setup so the FastAPI backend and built admin console can be deployed directly from GitHub to WeChat CloudBase Hosting.

**Architecture:** Use a multi-stage Docker build. Stage one builds `admin-console/dist` with Node. Stage two installs Python dependencies, copies the backend runtime files plus built admin assets, and starts `uvicorn` on the CloudBase-provided port.

**Tech Stack:** Docker, Python 3.12, FastAPI, Uvicorn, Node 20, Vite

---

### Task 1: Add Docker build files

**Files:**
- Create: `E:/game/wechat-miniprogram-game/Dockerfile`
- Create: `E:/game/wechat-miniprogram-game/.dockerignore`

**Step 1: Write the deployment files**

- Create a multi-stage `Dockerfile` that:
  - installs `admin-console` dependencies with `npm ci`
  - runs `npm run build`
  - installs Python dependencies from `requirements.txt`
  - copies `app`, `config`, `requirements.txt`, and `admin-console/dist`
  - starts `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-80}`
- Create `.dockerignore` to exclude `.git`, test artifacts, docs, and local dependency folders.

**Step 2: Verify file contents are correct**

Run:
`Get-Content E:/game/wechat-miniprogram-game/Dockerfile`
`Get-Content E:/game/wechat-miniprogram-game/.dockerignore`

Expected:
- Dockerfile references `admin-console/dist`
- Dockerfile exposes runtime on `${PORT:-80}`
- `.dockerignore` excludes large local-only directories

### Task 2: Verify Docker build path

**Files:**
- Verify: `E:/game/wechat-miniprogram-game/app/admin/static.py`
- Verify: `E:/game/wechat-miniprogram-game/app/main.py`

**Step 1: Run a Docker build**

Run:
`docker build -t wendao-cloudbase E:/game/wechat-miniprogram-game`

Expected:
- Build succeeds
- `admin-console` finishes `vite build`
- Python runtime stage completes without missing file errors

**Step 2: If Docker is unavailable, record the gap**

Expected:
- Explicit note that runtime image build could not be validated locally

### Task 3: Summarize CloudBase console values

**Files:**
- Reference: `E:/game/wechat-miniprogram-game/Dockerfile`

**Step 1: Confirm final console inputs**

Expected:
- `目标目录` 留空
- `Dockerfile 文件` 选 `有`
- `Dockerfile 名称` 填 `Dockerfile`
- 环境变量默认留空，后续按数据库与鉴权需求增加
