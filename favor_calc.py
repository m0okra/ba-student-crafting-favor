import json
import os
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

NAME_LANGUAGE = "cn"
CHANCE_REGION = "Cn"
OUTPUT_JSON = False
P_REACH_MAX = 0.5

REGIONS = ["cn", "en", "jp", "kr", "th", "tw", "zh"]
NAME_XX_MAP = {
    "cn": "NameCn", "en": "NameEn", "jp": "NameJp",
    "kr": "NameKr", "th": "NameTh", "tw": "NameTw", "zh": "NameZh",
}
CHANCE_FIELD = f"Chance{CHANCE_REGION}"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_name(name):
    return name.replace("\n", " ")


def vis_len(s):
    return sum(2 if ord(c) > 0x2e80 else 1 for c in s)


def cjk_ljust(s, width):
    pad = max(0, width - vis_len(s))
    return s + " " * pad


def cjk_rjust(s, width):
    pad = max(0, width - vis_len(s))
    return " " * pad + s


def build_name_index():
    index = {}
    for region in REGIONS:
        path = os.path.join(DATA_DIR, region, "students.min.json")
        if not os.path.isfile(path):
            continue
        data = load_json(path)
        for sid, sdata in data.items():
            if sid not in index:
                index[sid] = {}
            index[sid][region] = clean_name(sdata.get("Name", ""))
    return index


def build_item_name_index():
    index = {}
    for region in REGIONS:
        path = os.path.join(DATA_DIR, region, "items.min.json")
        if not os.path.isfile(path):
            continue
        data = load_json(path)
        for iid, idata in data.items():
            if iid not in index:
                index[iid] = {}
            index[iid][region] = clean_name(idata.get("Name", ""))
    return index


def get_student_display_name(sid, students_jp, name_index):
    if NAME_LANGUAGE in REGIONS:
        lang_name = name_index.get(sid, {}).get(NAME_LANGUAGE)
        if lang_name:
            return lang_name
    jp_data = students_jp.get(sid, {})
    return clean_name(jp_data.get("Name", sid))


def get_item_display_name(iid, item_name_index):
    if NAME_LANGUAGE in REGIONS:
        lang_name = item_name_index.get(iid, {}).get(NAME_LANGUAGE)
        if lang_name:
            return lang_name
    jp_name = item_name_index.get(iid, {}).get("jp")
    if jp_name:
        return jp_name
    en_name = item_name_index.get(iid, {}).get("en")
    return en_name if en_name else iid


def get_node_display_name(node):
    xx_key = NAME_XX_MAP.get(NAME_LANGUAGE)
    if xx_key:
        name = node.get(xx_key)
        if name:
            return clean_name(name)
    return clean_name(node.get("NameJp", node.get("NameEn", "")))


def load_all_data():
    crafting = load_json(os.path.join(DATA_DIR, "crafting.min.json"))
    groups = load_json(os.path.join(DATA_DIR, "groups.min.json"))
    items = load_json(os.path.join(DATA_DIR, "en", "items.min.json"))
    students_jp = load_json(os.path.join(DATA_DIR, "jp", "students.min.json"))
    students_all = {}
    for region in REGIONS:
        path = os.path.join(DATA_DIR, region, "students.min.json")
        if os.path.isfile(path):
            students_all[region] = load_json(path)
    return crafting, groups, items, students_jp, students_all


