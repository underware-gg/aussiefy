"""Check an installed package through stdio, HTTP/ASGI and the changes Python API; no live host is contacted."""
import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile

import httpx2
import jsonschema
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

import aussiefy
from aussiefy import harness
from aussiefy.changes import SCHEMA
from aussiefy.mcp_server import build_server

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(aussiefy.__file__).resolve().parent
SOURCE = "🦘 Australian spelling. Rob waited at least 30 seconds. The toilet is broken. Keep `get_user()` unchanged."
COMMON = {"level": 4, "vulgarity": 1, "embellishment": 0, "document_type": "general"}
CAPS = {"allow_unlock": False, "allow_document_config": False, "max_chars": 180,
        "max_query_chars": 24, "lookup_limit": 3}
HIDDEN = {"unlock", "include_gated", "document_config"}
TOOLS = {"aussie_guide": harness.guide, "aussie_lookup": harness.lookup, "aussie_plan": harness.plan,
         "aussie_translate": harness.translate, "aussie_lint": harness.lint, "aussie_verify": harness.verify}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


async def exercise(client, translator, restricted):
    await client.initialize()
    tools = (await client.list_tools()).tools
    require({t.name for t in tools} == set(TOOLS), "Six shared tools must be discovered")
    for t in tools:
        a = t.annotations
        require((a.read_only_hint, a.destructive_hint, a.idempotent_hint, a.open_world_hint) ==
                (True, False, True, False), t.name + ": incorrect annotations")
        props = t.input_schema["properties"]
        if restricted:
            require(not (HIDDEN & props.keys()), t.name + ": hidden parameter leaked")
            require("custom" not in props["document_type"]["enum"], t.name + ": custom leaked")
    rows, translated = [], None
    for name, extra in [
        ("aussie_guide", {}), ("aussie_lookup", {"query": "very tired", "limit": 3}),
        ("aussie_plan", {"text": SOURCE, "markup": "markdown", "seed": 0}),
        ("aussie_translate", {"text": SOURCE, "markdown": True, "seed": 0}),
        ("aussie_lint", None), ("aussie_verify", None),
    ]:
        args = COMMON | (extra if extra is not None else
                         {"text": translated, "original": SOURCE, "markup": "markdown"})
        result = await client.call_tool(name, args)
        require(not result.is_error, f"{name}: {result}")
        expected = json.loads(json.dumps(TOOLS[name](**args, translator=translator)))
        require(result.structured_content == expected, name + ": wire result differs from toolkit")
        row = {"tool": name, "arguments": args, "result_sha256": digest(expected)}
        if name == "aussie_translate":
            translated = expected["text"]
            require(all(w in translated for w in ["🦘", "Australian", "Rob", "30", "`get_user()`"]),
                    "Source tokens changed")
            row["text"] = translated
        if name == "aussie_verify":
            require(expected["ok"], "Translation failed verification")
            row["ok"] = expected["ok"]
        rows.append(row)
    return {"tools": [t.model_dump(mode="json") for t in tools], "calls": rows}


async def http_probe(translator):
    server = build_server(translator=translator, **CAPS)
    app = server.streamable_http_app(stateless_http=True, json_response=True)
    async with app.router.lifespan_context(app):
        async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app)) as http:
            async with streamable_http_client("http://127.0.0.1:8765/mcp", http_client=http) as streams:
                async with ClientSession(*streams) as client:
                    report = await exercise(client, translator, True)
                    boundaries = []
                    for name, field in [("aussie_translate", "text"), ("aussie_plan", "text"),
                                        ("aussie_lint", "text"), ("aussie_lint", "original"),
                                        ("aussie_verify", "text"), ("aussie_verify", "original")]:
                        base = {"text": "Rob is tired."}
                        if name in {"aussie_lint", "aussie_verify"}:
                            base["original"] = "Rob is tired."
                        for size in [CAPS["max_chars"], CAPS["max_chars"] + 1]:
                            result = await client.call_tool(name, base | {field: "a" * size})
                            require(bool(result.is_error) == (size > CAPS["max_chars"]),
                                    f"{name}.{field}: wrong character boundary")
                            boundaries.append({"tool": name, "field": field, "length": size,
                                               "is_error": bool(result.is_error)})
                    for args, error in [({"query": "x" * 24}, False), ({"query": "x" * 25}, True),
                                        ({"query": "very tired", "limit": 4}, True)]:
                        result = await client.call_tool("aussie_lookup", args)
                        require(bool(result.is_error) == error, "Lookup cap not enforced")
                        boundaries.append({"tool": "aussie_lookup", "arguments": args, "is_error": error})
                    for size in [180, 181]:
                        result = await client.call_tool("aussie_translate", {"text": "🦘" * size})
                        require(bool(result.is_error) == (size > 180), "Unicode character cap differs")
                        boundaries.append({"tool": "aussie_translate", "fill": "🦘", "length": size,
                                           "is_error": bool(result.is_error)})
                    result = await client.call_tool("aussie_lookup", {"query": "very tired"})
                    require(not result.is_error and len(result.structured_content["results"]) <= 3,
                            "Default lookup limit exceeds cap")
                    args = COMMON | {"text": SOURCE, "markdown": True}
                    ordinary = await client.call_tool("aussie_translate", args)
                    hidden = await client.call_tool("aussie_translate", args | {
                        "unlock": ["all"], "document_config": {"profile": {"substitution": 0}}})
                    require(not hidden.is_error and hidden.structured_content == ordinary.structured_content,
                            "Hidden arguments changed the toolkit result")
                    custom = await client.call_tool("aussie_translate", {"text": SOURCE, "document_type": "custom"})
                    require(custom.is_error, "Custom document type was not refused")
                    report.update({"capabilities": CAPS, "boundaries": boundaries,
                                   "hidden_arguments_keep_defaults": True, "custom_refused": True})
                    return report


