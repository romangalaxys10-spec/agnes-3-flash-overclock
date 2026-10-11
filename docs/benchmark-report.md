# Agnes 3.0 Flash benchmark pack - Время script pipeline
Date: 2026-10-10. Run: 35/36 calls via Muse Bench /api/chat.
STATUS: EXPERIMENTAL. Nothing here is installed in any production pipeline. v1 prompt only.

## Results (auto constraint checks, checks passed / total)
- B plain prompt: 47/56 (84%), 5/11 samples fully perfect
- A adapted prompt alone (pre.txt): 36/51 (71%), 3/11 perfect - WORSE than plain
- AR adapted + editor revise pass (pre.txt then rev.txt): 43/49 (88%), 6/10 perfect - best, better voice kept
- Self-written reference (not a verified Opus 5 run): passes T1, T3, T4, T5; misses T2 narration lengths, T6 word count

Caveats: directional only. n=2 per cell, different denominators (empty/incomplete outputs excluded), one self-written reference. No blind quality judge. Do not claim parity with any Opus model; Opus 5 was never measured.


## Reproducibility and sample accounting

The published aggregate scores cannot be regenerated from repository contents.
Raw outputs (`raw.json`), full reference answers (`ref.py`), the executable original
scorer, and the call ledger are absent. The historical scorer excerpt below is
not a standalone scorer. Do not manufacture missing evidence or recalculate the
published scores using the newer checker.

36 samples were planned (6 tasks x 2 samples x 3 conditions). The report says
35/36 calls completed, but only 32 samples appear in the score denominators:
B = 11, A = 11, AR = 10. Thus the aggregates exclude 4 planned samples:
1 B, 1 A and 2 AR. The evidence ledger mentions an empty AR answer and an
incomplete AR call, but their task/sample IDs and their relation to the one
unfinished call cannot be recovered. The identities and precise reasons for
the B and A exclusions are also unrecoverable. These statements reconcile the
counts only; they do not establish a complete per-call exclusion ledger.

## English task and prompt gloss (not benchmark inputs)

- T1: Russian voiceover about why time seems faster with age, 150-170 words,
  strong opening hook, no lists/Markdown, ending with a viewer question.
- T2: Exactly six JSON scenes with Russian narration (20-30 words), English
  visual descriptions (15-30 words), integer durations totaling 60 seconds.
- T3: Five paragraphs of two sentences comparing a child and an older person's
  experience of an hour, distinct opening words, no forms of the Russian words
  for "time" or "fast", no Markdown/headings.
- T4: JSON metadata for "The Night That Never Was": title <=60 characters,
  caption 1-2 sentences <=150 characters, five hashtags including two Russian.
- T5: Conversational TikTok rewrite of the supplied passage, 80-100 words,
  preserve all facts and numbers (10 percent and 2.5 percent), add none.
- T6: Voiceover on perceived event duration, 90-110 words, no unsupported
  concrete numbers, scientist names or study titles, finish with a subscribe invitation.
- Generation prompt: Russian short-video writer, rhythmic conversational phrases
  addressed to "you", concrete images, no cliches or invented facts. List task
  constraints and a brief plan in `<check>`, deliver only the result in `<final>`,
  nothing after it. Includes hook and JSON examples, then the task label.
- Editor prompt: check every task constraint, explicitly count quantities and
  fix violations. Summarize violations in `<check>` and return only the final
  result in `<final>`.

## Where Agnes loses (measured)
- Hard count constraints (word counts, paragraph/sentence counts). T1 hit 150-170 words in only 2/6 runs.
- Adds numbers the source did not have (T5: 4/6 runs).
- Plain mode sometimes prepends a preamble line ("Вот закадровый текст:") + quotes - pollutes TTS.
- T4 (JSON metadata) clean in every condition (6/6).

## Historical recommendation (v2 was not tested)
Simple style prompt + CODE doing the counting (words, JSON validity, digits, preamble) and re-prompting with the exact violation. Drop plan-then-final for production. Generate-then-revise (AR) is the only prompt-level change that helped.

