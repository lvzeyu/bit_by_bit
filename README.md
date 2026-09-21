# Bit by Bit

> 课程一句话简介(待补充)

## 目录结构

| 目录 | 内容 | 面向 |
|---|---|---|
| [course/](course/) | 教学大纲、日程、评分标准等课程"门面"文件 | 学生 + 教师 |
| [lectures/](lectures/) | 每一讲的 slides、讲稿、课堂练习 | 教师(slides 可发布) |
| [materials/](materials/) | 发给学生的资料:数据集、示例代码、阅读材料、讲义 | 学生 |
| [references/](references/) | 备课参考:论文、笔记、链接、教材摘录 | 教师 |
| [admin/](admin/) | 课程管理:后勤、评分、通知;`private/` 不入库 | 教师 |
| [assets/](assets/) | 跨讲共用的图片与 slides 主题 | 教师 |
| [scripts/](scripts/) | 构建/导出/生成脚本 | 教师 |

## 快速开始

新增一讲:

```bash
scripts/new_lecture.sh 01 intro     # 生成 lectures/01_intro/
```

## 约定

- 讲次目录命名:`NN_short-name`(两位序号 + 小写英文/拼音,连字符分隔),如 `03_information-theory`
- 学生可见内容放 `course/`、`materials/`、`lectures/*/slides`;其余默认仅教师可见
- 学生名单、成绩等个人信息只放 `admin/private/`,已在 `.gitignore` 中排除
- 大文件(视频、大数据集)不直接入库,在对应 README 中记录下载地址
- 详见 [CLAUDE.md](CLAUDE.md)