def build_gift_data(items, groups, item_name_index):
    favor_items = {}
    for iid, idata in items.items():
        if idata.get("Category") == "Favor":
            favor_items[iid] = idata

    gift_groups = {}
    for gid_str, gdata in groups.items():
        gid = int(gid_str)
        favor_list = []
        group_items = gdata.get("Items", [])
        group_total = len(group_items)
        for item in group_items:
            iid = str(item["Id"])
            if iid in favor_items and item.get("Type") == "Item":
                amt_min = item.get("AmountMin", 1)
                amt_max = item.get("AmountMax", 1)
                favor_list.append({
                    "item_id": iid,
                    "name": get_item_display_name(iid, item_name_index),
                    "rarity": favor_items[iid].get("Rarity", ""),
                    "exp_value": favor_items[iid].get("ExpValue", 0),
                    "tags": list(favor_items[iid].get("Tags", [])),
                    "chance": 1.0 / group_total,
                    "amount_min": amt_min,
                    "amount_max": amt_max,
                    "amount_expected": amt_min + (amt_max - amt_min) * P_REACH_MAX,
                })
        if favor_list:
            gift_groups[gid] = favor_list

    return favor_items, gift_groups


def build_node_gift_map(crafting, gift_groups):
    gift_nodes = []
    for node in crafting["Nodes"]:
        groups_in_node = node.get("Groups", [])
        relevant_groups = []
        for g in groups_in_node:
            if g["GroupId"] in gift_groups:
                relevant_groups.append(g)

        if not relevant_groups:
            continue

        node_total_weight = sum(g["Weight"] for g in groups_in_node)

        gift_nodes.append({
            "node_id": node["Id"],
            "name_en": node.get("NameEn", ""),
            "name_jp": node.get("NameJp", ""),
            "NameCn": node.get("NameCn", ""),
            "NameEn": node.get("NameEn", ""),
            "NameJp": node.get("NameJp", ""),
            "NameKr": node.get("NameKr", ""),
            "NameTh": node.get("NameTh", ""),
            "NameTw": node.get("NameTw", ""),
            "NameZh": node.get("NameZh", ""),
            "tier": node["Tier"],
            "quality": node["Quality"],
            "node_chance": node[CHANCE_FIELD],
            "chance_jp": node.get("ChanceJp", 0),
            "total_weight": node_total_weight,
            "gift_groups": [
                {
                    "group_id": g["GroupId"],
                    "weight": g["Weight"],
                    "weight_ratio": g["Weight"] / node_total_weight,
                    "items": gift_groups[g["GroupId"]],
                }
                for g in relevant_groups
            ],
        })

    return gift_nodes


def find_student(students_jp, students_all, name_index, query):
    query_lower = query.lower().strip()
    matches = []

    for sid, sdata in students_jp.items():
        dev_name = sdata.get("DevName", "")
        path_name = sdata.get("PathName", "")

        if query_lower == sid.lower():
            matches.append((sid, sdata, "exact_id"))
        elif query_lower == path_name.lower():
            matches.append((sid, sdata, "exact_pathname"))
        elif query_lower == dev_name.lower():
            matches.append((sid, sdata, "exact_devname"))
        else:
            names = name_index.get(sid, {})
            for lang, n in names.items():
                if query_lower == n.lower():
                    matches.append((sid, sdata, f"exact_name_{lang}"))
                    break

    if not matches:
        for sid, sdata in students_jp.items():
            dev_name = sdata.get("DevName", "")
            path_name = sdata.get("PathName", "")
            names = name_index.get(sid, {})
            name_matches = False
            for n in names.values():
                if query_lower in n.lower():
                    name_matches = True
                    break
            if (name_matches or
                    query_lower in dev_name.lower() or
                    query_lower in path_name.lower() or
                    query_lower in sid.lower()):
                matches.append((sid, sdata, "partial"))

    return matches


def calc_multiplier(item_tags, student_favor_tags, student_unique_tags, rarity):
    favor_count = len(set(item_tags) & student_favor_tags)
    unique_count = len(set(item_tags) & student_unique_tags)

    if favor_count >= 2 and unique_count >= 1:
        base = 4.0
    elif favor_count >= 2 or unique_count >= 1:
        base = 3.0
    elif favor_count >= 1:
        base = 2.0
    else:
        base = 1.0

    if rarity == "SSR":
        return base + 1.0
    return base


