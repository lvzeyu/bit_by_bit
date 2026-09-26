#!/usr/bin/env python3
"""生成 Bit by Bit 阅读页面(Quarto)。

用法(在仓库任意位置):
    python3 scripts/build_reader.py              # 抓取缺失页面 + 生成 .qmd / 侧边栏 / 首页
    python3 scripts/build_reader.py --refresh    # 忽略缓存,重新抓取
    python3 scripts/build_reader.py --only 02    # 只处理编号以 02 开头的讲次

输入:
    lectures/toc.yml                        章节目录(提交)
    lectures/NN_x/notes/SS_slug.yml         翻译与笔记(提交,人工编辑;缺失时自动生成空模板)
输出(均不提交,见 .gitignore):
    lectures/.cache/                        抓取的原始 HTML
    lectures/NN_x/notes/SS_slug.qmd         阅读页面(含英文原文)
    lectures/index.qmd, lectures/_sidebar.yml

英文原文只在本机抓取、渲染,不写入受版本控制的文件。
"""
import argparse
import json
import re
import subprocess
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import yaml

ROOT = Path(__file__).resolve().parent.parent
LEC = ROOT / "lectures"
CACHE = LEC / ".cache"
UA = "Mozilla/5.0 (bit-by-bit course reader; personal study use)"

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
BLOCKS = {"p", "ul", "ol", "dl", "blockquote", "table", "pre", "figure", "div"}

# ---------------------------------------------------------------- 抓取

def write_if_changed(path: Path, text: str):
    """内容没变就不写,避免无谓触发 quarto preview 重新渲染。"""
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8")


def fetch(url: str, cache_file: Path, refresh: bool) -> str:
    if cache_file.exists() and not refresh:
        return cache_file.read_text(encoding="utf-8")
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        r = subprocess.run(
            ["curl", "-sSL", "--fail", "-A", UA, url], capture_output=True, text=True, encoding="utf-8"
        )
        if r.returncode == 0 and "book-html" in r.stdout:
            cache_file.write_text(r.stdout, encoding="utf-8")
            time.sleep(0.5)  # 对原站保持礼貌
            return r.stdout
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"抓取失败: {url} ({r.stderr.strip()})")


# ---------------------------------------------------------------- 切块

class BlockParser(HTMLParser):
    """把内容区顶层元素切成块。section 包装 div 视为透明,其余 div 作为一个整体块。"""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []
        self.blocks = []
        self.cur = None

    def handle_starttag(self, tag, attrs):
        if self.cur:
            self.cur["parts"].append(self.get_starttag_text())
            if tag == self.cur["tag"]:
                self.cur["depth"] += 1
            return
        cls = dict(attrs).get("class") or ""
        if tag == "div" and "section" in cls.split():
            self.stack.append(tag)
        elif tag in BLOCKS or tag in HEADINGS:
            self.cur = {"tag": tag, "parts": [self.get_starttag_text()], "depth": 1}
        elif tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        if self.cur:
            self.cur["parts"].append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self.cur:
            self.cur["parts"].append(f"</{tag}>")
            if tag == self.cur["tag"]:
                self.cur["depth"] -= 1
                if self.cur["depth"] == 0:
                    self._finish()
        elif self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_data(self, data):
        if self.cur:
            self.cur["parts"].append(data)

    def handle_entityref(self, name):
        if self.cur:
            self.cur["parts"].append(f"&{name};")

    def handle_charref(self, name):
        if self.cur:
            self.cur["parts"].append(f"&#{name};")

    def _add(self, tag, raw):
        text = re.sub(r"<[^>]+>", "", raw).strip()
        kind = "heading" if tag in HEADINGS else "text"
        if text or "<img" in raw:
            self.blocks.append({"kind": kind, "tag": tag, "html": raw, "text": text})

    def _finish(self):
        tag, raw = self.cur["tag"], "".join(self.cur["parts"])
        self.cur = None
        items = split_list(raw) if tag in ("ul", "ol") else []
        if len(items) > 1:
            # 顶层列表按条目拆成独立块,ol 用 start 保持原编号
            m = re.search(r'start="(\d+)"', raw[: raw.find(">") + 1])
            start = int(m.group(1)) if m else 1
            for k, item in enumerate(items):
                open_tag = f'<ol start="{start + k}">' if tag == "ol" else "<ul>"
                self._add(tag, f"{open_tag}{item}</{tag}>")
        else:
            self._add(tag, raw)


