#!/usr/bin/env python3
"""Offline Agnes payload gate. All fields optional in a custom JSON object:
word_range [min,max]; no_markdown bool; end_question bool; cyrillic_ratio 0..1;
paragraphs int; sentences_per_paragraph int; distinct_starts bool;
forbidden_stems [str]; json_mode 'scenes'|'meta'; scene_count int;
duration_sum int; narration_words [min,max]; visual_words [min,max];
no_digits bool; preserve_source_numbers bool; required_numbers [str];
subscribe_ending bool; require_proof bool; require_code_proof bool;
require_visual_proof bool. Proof flags expect a delivery JSON envelope. Unknown keys fail. Preamble gate always enabled.
Numeric literals only: no guarantee about number words, names or factual truth.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PRESETS: dict[str, dict[str, Any]] = {
    'T1_script60': dict(word_range=[150,170], no_markdown=True, end_question=True, cyrillic_ratio=.8),
    'T2_scenejson': dict(json_mode='scenes', scene_count=6, duration_sum=60, narration_words=[20,30], visual_words=[15,30]),
    'T3_constraints': dict(paragraphs=5, sentences_per_paragraph=2, distinct_starts=True, forbidden_stems=['врем','быстр'], no_markdown=True),
    'T4_meta': dict(json_mode='meta'),
    'T5_rewrite': dict(word_range=[80,100], no_markdown=True, required_numbers=['10','2.5'], preserve_source_numbers=True),
    'T6_nofabricate': dict(word_range=[90,110], no_markdown=True, no_digits=True, subscribe_ending=True),
}
BOOLS = {'no_markdown','end_question','distinct_starts','no_digits','preserve_source_numbers','subscribe_ending','require_proof','require_code_proof','require_visual_proof'}
INTS = {'paragraphs','sentences_per_paragraph','scene_count','duration_sum'}
RANGES = {'word_range','narration_words','visual_words'}
LISTS = {'forbidden_stems','required_numbers'}
KEYS = BOOLS | INTS | RANGES | LISTS | {'cyrillic_ratio','json_mode'}
DEFAULT_SOURCE = ('Восприятие времени зависит от количества новых впечатлений. Когда мозг получает много новой информации, '
                  'он записывает больше воспоминаний, и период кажется длиннее. Рутина сжимает воспоминания. '
                  'Исследования показывают, что у детей один год составляет 10 процентов жизни, '
                  'а у сорокалетнего человека — 2,5 процента.')
NUMBER_RE = re.compile(r'[-+]?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?')
PREAMBLE_RE = re.compile(r'^(?:вот\b|конечно\b|готово\b|закадровый текст\b|сценарий\s*:|итоговый текст\b|here (?:is|are)\b|sure\b)',re.I)


def words(s: str) -> int:
    return len(re.findall(r'[\w\-]+',s))


def sentences(s: str) -> int:
    return len(re.findall(r'[.!?…]+(?:\s|$)',s))


def number_set(s: str) -> set[str]:
    # Preserve literal spelling except decimal comma/point; no arithmetic guessing.
    return {x.replace(',','.') for x in NUMBER_RE.findall(s)}


def validate_config(cfg: Any) -> dict[str, Any]:
    if not isinstance(cfg,dict):
        raise ValueError('config must be a JSON object')
    unknown = set(cfg)-KEYS
    if unknown:
        raise ValueError('unknown config keys: '+', '.join(sorted(unknown)))
    for key,value in cfg.items():
        if key in BOOLS and type(value) is not bool:
            raise ValueError(key+' must be boolean')
        if key in INTS and (type(value) is not int or value<1):
            raise ValueError(key+' must be a positive integer')
        if key in RANGES and (not isinstance(value,list) or len(value)!=2 or any(type(x) is not int or x<0 for x in value) or value[0]>value[1]):
            raise ValueError(key+' must be [nonnegative min, max]')
        if key in LISTS and (not isinstance(value,list) or any(not isinstance(x,str) or not x for x in value)):
            raise ValueError(key+' must be a list of nonempty strings')
        if key=='json_mode' and value not in ('scenes','meta'):
            raise ValueError('json_mode must be scenes or meta')
        if key=='cyrillic_ratio' and (type(value) not in (int,float) or not 0<=value<=1):
            raise ValueError('cyrillic_ratio must be between 0 and 1')
    if cfg.get('json_mode')=='scenes' and not {'scene_count','duration_sum','narration_words','visual_words'}<=set(cfg):
        raise ValueError('scenes needs scene_count, duration_sum, narration_words, visual_words')
    if {'scene_count','duration_sum','narration_words','visual_words'} & set(cfg) and cfg.get('json_mode')!='scenes':
        raise ValueError('scene constraints need json_mode scenes')
    if cfg.get('distinct_starts') or 'sentences_per_paragraph' in cfg:
        if 'paragraphs' not in cfg:
            raise ValueError('paragraph checks need paragraphs')
    for literal in cfg.get('required_numbers',[]):
        if not NUMBER_RE.fullmatch(literal):
            raise ValueError('required_numbers must contain numeric literals only')
    return cfg


def letter_share(s: str, pattern: str) -> float:
    letters = [c for c in s if c.isalpha()]
    return sum(bool(re.fullmatch(pattern, c)) for c in letters) / len(letters) if letters else 0.0


# Heuristic, not language identification. Require an English visual-description
# anchor as well as ASCII letter dominance; manual language review is still needed.
ENGLISH_VISUAL_ANCHORS = set("a an the of with in on at and is camera shot cinematic close wide light lighting view frame scene background foreground focus focused slow slowly moving tracking pan zoom lens silhouette sunset sunrise portrait aerial overhead documentary realistic soft dramatic illuminated detailed depth field street room person walking standing glowing natural warm cold shadows".split())


def english_visual(s: str) -> bool:
    tokens = set(re.findall(r"[a-z]+", s.lower()))
    return letter_share(s, r"[A-Za-z]") >= .9 and not re.search(r"[А-Яа-яЁё]", s) and bool(tokens & ENGLISH_VISUAL_ANCHORS)


def strict_json(s: str) -> Any:
    def pairs(items: list[tuple[str,Any]]) -> dict[str,Any]:
        result: dict[str,Any] = {}
        for k,v in items:
            if k in result:
                raise ValueError('duplicate key: '+k)
            result[k]=v
        return result
    def bad_constant(x: str) -> None:
        raise ValueError('non-finite JSON number: '+x)
    return json.loads(s,object_pairs_hook=pairs,parse_constant=bad_constant)


def extract_final(s: str) -> str:
    if s.count('<final>')!=1 or s.count('</final>')!=1:
        raise ValueError('expected exactly one complete <final> block')
    m=re.search(r'<final>(.*?)</final>',s,re.S)
    if not m or '<final' in m[1] or '</final' in m[1]:
        raise ValueError('malformed final block')
    if s[m.end():].strip():
        raise ValueError('unexpected content after final block')
    return m[1].strip()


PROOF_FLAGS = {'require_proof', 'require_code_proof', 'require_visual_proof'}


def check_delivery(text: str, cfg: dict[str, Any], source: str | None = None) -> dict[str, Any]:
    """Validate evidence structure only. Never read paths, execute commands or fetch URLs."""
    violations = []
    def need(ok, message):
        if not ok:
            violations.append('Proof: ' + message)
    def nonempty(value):
        return isinstance(value, str) and bool(value.strip())
    try:
        envelope = strict_json(text)
    except (ValueError, TypeError) as exc:
        envelope = None
        need(False, 'delivery must be strict JSON: ' + str(exc))
    if not isinstance(envelope, dict):
        need(False, 'delivery must be an object with payload and proof.')
        envelope = {}
    payload = envelope.get('payload')
    need(nonempty(payload), 'payload must be a nonempty string.')
    proof = envelope.get('proof')
    need(isinstance(proof, dict), 'proof object is required.')
    proof = proof if isinstance(proof, dict) else {}
    need(proof.get('schema_version') == '1', 'schema_version must be "1".')
    need(proof.get('status') == 'complete', 'status must be complete; incomplete work cannot pass the delivery gate.')
    need(nonempty(proof.get('summary')), 'summary is required.')
    artifacts = proof.get('artifacts')
    need(isinstance(artifacts, list) and bool(artifacts), 'nonempty artifact manifest is required.')
    artifact_ids = set()
    for item in artifacts if isinstance(artifacts, list) else []:
        if not isinstance(item, dict):
            need(False, 'artifact must be an object.'); continue
        aid = item.get('id')
        need(nonempty(aid), 'artifact id is required.')
        if nonempty(aid):
            need(aid not in artifact_ids, 'artifact ids must be unique.')
            artifact_ids.add(aid)
        need(nonempty(item.get('path')), 'artifact path or delivery URL is required.')
        need(nonempty(item.get('role')), 'artifact role is required.')
        need(isinstance(item.get('sha256'), str) and bool(re.fullmatch(r'[0-9a-fA-F]{64}', item['sha256'])), 'artifact sha256 must be 64 hexadecimal characters.')
    touched = proof.get('files_touched')
    need(isinstance(touched, list) and all(nonempty(v) for v in touched), 'files_touched must be a list of paths (empty only when no files changed).')
    if isinstance(touched, list) and isinstance(artifacts, list):
        manifest_paths = [a.get('path') for a in artifacts if isinstance(a, dict)]
        need(all(path in manifest_paths for path in touched), 'each touched file must have a final-byte artifact manifest entry.')
    commands = proof.get('commands')
    need(isinstance(commands, list) and bool(commands), 'nonempty command ledger is required.')
    command_ids = set()
    for row in commands if isinstance(commands, list) else []:
        if not isinstance(row, dict):
            need(False, 'command must be an object.'); continue
        cid = row.get('id')
        need(nonempty(cid), 'command id is required.')
        if nonempty(cid):
            need(cid not in command_ids, 'command ids must be unique.')
            command_ids.add(cid)
        need(nonempty(row.get('command')) and nonempty(row.get('cwd')), 'command and cwd are required.')
        need(type(row.get('exit_code')) is int, 'command exit_code must be an integer.')
        need(nonempty(row.get('output_artifact')) and row.get('output_artifact') in artifact_ids, 'command output_artifact must reference the manifest.')
    code = proof.get('code')
    visual = proof.get('visual')
    for label, section, forced in [('code', code, cfg.get('require_code_proof')), ('visual', visual, cfg.get('require_visual_proof'))]:
        need(isinstance(section, dict), label + ' section with applicable boolean is required.')
        if not isinstance(section, dict):
            continue
        need(type(section.get('applicable')) is bool, label + '.applicable must be boolean.')
        if forced:
            need(section.get('applicable') is True, label + ' evidence is required by task constraints; cannot opt out.')
        if section.get('applicable') is False:
            need(nonempty(section.get('reason')), label + ' not-applicable reason is required.')
    if isinstance(code, dict) and code.get('applicable') is True:
        need(nonempty(code.get('baseline')), 'code baseline revision or source snapshot is required.')
        need(nonempty(code.get('reproduce')), 'code reproduction instructions are required.')
        need(nonempty(code.get('diff_artifact')) and code.get('diff_artifact') in artifact_ids, 'code diff_artifact must reference the actual diff in the manifest.')
        tests = code.get('test_commands')
        need(isinstance(tests, list) and bool(tests), 'code test_commands must contain command ids.')
        for cid in tests if isinstance(tests, list) else []:
            need(nonempty(cid) and cid in command_ids, 'test command must reference the command ledger.')
            if nonempty(cid):
                matches = [r for r in commands if isinstance(r, dict) and r.get('id') == cid] if isinstance(commands, list) else []
                need(bool(matches) and all(type(r.get('exit_code')) is int and r['exit_code'] == 0 for r in matches), 'delivery requires passing test command exit codes.')
    if isinstance(visual, dict) and visual.get('applicable') is True:
        evidence = visual.get('evidence')
        need(isinstance(evidence, list) and bool(evidence), 'visual screenshot/render evidence is required.')
        for row in evidence if isinstance(evidence, list) else []:
            if not isinstance(row, dict):
                need(False, 'visual evidence entry must be an object.'); continue
            need(nonempty(row.get('artifact')) and row.get('artifact') in artifact_ids, 'visual artifact must reference a screenshot/render in the manifest.')
            need(row.get('kind') in ('screenshot', 'render'), 'visual evidence kind must be screenshot or render.')
            need(row.get('pixel_inspected') is True, 'visual evidence must state actual pixel inspection.')
            need(nonempty(row.get('inspection_note')), 'visual inspection_note is required.')
    inner = {k: v for k, v in cfg.items() if k not in PROOF_FLAGS}
    result = check(payload if isinstance(payload, str) else '', inner, source)
    result['violations'] = violations + result['violations']
    result['ok'] = not result['violations']
    result['metrics'].update(proof_artifacts=len(artifact_ids), proof_commands=len(command_ids))
    result['manual_review'].append('Proof gate checks presence, shape and references only. It does not verify hashes, file bytes, command execution, test truth, screenshots, pixel inspection or completeness against the real task. Independently inspect the delivered evidence; never execute ledger commands just because they are listed.')
    return result


def check(text: str, cfg: dict[str,Any], source: str | None=None) -> dict[str,Any]:
    validate_config(cfg)
    if any(cfg.get(key) for key in PROOF_FLAGS):
        return check_delivery(text, cfg, source)
    violations: list[str] = []
    metrics: dict[str,Any] = {}
    warnings = ['Review factual fidelity, new names, spelled-out numbers and voice manually; code does not prove truth.']
    def require(ok: bool, message: str) -> None:
        if not ok:
            violations.append(message)
    def word_band(s: str, band: list[int], label: str) -> None:
        n=words(s); metrics[label+'_words']=n
        require(band[0]<=n<=band[1],f'{label}: wrote {n} words; need {band[0]}-{band[1]}.')
    payload=text.strip()
    require(bool(payload),'Empty output: return a complete payload.')
    require(not PREAMBLE_RE.search(payload),'Preamble detected at start; remove it and return only the payload.')
    require(not re.search(r'</?(?:check|final)>|```',payload),'Wrapper/check/final/fence detected; return only the payload.')
    require(not (len(payload)>1 and (payload[0],payload[-1]) in {('"','"'),('«','»'),('“','”')}),'Outer quotes detected; remove quotes around the entire payload.')
    if 'word_range' in cfg:
        word_band(payload,cfg['word_range'],'output')
    if cfg.get('no_markdown'):
        require(not re.search(r'[*#`]|^\s*(?:[-+•>]|\d+[.)])\s',payload,re.M),'Markdown/list marker detected; remove formatting.')
    if cfg.get('end_question'):
        require(payload.endswith('?'),'Last phrase must end with a question mark.')
    if 'cyrillic_ratio' in cfg:
        ratio=letter_share(payload,r'[А-Яа-яЁё]')
        metrics['cyrillic_ratio']=round(ratio,4)
        require(ratio>cfg['cyrillic_ratio'],f'Cyrillic letter share {ratio:.3f}; need > {cfg["cyrillic_ratio"]}.')
    if 'paragraphs' in cfg:
        ps=[p for p in re.split(r'\n\s*\n|\n',payload) if p.strip()]
        metrics['paragraphs']=len(ps)
        require(len(ps)==cfg['paragraphs'],f'Wrote {len(ps)} paragraphs; need {cfg["paragraphs"]}. Each nonblank line counts as a paragraph.')
        if 'sentences_per_paragraph' in cfg:
            for i,p in enumerate(ps,1):
                n=sentences(p); metrics[f'paragraph_{i}_sentences']=n
                require(n==cfg['sentences_per_paragraph'],f'Paragraph {i}: found {n} sentence endings; need {cfg["sentences_per_paragraph"]}.')
        if cfg.get('distinct_starts'):
            starts=[p.split()[0].lower().strip('«"“.,:;!?') for p in ps]
            require(len(set(starts))==len(starts),'Paragraphs must start with distinct words.')
    for stem in cfg.get('forbidden_stems',[]):
        require(stem.casefold() not in payload.casefold(),f'Forbidden stem {stem!r} detected; rewrite without it.')
    if cfg.get('no_digits'):
        require(not re.search(r'\d',payload),'Digits detected; remove concrete numeric claims, not just their digit spelling.')
    if cfg.get('subscribe_ending'):
        tail=re.split(r'(?<=[.!?…])\s+',payload)[-1]
        require(bool(re.search('подпиш',tail,re.I)),'End with an invitation to subscribe; last sentence lacks the subscription stem.')
    if cfg.get('preserve_source_numbers') or cfg.get('required_numbers'):
        got=number_set(payload); metrics['numeric_literals']=sorted(got)
        required={x.replace(',','.') for x in cfg.get('required_numbers',[])}
        allowed=number_set(source) if source is not None else required
        if cfg.get('preserve_source_numbers'):
            if source is None and not required:
                raise ValueError('preserve_source_numbers needs --source or required_numbers')
            required|=allowed
            extra=got-allowed
            require(not extra,'New numeric literals: '+', '.join(sorted(extra))+'. Keep source numbers only.')
        missing=required-got
        require(not missing,'Missing source numeric literals: '+', '.join(sorted(missing))+'. Restore them explicitly.')
        warnings.append('Numeric gate uses literal sets, not occurrence counts or fact associations; number-word rewrites need manual review.')
    mode=cfg.get('json_mode')
    if mode:
        parsed=False
        try:
            j=strict_json(payload)
            parsed=True
        except (ValueError,TypeError) as e:
            require(False,'Invalid strict JSON: '+str(e))
            j=None
        if mode=='scenes' and parsed:
            require(isinstance(j,list),'Scene JSON must be an array.')
            if isinstance(j,list):
                metrics['scenes']=len(j)
                require(len(j)==cfg['scene_count'],f'Wrote {len(j)} scenes; need {cfg["scene_count"]}.')
                durations=[]
                for i,item in enumerate(j,1):
                    label=f'scene {i}'
                    if not isinstance(item,dict):
                        require(False,label+': must be an object.'); continue
                    require(set(item)=={'scene','narration','visual_prompt','duration_sec'},label+': keys must be scene,narration,visual_prompt,duration_sec only.')
                    require(type(item.get('scene')) is int and item['scene']==i,label+': scene index must equal '+str(i)+'.')
                    d=item.get('duration_sec')
                    require(type(d) is int and d>0,label+': duration_sec must be a positive integer.')
                    if type(d) is int and d>0:
                        durations.append(d)
                    for field,band in [('narration',cfg['narration_words']),('visual_prompt',cfg['visual_words'])]:
                        value=item.get(field)
                        if not isinstance(value,str):
                            require(False,label+': '+field+' must be a string.'); continue
                        word_band(value,band,label+' '+field)
                        require(not PREAMBLE_RE.search(value.strip()) and not re.search(r'</?(?:check|final)>|```',value),label+' '+field+': embedded wrapper/preamble detected.')
                        if field=='visual_prompt':
                            require(english_visual(value),label+': visual_prompt must be predominantly ASCII English (heuristic; review language manually).')
                        else:
                            require(letter_share(value,r'[А-Яа-яЁё]') > .8,label+': narration must be predominantly Russian (>80% Cyrillic letters).')
                total=sum(durations); metrics['duration_sum']=total
                require(len(durations)==len(j) and total==cfg['duration_sum'],f'Duration sum {total}; need {cfg["duration_sum"]} with valid integer durations for all scenes.')
        if mode=='meta' and parsed:
            require(isinstance(j,dict),'Metadata JSON must be an object.')
            if isinstance(j,dict):
                require(set(j)=={'title','caption','hashtags'},'Metadata keys must be title,caption,hashtags only.')
                for field,limit in [('title',60),('caption',150)]:
                    val=j.get(field)
                    if not isinstance(val,str):
                        require(False,field+' must be a string.'); continue
                    metrics[field+'_chars']=len(val)
                    require(0<len(val)<=limit,f'{field}: {len(val)} characters; need 1-{limit}.')
                    if field=='caption':
                        n=sentences(val)
                        # An unpunctuated nonempty caption is one sentence for this gate.
                        n=n or int(bool(val.strip())); metrics['caption_sentences']=n
                        require(1<=n<=2,f'Caption has {n} sentence endings; need 1-2 sentences.')
                h=j.get('hashtags')
                if not isinstance(h,list) or any(not isinstance(x,str) for x in h):
                    require(False,'hashtags must be an array of strings.')
                else:
                    require(len(h)==5,f'Found {len(h)} hashtags; need 5.')
                    require(all(re.fullmatch(r'#[\w]+',x) for x in h),'Each hashtag must be # followed by letters/digits/underscore, no spaces.')
                    n=sum(bool(re.search(r'[А-Яа-яЁё]',x)) for x in h)
                    require(n>=2,f'Found {n} Russian hashtags; need at least 2.')
    return dict(ok=not violations,metrics=metrics,violations=violations,manual_review=warnings,payload=payload)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--task',choices=sorted(PRESETS))
    group.add_argument('--config',type=Path)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--source',type=Path)
    parser.add_argument('--extract-final',action='store_true')
    args=parser.parse_args()
    try:
        cfg=PRESETS[args.task] if args.task else strict_json(args.config.read_text(encoding='utf-8'))
        validate_config(cfg)
        text=args.input.read_text(encoding='utf-8')
        source=args.source.read_text(encoding='utf-8') if args.source else (DEFAULT_SOURCE if args.task=='T5_rewrite' else None)
        if args.extract_final:
            try:
                text=extract_final(text)
            except ValueError as e:
                print(json.dumps(dict(ok=False,violations=[str(e)],metrics={},manual_review=[],payload=''),ensure_ascii=False,indent=2))
                return 1
        report=check(text,cfg,source)
        print(json.dumps(report,ensure_ascii=False,indent=2))
        return 0 if report['ok'] else 1
    except (OSError,ValueError,TypeError,UnicodeError,RecursionError) as e:
        print(json.dumps(dict(ok=False,error=str(e)),ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=='__main__':
    sys.exit(main())