def calc_node_expected(node, student):
    student_favor_tags = set(student.get("FavorItemTags", []))
    student_unique_tags = set(student.get("FavorItemUniqueTags", []))

    node_raw = 0.0
    node_details = []

    for gg in node["gift_groups"]:
        group_raw = 0.0
        item_details = []

        for item in gg["items"]:
            mult = calc_multiplier(item["tags"], student_favor_tags, student_unique_tags, item["rarity"])
            contrib = item["chance"] * item["exp_value"] * item["amount_expected"] * mult
            group_raw += contrib
            item_details.append({
                "item_id": item["item_id"],
                "name": item["name"],
                "rarity": item["rarity"],
                "exp_value": item["exp_value"],
                "amount": item["amount_expected"],
                "multiplier": mult,
                "item_prob": item["chance"],
                "expected_contribution": round(contrib, 6),
            })

        weighted = gg["weight_ratio"] * group_raw
        node_raw += weighted

        node_details.append({
            "group_id": gg["group_id"],
            "weight_ratio": gg["weight_ratio"],
            "group_raw": group_raw,
            "weighted": weighted,
            "items": item_details,
        })

    result = {
        "node_id": node["node_id"],
        "name_en": node["name_en"],
        "name_jp": node["name_jp"],
        "NameCn": node.get("NameCn", ""),
        "NameEn": node.get("NameEn", ""),
        "NameJp": node.get("NameJp", ""),
        "NameKr": node.get("NameKr", ""),
        "NameTh": node.get("NameTh", ""),
        "NameTw": node.get("NameTw", ""),
        "NameZh": node.get("NameZh", ""),
        "tier": node["tier"],
        "quality": node["quality"],
        "chance_jp": node["chance_jp"],
        "chance": node["node_chance"],
        "node_raw": round(node_raw, 6),
        "expected_value": round(node_raw * node["node_chance"], 6),
        "details": node_details,
    }

    return result


