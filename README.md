# A09 海洋环境现象识别与多要素智能分析系统（前后端联调清理版）

本仓库已按“可联调运行 + 目录整洁”完成清理，仅保留当前项目运行必要内容（前端 + 三类后端能力）。

## 1. 当前目录结构（已清理）

```text
fwwb/
├─ frontend/                      # Vue3 + Vite 前端（Atlas 三层模块化）
│  ├─ src/
│  │  ├─ app/
│  │  ├─ core/
│  │  ├─ modules/
│  │  │  ├─ eddy/
│  │  │  ├─ hydro/
│  │  │  ├─ windwave/
│  │  │  └─ overview/
│  │  ├─ shared/
│  │  └─ views/Login.vue
│  └─ docs/
├─ apis/                          # FastAPI 聚合服务入口与路由（/predict /temp_salt/predict /wind_wave/predict）
│  ├─ api.py
│  ├─ temp_salt_api.py
│  └─ wind_wave_api.py
├─ peddy/                         # 涡旋推理核心能力
│  ├─ infer_v10_daily.py
│  ├─ checkpoints/
│  ├─ configs/
│  └─ eddy_project/
├─ predict/                       # 水文与流速推理资产
│  ├─ wyl_model.py
│  ├─ temp_salt/
│  │  ├─ ts_model.py
│  │  └─ result_temp_salt/
│  └─ speed/
│     ├─ preprocessed_speed/
│     ├─ result_speed/
│     └─ result_speed_backup1/
└─ warning/                       # 风浪预警推理资产
   ├─ run.py
   ├─ requirements.txt
   └─ ml_tc_dual_branch/
```

## 2. 前后端接口映射（联调基线）

- `POST /predict`：涡旋识别（前端 eddy 模块）
- `POST /temp_salt/predict`：水文要素预测（前端 hydro 模块）
- `POST /wind_wave/predict`：风浪识别预警（前端 windwave 模块）
- `GET /health`：后端健康检查

前端默认后端地址：`http://localhost:8000`（可通过 `VITE_API_BASE_URL` 调整）。

### 风浪预警临时接口开关（低内存模式）

当设备内存不足时，可启用风浪预警临时模式：

- `WINDWAVE_TEMP_MODE=1`：启用临时接口（跳过模型推理，固定读取 `apis/202509`）
- `WINDWAVE_TEMP_MODE=0`：禁用临时接口（恢复原始推理流程）

可选参数：

- `WINDWAVE_TEMP_MONTH=202509`：临时接口读取的月份目录（默认 `202509`）

说明：临时接口仍保持原有任务生命周期和输出契约（`/wind_wave/predict` 提交任务、`/wind_wave/tasks/{id}` 轮询、`/wind_wave/tasks/{id}/result` 取结果），并继续在 `api_output/windwave_tasks/` 生成任务文件，便于与原接口无缝切换。

## 3. 运行方式（不自动改环境）

### 3.1 你需要自行准备的软件/依赖

1. Node.js（建议 20+，你当前 Node 24 也可）
2. Python 3.10+（你当前 3.12 可用）
3. Python 包（至少）：
   - `fastapi`
   - `uvicorn`
   - `python-multipart`
   - 以及 `peddy/requirements_api.txt` 中列出的其余依赖

> 说明：当前环境已验证 `python-multipart` 缺失会导致 FastAPI 在导入 UploadFile 路由时报错。

### 3.2 启动后端

在项目根目录执行（你自己的环境中）：

```bash
python3 -m apis.api
```

服务默认监听：`http://localhost:8000`

### 3.3 启动前端

在 `frontend/` 目录执行（你自己的环境中）：

```bash
npm install
npm run dev
```

开发地址默认：`http://localhost:5173`

### 3.4 生产构建

```bash
cd frontend
npm run build
```

## 4. 本次清理说明（保留运行必要，移除无关冗余）

已移除内容类型：

- 前端构建产物与本地依赖目录（`dist/`, `node_modules/`）
- 各模块 Python 缓存目录（`__pycache__`, `.ipynb_checkpoints`）
- 训练/分析辅助脚本与说明中非运行必须内容（warning 与 speed 中部分训练侧文件）
- 历史输出缓存目录（`predict/output`, `warning/output` 等）

保留原则：

- 只保留“前端运行 + 后端接口 + 推理所需模型/配置/脚本”
- 不破坏三条后端主能力链路（涡旋、水文、风浪）

## 5. 验证结论（本次执行）

1. 前端代码构建验证：
   - 在依赖齐全前提下 `npm run build` 可通过（已执行通过一次）
2. 后端代码结构验证：
   - `python3 -m compileall peddy` 通过（语法可编译）
3. 后端启动前置检查：
   - `python3 -m apis.api --help` 报错提示缺少 `python-multipart`（属于环境依赖缺失，不是代码路径错误）

## 6. 文档清单

前端配套文档位于：`frontend/docs/`

- `前端系统架构说明文档.md`
- `前端使用操作说明文档.md`
- `前端可视化组件说明文档.md`

建议你将本 README 与上述 3 份前端文档一起作为当前阶段交付说明。
