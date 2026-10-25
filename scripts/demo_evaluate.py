"""Run a real demo audit and reproducible fixture comparisons through the public API."""

import argparse
import json
import time
from pathlib import Path
import httpx


def wait(client, path, limit=300):
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        response = client.get(path)
        response.raise_for_status()
        body = response.json()
        if body["status"] in {"completed", "failed", "invalidated"}:
            return body
        time.sleep(1)
    raise TimeoutError("Background job did not finish within the evaluation deadline.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--split", choices=["development", "held_out"], default="development")
    args = parser.parse_args()
    out = Path("artifacts")
    out.mkdir(exist_ok=True)
    with httpx.Client(base_url=args.url, timeout=30) as client:
        client.post("/api/v1/auth/guest").raise_for_status()
        account = client.get("/api/v1/auth/me").json()
        kb = client.get("/api/v1/knowledge-bases").json()[0]["id"]
        seeded = client.post("/api/v1/demo/seed", params={"kb_id": kb})
        seeded.raise_for_status()
        sample = seeded.json()
        for _ in range(120):
            docs = client.get("/api/v1/documents", params={"kb_id": kb}).json()
            if docs and all(d["status"] == "indexed" for d in docs):
                break
            if any(d["status"] in {"failed", "needs_ocr"} for d in docs):
                raise RuntimeError(docs)
            time.sleep(1)
        response = client.post("/api/v1/audits", json={"kb_id": kb, **sample, "mode": "corrective"})
        response.raise_for_status()
        report = wait(client, "/api/v1/audits/" + response.json()["id"])
        (out / "sample-audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("sample_status", report["status"], "counts", report.get("result", {}).get("counts"), flush=True)
        response = client.post("/api/v1/evaluations/run", json={"kb_id": kb, "split": args.split})
        response.raise_for_status()
        evaluation = wait(client, "/api/v1/evaluations/" + response.json()["id"], 600)
        (out / f"evaluation-{args.split}.json").write_text(json.dumps(evaluation, indent=2), encoding="utf-8")
        print("evaluation_status", evaluation["status"], flush=True)
        if evaluation["status"] == "completed":
            print(
                json.dumps(
                    {
                        k: {
                            "fixture_agreement": v["fixture_agreement"],
                            "macro_f1": v["macro_f1"],
                            "cases": v["case_count"],
                            "p95_ms": v["p95_ms"],
                        }
                        for k, v in evaluation["result"]["modes"].items()
                    },
                    indent=2,
                )
            )
        (out / "demo-context.json").write_text(
            json.dumps({"email": account["email"], "kb_id": kb}), encoding="utf-8"
        )
        # No session token is written to disk.


if __name__ == "__main__":
    main()
