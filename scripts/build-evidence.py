"""Build offline evidence pages from the captured rsi-flow A/B returns."""

import html
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
KEYS = ("Recall@10", "Precision@10", "Completeness@10", "NDCG@10", "MAP@10")
DIAGNOSES = {
    "q-02592": "report-generator 在两组均排第 3。extracting-code-structure 未进入整题和两条分支的候选前十。",
    "q-00821": "产品框架技能在两组均排第 2。code-search 未进入整题和两条分支的候选前十。",
    "q-03697": "synthesis-matrix 在两组均排第 1。devops 未进入整题和两条分支的候选前十。",
    "q-02870": "page-estimation 保持第 1。developer 未进入整题和两条分支的候选前十。",
    "q-01769": "skill-learning-patterns 在经验分支排第 5，合并时没有进入该分支前两条未选候选。doc-management 未进入任一候选前十。",
    "q-01901": "语义提交技能由未进前十升至第 9，interaction-design 从第 7 掉出前十。召回持平，NDCG 下降。",
    "q-01364": "specs-dev 在规格分支排第 2，最终排第 5。原先命中的两条技能都留在前十，标注技能全部找齐。",
    "q-01921": "git-hygiene-enforcer 在工作流分支排第 1，最终排第 8。ui-design 仍未进入任一候选前十。",
    "q-00137": "tool-discovery 在工具分支排第 1，最终排第 8。nextjs-canary-docs 后移到第 10，标注技能仍全部找齐。",
    "q-00463": "样式与验证技能保持第 1、2。Config Distribution 未进入整题和各分支的候选前十。",
}


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def esc(value):
    return html.escape(str(value), quote=True)


def percent(value):
    return f"{value:.2%}"


def table(headers, rows):
    header = "".join(f"<th scope='col'>{esc(label)}</th>" for label in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<div class='table'><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>"


def write_page(name, title, content):
    (ROOT / "pages" / name).write_text(
        "<!doctype html>\n<html lang='zh-CN'><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{esc(title)}</title><link rel='stylesheet' href='style.css'>"
        f"<main>{content}</main></html>\n",
        encoding="utf-8",
    )


def ranks(skills):
    return "<ol>" + "".join(f"<li>{esc(skill['name'])}</li>" for skill in skills) + "</ol>"


def case_page(case, pair):
    case_id = case["id"]
    title = f"{case_id} {case['title']}"
    a, b = pair["a"], pair["b"]
    ordered_stages = [("整题融合检索", b["stages"][0]), *zip(
        (branch["label"] for branch in case["branches"]), b["stages"][1:]
    )]
    stage_details = "".join(
        f"<details><summary>{esc(label)}</summary><p>{esc(stage['query'])}</p>{ranks(stage['skills'])}</details>"
        for label, stage in ordered_stages
    )
    positions = [{skill["skill_id"]: skill["rank"] for skill in run["skills"]} for run in (a, b)]
    label_rows = [
        (esc(skill["name"]), *(esc(rank.get(skill["skill_id"], "未进前十")) for rank in positions))
        for skill in a["expected"]
    ]
    metrics = table(("指标", "A 整题", "B 按需求补查"), [
        ("AP@10" if key == "MAP@10" else key, percent(a["metrics"][key]), percent(b["metrics"][key]))
        for key in KEYS
    ])
    write_page(f"{case_id}.html", title, f"""
<nav><a href="index.html">十题总览</a> · <a href="../evidence/{case_id}.json">原始运行记录</a></nav>
<h1>{esc(title)}</h1>
<p>{esc(DIAGNOSES[case_id])}</p>
<h2>A/B 指标</h2>
{metrics}
<h2>数据集标注技能的名次</h2>
{table(("标注技能", "A", "B"), label_rows)}
<h2>原题与 B 组各节点</h2>
{stage_details}
<h2>最终候选</h2>
<div class="rankings"><div><h3>A Top 10</h3>{ranks(a['skills'])}</div>
<div><h3>B Top 10</h3>{ranks(b['skills'])}</div></div>
<h2>RSI 实测截图</h2>
<a href="../evidence/{case_id}.png"><img src="../evidence/{case_id}.png" alt="{case_id} 的画布与 A/B 实测结果"></a>
""")


def main():
    cases = read_json("config/retrieval-cases.json")
    summary = read_json("evidence/summary.json")
    assert len(cases) == 10 and [c["id"] for c in cases] == [s["id"] for s in summary]
    overview = []
    for case, row in zip(cases, summary):
        case_id = case["id"]
        pair = read_json(f"evidence/{case_id}.json")
        a, b = pair["a"], pair["b"]
        assert a["queryId"] == b["queryId"] == case_id
        assert a["skills"] == b["stages"][0]["skills"]
        assert a["metrics"] == row["a"] and b["metrics"] == row["b"]
        assert a["stages"][0]["query"] == b["stages"][0]["query"]
        assert [node["query"] for node in b["stages"][1:]] == [node["query"] for node in case["branches"]]
        assert (ROOT / "evidence" / f"{case_id}.png").is_file()
        overview.append([f'<a href="{case_id}.html">{case_id} {esc(case["title"])}</a>',
                         *(f"{percent(row['a'][key])} → {percent(row['b'][key])}" for key in KEYS)])
        case_page(case, pair)
    overview.append(["十题均值", *(f"{percent(mean(x['a'][key] for x in summary))} → "
                                  f"{percent(mean(x['b'][key] for x in summary))}" for key in KEYS)])
    write_page("index.html", "SkillRet 十题检索对照", f"""
<h1>SkillRet 十题检索对照</h1>
<p>A 用整题融合检索。B 保留整题检索并按人工拆出的需求补查。表内每格为 A → B。</p>
{table(("题目", "Recall@10", "Precision@10", "Completeness@10", "NDCG@10", "AP@10"), overview)}
<p>末行是十题算术均值，AP@10 的均值为 MAP@10。3 题召回提升，其中 2 题找齐标注技能。</p>
<p><a href="../evidence/summary.json">逐题指标记录</a> · <a href="../README.md">复现说明</a></p>
""")


if __name__ == "__main__":
    main()
