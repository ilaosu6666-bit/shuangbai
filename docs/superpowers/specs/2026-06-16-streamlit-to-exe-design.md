# 设计：Streamlit 应用打包为 Windows EXE 桌面应用

## 目标

将智影溯源 Streamlit 教学平台打包为单个 EXE 文件，双击后弹出干净桌面窗口，体验类似 Steam 客户端。

## 用户体验

- 双击 EXE → 桌面窗口打开（无浏览器地址栏、标签页、工具栏）
- 标题栏显示 "智影溯源 - AI肺结节教学平台"
- 窗口可调整大小、最小化、关闭
- 关闭窗口即退出应用

## 技术选型

- **窗口壳**：`pywebview`（使用 Windows 内置 Edge WebView2，无需额外安装）
- **后端**：Streamlit 保持现状，后台线程运行
- **打包**：PyInstaller（`--onefile --windowed`）

## 架构

```
EXE 启动 → desktop_launcher.py
              ├── 找空闲端口
              ├── 后台线程启动 Streamlit (streamlit.web.bootstrap.run)
              ├── 等待服务器就绪
              ├── 打开 pywebview 桌面窗口 → 加载 localhost:{port}
              └── 窗口关闭 → 退出
```

## 新增文件

### `desktop_launcher.py`

入口脚本，负责：
1. 检测运行模式（打包模式用 `sys._MEIPASS` 定位资源）
2. 找空闲端口
3. 线程启动 Streamlit
4. 轮询等待服务就绪
5. 打开 pywebview 窗口
6. 窗口关闭后退出

### `app-entry.spec`

PyInstaller 打包配置：
- `--onefile` + `--windowed`
- 数据目录：`cases/`, `model_parameter/`, `loss_fig/`
- Python 源文件：`game.py`, `part1.py`, `streamlit_app.py`
- 隐藏导入：torch, torchvision, pydicom, SimpleITK, streamlit 等
- 输出名：`智影溯源.exe`
- PNG 图标由 Pillow 转为 ICO 后嵌入

### `build.bat`

一键打包脚本：先转换图标，再运行 PyInstaller。

## 现有文件

不做修改：`streamlit_app.py`, `game.py`, `part1.py`

## 新增依赖

- `pywebview`
- `pyinstaller`

## 预估体积

~3 GB（PyTorch ~2 GB + cases 680 MB + 模型 130 MB + 其他 ~200 MB）

## 注意事项

- 单文件 EXE 首次启动需解压到临时目录，约需 30-60 秒
- 需要用户机器有 Edge WebView2 Runtime（Windows 10/11 自带）
- 打包时需检查 CUDA DLL 是否正确收集
