#!/usr/bin/env python3
"""Run Member external-auth boundary checks on the current fixed Demo JAR."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

import erp_finance_edit_runner as base

ROOT = base.ROOT
JAR_HASH = "4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1"
SCHEMA = "yuheng_p2_member_auth_20261123_current"
APP_PORT, MYSQL_PORT, REDIS_PORT = 48278, 13436, 16491
MYSQL, REDIS = "yh-p2-member-auth-current-mysql-20261123", "yh-p2-member-auth-current-redis-20261123"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/p2-member-external-auth-current-20261123"
SOURCE = ROOT / "scripts/verification/p2_member_external_auth_probe.py"


def run(*args, check=True):
    return subprocess.run(args, text=True, capture_output=True, check=check)


def main():
    jar = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
    jar_hash = hashlib.sha256(jar.read_bytes()).hexdigest()
    assert jar_hash == JAR_HASH, jar_hash
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT)
    assert not any(base.listening(port) for port in ports), "dedicated verification port is occupied"
    names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in names and REDIS not in names, "dedicated container name already exists"
    OUT.mkdir(parents=True, exist_ok=True)
    source = SOURCE.read_text()
    replacements = {
        'SCHEMA = "yuheng_p2_member_auth_20261122"': f'SCHEMA = "{SCHEMA}"',
        'APP_PORT, MYSQL_PORT, REDIS_PORT = 48255, 13388, 16468':
            f'APP_PORT, MYSQL_PORT, REDIS_PORT = {APP_PORT}, {MYSQL_PORT}, {REDIS_PORT}',
        'MYSQL, REDIS = "yh-p2-member-auth-mysql-20261122", "yh-p2-member-auth-redis-20261122"':
            f'MYSQL, REDIS = "{MYSQL}", "{REDIS}"',
        'ROOT / "docs/verification/2026-11-11-full-source-migration/p2-member-external-auth-20261122"':
            f'ROOT / "{OUT.relative_to(ROOT).as_posix()}"',
    }
    for old, new in replacements.items():
        assert old in source, old
        source = source.replace(old, new)
    excerpt_write = '(OUT / "application-error-excerpt.txt").write_text(excerpt + "\\n")'
    assert excerpt_write in source
    source = source.replace(excerpt_write, 'pass  # Do not persist third-party response or correlation details.')
    containers = []
    report = {"result": "FAIL", "jar_sha256": jar_hash, "schema": SCHEMA,
              "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
              "credentials_recorded": False,
              "scope": "debug SMS channel success plus social/WeChat failure boundaries; no real provider callback"}
    try:
        temp_probe = ROOT / "scripts/verification/.p2_member_external_auth_current_probe.py"
        temp_probe.write_text(source)
        probe_env = dict(os.environ)
        probe_env.pop("YH_MEMBER_EXTERNAL_AUTH_OUTPUT_DIR", None)
        try:
            result = subprocess.run(["python3", str(temp_probe)], text=True,
                                    capture_output=True, check=False, env=probe_env)
        finally:
            temp_probe.unlink(missing_ok=True)
        report["probe_stdout"], report["probe_stderr"] = result.stdout[-5000:], result.stderr[-5000:]
        assert result.returncode == 0, "current-JAR Member external-auth probe failed"
        probe_path = OUT / "member-external-auth-runtime.json"
        report["probe"] = json.loads(probe_path.read_text())
        assert report["probe"]["jar_sha256"] == jar_hash
        assert report["probe"]["cases"]["cleanup"] is True
        report["result"] = "PASS"
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
        report["cleanup"] = {"containers_absent": all(name not in names for name in (MYSQL, REDIS)),
                              "ports_listening": {str(port): base.listening(port) for port in ports}}
        report["cleanup"]["passed"] = report["cleanup"]["containers_absent"] and not any(
            report["cleanup"]["ports_listening"].values())
        (OUT / "runtime.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        assert report["cleanup"]["passed"], report["cleanup"]
    print(json.dumps({"result": report["result"], "jar_sha256": jar_hash,
                      "cases": report["probe"]["cases"], "cleanup": report["cleanup"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