def changes_probe():
    schema = json.loads(SCHEMA.read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    tr = aussiefy.Translator(lookup_embedder=None)
    rows = []
    for name in ["site-defaults", "every-kind"]:
        fixture = json.loads((ROOT / "tests/fixtures/changes" / (name + ".json")).read_text())
        built = aussiefy.translate_changes(**fixture["request"], translator=tr)
        data = built.to_dict()
        require(data == fixture["response"], name + ": fixture differs")
        require(built.text == aussiefy.translate(**fixture["request"], translator=tr).text, "Observer changed text")
        jsonschema.validate(data, schema)
        for change in data["changes"]:
            require(data["text"][slice(*change["out_span"])] == change["output"], "Wrong output span")
            for option in change["alternatives"]:
                if option["entry_id"] == change["entry_id"]:
                    require(data["text"][slice(*option["out_span"])] == option["rendered"], "Wrong picked region")
        rows.append({"case": name, "request": fixture["request"], "response_sha256": digest(data),
                     "changes": len(data["changes"]), "kinds": sorted({c["kind"] for c in data["changes"]})})
    return rows


async def main(output, wheel):
    runtime_files = {str(p.relative_to(PACKAGE)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(PACKAGE.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
    with ZipFile(wheel) as archive:
        wheel_files = {p.filename.removeprefix("aussiefy/"): hashlib.sha256(archive.read(p)).hexdigest()
                       for p in archive.infolist() if p.filename.startswith("aussiefy/") and not p.is_dir()}
    require(runtime_files == wheel_files, "Imported package differs from the wheel payload")
    translator = aussiefy.Translator(lookup_embedder="bundled")
    with tempfile.TemporaryDirectory(prefix="aussiefy-installed-probe-") as work:
        env = os.environ | {"AUSSIEFY_HOME": work}
        child = subprocess.run([sys.executable, "-c", "import aussiefy; print(aussiefy.__file__)"],
                               env=env, cwd=work, check=True, capture_output=True, text=True)
        require(Path(child.stdout.strip()).resolve().parent == PACKAGE, "Child imported another package")
        params = StdioServerParameters(command=sys.executable, args=["-m", "aussiefy.mcp_server"], cwd=work, env=env)
        async with stdio_client(params) as streams:
            async with ClientSession(*streams) as client:
                stdio = await exercise(client, translator, False)
        http = await http_probe(translator)
    report = {"package_path": str(PACKAGE), "package_version": aussiefy.__version__,
              "dependencies": {n: importlib.metadata.version(n) for n in ["mcp", "mcp-types", "jsonschema", "httpx2"]},
              "runtime_files_sha256": runtime_files,
              "wheel": {"filename": wheel.name, "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
                        "payload_matches_imported_package": True},
              "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "stdio": stdio, "http_asgi": http, "changes": changes_probe(),
              "browser_case": aussiefy.translate_changes("🦘 My car is broken.",
                  translator=aussiefy.Translator(lookup_embedder=None), level=4, vulgarity=1,
                  embellishment=0).to_dict()}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("Installed-package stdio, HTTP/ASGI capability boundaries and changes fixtures passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wheel", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(asyncio.wait_for(main(args.output, args.wheel), timeout=90))
