# CLAUDE.md

本仓库是 "Bit by bit" 课程的资料库(slides、教学材料、备课参考、课程管理)。

## 结构与规则

- `course/`:syllabus、schedule、grading 政策。修改日程时同步更新 `admin/` 中的相关安排。
- `lectures/NN_name/`:每讲一个目录,由 `lectures/_template/` 复制而来。结构:`README.md`(讲次元信息:目标、前置知识、时间安排、材料清单)、`slides/`、`notes/`(讲稿与教学笔记)、`exercises/`。
- `materials/`:学生可见的资料。放入前确认版权允许分发。
- `references/`:仅备课用,可含受版权保护的论文,不对外发布。
- `admin/private/`:含个人信息,**不得提交、不得贴入 issue/PR/对外内容**。
- 新增讲次用 `scripts/new_lecture.sh`,不要手工建目录。

## 写作约定

- 文档以中文为主;代码、文件名使用英文。
- 每个目录的 README 说明"这里放什么、如何命名"。