def save_json_output(student, node_results, name_index, mc_total):
    output = {
        "timestamp": int(time.time()),
        "config": {
            "NAME_LANGUAGE": NAME_LANGUAGE,
            "CHANCE_REGION": CHANCE_REGION,
        },
        "student": {
            "id": int(student[0]),
            "dev_name": student[1].get("DevName", ""),
            "path_name": student[1].get("PathName", ""),
            "names": name_index.get(student[0], {}),
            "display_name": get_student_display_name(student[0], student[1], name_index),
            "favor_item_tags": student[1].get("FavorItemTags", []),
            "favor_item_unique_tags": student[1].get("FavorItemUniqueTags", []),
        },
        "nodes": [],
        "total_expected": 0.0,
        "mc_total": round(mc_total, 6),
    }

    for nr in node_results:
        node_data = {
            "node_id": nr["node_id"],
            "display_name": get_node_display_name(nr),
            "tier": nr["tier"],
            "quality": nr["quality"],
            "chance": nr["chance"],
            "selection_prob": nr.get("selection_prob", 0.0),
            "node_raw": nr["node_raw"],
            "expected_value": nr["expected_value"],
            "mc_expected": nr.get("mc_expected", 0.0),
            "groups": [],
        }

        for gd in nr["details"]:
            group_data = {
                "group_id": gd["group_id"],
                "weight_ratio": gd["weight_ratio"],
                "group_raw": gd["group_raw"],
                "weighted": gd["weighted"],
                "items": gd["items"],
            }
            node_data["groups"].append(group_data)

        output["nodes"].append(node_data)
        output["total_expected"] += nr["mc_expected"]

    output["total_expected"] = round(output["total_expected"], 6)

    sid = student[0]
    filename = f"favor_{sid}_{student[1].get('DevName', '')}.json"
    path = os.path.join(BASE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    return path


def print_results(student_data, node_results, name_index, mc_total):
    sid = student_data[0]
    sdata = student_data[1]

    display_name = get_student_display_name(sid, sdata, name_index)

    favor_str = ", ".join(sdata.get("FavorItemTags", []))
    unique_str = ", ".join(sdata.get("FavorItemUniqueTags", []))

    name_tags = []
    for lang in REGIONS:
        n = name_index.get(sid, {}).get(lang)
        if n:
            name_tags.append(f"{lang}={n}")
    names_line = ", ".join(name_tags)

    print(f"Student: {display_name}  [{NAME_LANGUAGE}]")
    print(f"  Id: {sid}  DevName: {sdata.get('DevName', '')}  PathName: {sdata.get('PathName', '')}")
    print(f"  Names: {names_line}")
    print(f"  FavorItemTags: [{favor_str}]")
    print(f"  FavorItemUniqueTags: [{unique_str}]")
    print(f"  Chance Region: {CHANCE_REGION}")
    print()

    h_node = "Node"
    h_name = "Name"
    h_tq = "T/Q"
    h_sel = "Sel%"
    h_raw = "Raw"
    h_final = "Expected"

    sep = f"{'':-<6} {'':-<30} {'':-<5} {'':->7} {'':->8} {'':->8}"
    header = f"{h_node:<6} {cjk_ljust(h_name, 30)} {h_tq:<5} {h_sel:>7} {h_raw:>8} {h_final:>8}"
    print(header)
    print(sep)

    for nr in node_results:
        sel_p = nr.get("selection_prob", 0.0)
        node_name = get_node_display_name(nr)
        line = f"{nr['node_id']:<6} {cjk_ljust(node_name, 30)} T{nr['tier']}Q{nr['quality']:<2} {sel_p*100:>6.2f}% {nr['node_raw']:>8.4f} {nr['mc_expected']:>8.4f}"
        print(line)

    print(sep)
    print(f"{'':<6} {cjk_ljust('', 30)} {'':<5} {'':>7} {'':>8} {mc_total:>8.4f}")
    print()

    print(f"TOTAL EXPECTED FAVOR: {mc_total:.4f}")
    print()


def exact_expected(all_nodes, node_raw_map, chance_field):
    """Calculate exact expected value per round using independent appearance model.
    
    Each node independently appears with probability = chance_field value.
    Among appearing nodes, pick the one with highest raw value.
    For same-raw nodes, first-in-list (by sorted order) wins.
    """
    probs = [n.get(chance_field, n.get("ChanceJp", 0)) for n in all_nodes]
    raw_values = [node_raw_map.get(n["Id"], 0.0) for n in all_nodes]
    node_ids = [n["Id"] for n in all_nodes]

    indexed = list(zip(node_ids, probs, raw_values))
    indexed.sort(key=lambda x: (-x[2], -x[1]))

    sorted_ids = [x[0] for x in indexed]
    sorted_probs = [x[1] for x in indexed]
    sorted_raws = [x[2] for x in indexed]
    N = len(sorted_probs)

    node_sel_prob = {nid: 0.0 for nid in node_ids}
    total = 0.0

    cum_no_high = 1.0
    i = 0
    while i < N:
        j = i
        while j < N and sorted_raws[j] == sorted_raws[i]:
            j += 1

        raw = sorted_raws[i]
        if raw <= 0:
            i = j
            continue

        for k in range(i, j):
            p_k = sorted_probs[k]
            no_high_factor = cum_no_high
            for kk in range(i, k):
                no_high_factor *= (1 - sorted_probs[kk])
            sel_prob = p_k * no_high_factor
            node_sel_prob[sorted_ids[k]] = sel_prob
            total += raw * sel_prob

        for k in range(i, j):
            cum_no_high *= (1 - sorted_probs[k])

        i = j

    return total, node_sel_prob


def main():
    global NAME_LANGUAGE, CHANCE_REGION, OUTPUT_JSON, CHANCE_FIELD

    import argparse

    parser = argparse.ArgumentParser(
        description="Calculate expected favor value from manufacturing nodes for a given student.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python favor_calc.py Aru
  python favor_calc.py 10000
  python favor_calc.py -n Aru -l jp -r Jp -o
  python favor_calc.py \u7231\u9732 --lang cn --region Cn""",
    )
    parser.add_argument(
        "student", nargs="?",
        help="Student name (Id, PathName, DevName, or display name in any language)",
    )
    parser.add_argument(
        "-n", "--name", dest="student_opt",
        help="Student name (alternative to positional argument)",
    )
    parser.add_argument(
        "-l", "--lang", default=NAME_LANGUAGE,
        help=f"Display language for names (default: {NAME_LANGUAGE})",
    )
    parser.add_argument(
        "-r", "--region", default=CHANCE_REGION,
        help=f"Chance region for node probabilities (default: {CHANCE_REGION})",
    )
    parser.add_argument(
        "-o", "--output", action="store_true",
        help="Output full results to a JSON file",
    )

    args = parser.parse_args()

    student_name = args.student or args.student_opt

    if not student_name:
        parser.print_help()
        sys.exit(1)

    NAME_LANGUAGE = args.lang.lower()
    region_raw = args.region
    if len(region_raw) >= 2:
        CHANCE_REGION = region_raw[0].upper() + region_raw[1:].lower()
    else:
        CHANCE_REGION = region_raw
    OUTPUT_JSON = args.output
    CHANCE_FIELD = f"Chance{CHANCE_REGION}"

    crafting, groups, items, students_jp, students_all = load_all_data()
    if not any(CHANCE_FIELD in node for node in crafting["Nodes"]):
        CHANCE_FIELD = "ChanceJp"
        CHANCE_REGION = "Jp"

    name_index = build_name_index()
    item_name_index = build_item_name_index()
    favor_items, gift_groups = build_gift_data(items, groups, item_name_index)
    gift_nodes = build_node_gift_map(crafting, gift_groups)

    matches = find_student(students_jp, students_all, name_index, student_name)

    if not matches:
        print(f"No student found matching '{student_name}'")
        sys.exit(1)

    if len(matches) > 1:
        print(f"Multiple matches for '{student_name}':")
        for i, (sid, sdata, mt) in enumerate(matches):
            display = get_student_display_name(sid, sdata, name_index)
            print(f"  [{i}] {display} (Id={sid}, DevName={sdata.get('DevName', '')}, PathName={sdata.get('PathName', '')}) [{mt}]")
        print()
        try:
            idx = int(input("Select index: "))
            if idx < 0 or idx >= len(matches):
                print("Invalid index")
                sys.exit(1)
        except (ValueError, EOFError):
            print("Invalid input")
            sys.exit(1)
        selected = matches[idx]
    else:
        selected = matches[0]

    sid, sdata, match_type = selected

    node_results = []
    for node in gift_nodes:
        result = calc_node_expected(node, sdata)
        node_results.append(result)

    node_results.sort(key=lambda r: (-r["tier"], -r["node_raw"]))

    node_raw_map = {nr["node_id"]: nr["node_raw"] for nr in node_results}

    tiers = {1: [], 2: [], 3: []}
    for node in crafting["Nodes"]:
        if node.get("Tier") in tiers:
            tiers[node["Tier"]].append(node)

    mc_total = 0.0
    node_sel_prob = {}
    for tier, nodes in tiers.items():
        t_total, t_sel = exact_expected(nodes, node_raw_map, CHANCE_FIELD)
        mc_total += t_total
        node_sel_prob.update(t_sel)

    for nr in node_results:
        sel_p = node_sel_prob.get(nr["node_id"], 0.0)
        nr["selection_prob"] = sel_p
        nr["mc_expected"] = nr["node_raw"] * sel_p

    print_results((sid, sdata), node_results, name_index, mc_total)

    if not OUTPUT_JSON:
        return
    json_path = save_json_output((sid, sdata), node_results, name_index, mc_total)
    print(f"Full results saved to: {json_path}")


if __name__ == "__main__":
    main()
