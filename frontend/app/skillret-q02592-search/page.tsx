"use client";

import { useEffect, useMemo, useState } from "react";
import SkillRetCanvas, { type CanvasGraph } from "./SkillRetCanvas";
import styles from "./page.module.css";

const flowId = "@com.horsecoder.common.whuTalent.skillTesting.core/FLOW_SKILLRET_RETRIEVAL";
const final = { id: "SEARCH_SCORE", name: "合并排名及评测", color: "#337a54", column: .5, row: 2 };
const whole = { id: "SEARCH_WHOLE", name: "整题融合检索", color: "#416ca8", column: .5, row: 1 };
const colors = ["#8167a0", "#9d6d2c", "#337b91"];
const metrics = ["Recall@10", "Precision@10", "Completeness@10", "NDCG@10", "MAP@10"];

type Case = { id: string; title: string; branches: { id: string; label: string }[] };
type Skill = { skill_id: string; name: string; rank: number };
type Result = {
  variant: "A" | "B";
  candidateCount: number;
  shardSizes: number[];
  skills: Skill[];
  expected: Skill[];
  metrics: Record<string, number>;
  stages: { branch: string; query: string; skills: Skill[]; ms: number }[];
};
const percent = (n: number) => new Intl.NumberFormat("zh-CN", { style: "percent", maximumFractionDigits: 2 }).format(n);

function makeGraph(current: Case, view: "A" | "B"): CanvasGraph {
  const input = { id: "INPUT", name: `原题 ${current.id}`, color: "#337a76", column: .5, row: 0 };
  const branches = view === "B" ? current.branches : [];
  return {
    nodes: [
      input,
      { ...whole, column: branches.length ? 0 : .5 },
      ...branches.map((branch, i) => ({
        id: branch.id, name: branch.label, color: colors[i], column: (i + 1) / branches.length, row: 1,
      })),
      final,
    ],
    edges: [
      { from: input.id, to: whole.id, label: "原题" },
      ...branches.map((branch, i) => ({ from: input.id, to: branch.id, label: `需求 ${i + 1}` })),
      { from: whole.id, to: final.id, label: "整题候选" },
      ...branches.map((branch, i) => ({ from: branch.id, to: final.id, label: `候选 ${i + 1}` })),
    ],
  };
}

export default function RetrievalDemo() {
  const [cases, setCases] = useState<Case[]>([]);
  const [selected, setSelected] = useState("q-02592");
  const [view, setView] = useState<"A" | "B">("B");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [pair, setPair] = useState<{ a: Result; b: Result } | null>(null);
  const current = cases.find((item) => item.id === selected);
  const graph = useMemo(() => current && makeGraph(current, view), [current, view]);

  useEffect(() => {
    const controller = new AbortController();
    async function loadCases() {
      try {
        const response = await fetch("/skillret-runtime/cases", { signal: controller.signal });
        if (!response.ok) throw new Error("题目清单加载失败");
        setCases(await response.json());
      } catch (failure) {
        if (!controller.signal.aborted) setError(failure instanceof Error ? failure.message : String(failure));
      }
    }
    void loadCases();
    return () => controller.abort();
  }, []);

  async function run() {
    if (!current) return;
    setPending(true);
    setError("");
    setPair(null);
    try {
      const results: Result[] = [];
      for (const variant of ["A", "B"]) {
        const response = await fetch("/skillret-runtime/api/engine/flow", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ flowId, params: { queryId: current.id, variant } }),
          signal: AbortSignal.timeout(90000),
        });
        const payload = await response.json();
        if (!response.ok || typeof payload.data?.value?.result !== "string") {
          throw new Error(payload.message || "检索运行失败");
        }
        results.push(JSON.parse(payload.data.value.result) as Result);
      }
      setPair({ a: results[0], b: results[1] });
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      setPending(false);
    }
  }

  const visible = pair && (view === "A" ? pair.a : pair.b);
  const branchName = (id: string) => id === "whole" ? whole.name : current?.branches.find((branch) => branch.id === id)?.label;
  const rank = (result: Result, id: string) =>
    result.skills.find((skill) => skill.skill_id === id)?.rank ?? "未进前十";

  return (
    <main className={styles.workspace}>
      <header className={styles.header}>
        <div>
          <p className={styles.context}>SkillRet · {selected}</p>
          <h1>{current?.title ?? "技能检索对照"}</h1>
          <p>A 做整题融合检索。B 保留整题检索，并按画布上的需求分别补查。</p>
        </div>
        <div className={styles.runControls}>
          <label htmlFor="case-picker">题目</label>
          <select id="case-picker" value={selected} disabled={pending || !current} onChange={(event) => {
            setSelected(event.target.value);
            setPair(null);
            setError("");
          }}>
            {cases.map((item) => <option key={item.id} value={item.id}>{item.id}</option>)}
          </select>
          <label htmlFor="search-canvas-view">画布</label>
          <select id="search-canvas-view" value={view} onChange={(event) => setView(event.target.value === "A" ? "A" : "B")}>
            <option value="A">A 整题</option>
            <option value="B">B 按需补查</option>
          </select>
          <button type="button" disabled={pending || !current} onClick={run}>{pending ? "检索中…" : "运行 A/B"}</button>
        </div>
      </header>
      {graph && <SkillRetCanvas graph={graph} />}
      {error && <p role="alert" className={styles.error}>{error}</p>}
      {pair && visible && (
        <section className={styles.evidence} aria-label="检索对照">
          <h2>检索结果对照</h2>
          <p>同一语料 {pair.a.candidateCount} 条，三个逻辑分片全查。两组最终各返回 Top 10。</p>
          <table>
            <thead><tr><th scope="col">标注技能</th><th scope="col">A 名次</th><th scope="col">B 名次</th></tr></thead>
            <tbody>{pair.a.expected.map((skill) => (
              <tr key={skill.skill_id}><th scope="row">{skill.name}</th>
                <td>{rank(pair.a, skill.skill_id)}</td><td>{rank(pair.b, skill.skill_id)}</td></tr>
            ))}</tbody>
          </table>
          <table>
            <thead><tr><th scope="col">指标</th><th scope="col">A 整题</th><th scope="col">B 按需补查</th></tr></thead>
            <tbody>{metrics.map((key) => (
              <tr key={key}><th scope="row">{key === "MAP@10" ? "AP@10" : key}</th>
                <td>{percent(pair.a.metrics[key])}</td><td>{percent(pair.b.metrics[key])}</td></tr>
            ))}</tbody>
          </table>
          <h3>{view} 组节点检索记录</h3>
          {visible.stages.map((stage) => (
            <details key={stage.branch}>
              <summary>{branchName(stage.branch)} · 首位 {stage.skills[0]?.name} · {stage.ms} ms</summary>
              <p>{stage.query}</p>
              <ol>{stage.skills.map((skill) => <li key={skill.skill_id}>{skill.name}</li>)}</ol>
            </details>
          ))}
          <details>
            <summary>{view} 组最终 Top 10</summary>
            <ol>{visible.skills.map((skill) => <li key={skill.skill_id}>{skill.name}</li>)}</ol>
          </details>
        </section>
      )}
    </main>
  );
}

