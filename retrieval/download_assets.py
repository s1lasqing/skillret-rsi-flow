"""Download the dataset snapshot and embedding weights used by the demo."""

from pathlib import Path

from huggingface_hub import hf_hub_download, snapshot_download

from retrieve import ASSETS, DATA, MODEL, MODEL_REVISION

DATASET = "ThakiCloud/SKILLRET"
DATASET_REVISION = "6583d7d2ed07644d0fb8938ed8178f3a7dc42a12"


def main():
    for subset in ("skills", "queries", "qrels"):
        hf_hub_download(
            repo_id=DATASET,
            repo_type="dataset",
            revision=DATASET_REVISION,
            filename=f"data/{subset}/test.jsonl",
            local_dir=DATA.parent,
        )
    snapshot_download(
        MODEL, revision=MODEL_REVISION,
        local_dir=ASSETS / "models" / "skillret",
        allow_patterns=["config.json", "tokenizer*.json", "model.safetensors", "chat_template.jinja"],
    )
    print(f"Assets ready at {Path(ASSETS).resolve()}")


if __name__ == "__main__":
    main()
