#!/usr/bin/env python3
"""真实启动 stdio 可执行文件；只使用临时数据与具名私有 pasteboard。"""
import argparse
import base64
import concurrent.futures
import contextlib
import hashlib
import json
import pathlib
import select
import subprocess
import struct
import tempfile
import time
import uuid
import zlib


class Client:
    def __init__(self, binary, directory, initialize=True):
        self.process = subprocess.Popen([str(binary), "--data-dir", str(directory)],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, bufsize=0)
        self.sequence = 0
        if initialize:
            result = self.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                                 "clientInfo": {"name": "fixture-test", "version": "1"}})
            assert result["result"]["capabilities"]["tools"]["listChanged"] is False

    def send(self, value):
        self.process.stdin.write(json.dumps(value, ensure_ascii=False).encode() + b"\n")

    def read(self):
        assert select.select([self.process.stdout], [], [], 15)[0], "MCP response timed out"
        line = self.process.stdout.readline()
        assert line and len(line) <= 2 * 1024 * 1024 + 1, "Bad response frame"
        value = json.loads(line)
        assert value["jsonrpc"] == "2.0", "stdout contains non-protocol output"
        return value

    def request(self, method, params=None):
        self.sequence += 1
        request = {"jsonrpc": "2.0", "id": self.sequence, "method": method}
        if params is not None:
            request["params"] = params
        self.send(request)
        reply = self.read()
        assert reply["id"] == self.sequence, reply
        return reply

    def tool(self, name, arguments=None):
        reply = self.request("tools/call", {"name": name, "arguments": arguments or {}})
        assert "error" not in reply and not reply["result"].get("isError", False), reply
        return reply["result"].get("structuredContent", reply["result"])

    def invalid_tool(self, name, arguments):
        reply = self.request("tools/call", {"name": name, "arguments": arguments})
        assert reply["error"]["code"] == -32602, reply

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                raise
        stderr = self.process.stderr.read().decode(errors="replace")
        assert self.process.returncode == 0, stderr
        assert not stderr.strip(), stderr
        assert self.process.stdout.read() == b"", "Unexpected stdout after final protocol response"
        self.process.stdout.close()
        self.process.stderr.close()


@contextlib.contextmanager
def client(binary, directory, initialize=True):
    instance = Client(binary, directory, initialize)
    try:
        yield instance
    finally:
        instance.close()


