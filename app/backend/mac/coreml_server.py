#!/usr/bin/env python3
import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


MODEL_VERSION_BY_NAME = {
    "coreml-stable-diffusion-v1-5": "runwayml/stable-diffusion-v1-5",
    "stable-diffusion-v1-5": "runwayml/stable-diffusion-v1-5",
    "stable-diffusion-v1-4": "CompVis/stable-diffusion-v1-4",
    "cyberrealistic": "runwayml/stable-diffusion-v1-5",
}


def json_response(handler, code, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def find_coreml_resource_dir(model_path: Path) -> Path:
    candidates = [
        model_path,
        model_path / "Resources",
        model_path / "compiled",
        model_path / "packages",
        model_path / "split_einsum_v2" / "compiled",
        model_path / "split_einsum" / "compiled",
        model_path / "original" / "compiled",
        model_path / "split_einsum_v2" / "packages",
        model_path / "split_einsum" / "packages",
        model_path / "original" / "packages",
    ]

    required_names = {
        "text_encoder.mlmodelc",
        "text_encoder.mlpackage",
        "textencoder.mlmodelc",
        "textencoder.mlpackage",
    }
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        names = {entry.name.lower() for entry in candidate.iterdir()}
        has_text_encoder = bool(names & required_names)
        has_unet = "unet.mlmodelc" in names or "unet.mlpackage" in names
        if has_text_encoder and has_unet:
            return candidate

    for candidate in model_path.rglob("*"):
        if not candidate.is_dir():
            continue
        names = {entry.name.lower() for entry in candidate.iterdir()}
        has_text_encoder = bool(names & required_names)
        has_unet = "unet.mlmodelc" in names or "unet.mlpackage" in names
        if has_text_encoder and has_unet:
            return candidate

    raise FileNotFoundError(
        f"Could not find CoreML resources under {model_path}. "
        "Expected a folder containing text_encoder and unet .mlmodelc/.mlpackage files."
    )


def infer_model_version(model_path: Path) -> str:
    override = os.environ.get("COREML_MODEL_VERSION")
    if override:
        return override
    lower = model_path.name.lower()
    for needle, version in MODEL_VERSION_BY_NAME.items():
        if needle in lower:
            return version
    return "runwayml/stable-diffusion-v1-5"


def infer_model_sources(resource_dir: Path) -> str:
    names = {entry.name.lower() for entry in resource_dir.iterdir()}
    if any(name.endswith(".mlmodelc") for name in names):
        return "compiled"
    return "packages"


def latest_png(root: Path) -> Path:
    images = sorted(root.rglob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not images:
        raise FileNotFoundError("CoreML generation finished but did not write a PNG output.")
    return images[0]


class CoreMLServerState:
    def __init__(self, model: Path, steps: int, cfg_scale: float):
        self.model = model
        self.resources = find_coreml_resource_dir(model)
        self.model_version = infer_model_version(model)
        self.steps = steps
        self.cfg_scale = cfg_scale
        self.started_at = time.time()


def make_handler(state: CoreMLServerState):
    class Handler(BaseHTTPRequestHandler):
        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.end_headers()

        def do_GET(self):
            if self.path == "/health":
                json_response(self, 200, {
                    "ok": True,
                    "ready": True,
                    "model": str(state.model),
                    "resources": str(state.resources),
                    "model_version": state.model_version,
                    "uptime_sec": round(time.time() - state.started_at, 1),
                })
                return
            if self.path == "/v1/models":
                json_response(self, 200, {
                    "object": "list",
                    "data": [{
                        "id": state.model.name,
                        "object": "model",
                        "owned_by": "local-coreml",
                    }],
                })
                return
            json_response(self, 404, {"ok": False, "error": "Unknown endpoint"})

        def do_POST(self):
            if self.path != "/v1/images/generations":
                json_response(self, 404, {"ok": False, "error": "Unknown endpoint"})
                return

            try:
                length = int(self.headers.get("Content-Length", "0") or "0")
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                prompt = str(payload.get("prompt") or "").strip()
                if not prompt:
                    raise ValueError("Prompt is required")

                size = str(payload.get("size") or "512x512").lower().split("x")
                if len(size) == 2 and size != ["512", "512"]:
                    raise ValueError("CoreML models in this app currently generate at their compiled resolution, normally 512x512.")

                steps = max(1, int(payload.get("steps") or state.steps or 30))
                guidance = float(payload.get("cfg_scale") or state.cfg_scale or 7.0)
                seed = int(payload.get("seed")) if payload.get("seed") not in (None, -1) else int(time.time_ns() % (2 ** 32))
                negative_prompt = str(payload.get("negative_prompt") or "").strip()

                started = time.time()
                out_dir = Path(tempfile.mkdtemp(prefix="portable-diffusion-coreml-"))
                cmd = [
                    sys.executable,
                    "-m",
                    "python_coreml_stable_diffusion.pipeline",
                    "--prompt",
                    prompt,
                    "-i",
                    str(state.resources),
                    "-o",
                    str(out_dir),
                    "--compute-unit",
                    os.environ.get("COREML_COMPUTE_UNIT", "CPU_AND_NE"),
                    "--seed",
                    str(seed),
                    "--model-version",
                    state.model_version,
                    "--num-inference-steps",
                    str(steps),
                    "--guidance-scale",
                    str(guidance),
                    "--model-sources",
                    infer_model_sources(state.resources),
                ]
                if negative_prompt:
                    cmd.extend(["--negative-prompt", negative_prompt])

                print("[coreml-npu] generating image", flush=True)
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                output_lines = []
                assert proc.stdout is not None
                for line in proc.stdout:
                    output_lines.append(line.rstrip())
                    print(line, end="", flush=True)
                code = proc.wait()
                if code != 0:
                    raise RuntimeError("CoreML generation failed with code %s:\n%s" % (code, "\n".join(output_lines[-30:])))

                image_path = latest_png(out_dir)
                encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
                shutil.rmtree(out_dir, ignore_errors=True)
                print("[coreml-npu] decoding complete", flush=True)
                json_response(self, 200, {
                    "created": int(time.time()),
                    "data": [{
                        "b64_json": encoded,
                        "seed": seed,
                    }],
                    "duration_sec": round(time.time() - started, 2),
                })
            except Exception as exc:
                json_response(self, 500, {"ok": False, "error": str(exc)})

        def log_message(self, fmt, *args):
            print("[coreml-npu-http] " + fmt % args, flush=True)

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen-port", required=True, type=int)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--cfg-scale", type=float, default=7.0)
    args = parser.parse_args()

    state = CoreMLServerState(args.model, args.steps, args.cfg_scale)
    print(f"[coreml-npu] Model: {state.model}", flush=True)
    print(f"[coreml-npu] Resources: {state.resources}", flush=True)
    print(f"[coreml-npu] Model version: {state.model_version}", flush=True)
    print("| 1/1 - CoreML resources ready", flush=True)
    server = ThreadingHTTPServer(("127.0.0.1", args.listen_port), make_handler(state))
    print(f"[coreml-npu] listening on http://127.0.0.1:{args.listen_port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
