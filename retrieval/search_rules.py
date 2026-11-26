import math
from pathlib import Path

from retrieve import read_jsonl


def doc_text(skill):
    name = (skill.get("name") or "").strip()
    description = (skill.get("description") or "").strip()
    body = (skill.get("skill_md") or description).strip()
    return f"{name} | {description} | {body}"


def partition(domains, shards=3):
    counts = {}
    for domain in domains:
        counts[domain] = counts.get(domain, 0) + 1
    assign, totals = {}, {i: 0 for i in range(shards)}
    for domain, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        target = min(totals, key=lambda i: (totals[i], i))
        assign[domain] = target
        totals[target] += count
    return assign, totals


def rrf(lists, weights, k):
    scores = {}
    for ids, weight in zip(lists, weights):
        for rank, skill_id in enumerate(ids, 1):
            scores[skill_id] = scores.get(skill_id, 0.0) + weight / (k + rank)
    return [skill_id for skill_id, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]


def load_qrels(path: Path):
    qrels = {}
    for row in read_jsonl(path):
        if row["relevance"] > 0:
            qrels.setdefault(row["query_id"], {})[row["skill_id"]] = row["relevance"]
    return qrels


def query_metrics(ranked_ids, labels, k=10):
    relevant = set(labels)
    hits = [skill_id in relevant for skill_id in ranked_ids[:k]]
    found = sum(hits)
    dcg = sum(hit / math.log2(i + 2) for i, hit in enumerate(hits))
    idcg = sum(1 / math.log2(i + 2) for i in range(min(len(relevant), k)))
    running = 0
    ap = 0.0
    for i, hit in enumerate(hits, 1):
        if hit:
            running += 1
            ap += running / i
    return {
        f"NDCG@{k}": dcg / idcg if idcg else 0.0,
        f"Recall@{k}": found / len(relevant) if relevant else 0.0,
        f"Completeness@{k}": float(bool(relevant) and found == len(relevant)),
        f"Precision@{k}": found / k,
        f"MAP@{k}": ap / len(relevant) if relevant else 0.0,
    }