def run(binary):
    checks = []
    with tempfile.TemporaryDirectory(prefix="pasto-mcp-test-") as temporary:
        directory = pathlib.Path(temporary) / "store"
        with client(binary, directory, initialize=False) as c:
            assert c.request("tools/list")["error"]["code"] == -32002
            assert c.request("ping")["result"] == {}
            assert c.request("initialize", {})["error"]["code"] == -32602
            assert c.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {}})["error"]["code"] == -32602
        checks.append("initialization gate and ping before initialize")
        with client(binary, directory) as c:
            tools = {t["name"]: t for t in c.request("tools/list")["result"]["tools"]}
            original = {"search", "read_item", "create_item", "update_item", "delete_item", "list_pinboards",
                        "create_pinboard", "rename_pinboard", "delete_pinboard", "add_item_to_pinboard", "remove_item_from_pinboard"}
            assert set(tools) == original | {"replica_restore_item", "replica_copy_item"}
            for name in original:
                assert tools[name]["inputSchema"]["additionalProperties"] is False
            assert tools["read_item"]["inputSchema"]["required"] == ["id"]
            assert tools["delete_item"]["annotations"]["destructiveHint"] is True
            assert tools["create_item"]["inputSchema"]["required"] == ["content"]
            assert set(tools["search"]["inputSchema"]["properties"]) == {
                "query", "type", "app", "device", "pinboard_id", "title", "date_from", "date_to", "limit"}
            assert set(tools["add_item_to_pinboard"]["inputSchema"]["required"]) == {"item_id", "pinboard_id"}
            checks.append("all 11 evidence-backed tool names and schemas; 2 extensions separately named")

            c.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
            c.send({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "create_item", "arguments": {"content": "notification must not mutate"}}})
            assert c.request("ping")["result"] == {}
            assert not c.tool("search")["items"]
            checks.append("notifications produce no response and never execute mutation tools")

            text = "中文 🧪 café e\u0301\n第二行\r\t\u0000 JSON \\\""
            item = c.tool("create_item", {"content": text})
            identity = item["id"]
            assert "timestamp" in item
            assert c.tool("read_item", {"id": identity})["content"][0]["text"] == text
            assert c.tool("search", {"query": "中文 第二行"})["items"][0]["id"] == identity
            assert c.tool("create_item", {"content": text})["id"] == identity
            checks.append("Unicode, combining characters, escaped NUL/newlines and exact full-content roundtrip; deduplication")

            board = c.tool("create_pinboard", {"name": "  测试 Pinboard  "})
            assert board["name"] == "测试 Pinboard"
            pinned = c.tool("create_item", {"content": "pinned-only fixture", "list_id": board["id"]})
            assert "timestamp" not in pinned
            assert any(i["id"] == pinned["id"] for i in c.tool("search")["items"])
            assert c.tool("search", {"pinboard_id": board["id"]})["items"][0]["id"] == pinned["id"]
            assert c.tool("create_item", {"content": "pinned-only fixture", "list_id": board["id"]})["id"] == pinned["id"]
            promoted = c.tool("create_item", {"content": "pinned-only fixture"})
            assert promoted["id"] == pinned["id"] and "timestamp" in promoted
            c.tool("add_item_to_pinboard", {"item_id": identity, "pinboard_id": board["id"]})
            assert c.tool("add_item_to_pinboard", {"item_id": identity, "pinboard_id": board["id"]})["itemCount"] == 2
            board2 = c.tool("create_pinboard", {"name": "second"})
            c.tool("add_item_to_pinboard", {"item_id": identity, "pinboard_id": board2["id"]})
            c.tool("remove_item_from_pinboard", {"item_id": identity, "pinboard_id": board["id"]})
            assert c.tool("search", {"pinboard_id": board2["id"]})["items"][0]["id"] == identity
            assert c.tool("rename_pinboard", {"id": board2["id"], "name": "  renamed  "})["name"] == "renamed"
            checks.append("Pinboard creation/rename/list, pinned-only items, promotion, idempotent pinning, selective unpin")

            assert c.tool("update_item", {"id": identity, "title": "", "content": "#AABBCC"})["type"] == "color"
            color = c.tool("create_item", {"content": "abcdef"})
            assert c.tool("read_item", {"id": color["id"]})["content"][0]["text"] == "#ABCDEF"
            assert c.tool("update_item", {"id": identity, "content": "https://example.invalid/测试"})["type"] == "link"
            c.tool("update_item", {"id": identity, "title": "fixture-title", "content": text})
            assert c.tool("search", {"type": "text", "title": "fixture-title", "app": "MCP", "device": "此Mac"})["items"][0]["id"] == identity
            assert not c.tool("search", {"date_from": "2099-01-01"})["items"]
            assert c.tool("search", {"limit": 1})["hasMore"] is True
            assert len(c.tool("search", {"limit": 0})["items"]) == 1
            assert len(c.tool("search", {"limit": 101})["items"]) <= 100
            checks.append("update title/body and type detection; combined type/title/app/device/date filters and pagination")

            assert c.tool("delete_item", {"id": pinned["id"]})["deleted"] is False
            assert c.tool("read_item", {"id": pinned["id"]})["content"][0]["text"] == "pinned-only fixture"
            assert c.tool("delete_item", {"id": pinned["id"], "confirm": True})["deleted"] is True
            c.invalid_tool("read_item", {"id": pinned["id"]})
            c.invalid_tool("replica_restore_item", {"item_id": pinned["id"]})
            assert c.tool("delete_pinboard", {"id": board2["id"]})["deleted"] is False
            assert c.tool("delete_pinboard", {"id": board2["id"], "confirm": True})["deleted"] is True
            assert c.tool("read_item", {"id": identity})["content"][0]["text"] == text
            checks.append("two-step deletion preview; confirmed permanent deletion; board removal preserves historical item")

            c.invalid_tool("replica_copy_item", {"item_id": identity, "pasteboard_name": "general"})
            copied = c.tool("replica_copy_item", {"item_id": identity, "pasteboard_name": "pasto-test-" + str(uuid.uuid4()), "plain_text_only": True})
            assert copied["copied"] is True and copied["system_clipboard_changed"] is False
            checks.append("general clipboard denied by default; explicit copy writes only unique private pasteboard")

            for name, args in [
                ("search", {"limit": True}), ("search", {"limit": 1.5}), ("search", {"date_from": "bad"}),
                ("search", {"date_from": "2026-10-23", "date_to": "2026-10-21"}),
                ("search", {"date_to": "2026-02-30"}), ("search", {"unknown": 1}),
                ("read_item", {"id": "bad"}), ("create_item", {"content": "  "}),
                ("create_item", {"content": None}), ("update_item", {"id": identity}),
                ("delete_item", {"id": identity, "confirm": 1}), ("not-a-tool", {})]:
                c.invalid_tool(name, args)
            assert c.request("unknown/method")["error"]["code"] == -32601
            for raw, code in [(b"{broken\n", -32700), (b'{"a":"\xff"}\n', -32700),
                              (b"[]\n", -32600), (b'{"jsonrpc":"2.0","id":false,"method":"ping"}\n', -32600),
                              (b"x" * (1024 * 1024 + 1) + b"\n", -32600)]:
                c.process.stdin.write(raw)
                assert c.read()["error"]["code"] == code
            assert c.request("ping")["result"] == {}
            checks.append("invalid params/types/UUID/dates, unknown methods/tools, JSON/UTF-8 errors, 1 MiB bound and recovery")

            with client(binary, directory) as other:
                assert other.tool("read_item", {"id": identity})["content"][0]["text"] == text
                changed = other.tool("create_item", {"content": "cross-process-visible"})
                assert c.tool("read_item", {"id": changed["id"]})["content"][0]["text"] == "cross-process-visible"
            # 只改测试目录fixture，以模拟UI软删除，再验证扩展恢复。
            state_path = directory / "clipboard.json"
            state = json.loads(state_path.read_text())
            next(i for i in state["items"] if i["id"] == identity)["isDeleted"] = True
            state_path.write_text(json.dumps(state))
            c.invalid_tool("read_item", {"id": identity})
            assert c.tool("replica_restore_item", {"item_id": identity})["id"] == identity
            checks.append("shared persistence across running processes, reload before each call and soft-delete restoration extension")

            state = json.loads(state_path.read_text())
            template = next(i for i in state["items"] if i["id"] == identity)
            def png_chunk(kind, payload):
                return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))
            png = (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
                   + png_chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00\xff")) + png_chunk(b"IEND", b""))
            wide_png = (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 2048, 2, 8, 6, 0, 0, 0))
                        + png_chunk(b"IDAT", zlib.compress((b"\x00" + b"\xff\x00\x00\xff" * 2048) * 2)) + png_chunk(b"IEND", b""))
            image_id, files_id, large_id, wide_id = [str(uuid.uuid4()).upper() for _ in range(4)]
            fixtures = [
                {**template, "id": image_id, "kind": "image", "title": "fixture-image", "plainText": None,
                 "payloads": {"public.png": base64.b64encode(png).decode()}},
                {**template, "id": files_id, "kind": "files", "title": "fixture-files", "plainText": "/fixture/one\n/fixture/two", "payloads": {}},
                {**template, "id": wide_id, "kind": "image", "title": "fixture-wide-image", "plainText": None,
                 "payloads": {"public.png": base64.b64encode(wide_png).decode()}},
                {**template, "id": large_id, "kind": "text", "title": "fixture-large", "plainText": "x" * (3 * 1024 * 1024), "payloads": {}}
            ]
            state["items"].extend(fixtures)
            state_path.write_text(json.dumps(state))
            image = c.tool("read_item", {"id": image_id})["content"][0]
            assert image["type"] == "image" and image["mimeType"] == "image/png"
            assert base64.b64decode(image["data"]).startswith(b"\x89PNG")
            downscaled = base64.b64decode(c.tool("read_item", {"id": wide_id})["content"][0]["data"])
            assert struct.unpack(">II", downscaled[16:24]) == (1024, 1)
            assert c.tool("read_item", {"id": files_id})["content"][0]["text"] == "/fixture/one\n/fixture/two"
            c.invalid_tool("update_item", {"id": image_id, "content": "disallowed"})
            c.invalid_tool("update_item", {"id": files_id, "content": "disallowed"})
            assert c.tool("update_item", {"id": image_id, "title": "new image title"})["type"] == "image"
            assert c.request("tools/call", {"name": "read_item", "arguments": {"id": large_id}})["error"]["code"] == -32001
            assert c.request("ping")["result"] == {}
            checks.append("PNG/file fixture reads and image downscaling, image/file body edit rejection, image title edit and 2 MiB response bound recovery")

        def worker(number):
            with client(binary, directory) as c:
                return [c.tool("create_item", {"content": f"concurrent-{number}-{i}"})["id"] for i in range(8)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            identities = sum(list(pool.map(worker, range(6))), [])
        assert len(set(identities)) == 48
        with client(binary, directory) as c:
            results = c.tool("search", {"query": "concurrent-", "limit": 100})["items"]
            assert {i["id"] for i in results} == set(identities)
        checks.append("6 real concurrent CLI processes, 48 persistent writes without lost updates")
    return {"status": "passed", "checks": checks, "check_groups": len(checks),
            "scope": "Replica MCP executable end-to-end; fixture-only. Not an original-vs-replica semantic equivalence claim.",
            "system_clipboard_used": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1] / ".build/debug/pasto-mcp")
    parser.add_argument("--report", type=pathlib.Path)
    args = parser.parse_args()
    started = time.monotonic()
    result = run(args.binary.resolve())
    result["binary_sha256"] = hashlib.sha256(args.binary.resolve().read_bytes()).hexdigest()
    result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
