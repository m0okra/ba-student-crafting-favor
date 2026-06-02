# BA Student Crafting Favor

[**中文**](README_CN.md) | **English**

A toolset for calculating crafting node expected favor values for specified students in *Blue Archive*, based on [SchaleDB](https://schaledb.com/) data.

## Requirements

- Python 3.7+
- Dependencies: `requests` (only required by `catcher_simple.py`)

```bash
pip install requests
```

## File Overview

| File | Purpose |
|------|---------|
| `catcher_simple.py` | Data scraper that downloads required data from SchaleDB |
| `favor_calc.py` | Favor calculation script — computes crafting node expected values for a given student |

---

## Usage

```bash
# 1. Scrape data (only needed once; afterwards just run favor_calc.py)
python catcher_simple.py

# 2. Calculate favor
python favor_calc.py Aru -l cn -r Cn
```

---

## catcher_simple.py — Data Scraping

Downloads all data required by `favor_calc.py` from `https://schaledb.com/` and saves it to the `data/` directory.

### Usage

```bash
python catcher_simple.py
```

### Downloaded Content

| Type | Data | Path |
|------|------|------|
| Global | Crafting system | `data/crafting.min.json` |
| Global | Gift groups | `data/groups.min.json` |
| Per language | Student info | `data/{region}/students.min.json` |
| Per language | Item info | `data/{region}/items.min.json` |

Supported language regions: `cn` `en` `jp` `kr` `th` `tw` `zh`

### Features

- Incremental download: existing files are automatically skipped; only missing or empty files are downloaded
- Retry on failure: each request is retried up to 3 times

---

## favor_calc.py — Favor Calculation

Takes a student name and calculates the expected favor value of every crafting node that can produce gifts for that student.

### Usage

```bash
python favor_calc.py [-h] [-n STUDENT_OPT] [-l LANG] [-r REGION] [-o] [student]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `student` | Student name (positional argument; can omit the prefix) |
| `-n`, `--name` | Student name (named argument, equivalent to positional) |
| `-l`, `--lang` | Display language, e.g. `cn` `en` `jp` `kr` `th` `tw` `zh` (default: `cn`) |
| `-r`, `--region` | Node probability region, e.g. `Cn` `En` `Jp` `Kr` `Th` `Tw` `Zh` (default: `Cn`) |
| `-o`, `--output` | When set, outputs full calculation results as a JSON file |
| `-h`, `--help` | Show help message |

### Student Lookup

The following lookup methods are supported:

- **Id**: `10000`
- **PathName**: `aru`
- **DevName**: `Aru`
- **Name** (any language): `Aru`, `アル`, etc.

Partial matching is supported. If multiple students match, a list will be shown for selection.

### Examples

```bash
# Default language (cn) and region (Cn)
python favor_calc.py Aru

# Lookup by Id
python favor_calc.py 10000

# Lookup by Japanese name
python favor_calc.py アル

# Japanese display name, JP server probabilities
python favor_calc.py -n Aru -l jp -r Jp

# Enable JSON output
python favor_calc.py Aru -o

# Show help
python favor_calc.py -h
```

### Multiplier Table

Gift favor values are multiplied based on the student's tags (`FavorItemTags` / `FavorItemUniqueTags`):

| Condition | SR Multiplier | SSR Multiplier |
|-----------|:-------------:|:--------------:|
| 2+ normal tags **and** 1+ unique tags | 4x | 5x |
| 2+ normal tags **or** 1+ unique tags | 3x | 4x |
| 1 normal tag | 2x | 3x |
| No match | 1x | 2x |

### JSON Output

When the `-o` flag is used, a file named `favor_{Id}_{DevName}.json` is generated in the script directory, containing the full calculation details for nodes, groups, and items.

## License

This repository is licensed under the MIT License.
