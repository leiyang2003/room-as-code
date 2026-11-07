"""Explicit live host acceptance. Uses installed skill copies and private local logs.

Run separately from unit tests; invokes the user's configured Codex or Claude Code.
No model API key, custom web chat, bypass-permission flag, or scene keyword parser.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'skills/room-studio/scripts'))
from install_skill import install
from core import content, load, save


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--host', choices=['codex','claude'], required=True)
    ap.add_argument('--output', type=Path, required=True)
    args=ap.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='room-studio-host-edit-') as directory:
        project=Path(directory)
        skill=install(args.host, project)
        fixture=ROOT/'examples/quiet-house.scene.json'
        scene=load(fixture if fixture.exists() else ROOT/'examples/kit-grid.scene.json')
        scene['entities']['living.sofa']['overrides']['fabric']='#778899'
        scene['entities']['dining.table']['overrides']['wood']='#223344'
        save(project/'house.scene.json',scene)
        prompt=(('$room-studio' if args.host=='codex' else '/room-studio')+
            '\n使用已安装的room-studio skill，实际修改当前项目的house.scene.json。'
            '先读取磁盘状态。把客厅沙发沿世界+X方向移动30厘米，绕Z轴增加15度；'
            '把客厅墙上挂画垂直上移15厘米，并只将该画框颜色改为#334455。'
            '保持挂画贴墙的两个水平坐标、朝向和画面内容；沙发已有布料颜色覆盖保留。'
            '餐桌、岛台及其余所有对象都不动，材质也保留。'
            '生成可审阅原子patch，执行并核对实际保存状态；不启动预览、不渲染、不导出。'
            '本次验收只检查已保存编辑，浏览器视觉验收由独立流程负责。'
            '请报告变更对象和字段、修订号、哪些验证实际执行。')
        if args.host=='codex':
            command=['codex','exec','--sandbox','workspace-write','--skip-git-repo-check',
                     '--ephemeral','--json',prompt]
        else:
            command=['claude','--print','--output-format','json','--permission-mode','default',
                     '--allowedTools','Read','Write','Edit','Bash(python3 *)','--',prompt]
        started=time.perf_counter()
        completed=subprocess.run(command,cwd=project,capture_output=True,text=True,timeout=900)
        elapsed=time.perf_counter()-started
        # Logs can contain personal environment paths; never bundle them for release.
        args.output.with_suffix('.local.log').write_text(completed.stdout+'\nSTDERR\n'+completed.stderr)
        if completed.returncode:
            raise RuntimeError(f'{args.host} failed; inspect private local log')
        after=load(project/'house.scene.json')
        expected=copy.deepcopy(scene)
        sofa=expected['entities']['living.sofa']
        sofa['position'][0]+=.3;sofa['rotation']+=15
        picture=expected['entities']['living.picture']
        picture['position'][2]+=.15;picture['overrides']['frame']='#334455'
        if content(after)!=content(expected):
            raise AssertionError('Actual saved scene differs from independently computed expected result')
        changed=[eid for eid in scene['entities'] if scene['entities'][eid]!=after['entities'][eid]]
        assert set(changed)=={'living.sofa','living.picture'}
        assert after['revision']>scene['revision']
        assert not list(project.rglob('*.blend'))+list(project.rglob('*.png'))
        # Fresh processes prove history and state survive a host/session restart.
        cli=[sys.executable,str(skill/'scripts/room.py')]
        start=time.perf_counter()
        subprocess.run(cli+['undo',str(project/'house.scene.json')],capture_output=True,check=True)
        assert content(load(project/'house.scene.json'))==content(scene)
        subprocess.run(cli+['redo',str(project/'house.scene.json')],capture_output=True,check=True)
        assert content(load(project/'house.scene.json'))==content(after)
        script_seconds=time.perf_counter()-start
        result={'status':'PASS','host':args.host,'task':'Move furniture, rotate it, move fixed wall art and recolor its frame',
                'skill_discovery':'project '+('.agents' if args.host=='codex' else '.claude')+'/skills/room-studio',
                'revision_before':scene['revision'],'revision_after_host':after['revision'],
                'changed_entities':changed,'other_entities_unchanged':len(scene['entities'])-len(changed),
                'checks':['actual scene content matches independent expected content',
                          'sofa +X 0.30 m and +Z rotation 15 degrees; fabric override preserved',
                          'wall art +Z 0.15 m; attachment XY and picture content preserved; frame recolored',
                          'all unrelated entities and material overrides unchanged',
                          'undo and redo in fresh processes restore exact scene content',
                          'no native export or render during editing'],
                'host_wall_seconds':round(elapsed,3),'two_restart_cli_seconds':round(script_seconds,3),
                'timing_note':'Host wall time includes model, tool and service waiting; restart CLI timing measures two local script processes only.',
                'scope':'One live text-edit task per host; does not establish arbitrary-language, photo reconstruction or browser visual quality.'}
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
