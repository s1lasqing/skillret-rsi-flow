"""Local SkillRet A/B retrieval for the course rsi-flow runner."""

import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import bm25s
import numpy as np
import torch

from retrieve import ASSETS, DATA, QUERY_PREFIX, Encoder, read_jsonl
from search_rules import doc_text, load_qrels, partition, query_metrics, rrf

CONFIG = Path(__file__).resolve().parents[1] / "config"
CASES = {}
for filename in ("retrieval-cases.json", "retest-cases.json"):
    for case in json.loads((CONFIG / filename).read_text(encoding="utf-8")):
        case_id = case["id"]
        if case_id in CASES:
            raise ValueError(f"Duplicate SkillRet case: {case_id}")
        CASES[case_id] = case


class Search:
    def __init__(self):
        torch.set_num_threads(4)
        rows = list(read_jsonl(DATA / "skills/test.jsonl"))
        self.questions = {row["id"]: row["query"] for row in read_jsonl(DATA / "queries/test.jsonl")
                          if row["id"] in CASES}
        if self.questions.keys() != CASES.keys():
            raise ValueError("Configured cases must exist in SkillRet")
        with np.load(ASSETS / "indexes/skillret-full-1024.npz", allow_pickle=False) as index:
            self.ids = index["ids"]
            self.vectors = index["vectors"]
        if self.ids.tolist() != [row["id"] for row in rows]:
            raise ValueError("Vector index and skill catalog IDs differ")
        self.names = {row["id"]: row["name"] for row in rows}
        domains = [row.get("domain") or "unknown" for row in rows]
        assignment, _ = partition(domains)
        shard_by_row = np.array([assignment[domain] for domain in domains])
        self.shards = [np.flatnonzero(shard_by_row == i) for i in range(3)]
        self.bm25 = bm25s.BM25()
        self.bm25.index(bm25s.tokenize([doc_text(row) for row in rows], stopwords="en",
                                      show_progress=False), show_progress=False)
        self.encoder = Encoder("cpu")

    def top_from_shards(self, scores, limit, *, positive_only=False):
        def order(indices):
            return indices[np.lexsort((self.ids[indices], -scores[indices]))[:limit]]

        candidates = np.concatenate([order(indices) for indices in self.shards])
        if positive_only:
            candidates = candidates[scores[candidates] > 0]
        return self.ids[order(candidates)].tolist()

    def rows(self, ids, limit):
        return [{"rank": rank, "skill_id": sid, "name": self.names[sid]}
                for rank, sid in enumerate(ids[:limit], 1)]

    def retrieve(self, case_id, branch):
        branches = CASES[case_id]["branches"]
        if branch == "whole":
            query = self.questions[case_id]
        else:
            entry = branches[int(branch)] if isinstance(branch, int) else next(
                (stage for stage in branches if stage["id"] == branch), None
            )
            if entry is None:
                raise ValueError("Unknown case branch")
            branch, query = entry["id"], entry["query"]
        tokens = bm25s.tokenize([query], stopwords="en", show_progress=False,
                                return_ids=False)[0]
        started = time.perf_counter()
        lexical = self.bm25.get_scores(tokens)
        vector = self.encoder.encode([QUERY_PREFIX + query])[0]
        ranked = rrf([
            self.top_from_shards(lexical, 100, positive_only=True),
            self.top_from_shards(self.vectors @ vector, 20),
        ], [1, 2], 10)[:10]
        return {"branch": branch, "query": query, "skills": self.rows(ranked, 10),
                "branchCount": len(branches),
                "ms": round((time.perf_counter() - started) * 1000)}

    def score(self, data):
        case_id, variant = data["queryId"], data["variant"]
        whole = data["whole"]
        branches = data["branches"]
        requested = [branch["id"] for branch in CASES[case_id]["branches"]] if variant == "B" else []
        if variant not in ("A", "B") or [stage["branch"] for stage in branches] != requested:
            raise ValueError("Each variant must submit its configured search stages")
        stages = [whole, *branches]

        def skill_ids(stage):
            return [row["skill_id"] for row in stage["skills"]]
        whole_ids = skill_ids(whole)
        if branches:
            selected = whole_ids[:3]
            for branch in branches:
                unseen = [sid for sid in skill_ids(branch) if sid not in selected]
                selected.extend(unseen[:2])
            selected.extend(sid for sid in whole_ids if sid not in selected)
        else:
            selected = whole_ids
        selected = selected[:10]
        # qrels enter only after the final ranking is determined.
        labels = load_qrels(DATA / "qrels/test.jsonl")[case_id]
        return {
            "queryId": case_id, "variant": variant, "stages": stages,
            "skills": self.rows(selected, 10),
            "expected": self.rows(list(labels), len(labels)),
            "metrics": query_metrics(selected, labels),
            "candidateCount": len(self.ids), "shardSizes": [len(s) for s in self.shards],
            "ms": sum(stage["ms"] for stage in stages),
        }

class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/cases":
            self.send_json(200, list(CASES.values()))
        elif self.path == "/health":
            self.send_json(200, {"ready": True})
        else:
            self.send_json(404, {"error": "Unknown API"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 0 < length <= 65536:
                raise ValueError("Invalid request body length")
            data = json.loads(self.rfile.read(length))
            if data["queryId"] not in CASES:
                raise ValueError("Unknown SkillRet case")
            if self.path == "/retrieve":
                output = search.retrieve(data["queryId"], data["branch"])
            elif self.path == "/score":
                output = search.score(data)
            else:
                self.send_json(404, {"error": "Unknown API"})
                return
            self.send_json(200, output)
        except (KeyError, IndexError, TypeError, ValueError) as error:
            self.send_json(400, {"error": str(error)})

if __name__ == "__main__":
    search = Search()
    print(f"Search ready on localhost:18940, shard sizes {[len(s) for s in search.shards]}", flush=True)
    HTTPServer(("127.0.0.1", 18940), Handler).serve_forever()

