# BA Student Crafting Favor

**中文** | [**English**](README.md)

基于 [SchaleDB](https://schaledb.com/) 数据计算制造节点对指定学生好感度期望值的工具集。

## 环境要求

- Python 3.7+
- 依赖：`requests`（仅 `catcher_simple.py` 需要）

```bash
pip install requests
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `catcher_simple.py` | 数据爬取脚本，从 SchaleDB 下载所需数据 |
| `favor_calc.py` | 好感度计算脚本，输入学生名计算制造节点期望值 |

---

## 使用流程

```bash
# 1. 爬取数据（仅需执行一次，后续只需运行 favor_calc.py）
python catcher_simple.py

# 2. 计算好感度
python favor_calc.py Aru -l cn -r Cn
```

---

## catcher_simple.py — 数据爬取

从 `https://schaledb.com/` 下载 `favor_calc.py` 所需的全部数据，保存至 `data/` 目录。

### 用法

```bash
python catcher_simple.py
```

### 下载内容

| 类型 | 数据 | 路径 |
|------|------|------|
| 全局数据 | 制造系统 | `data/crafting.min.json` |
| 全局数据 | 礼物分组 | `data/groups.min.json` |
| 各语言数据 | 学生信息 | `data/{region}/students.min.json` |
| 各语言数据 | 物品信息 | `data/{region}/items.min.json` |

支持的语言区域：`cn` `en` `jp` `kr` `th` `tw` `zh`

### 特性

- 增量下载：已存在的文件会自动跳过，仅下载缺失或为空的文件
- 失败重试：每个请求最多重试 3 次

---

## favor_calc.py — 好感度计算

输入学生名，计算所有能产出礼物的制造节点对该学生的好感度期望值。

### 用法

```bash
python favor_calc.py [-h] [-n STUDENT_OPT] [-l LANG] [-r REGION] [-o] [student]
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `student` | 学生名（位置参数，可省略前缀直接传入） |
| `-n`, `--name` | 学生名（命名参数，与位置参数等效） |
| `-l`, `--lang` | 名称显示语言，如 `cn` `en` `jp` `kr` `th` `tw` `zh`（默认：`cn`） |
| `-r`, `--region` | 节点概率区域，如 `Cn` `En` `Jp` `Kr` `Th` `Tw` `Zh`（默认：`Cn`） |
| `-o`, `--output` | 启用后将完整计算结果输出为 JSON 文件 |
| `-h`, `--help` | 显示帮助信息 |

### 查询方式

支持以下方式查询学生：

- **Id**：`10000`
- **PathName**：`aru`
- **DevName**：`Aru`
- **Name**（任意语言）：`爱露` `Aru` `アル` 等

支持部分匹配，若匹配到多个学生会列出供选择。

### 示例

```bash
# 默认语言(CN)和区域(Cn)查询
python favor_calc.py Aru

# 使用 Id 查询
python favor_calc.py 10000

# 使用日文名查询
python favor_calc.py アル

# 指定日文显示、日服概率
python favor_calc.py -n Aru -l jp -r Jp

# 启用 JSON 输出
python favor_calc.py Aru -o

# 查看帮助
python favor_calc.py -h
```

### 倍率说明

礼物好感度基于学生标签（`FavorItemTags` / `FavorItemUniqueTags`）计算倍率：

| 条件 | SR 倍率 | SSR 倍率 |
|------|--------|---------|
| 2+ 普通标签 **且** 1+ 专属标签 | 4x | 5x |
| 2+ 普通标签 **或** 1+ 专属标签 | 3x | 4x |
| 1 普通标签 | 2x | 3x |
| 无匹配 | 1x | 2x |

### JSON 输出

使用 `-o` 参数后，会在脚本目录下生成 `favor_{Id}_{DevName}.json`，包含完整的节点、分组、物品计算明细。

## 许可

本仓库代码使用MIT许可证发布。