## tasks.json (6 eval tasks, Russian)
```json
[
{"id":"T1_script60","task":"Напиши закадровый текст для 60-секундного вертикального видео на русском языке на тему: «Почему время летит всё быстрее с возрастом». Объём 150-170 слов. Первая фраза — сильный крючок. Без списков и markdown. Последняя фраза — вопрос зрителю.","check":"words:150-170;nomd;endq;cyr"},
{"id":"T2_scenejson","task":"Разбей видео «Почему время летит всё быстрее с возрастом» на ровно 6 сцен. Верни ТОЛЬКО валидный JSON-массив из 6 объектов с полями: scene (число 1-6), narration (русский текст, 20-30 слов), visual_prompt (английский, 15-30 слов, кинематографичное описание кадра), duration_sec (целое число). Сумма duration_sec должна быть ровно 60. Без пояснений и без markdown-ограждений.","check":"json6;sum60"},
{"id":"T3_constraints","task":"Напиши ровно 5 абзацев по 2 предложения о том, как ребёнок и пожилой человек по-разному ощущают один и тот же час. Каждый абзац должен начинаться с другого слова. В тексте не должно быть слов «время» и «быстро» (в любых формах). Без markdown и заголовков.","check":"paras5;sent2;noforbid"},
{"id":"T4_meta","task":"Для видео «Ночь, которой не было» дай: 1) title — не длиннее 60 символов; 2) caption — 1-2 предложения, не длиннее 150 символов; 3) hashtags — ровно 5 хэштегов, из них минимум 2 на русском. Верни ТОЛЬКО валидный JSON-объект с ключами title, caption, hashtags (массив строк).","check":"jsonmeta"},
{"id":"T5_rewrite","task":"Перепиши этот сухой текст в живой разговорный закадровый голос для TikTok (80-100 слов), сохранив ВСЕ факты и числа и не добавляя новых фактов и чисел: «Восприятие времени зависит от количества новых впечатлений. Когда мозг получает много новой информации, он записывает больше воспоминаний, и период кажется длиннее. Рутина сжимает воспоминания. Исследования показывают, что у детей один год составляет 10 процентов жизни, а у сорокалетнего человека — 2,5 процента.» Без markdown.","check":"words:80-100;nomd;keepnums:10,2,5"},
{"id":"T6_nofabricate","task":"Напиши 90-110 слов закадрового текста о том, как мозг оценивает длительность событий. Правило: не приводи никаких конкретных цифр, имён учёных и названий исследований, если ты не уверен на 100%; вместо этого говори общими словами. Без markdown. Закончи фразой-приглашением подписаться.","check":"words:90-110;nomd;nodigits"}
]
```

## pre.txt (adapted prompt v1 - generation pass)
````text
Ты — сценарист коротких вертикальных видео на русском языке («Время» — философско-научная серия для TikTok/YouTube Shorts). Правила стиля: короткие ритмичные фразы; живой разговорный голос, на «ты»; конкретные образы вместо абстракций; никаких клише («в современном мире», «давайте разберёмся»); ни одного выдуманного факта, цифры или цитаты; строго соблюдай ВСЕ числовые и структурные ограничения задачи (объём, количество, формат). Если формат — JSON, выдай только JSON.

Порядок работы: сначала в блоке <check> кратко перечисли ограничения задачи списком и план (3-6 строк). Затем в блоке <final> выдай готовый результат — только то, что должно попасть в видео или файл, без пояснений. После <final> ничего не пиши.

Пример хорошего крючка: «Тебе было десять, и лето тянулось вечность. Куда оно делось?»
Пример структуры JSON-ответа: сразу открывающая скобка, без ```.

ЗАДАЧА:
````

## rev.txt (editor revise pass - the piece that actually helped)
```
Ты редактор-проверяющий. Ниже ЗАДАЧА и ЧЕРНОВИК. Проверь черновик по каждому ограничению задачи (посчитай слова/абзацы/предложения/символы/сумму явно, запрещённые слова, формат). Если есть нарушение — исправь. В блоке <check> кратко перечисли найденные нарушения (или «нет»). В блоке <final> выдай итоговую версию (исправленную или без изменений) — только результат, без пояснений.
```

## Suggested v2 (untested)
Drop <check>/<final> blocks, keep the style rules, add "no preamble, no quotes", code does counting + retry with exact violation ("you wrote 138 words, need 150-170, extend only the middle").

## Historical score.py excerpt (not standalone: raw.json and ref.py are not included)
```python
import json,re,sys
exec(open('ref.py').read())
d=json.load(open('raw.json'))['content']
c=d if isinstance(d,str) else d[0]['text']
try: R=json.loads(json.loads(c)['result'] if c.strip().startswith('{"result"') else c)
except Exception: 
    j=json.loads(c); R=json.loads(j['result']) if isinstance(j,dict) and 'result' in j else j
