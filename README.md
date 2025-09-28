# 图片水印应用 (Photo Watermark Tool)

一个易于使用的图片水印添加工具，支持文本水印和图片水印，提供直观的图形界面和丰富的自定义选项。

## 📋 项目概述

本项目是一个基于 Python 和 Tkinter 开发的桌面应用程序，专为需要批量添加水印的用户设计。无论是摄影师保护作品版权，还是企业为产品图片添加品牌标识，这个工具都能满足您的需求。

### ✨ 主要特色

- 🖼️ **多格式支持**：支持 JPEG、PNG、BMP、TIFF 等主流图片格式
- 📝 **双重水印**：支持文本水印和图片水印两种类型
- 🎨 **丰富自定义**：字体、颜色、透明度、位置、旋转角度等全面可调
- 👀 **实时预览**：所见即所得的预览效果
- 📁 **批量处理**：支持单张或批量图片处理
- 💾 **模板管理**：保存和复用水印配置
- 🖱️ **拖拽操作**：支持文件拖拽导入和水印位置拖拽调整

## 🚀 功能介绍

### 1. 文件处理

#### 1.1 图片导入
- **单张导入**：支持拖拽或文件选择器导入单张图片
- **批量导入**：一次性选择多张图片或导入整个文件夹
- **预览列表**：界面显示已导入图片的缩略图和文件名

#### 1.2 支持格式
- **输入格式**：JPEG、PNG、BMP、TIFF（PNG 支持透明通道）
- **输出格式**：用户可选择输出为 JPEG 或 PNG

#### 1.3 图片导出
- **输出目录**：用户指定输出文件夹，默认禁止覆盖原文件
- **命名规则**：
  - 保留原文件名
  - 添加自定义前缀（如 `wm_`）
  - 添加自定义后缀（如 `_watermarked`）
- **质量控制**：JPEG 格式提供压缩质量调节（0-100）
- **尺寸调整**：支持导出时调整图片尺寸

### 2. 水印类型

#### 2.1 文本水印
- **内容自定义**：支持任意文本输入
- **字体设置**：
  - 选择系统已安装字体
  - 调整字号大小
  - 支持粗体、斜体样式
- **外观控制**：
  - 调色板选择字体颜色
  - 透明度调节（0-100%）
  - 阴影或描边效果

#### 2.2 图片水印
- **Logo 支持**：导入本地图片作为水印
- **透明通道**：完美支持 PNG 透明图片
- **尺寸控制**：按比例调整水印大小
- **透明度**：调节整体透明度（0-100%）

### 3. 水印布局与样式

#### 3.1 实时预览
- 所有调整实时显示在预览窗口
- 点击图片列表切换预览不同图片

#### 3.2 位置控制
- **预设位置**：九宫格布局快速定位（四角、正中心等）
- **手动拖拽**：鼠标直接拖拽水印到任意位置

#### 3.3 旋转功能
- 滑块或输入框控制旋转角度
- 支持任意角度旋转

### 4. 配置管理

#### 4.1 水印模板
- **保存模板**：将当前水印设置保存为模板
- **模板管理**：加载、管理和删除已保存模板
- **自动恢复**：程序启动时自动加载上次设置

## 🔧 运行环境

### 系统要求
- **主要支持**：macOS 12.0+ (已在 macOS(arm) 15.7 上测试), Windows 10+ (已在 Windows 11 上测试)
- **Python 版本**：3.8+
- **开发环境**：基于 macOS 15.7 + Apple M1 芯片开发测试

### Python 命令兼容性
- **Python 版本**：建议使用 Python 3.8，已在此版本下充分测试
- **虚拟环境**：激活虚拟环境后，通常可以直接使用 `python` 命令
- **版本检查**：运行 `python3 --version` 确认版本为 3.8+
- **如果遇到问题**：请尝试将所有 `python` 命令替换为 `python3`

### 依赖库
- **GUI 框架**：Tkinter (Python 内置)
- **图像处理**：Pillow >= 9.5.0
- **配置管理**：PyYAML >= 6.0
- **拖拽支持**：tkinterdnd2 >= 0.3.0

## 📦 安装与运行

> **系统兼容性说明**：macOS 用户推荐使用 micromamba 或 conda 来管理 Python 环境，方法二在某些macOS版本上可能会遇到兼容性问题。

### 方法一：使用 Conda 或 Micromamba（推荐）

1. **克隆项目**
```bash
git clone https://github.com/doubleyl/photo-watermark2.git
cd photo-watermark2
```

2. **创建 Conda 环境**
```bash
conda env create -f environment.yml
```

3. **激活环境**
```bash
conda activate photo-watermark-env
```

4. **运行应用**
```bash
# 在激活的 Conda 环境中
python main.py

# 如果上述命令不工作，请尝试
# python3 main.py
```

### 方法二：使用 pip

> macOS 一些版本可能遇到如下问题，可切换windows或使用方法一：
> macOS xx (xxxx) or later required, have instead xx (xxxx) !
> zsh: abort      python3 main.py

1. **克隆项目**
```bash
git clone https://github.com/doubleyl/photo-watermark2.git
cd photo-watermark2
```

2. **创建虚拟环境（推荐）**
```bash
# macOS 系统通常使用 python3 命令
python -m venv photo-watermark-env

# 如果系统中 python 命令可用，也可以使用
# python -m venv photo-watermark-env
```

3. **激活虚拟环境**
```bash
# macOS
source photo-watermark-env/bin/activate

# Windows PowerShell
.\photo-watermark-env\Scripts\Activate.ps1
# 或者 Windows CMD
.\photo-watermark-env\Scripts\activate.bat
```

4. **安装依赖**
```bash
pip install -r requirements.txt
```

5. **运行应用**
```bash
# 在激活的虚拟环境中
python main.py

# 如果上述命令不工作，请尝试
# python3 main.py
```