from __future__ import annotations
import subprocess, sys, json, os, textwrap, shutil, tempfile, pathlib

CLI = [sys.executable, '-m', 'myfastapi_cli.cli']

def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, f"Command failed: {cmd}\nSTDOUT: {r.stdout}\nSTDERR: {r.stderr}"
    return r.stdout

def test_generate_async_crud(tmp_path: pathlib.Path):
    # create new layered project
    run(CLI + ['new', 'demo_async'], cwd=tmp_path)
    proj = tmp_path / 'demo_async'
    # generate async crud
    run(CLI + ['generate-crud', 'Widget', '--async'], cwd=proj)
    # verify handler async
    create_handler_file = proj / 'app' / 'application' / 'widgets' / 'commands' / 'create_widget.py'
    text = create_handler_file.read_text(encoding='utf-8')
    assert 'async def handle' in text, text
    service_file = proj / 'app' / 'application' / 'widgets' / 'services' / 'widget_service.py'
    stext = service_file.read_text(encoding='utf-8')
    assert 'async def create' in stext
    router_file = proj / 'app' / 'presentation' / 'api' / 'routers' / 'widget.py'
    rtext = router_file.read_text(encoding='utf-8')
    assert 'async def create_widget' in rtext
    assert 'await _m.send_async' in rtext
    assert 'await _m.ask_async' in rtext
