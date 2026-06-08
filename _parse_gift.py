# -*- coding: utf-8 -*-
"""Парсер банка вопросов Moodle GIFT -> content/content.js для тренажера.
Раскладывает вопросы по темам (Тема N / Тест N) в структуру TRENAGER_CONTENT."""
import re, json, os, html

SRC = r"D:\Claude\DigitalTwins\Материалы курса\вопросы-Цифровая инженерия (факультет химии)-top-20260603-1726.txt"
OUT = r"D:\Claude\DigitalTwins\trenajer\content\content.js"

TITLES = {
 "1":"Концепция цифровых двойников","2":"Подходы к определению","3":"Концепция ЦД изделий",
 "4":"Математические и компьютерные модели","5":"Адекватность модели","6":"Верификация моделей",
 "7":"Валидация моделей","8":"Верификация и валидация ПО","9":"Многоуровневая система требований",
 "10":"Цифровые (виртуальные) испытания","11":"Стенды и полигоны","12":"Платформа ЦД",
 "13":"Цифровая модель изделия","14":"Двусторонние связи","15":"ЦД новых и существующих","16":"Перспективы"
}

with open(SRC, encoding="utf-8") as f:
    lines = f.read().splitlines()

# сегменты по категориям, комментарии // отбрасываем
segments=[]; cur=None; buf=[]
def flush():
    if buf: segments.append((cur,"\n".join(buf)))
for ln in lines:
    s=ln.strip()
    if s.startswith("$CATEGORY:"):
        flush(); buf.clear(); cur=ln.split(":",1)[1].strip()
    elif s.startswith("//"):
        continue
    else:
        buf.append(ln)
flush()

def theme_of(cat):
    # категория - путь вида .../Тема 12 или .../Тест 13/Тест 14 (вложенная).
    # Берем ПОСЛЕДНИЙ номер в пути: для «Тест 13/Тест 14» это тема 14, а не 13.
    if not cat: return None
    ms=re.findall(r"(?:Тема|Тест)\s*(\d+)", cat)
    return ms[-1] if ms else None

def clean(s):
    s=re.sub(r"^\s*\[(?:html|markdown|moodle|plain)\]","",s)
    s=re.sub(r"%-?\d+(?:\.\d+)?%","",s)          # веса
    s=re.split(r"(?<!\\)#",s)[0]                  # обратная связь
    s=re.sub(r"\\([:=~{}#%])",r"\1",s)            # снятие экранирования GIFT
    s=re.sub(r"<[^>]+>","",s)                      # html-теги
    s=html.unescape(s).replace("\xa0"," ")
    # стиль проекта: без буквы «е с точками» и длинных/средних тире
    s=s.replace("ё","е").replace("Ё","Е").replace("—","-").replace("–","-")
    return re.sub(r"\s+"," ",s).strip()

ANS=re.compile(r"(?<!\\)([=~])\s*(.*?)(?=(?:\s*(?<!\\)[=~])|\Z)", re.DOTALL)

# Фильтр «назови год»: выкидываем фактологические вопросы, у которых верный ответ -
# по сути просто год/десятилетие (короткий, с 4-значным годом, без ссылки на ГОСТ).
# Ссылки на ГОСТ (напр. 57700.37-2021) НЕ трогаем - там год это номер стандарта.
def is_year_fact(opts):
    cor=[o["t"].strip() for o in opts if o["c"]]
    if not cor: return False
    for c in cor:
        if "ГОСТ" in c or "гост" in c.lower(): return False
        if len(c) > 18: return False
        if not re.search(r"(19|20)\d\d", c): return False
    return True

themes={}
seen_q=set()   # глобальный дедуп: один и тот же текст вопроса не должен попасть в разные темы
               # (в исходном банке категория «Тест 13» продублирована вопросами «Платформа ЦД»)
for cat,seg in segments:
    th=theme_of(cat)
    if th is None: continue
    for block in re.split(r"\n\s*\n", seg):
        if "{" not in block or "}" not in block: continue
        m=re.match(r"\s*::(.*?)::(.*)", block, re.DOTALL)
        body_ans = m.group(2) if m else block
        bi=body_ans.find("{"); ei=body_ans.rfind("}")
        if bi<0 or ei<bi: continue
        qtext=clean(body_ans[:bi])
        if not qtext: continue
        opts=[]
        for am in ANS.finditer(body_ans[bi+1:ei]):
            atext=clean(am.group(2))
            if atext: opts.append({"t":atext,"c":am.group(1)=="="})
        if len(opts)<2 or not any(o["c"] for o in opts): continue
        if is_year_fact(opts): continue   # выкидываем «назови год»
        if qtext in seen_q: continue       # глобальный дедуп (см. seen_q выше)
        seen_q.add(qtext)
        themes.setdefault(th,[]).append({"q":qtext,"options":opts})

out={"themes":{}}
for th in sorted(themes, key=lambda x:int(x)):
    out["themes"][th]={"title":TITLES.get(th,"Тема "+th),"questions":themes[th]}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT,"w",encoding="utf-8") as f:
    f.write("/* Сгенерировано из банка GIFT: py _parse_gift.py */\n")
    f.write("window.TRENAGER_CONTENT = ")
    f.write(json.dumps(out, ensure_ascii=False, indent=1))
    f.write(";\n")

print("Темы и число вопросов:")
for th in sorted(out["themes"], key=lambda x:int(x)):
    print("  Тема %s: %d" % (th, len(out["themes"][th]["questions"])))
print("Всего тем:", len(out["themes"]), "-> ", OUT)
