"""Build the vector index used by the ten-question SkillRet flow."""

import argparse
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import torch

ASSETS = Path(os.environ.get("SKILLRET_ASSETS") or Path(__file__).resolve().parents[1] / "local-assets")
DATA = ASSETS / "data"
MODEL = "anonymous-ed-benchmark/SKILLRET-Embedding-0.6B"
MODEL_REVISION = "408aa6e2c1db2f89c791000000c70843154ed48b"
MAX_LENGTH = 1024
QUERY_PREFIX = (
    "Instruct: Given a skill search query, retrieve relevant skills that match the query\n"
    "Query: "
)


def read_jsonl(path):
    with path.open(encoding="utf-8") as source:
        for line in source:
            if line.strip():
                yield json.loads(line)


class Encoder:
    def __init__(self, device):
        os.environ.setdefault("TORCHINDUCTOR_CACHE_DIR", str(ASSETS / ".torchinductor-cache"))
        from transformers import AutoModel, AutoTokenizer

        self.device = device
        self.device_name = torch.cuda.get_device_name() if device == "cuda" else "CPU"
        self.max_length = MAX_LENGTH
        dtype = torch.bfloat16 if self.device == "cuda" else torch.float32
        path = ASSETS / "models" / "skillret"
        if not (path / "model.safetensors").is_file():
            raise ValueError(f"Model weights are missing from {path}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            path, padding_side="left", local_files_only=True, trust_remote_code=False
        )
        self.model = AutoModel.from_pretrained(
            path,
            dtype=dtype,
            local_files_only=True,
            trust_remote_code=False,
            use_safetensors=True,
            attn_implementation="sdpa",
        ).to(device).eval()

    @torch.inference_mode()
    def encode(self, texts):
        batch = self.tokenizer(
            texts, truncation=True, max_length=self.max_length, padding=True, return_tensors="pt"
        ).to(self.device)
        # Left padding keeps the last real token at the end of every row.
        output = self.model(**batch, use_cache=False).last_hidden_state[:, -1]
        return torch.nn.functional.normalize(output.float(), dim=1).cpu().numpy()


def skill_text(skill):
    return " | ".join(
        (skill.get(field) or "").strip() for field in ("name", "description", "skill_md")
    )


def build_index(encoder, catalog, batch_size, index_path):
    rows = list(read_jsonl(catalog))
    ids = np.array([row["id"] for row in rows])
    names = np.array([row["name"] for row in rows])
    if not len(ids) or len(set(ids)) != len(ids):
        raise ValueError("The skill catalog is empty or has duplicate skill IDs")

    texts = [skill_text(row) for row in rows]
    del rows
    sorted_indices = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    vectors = np.empty((len(ids), encoder.model.config.hidden_size), dtype=np.float32)
    for start in range(0, len(ids), batch_size):
        indices = sorted_indices[start : start + batch_size]
        vectors[indices] = encoder.encode([texts[i] for i in indices])
        done = start + len(indices)
        if done == len(ids) or done // 512 != start // 512:
            print(f"Encoded {done}/{len(ids)} skills", file=sys.stderr, flush=True)
    if not np.isfinite(vectors).all():
        raise ValueError("The encoder returned non-finite vectors")

    index_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=index_path.parent, prefix=index_path.stem + ".", delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
        try:
            np.savez(temporary, ids=ids, names=names, vectors=vectors, metadata=json.dumps({"model": MODEL, "revision": MODEL_REVISION, "max_length": MAX_LENGTH, "device": encoder.device}))
            temporary.close()
            os.replace(temporary_path, index_path)
        finally:
            temporary.close()
            temporary_path.unlink(missing_ok=True)
    return {"candidate_count": len(ids), "dimension": int(vectors.shape[1]), "index": str(index_path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--batch-size", type=int, default=24)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("CUDA is unavailable. Use --device cpu for a CPU build.")
    if args.device == "cpu":
        torch.set_num_threads(4)
    encoder = Encoder(args.device)
    index_path = ASSETS / "indexes/skillret-full-1024.npz"
    print(json.dumps(build_index(encoder, DATA / "skills/test.jsonl", args.batch_size, index_path)))


if __name__ == "__main__":
    main()
