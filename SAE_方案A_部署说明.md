# SAE 方案A 部署说明（前后端分离镜像）

本项目按"前端一个镜像 + 后端一个镜像"部署到阿里云 SAE。
通信方式：前端不注入后端地址，所有 API 请求通过 Nginx 反向代理转发到后端（同源请求，无跨域问题）。

---

## 1. 项目结构概览

```
fwwb_new/
├── apis/                        # FastAPI 后端
│   ├── api.py                   # 主入口（app = FastAPI()）
│   ├── chat_api.py              # AI 对话 API（DeepSeek）
│   ├── temp_salt_api.py         # 温盐要素预测 API
│   ├── wind_wave_api.py         # 风浪/台风预测 API
│   └── 202509/                  # 风浪临时模式参考数据（必须打入镜像）
│       ├── csv/
│       └── figures/
├── peddy/                       # 涡旋预测模块
│   ├── checkpoints/best_model_v10.pt  # 模型权重（~465MB）
│   ├── configs/v10_fusionnet.yaml
│   ├── eddy_project/            # 核心推理代码
│   └── infer_v10_daily.py
├── predict/                     # 温盐/流速预测模块
│   ├── temp_salt/result_temp_salt/ts_best.pt
│   ├── speed/result_speed_backup1/best.pt
│   └── wyl_model.py
├── warning/                     # 台风预警模块
│   ├── ml_tc_dual_branch/runs_binary/.../best.pt
│   └── run.py
├── frontend/                    # Vue 3 + Vite 前端
│   ├── Dockerfile
│   ├── nginx.conf               # Nginx 配置（反向代理核心）
│   ├── package.json
│   ├── vite.config.js
│   └── src/
├── Dockerfile.backend           # 后端镜像构建文件
├── requirements.txt             # Python 依赖清单
├── pytorch_cpu_utils.py         # CPU 推理加速工具
└── .dockerignore
```

---

## 2. 镜像相关文件说明

| 文件 | 用途 |
|------|------|
| `Dockerfile.backend` | 后端镜像：Python 3.12-slim + FastAPI + 模型权重 |
| `frontend/Dockerfile` | 前端镜像：Node 20 构建 + Nginx 1.27 提供静态服务 |
| `frontend/nginx.conf` | Nginx 配置（API 反向代理 + SPA 路由） |
| `.dockerignore` | 排除 node_modules、__pycache__、日志、文档等 |
| `requirements.txt` | 后端 Python 依赖（完整清单） |

---

## 3. 构建前检查

### 3.1 确认模型文件存在

以下文件必须存在于仓库中（已确认全部存在）：

- `peddy/checkpoints/best_model_v10.pt` ✓
- `warning/ml_tc_dual_branch/runs_binary/20260319_184414/checkpoints/best.pt` ✓
- `predict/temp_salt/result_temp_salt/ts_best.pt` ✓
- `predict/speed/result_speed_backup1/best.pt` ✓
- `apis/202509/csv/summary_202509.csv` ✓（风浪临时模式参考数据）

### 3.2 确认依赖清单

- Python 依赖：`requirements.txt`（已通过全量导入分析验证，覆盖所有运行时依赖）
- 前端依赖：`frontend/package.json` + `frontend/package-lock.json`（由 `npm ci` 自动安装）

---

## 4. 阿里云容器镜像仓库信息

| 项目 | 值 |
|------|-----|
| 仓库地址 | `crpi-waaaxxrbmzni92ye-vpc.cn-shanghai.personal.cr.aliyuncs.com` |
| 命名空间 | `fwwb_gch` |
| 后端镜像 | `fwwb_gch/fwwb` |
| 前端镜像 | `fwwb_gch/fwwb-frontend` |
| 登录账号 | `liangyuan1114` |

---

## 5. 在轻量服务器上构建 & 推送镜像

以下命令在轻量服务器项目根目录（`/home/yuanliang/code/fwwb_new`）执行。

### 5.1 登录 ACR

```bash
sudo docker login --username=liangyuan1114 crpi-waaaxxrbmzni92ye-vpc.cn-shanghai.personal.cr.aliyuncs.com
```

### 5.2 构建 & 推送后端镜像

```bash
# 构建后端镜像（在项目根目录执行）
sudo docker build -f Dockerfile.backend -t crpi-waaaxxrbmzni92ye-vpc.cn-shanghai.personal.cr.aliyuncs.com/fwwb_gch/fwwb:v3 .

# 推送后端镜像
sudo docker push crpi-waaaxxrbmzni92ye-vpc.cn-shanghai.personal.cr.aliyuncs.com/fwwb_gch/fwwb:v3
```

### 5.3 构建 & 推送前端镜像

**重要：** 构建前端镜像前，必须先将后端部署到 SAE 并获取其后端应用的内网地址，然后修改 `frontend/nginx.conf` 中 `upstream backend_api` 的 `server` 地址。

```bash
# 构建前端镜像（不传 --build-arg，前端走相对路径，由 nginx 反向代理到后端）
sudo docker build -t crpi-waaaxxrbmzni92ye-vpc.cn-shanghai.personal.cr.aliyuncs.com/fwwb_gch/fwwb-frontend:v4 ./frontend

# 推送前端镜像
sudo docker push crpi-waaaxxrbmzni92ye-vpc.cn-shanghai.personal.cr.aliyuncs.com/fwwb_gch/fwwb-frontend:v4
```