class ListSplitter(HTMLParser):
    """取出 ul/ol 的顶层 li(嵌套列表留在所属 li 内)。"""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.items, self.cur, self.depth = [], None, 0

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.depth += 1
            if self.cur is None:
                self.cur = []
        if self.cur is not None:
            self.cur.append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        if self.cur is not None:
            self.cur.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self.cur is None:
            return
        self.cur.append(f"</{tag}>")
        if tag == "li":
            self.depth -= 1
            if self.depth == 0:
                self.items.append("".join(self.cur))
                self.cur = None

    def handle_data(self, data):
        if self.cur is not None:
            self.cur.append(data)

    def handle_entityref(self, name):
        if self.cur is not None:
            self.cur.append(f"&{name};")

    def handle_charref(self, name):
        if self.cur is not None:
            self.cur.append(f"&#{name};")


def split_list(raw: str):
    p = ListSplitter()
    p.feed(raw)
    return p.items


def parse_blocks(page_html: str, site_root: str):
    # 原页面带 <base href="/">,相对路径以站点根为基准
    k = page_html.find('<div class="book-html">')
    e = page_html.find('<div class="ort-footer">')
    if k < 0 or e < 0:
        raise RuntimeError("找不到内容区(网站结构可能已变化)")
    p = BlockParser()
    p.feed(page_html[k + len('<div class="book-html">'):e])
    blocks = p.blocks
    # 第一个 h1/h2 是页面标题,由 toc.yml 提供,去掉
    if blocks and blocks[0]["kind"] == "heading" and blocks[0]["tag"] in ("h1", "h2"):
        blocks = blocks[1:]
    for b in blocks:
        b["html"] = re.sub(
            r'(src|href)="([^"]+)"',
            lambda m: m.group(0)
            if m.group(2).startswith(("http", "#", "mailto:", "//"))
            else f'{m.group(1)}="{urljoin(site_root, m.group(2))}"',
            b["html"],
        )
    return blocks


# ---------------------------------------------------------------- 笔记

def stub_text(title: str, url: str, n: int) -> str:
    lines = [
        f"# {title}",
        f"# 原文: {url}",
        "# 每段一条,id 对应页面上的段落编号。status: todo / draft / reviewed",
        "# 可选字段(按需添加): vocab([{term, gloss}])、syntax、background",
        f"blocks: {n}   # 原文段落数,build 时校验",
        "paragraphs:",
    ]
    for i in range(1, n + 1):
        lines += [f"  - id: {i}", "    status: todo", '    ja: ""', '    point: ""']
    return "\n".join(lines) + "\n"


def load_notes(path: Path, n: int, label: str):
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if data.get("blocks") not in (None, n):
        print(f"  ! {label}: 原文段落数 {n} ≠ 笔记记录的 {data['blocks']},请核对对应关系", file=sys.stderr)
    notes = {}
    for p in data.get("paragraphs") or []:
        if p.get("id") in notes:
            print(f"  ! {label}: id {p['id']} 重复", file=sys.stderr)
        notes[p.get("id")] = p
    for i in notes:
        if not isinstance(i, int) or not 1 <= i <= n:
            print(f"  ! {label}: 笔记 id {i!r} 超出原文段落范围 1..{n}", file=sys.stderr)
    return notes


def has(note, key):
    v = note.get(key)
    return bool(v and (str(v).strip() if not isinstance(v, list) else v))


def render_note_blocks(note: dict) -> str:
    out = []
    if has(note, "ja"):
        out.append(f'::: {{.callout-tip .bb-ja collapse="true" lang="ja" title="日本語訳"}}\n{str(note["ja"]).strip()}\n:::')
    body = []
    if has(note, "point"):
        body.append(f"**要点**:{str(note['point']).strip()}")
    if has(note, "vocab"):
        body.append("**語彙**\n\n" + "\n".join(f"- {v['term']} — {v['gloss']}" for v in note["vocab"]))
    if has(note, "syntax"):
        body.append(f"**構文**:{str(note['syntax']).strip()}")
    if has(note, "background"):
        body.append(f"**背景**:{str(note['background']).strip()}")
    if body:
        out.append(
            '::: {.callout-note .bb-note collapse="true" lang="ja" title="理解のポイント"}\n'
            + "\n\n".join(body) + "\n:::"
        )
    return "\n\n".join(out)


# ---------------------------------------------------------------- 页面

def render_qmd(title, url, blocks, notes, n_done, n_rev):
    n = sum(b["kind"] == "text" for b in blocks)
    parts = [
        "---",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        "---",
        "",
        "::: {.bb-meta}",
        f'[原文を開く ↗]({url}){{target="_blank"}} [· 日本語訳 {n_done}/{n} 段落 · 審校済み {n_rev}]{{.bb-progress}}',
        ":::",
        "",
    ]
    i = 0
    for b in blocks:
        if b["kind"] == "heading":
            level = int(b["tag"][1])
            parts += [f"{'#' * level} {b['text'] if '<' not in b['html'] else re.sub(r'^<h.>|</h.>$', '', b['html'])}", ""]
            continue
        i += 1
        raw = f'<div class="bb-en"><a class="bb-num" href="#p{i}">{i}</a><div class="bb-body">{b["html"]}</div></div>'
        parts += [f"::: {{#p{i} .bb-block}}", "", "````{=html}", raw, "````", ""]
        nb = render_note_blocks(notes.get(i, {}))
        if nb:
            parts += [nb, ""]
        parts += [":::", ""]
    return "\n".join(parts)


