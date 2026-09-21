# Lectures

每讲一个目录,命名 `NN_short-name`。用 `scripts/new_lecture.sh NN name` 从 [_template/](_template/) 生成。

| 讲次 | 主题 | 状态 |
|---|---|---|
| 00 | Preface(前言) | 草稿 |
| 01 | Introduction(导论) | 草稿 |
| 02 | Observing behavior(观察行为) | 草稿 |
| 03 | Asking questions(提问) | 草稿 |
| 04 | Running experiments(开展实验) | 草稿 |
| 05 | Creating mass collaboration(构建大规模协作) | 草稿 |
| 06 | Ethics(伦理) | 草稿 |
| 07 | The future(未来) | 草稿 |

## 阅读页面(Quarto)

每讲对应教材 *Bit by Bit* 的一章(00 = Preface,01–07 = 第 1–7 章);章节结构见 [toc.yml](toc.yml)。英文原文按段落展示,每段下有可折叠的「日本語訳」「理解のポイント」。

```bash
cd lectures
quarto preview          # 边编辑边预览
quarto render           # 输出 _site/
python3 ../scripts/build_reader.py --refresh   # 重新抓取原文
```

- 渲染前 `scripts/build_reader.py` 会自动运行:抓取原文(缓存于 `.cache/`)→ 生成各讲 `notes/*.qmd`、`index.qmd`、`_sidebar.yml`。首次运行需联网,约 1–2 分钟。
- **翻译与笔记写在 `NN_x/notes/SS_slug.yml`**(按段落编号 `id` 对应),这是唯一需要手工编辑并提交的内容。
- 字段:`status`(todo / draft / reviewed)、`ja`(日本語訳)、`point`(要点),可选 `vocab`、`syntax`、`background`。字段为空则不显示对应折叠块。
- 含英文原文的生成物(`.qmd`、`.cache/`、`_site/`)受版权保护,已在 `.gitignore` 中排除,**不要提交、不要对外发布**;对外发布前须先确认授权。
- 未收录:各章章首索引页、Acknowledgments、References。