if isinstance(R,str): R=json.loads(R)
T={t['id']:t for t in json.load(open('tasks.json'))}
def words(s): return len(re.findall(r'[\w\-]+',s))
def strip(s):
    s=s.strip(); s=re.sub(r'^```\w*\n|\n```$','',s); return s
def chk(id,o):
    if not o: return {'empty':0}
    r={}
    if id=='T1_script60':
        w=words(o); r['words150-170']=150<=w<=170; r['nomd']=not re.search(r'[*#`]|^\s*[-•]',o,re.M); r['endq']=o.strip().endswith('?'); r['cyr']=len(re.findall('[А-Яа-яЁё]',o))>0.8*len(re.findall(r'[A-Za-zА-Яа-яЁё]',o))
    if id=='T2_scenejson':
        try:
            j=json.loads(strip(o)); r['json']=True; r['six']=len(j)==6; r['sum60']=sum(x.get('duration_sec',0) for x in j)==60
            r['narr20-30']=all(20<=words(x.get('narration',''))<=30 for x in j); r['vp15-30']=all(15<=words(x.get('visual_prompt',''))<=30 for x in j)
            r['vp_en']=all(not re.search('[А-Яа-я]',x.get('visual_prompt','')) for x in j)
        except Exception: r['json']=False
    if id=='T3_constraints':
        ps=[p for p in re.split(r'\n\s*\n|\n',o.strip()) if p.strip()]; r['paras5']=len(ps)==5
        r['sent2']=all(len(re.findall(r'[.!?…]+(?:\s|$)',p))==2 for p in ps)
        r['distinct_start']=len({p.split()[0].lower().strip('«"') for p in ps})==len(ps)
        r['noforbid']=not re.search(r'врем|быстр',o,re.I); r['nomd']=not re.search(r'[*#`]',o)
    if id=='T4_meta':
        try:
            j=json.loads(strip(o)); r['json']=True; r['title<=60']=len(j['title'])<=60; r['cap<=150']=len(j['caption'])<=150
            h=j['hashtags']; r['5tags']=len(h)==5; r['2ru']=sum(bool(re.search('[А-Яа-я]',x)) for x in h)>=2
        except Exception: r['json']=False
    if id=='T5_rewrite':
        w=words(o); r['words80-100']=80<=w<=100; r['nomd']=not re.search(r'[*#`]',o)
        r['nums']=bool(re.search(r'10|десят',o)) and bool(re.search(r'2[,.]5|два с половиной',o)) 
        r['no_new_nums']=not re.search(r'\b(?!10\b|2[,.]5\b)\d+',o)
    if id=='T6_nofabricate':
        w=words(o); r['words90-110']=90<=w<=110; r['nomd']=not re.search(r'[*#`]',o); r['nodigits']=not re.search(r'\d',o); r['subscribe']=bool(re.search('подпиш',o,re.I))
    return r
agg={}
for x in R:
    o=x['out']; o=o.strip() if o else o
    r=chk(x['id'],o); sc=sum(bool(v) for v in r.values()); n=len(r)
    agg.setdefault(x['cond'],[0,0,0]); agg[x['cond']][0]+=sc; agg[x['cond']][1]+=n; agg[x['cond']][2]+=sc==n
    print(x['id'],x['s'],x['cond'],f'{sc}/{n}',[k for k,v in r.items() if not v])
print({k:(f'{v[0]}/{v[1]} checks, {v[2]} perfect') for k,v in agg.items()})
print('REF'); 
for k,v in REF.items(): print(k,chk(k,v))
```

## Reference outputs (ref.py) - used as the comparison baseline
T1 script (151 words), T2 scene JSON, T3 5x2 paragraphs, T4 meta JSON, T5 rewrite (80 words), T6 (85 words). Full reference texts and raw run outputs are not included in this release.
