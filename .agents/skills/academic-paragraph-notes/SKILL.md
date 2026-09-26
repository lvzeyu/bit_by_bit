---
name: academic-paragraph-notes
description: Generate or complete concise Japanese translations and reading notes for paragraph-aligned lecture YAML files rendered by scripts/build_reader.py. Use when working on lectures/*/notes/*.yml in this course repository; do not use for general translation or unrelated YAML.
---

# Academic Paragraph Notes

Create compact, academically appropriate Japanese notes for English source paragraphs while preserving the repository's existing YAML schema and paragraph alignment.

## Inspect the target

- Read the complete target YAML, the corresponding page information in `lectures/toc.yml`, and the relevant note rendering code in `scripts/build_reader.py` before editing.
- Use the English paragraphs associated with the target page as the source text. Do not translate from an existing Japanese summary.
- Treat `blocks` and paragraph `id` values as alignment constraints. Do not merge, split, reorder, add, or remove paragraph entries unless the user explicitly asks to repair the structure.
- Preserve unrelated comments and existing user edits.
- Do not modify a paragraph whose `status` is `reviewed` unless the user explicitly requests it.

## Fill each paragraph

Use only fields supported by the renderer:

```yaml
- id: 1
  status: draft
  ja: |
    原文に忠実で自然な日本語訳。
  point: |
    段落の中心的な内容を簡潔に説明する。
  vocab:
    - {term: "English term", gloss: "簡潔な日本語の意味"}
  syntax: |
    必要な場合のみ、理解しにくい構文を簡潔に説明する。
  background: |
    理解に不可欠な場合のみ、背景を簡潔に補足する。
```

Apply these rules:

- `status`: set newly generated or materially revised notes to `draft`. Preserve `reviewed` as required above.
- `ja`: required for each requested paragraph. Translate the complete paragraph into natural, formal Japanese suitable for academic reading. Do not prefix it with `（要約）` and do not replace translation with summary.
- `point`: required for each requested paragraph. State the central idea in one concise sentence. Use a second sentence only when the paragraph's role in the argument materially aids understanding, such as introducing a topic, stating a claim, supplying evidence, marking a contrast, or concluding a discussion.
- `vocab`: optional. Select only words or phrases important to understanding the paragraph, normally zero to four entries. Give only a short contextual Japanese meaning in `gloss`; do not add usage essays, etymology, or extended commentary.
- `syntax`: optional. Add only when a genuinely difficult construction, scope, reference, ellipsis, or long dependency could cause misreading. Explain only the key point, normally in one or two sentences.
- `background`: optional. Add only when information absent from the paragraph is necessary for comprehension, normally in one or two sentences.
- Write `ja`, `point`, `gloss`, `syntax`, and `background` in Japanese.
- Omit unused optional fields instead of writing empty values or empty lists.

## Translation discipline

- Preserve claims, logical relations, uncertainty, modality, negation, comparison, numbers, citations, names, and technical distinctions.
- Keep important terminology consistent across the page and, when context is available, across the chapter.
- Do not turn association into causation or tentative language into certainty.
- Do not invent an author's intention, missing context, or factual background. If ambiguity materially affects understanding, describe it cautiously in `syntax` rather than silently resolving it.
- Retain equations, citation markers, and inline technical notation accurately.

## Keep the YAML renderable

- Produce valid UTF-8 YAML using the existing top-level `blocks` and `paragraphs` structure.
- Quote compact `term` and `gloss` strings when punctuation or YAML-like values could be ambiguous. Use block scalars for prose when they improve safety or readability.
- Do not add the English source text to the YAML; the generated page already displays it.
- Keep `blocks` equal to the source paragraph count and ensure paragraph IDs are unique integers in the range `1..blocks`.

## Verify

After editing:

1. Parse the YAML to confirm it is valid.
2. Confirm paragraph count, IDs, and protected `reviewed` entries remain correct.
3. Run the narrowest applicable `scripts/build_reader.py --only ...` build for the target chapter when source access and the local environment permit it.
4. Inspect build warnings and confirm the generated page contains the Japanese translation and understanding-note callouts.

Favor concise notes. Additional explanation is justified only when it resolves a real comprehension problem.