---

## 6. SAE 创建应用

**部署顺序：先部署后端，获取后端内网地址并更新 nginx.conf 后，再构建并部署前端。**

### 6.1 后端应用（fwwb-backend）

| 配置项 | 值 |
|------|-----|
| 部署方式 | 镜像部署 |
| 镜像地址 | `crpi-waaaxxrbmzni92ye-vpc.cn-shanghai.personal.cr.aliyuncs.com/fwwb_gch/fwwb:v3` |
| 端口 | `8000` |
| 启动命令 | 使用镜像默认 CMD（无需覆盖） |
| 公网访问 | 可关闭（前端通过 SAE 内网访问后端） |

**建议环境变量：**

| 变量名 | 推荐值 | 说明 |
|--------|--------|------|
| `EDDY_FAST_MODE` | `1` | 涡旋推理快速模式 |
| `EDDY_FAST_MAX_DAYS` | `365` | 涡旋最大推理天数 |
| `WINDWAVE_FAST_MODE` | `1` | 风浪快速模式 |
| `WINDWAVE_FAST_NUM_IMAGES` | `2` | 风浪图片数量 |
| `WINDWAVE_BATCH_SIZE` | `1` | 风浪批处理大小 |
| `WINDWAVE_FAST_MAX_STEPS` | `248` | 风浪最大步数 |
| `WINDWAVE_TEMP_MODE` | `0` | 风浪温度模式 |
| `WINDWAVE_TEMP_MONTH` | `202509` | 风浪参考数据月份 |
| `DEEPSEEK_API_KEY` | 你的 API Key | AI 对话功能（可选） |

**健康检查：**
- 路径：`/health`
- 协议：HTTP
- 端口：`8000`

### 6.2 部署后端后 —— 获取后端内网地址

后端部署成功后，在 SAE 控制台 → 应用详情 → 基本信息中，找到后端的**内网地址**（通常格式为 `<app-name>.<namespace>.sae.svc.cluster.local` 或 SAE 分配的私网 IP）。

将此地址填入 `frontend/nginx.conf`：

```nginx
upstream backend_api {
    server <此处替换为后端内网地址>:8000;
}
```

### 6.3 前端应用（fwwb-frontend）

| 配置项 | 值 |
|------|-----|
| 部署方式 | 镜像部署 |
| 镜像地址 | `crpi-waaaxxrbmzni92ye-vpc.cn-shanghai.personal.cr.aliyuncs.com/fwwb_gch/fwwb-frontend:v4` |
| 端口 | `80` |
| 启动命令 | 使用镜像默认 CMD（Nginx） |
| 公网访问 | **必须开启**（用户浏览器需要访问） |

---

## 7. 发布验证

### 7.1 后端验证

```bash
curl http://<SAE后端内网地址>:8000/health
```

期望返回：
```json
{"status":"ok"}
```

### 7.2 前端验证

打开前端公网地址，确认页面正常加载。然后验证 API 代理是否正常工作：

```bash
curl http://<SAE前端公网地址>/health
```

应同样返回 `{"status":"ok"}`，说明 nginx 已成功将请求代理到后端。

### 7.3 完整功能验证

1. 打开前端页面，确认页面正常加载
2. 上传 NetCDF 文件进行涡旋预测
3. 测试风浪/台风预测功能
4. 测试温盐要素预测功能
5. 测试 AI 对话功能（需配置 DEEPSEEK_API_KEY）

---

## 8. 版本升级与回滚

- **升级**：在轻量服务器上构建新版本镜像（递增 tag，如 `v4` → `v5`），推送后在 SAE 控制台更改镜像版本重新部署
- **回滚**：在 SAE 控制台将镜像版本切回上一个 tag（如 `v5` → `v4`），重新部署即可

---

## 9. 常见问题

1. **前端能打开但接口报 502/504**
   - 检查 `nginx.conf` 中 `upstream backend_api` 的后端内网地址是否正确
   - 检查后端 SAE 应用是否正常运行
   - 检查前后端是否在同一 VPC/地域（SAE 内网通信的前提）

2. **后端 500 且提示 checkpoint 不存在**
   - 模型文件未打入镜像，检查构建日志中模型文件是否被 `.dockerignore` 误排除
   - 按第 3.1 节逐一核对模型文件路径

3. **后端推理超时**
   - 增加 SAE 应用的超时配置
   - 保持 `EDDY_FAST_MODE=1` 启用快速模式
   - 减小 `WINDWAVE_FAST_NUM_IMAGES` / `WINDWAVE_BATCH_SIZE`

4. **容器内存占用高**
   - PyTorch + 多个模型权重会占用大量内存
   - 建议 SAE 实例规格 ≥ 4GB 内存
   - 保持 `WINDWAVE_FAST_MODE=1`
   - 可考虑使用 SAE 的弹性伸缩策略

5. **推送镜像速度慢**
   - 后端镜像约 2-3GB（含 465MB 模型权重 + PyTorch）
   - 前端镜像约 50MB（Nginx + 静态文件）
   - 建议在轻量服务器所在可用区使用 VPC 内网推送加速