def depth_of(title: str) -> int:
    m = re.match(r"^(\d+(?:\.\d+)*)\s", title)
    return m.group(1).count(".") if m and "." in m.group(1) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    toc = yaml.safe_load((LEC / "toc.yml").read_text(encoding="utf-8"))
    base = toc["base_url"]
    sidebar = [{"href": "index.qmd", "text": "目次"}]
    index = [
        "---",
        'title: "英語原書講読入門"',
        "---",
        "",
        "本授業では、英語で書かれた学術文献を読み解く力を身につけるとともに、"
        "『Bit by Bit: Social Research in the Digital Age』の講読を通して、"
        "計算社会科学とその研究方法の基礎を学びます。",
        "",
        "本サイトに掲載する英文本文は、Matthew J. Salganik, "
        "[*Bit by Bit: Social Research in the Digital Age*](https://www.bitbybitbook.com/en/) "
        "の公開オンライン版に基づいています。",
        "",
        "## 授業の目標",
        "",
        "- 英語の学術文献を正確に読み、内容を理解できるようになる。",
        "- 文献の理解に必要な背景情報を調べ、適切に活用できるようになる。",
        "- 英語の学術文献を要約し、その内容を発表できるようになる。",
        "- 計算社会科学とその主要な研究方法について、基礎的な理解を得る。",
        "",
    ]
    failed = []

    for ch in toc["chapters"]:
        selected = not args.only or ch["dir"].startswith(args.only)
        notes_dir = LEC / ch["dir"] / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        index += [f"## {ch['title']}", ""]
        sec = {"section": ch["title"], "contents": []}
        stack = []  # 当前二级父节点
        for seq, pg in enumerate(ch["pages"], 1):
            slug = pg["path"].strip("/").split("/")[-1]
            stem = f"{seq:02d}_{slug}"
            url = base + pg["path"]
            qmd_rel = f"{ch['dir']}/notes/{stem}.qmd"
            qmd, yml = notes_dir / f"{stem}.qmd", notes_dir / f"{stem}.yml"
            n_done = n_rev = n = 0
            if selected or not qmd.exists():
                try:
                    html_text = fetch(url, CACHE / ch["dir"] / f"{stem}.html", args.refresh)
                    blocks = parse_blocks(html_text, "https://" + url.split("/")[2] + "/")
                    n = sum(b["kind"] == "text" for b in blocks)
                    if not yml.exists():
                        yml.write_text(stub_text(pg["title"], url, n), encoding="utf-8")
                    notes = load_notes(yml, n, qmd_rel)
                    n_done = sum(has(v, "ja") for v in notes.values())
                    n_rev = sum(v.get("status") == "reviewed" for v in notes.values())
                    write_if_changed(qmd, render_qmd(pg["title"], url, blocks, notes, n_done, n_rev))
                    print(f"  {qmd_rel}: {n} 段落, 日本語訳 {n_done}")
                except Exception as e:  # noqa: BLE001
                    failed.append((qmd_rel, str(e)))
                    print(f"  ✗ {qmd_rel}: {e}", file=sys.stderr)
                    continue
            # 侧边栏与首页(即使跳过重建,也按已有文件登记)
            if not qmd.exists():
                continue
            d = depth_of(pg["title"])
            item = {"href": qmd_rel, "text": pg["title"]}
            index.append(f"{'  ' * (d - 1)}- [{pg['title']}]({qmd_rel})")
            if d >= 2 and stack:
                stack[-1].setdefault("contents", []).append(item)
                if "section" not in stack[-1]:
                    stack[-1]["section"] = stack[-1].pop("text")
            else:
                sec["contents"].append(item)
                stack = [item]
        index.append("")
        sidebar.append(sec)

    write_if_changed(LEC / "index.qmd", "\n".join(index) + "\n")
    write_if_changed(
        LEC / "_sidebar.yml",
        yaml.safe_dump({"website": {"sidebar": {"style": "docked", "search": True, "contents": sidebar}}},
                       allow_unicode=True, sort_keys=False, width=200),
    )
    if failed:
        print(f"\n{len(failed)} 页失败,重新运行可只补抓缺失页面。", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
