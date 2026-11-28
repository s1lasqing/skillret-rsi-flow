# SkillRet RSI Flow 人工编排实验

本项目在 rsi-skill-platform 上对同一批十道 SkillRet 题运行 A/B 检索。A 用整题检索，B 保留整题检索，并为人工拆出的 2–3 项需求分别补查。两组使用同一测试语料、索引和评分口径。

另选 8 道 SkillRet 官方测试题，沿用同一流程和检索参数复试。召回提升 5 题，完全修复 3 题，平均 Recall@10 从 41.67% 到 70.83%。 [八题复试总览](pages/retest.html) · [复试记录](docs/%E8%BF%9B%E9%98%B6%E6%A1%A3-%E5%85%AB%E9%A2%98%E5%A4%8D%E8%AF%95.md) · [LLM 编排设计](docs/%E6%8C%91%E6%88%98%E6%A1%A3-LLM%E8%87%AA%E4%B8%BB%E7%BC%96%E6%8E%92%E8%AE%BE%E8%AE%A1.md)

## 案例与实验记录

| 内容 | 查看入口 |
| --- | --- |
| 代码与报告 | [仓库](https://github.com/s1lasqing/skillret-rsi-flow) · [八题复试报告](docs/%E8%BF%9B%E9%98%B6%E6%A1%A3-%E5%85%AB%E9%A2%98%E5%A4%8D%E8%AF%95.md) · [LLM 编排设计](docs/%E6%8C%91%E6%88%98%E6%A1%A3-LLM%E8%87%AA%E4%B8%BB%E7%BC%96%E6%8E%92%E8%AE%BE%E8%AE%A1.md) |
| 问题清单 | 下方列出 18 道题。点题号可查看原始输入、官方标注技能和检索分支。 |
| 修复前后对照 | [原十题](pages/index.html) · [复试八题](pages/retest.html)。每题保留 A/B 最终排名、五项指标、平台截图和原始返回。 |
| 失败项 | 逐题原因见下表，汇总见[失败项与原因](#失败项与原因)。 |
| AI 使用与核实方式 | 见 [AI 使用与核实](#ai-使用与核实)。 |

### 问题清单

A 使用整题检索，B 使用同一整题加人工配置的需求分支。表中的命中指官方标注技能进入最终 Top 10。期望结果为该题全部标注技能进入 Top 10。按此口径，原组 **2/10**、复试 **3/8** 完全修复，合计 **5/18**。

| 批次 | 题号与查询主题 | A → B 命中 | B 的结果或仍存在的问题 |
| --- | --- | --- | --- |
| 原十题 | [q-02592 Ruby 代码与工程报告](pages/q-02592.html) | 1/2 → 1/2 | 代码结构技能未进入节点候选前十。 |
| 原十题 | [q-00821 旅行应用引导设计](pages/q-00821.html) | 1/2 → 1/2 | 代码查找技能未进入节点候选前十。 |
| 原十题 | [q-03697 容器部署证据综述](pages/q-03697.html) | 1/2 → 1/2 | DevOps 技能未进入节点候选前十。 |
| 原十题 | [q-02870 Fountain 剧本页数和 CI](pages/q-02870.html) | 1/2 → 1/2 | 开发流程技能未进入节点候选前十。 |
| 原十题 | [q-01769 沿海传感网络运维材料](pages/q-01769.html) | 1/3 → 1/3 | 经验沉淀技能进了分支候选但未合入，文档管理技能未进入候选前十。 |
| 原十题 | [q-01901 开户向导规格与交互](pages/q-01901.html) | 2/3 → 2/3 | 语义提交技能入选，原第 7 的交互设计技能掉出前十，NDCG 下降。 |
| 原十题 | [q-01364 事故分级与响应式规格](pages/q-01364.html) | 2/3 → 3/3 | 补入规格编写技能，完全修复。 |
| 原十题 | [q-01921 开发者门户三项需求](pages/q-01921.html) | 1/3 → 2/3 | 补入 Git 规范技能，UI 设计技能仍未进入候选前十。 |
| 原十题 | [q-00137 终端式工具市场](pages/q-00137.html) | 2/3 → 3/3 | 补入工具发现技能，完全修复。 |
| 原十题 | [q-00463 状态组件与环境交付](pages/q-00463.html) | 2/3 → 2/3 | 配置分发技能未进入节点候选前十。 |
| 复试八题 | [q-03910 密钥扫描插件与提示文案](pages/q-03910.html) | 1/2 → 2/2 | 补入提示文案技能，完全修复。 |
| 复试八题 | [q-00498 日记应用审查与导航](pages/q-00498.html) | 2/3 → 3/3 | 补入界面审查技能，完全修复。 |
| 复试八题 | [q-00095 Vue 重连与严格类型](pages/q-00095.html) | 2/3 → 2/3 | 类型技能超出分支追加名额，问题解析技能从第 8 降至第 10，NDCG 下降。 |
| 复试八题 | [q-00360 动态路线 PRD 与发布流水线](pages/q-00360.html) | 1/2 → 2/2 | 补入 CI/CD 技能，完全修复。 |
| 复试八题 | [q-00199 跨服务追踪与事故分析](pages/q-00199.html) | 1/2 → 1/2 | 提示词设计技能未进入节点候选前十。 |
| 复试八题 | [q-02596 多团队国际化与同步](pages/q-02596.html) | 1/2 → 1/2 | 翻译冲突处理技能未进入节点候选前十。 |
| 复试八题 | [q-01929 Unity 计时与发行素材](pages/q-01929.html) | 0/3 → 2/3 | 补入素材和社媒技能，Unity 编辑技能仍未进入候选前十。 |
| 复试八题 | [q-00306 Go 服务骨架与入门](pages/q-00306.html) | 0/3 → 1/3 | 补入入门指南技能，服务基础和数据访问审查技能仍未进入候选前十。 |

### 失败项与原因

- **节点候选缺失。** 例如 `q-00199` 的提示词设计技能在整题和各分支的候选前十都没出现，合并节点没有该技能可选。这个现象只能定位到候选阶段，现有记录不足以区分词法匹配、向量匹配和融合截断各自的影响。
- **候选出现但合并未保留。** `q-01769` 的经验沉淀技能排在分支第 5，`q-00095` 的类型技能排在分支第 6。两个技能都超出固定的分支追加范围。
- **已命中的技能被挤出或后移。** `q-01901` 和 `q-00095` 的召回持平，NDCG 下降。固定合并规则贯穿两批实验，失败和退化保留在结果中，供后续单独验证排序调整。

### 十题独立配置

[前端配置](frontend/cases/)记录各题 A/B 画布的节点、连线和实际执行请求体。网页运行时通过 `/skillret-runtime/cases` 读取配置并生成画布，导出的 JSON 可用于核对。[后端配置](backend/cases/)记录每题的需求分支和检索文本，与 `config/retrieval-cases.json` 中的对应条目一致。调整后端单题配置时，将对应条目改入汇总配置，再重启 Python 检索服务。各题共用同一份 Java 流程定义。结果原因见上方的问题清单。

| 编号 | SkillRet 题号 | 前端配置 | 后端配置 | A/B 实跑 |
| --- | --- | --- | --- | --- |
| 1 | `q-02592` | [JSON](frontend/cases/case1.json) | [JSON](backend/cases/case1.json) | [结果](evidence/q-02592.json) |
| 2 | `q-00821` | [JSON](frontend/cases/case2.json) | [JSON](backend/cases/case2.json) | [结果](evidence/q-00821.json) |
| 3 | `q-03697` | [JSON](frontend/cases/case3.json) | [JSON](backend/cases/case3.json) | [结果](evidence/q-03697.json) |
| 4 | `q-02870` | [JSON](frontend/cases/case4.json) | [JSON](backend/cases/case4.json) | [结果](evidence/q-02870.json) |
| 5 | `q-01769` | [JSON](frontend/cases/case5.json) | [JSON](backend/cases/case5.json) | [结果](evidence/q-01769.json) |
| 6 | `q-01901` | [JSON](frontend/cases/case6.json) | [JSON](backend/cases/case6.json) | [结果](evidence/q-01901.json) |
| 7 | `q-01364` | [JSON](frontend/cases/case7.json) | [JSON](backend/cases/case7.json) | [结果](evidence/q-01364.json) |
| 8 | `q-01921` | [JSON](frontend/cases/case8.json) | [JSON](backend/cases/case8.json) | [结果](evidence/q-01921.json) |
| 9 | `q-00137` | [JSON](frontend/cases/case9.json) | [JSON](backend/cases/case9.json) | [结果](evidence/q-00137.json) |
| 10 | `q-00463` | [JSON](frontend/cases/case10.json) | [JSON](backend/cases/case10.json) | [结果](evidence/q-00463.json) |

### AI 使用与核实

- **开发和实验辅助。** 使用 Codex 协助整理、实现和排查运行流程，拟定部分需求分支，执行复试，整理截图、失败归因和报告。这里的「人工编排」指实验运行前配置分支并保存到 JSON。分支拟写有 AI 辅助，运行中由固定流程读取配置。
- **运行时模型。** 本地 SkillRet-Embedding-0.6B 负责向量编码。搜索结果来自 RSI Flow 实际调用的检索服务，五项指标由程序根据最终排名和官方标注计算。LLM 自动编排目前处于设计阶段。
- **数据与评分核实。** 根据题号对照固定版本的官方 `queries/test.jsonl` 和 `qrels/test.jsonl`，核对原题及标注技能 ID。检查 A 和 B 的整题节点使用同一原题且返回相同整题排名，再根据 A/B 实际 Top 10 与标注的交集复算五项指标。两批 JSON 保留了逐节点候选，可追到漏召回或合并丢失发生在哪一层。[原十题原始记录](evidence/) · [复试八题原始记录](evidence/retest/)
- **平台复核。** 在画布上选择 `q-01364`，重新点击「运行 A/B」，核对命中从 2/3 到 3/3，规格技能进入第 5。也可复跑 `q-00095` 核对失败案例，类型技能在分支第 6，最终前十仍缺失，问题解析技能从第 8 移到第 10。[主实验复核样例](pages/q-01364.html) · [复试失败样例](pages/q-00095.html)

## 查看结果

- [打开十题总览](pages/index.html)，从题号进入各题的证据页。页面包含原题、人工分支、A/B 排名、五项指标、失败分析和现场截图。
- [十题指标 JSON](evidence/summary.json)。[原始记录和截图](evidence/)以题号命名。静态网页读取的是已留存的实测记录，解压后可用浏览器打开。
- 原十题和复试八题共用一个流程定义和一个可拖拽的现场运行页面。[原题分支定义](config/retrieval-cases.json) · [复试分支定义](config/retest-cases.json)

| 十题均值 | A 整题 | B 按需补查 |
| --- | ---: | ---: |
| Recall@10 | 53.33% | 63.33% |
| Precision@10 | 14.00% | 17.00% |
| Completeness@10 | 0.00% | 20.00% |
| NDCG@10 | 49.12% | 52.75% |
| MAP@10 | 34.90% | 37.11% |

召回提升 3 题，其中 `q-01364` 和 `q-00137` 找齐全部标注技能。6 题的五项指标持平。另有 `q-01901` 召回持平且 NDCG 下降，一条新标注技能入选，同时挤掉原先命中的一条。十题来自此前选出的漏召回案例，结果反映这批样本。

## 流程如何运行

1. 页面把 `queryId` 和 `variant` 传给 rsi-flow。Python 检索服务按题号从 SkillRet 测试集取原题。
2. 整题和各需求节点的每次查询都覆盖 3 个逻辑分片，共 6,006 条技能。BM25 用全库统计，合并全局前 100 条正分候选。向量检索按余弦相似度取全局前 20。加权 RRF 以 BM25:向量 = 1:2、`k=10` 融合，每个节点保留 Top 10。
3. A 输出整题排名。B 保留整题前 3 条，按分支配置顺序，每条追加前 2 个尚未入选的候选，再从整题排名补至 10 条。
4. 最终排名确定后，读取该题官方相关性标注 `qrels` 计算五项指标。网页单题显示 AP@10，十题均值是 MAP@10。

分片规模是 1,964、2,032、2,010，均在本机 Python 进程中模拟。向量索引由本地 SkillRet-Embedding-0.6B 建成，运行时同一模型编码查询。画布的箭头表示查询和候选去向，后端的 `routes` 定义实际执行顺序，B 的补查按配置依次执行。

| 路径 | 用途 |
| --- | --- |
| [backend/](backend/) | Java `@Flow` 节点和 RSI 流程 JSON，覆盖整题、需求补查、合并评测。 |
| [frontend/](frontend/) | 复用 rsi-flow-visual 的共享画布、题号选择和 A/B 结果。 |
| [retrieval/](retrieval/) | 下载本次固定版本的数据与模型、构建向量索引、执行检索和评分。 |
| [config/](config/) | 两批题目的分支定义、本地后端配置和 Maven 缓存设置。 |
| [pages/](pages/) · [evidence/](evidence/) | 两批实验的静态网页、截图、原始排名和指标。 |

## 在 Windows 或 IDEA Terminal 复跑

运行依赖为 **JDK 8、Maven 3.9、Python 3.12、Node.js 24、Yarn 1.22.22、pnpm 11 和 Git**。准备一份独立 RSI 工作目录，以下用 `D:/rsi-demo` 举例。三个前后端仓库需在同一层。

| 上游仓库 | 验证所用提交 |
| --- | --- |
| [rsi-skill-spring-boot](https://github.com/ymxiong/rsi-skill-spring-boot) | `ff6db08d5acee0446e8074b608253a57c9916fb6` |
| [rsi-skill-platform](https://github.com/ymxiong/rsi-skill-platform) | `ff97757481f70293807f81cec78df9eea25b3119` |
| [rsi-flow-visual](https://github.com/ymxiong/rsi-flow-visual) | `43b8f53a7c77cbc6ea5f655820dfbe9336cb4452` |

Java 流程引擎通过 Maven 使用 `cc.eamon.open:flow-spring-boot-starter:0.4.14`。首次配置需要通过可访问的 Maven 私服解析 RSI 依赖，或导入已准备的依赖缓存。下方离线构建在依赖已缓存的环境中验证过。在仓库根目录执行以下命令，将源码和开发配置应用到上游工作目录。

```powershell
$package = (Get-Location).Path
$rsi = 'D:/rsi-demo'
& "$package/scripts/install-overlay.ps1" -RsiWorkspace $rsi
```

该脚本应用前端代理及依赖兼容补丁，并复制流程源码。遇到不同内容的同名源码会停止。以下三个终端都从包根目录打开。

### 终端一 · 准备数据与启动检索

```powershell
$package = (Get-Location).Path
py -3.12 -m venv .venv
$python = Join-Path $package '.venv/Scripts/python.exe'
& $python -m pip install -r retrieval/requirements.txt
& $python retrieval/download_assets.py
& $python retrieval/retrieve.py --device cpu --batch-size 8
$env:OMP_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
& $python -u retrieval/retrieval_demo.py
```

若本机用 uv 管理 Python，可用 `uv venv --seed --python 3.12 .venv` 创建环境。首次需下载约 1.2 GB 模型权重并为 6,006 条技能编码。使用支持 CUDA 的 PyTorch 时，可用 `--device cuda --batch-size 24`，与留存索引采用相同的 GPU 编码方式。CPU 也可重建，数值精度和批大小可能使个别名次不同。若已有原始索引 `skillret-cuda-full-1024.npz`，可复制到 `local-assets/indexes/skillret-full-1024.npz` 并跳过建索引命令。产物目录默认为 `local-assets/`，可用 `SKILLRET_ASSETS` 指向另一个同结构目录。服务打印 `Search ready on localhost:18940` 后可查询。

### 终端二 · 打包并启动 RSI Java 后端

用 JDK 8 打开终端并确认 `JAVA_HOME` 指向 JDK 8。下载一次 [H2 1.4.200](https://repo.maven.apache.org/maven2/com/h2database/h2/1.4.200/h2-1.4.200.jar) 到 `local-assets/h2/`。将 `mvn` 替换成 IDEA 内置 Maven 的 `mvn.cmd` 绝对路径也可以。

```powershell
$package = (Get-Location).Path
$rsi = 'D:/rsi-demo'
Set-Location "$rsi/rsi-skill-spring-boot"
mvn -o -s "$package/config/maven-offline.xml" -pl core-starter -am -DskipTests package
$localConfig = ([uri](Join-Path $package 'config/backend.yml')).AbsoluteUri
& "$env:JAVA_HOME/bin/java.exe" "-Dloader.path=$package/local-assets/h2" `
  -cp 'core-starter/target/core-starter-1.0.0-executable.jar' `
  org.springframework.boot.loader.PropertiesLauncher `
  "--spring.config.additional-location=$localConfig"
```

等 Tomcat 在 `33478` 启动。演示配置使用 H2 内存数据库并关闭 Eureka。IDEA 中通过后端根目录 `pom.xml` 导入 Maven 项目，保存节点 Java 或 `routes` 后重新打包，并用新 JAR 启动。

### 终端三 · 运行画布

```powershell
$rsi = 'D:/rsi-demo'
Set-Location "$rsi/rsi-flow-visual"
yarn install --frozen-lockfile
yarn build:lib
Set-Location "$rsi/rsi-skill-platform"
pnpm install --frozen-lockfile
pnpm dev --hostname 127.0.0.1 --port 3400
```

[打开本机演示](http://127.0.0.1:3400/skillret-q02592-search)。选择 `q-01364`，点击「运行 A/B」。参考实测中 A 命中 2/3，B 命中 3/3，`specs-dev` 最终排第 5。复试可选择 `q-03910`，其实测 A 命中 1/2，B 命中 2/2。切换题号可复跑两批共 18 题。运行页面的转发规则随 Next.js 开发服务生效。

## 数据与证据来源

- [SkillRet 测试快照](https://huggingface.co/datasets/ThakiCloud/SKILLRET/tree/6583d7d2ed07644d0fb8938ed8178f3a7dc42a12)，固定修订 `6583d7d2ed07644d0fb8938ed8178f3a7dc42a12`。本包按官方公开数据核对原题和相关性标注。
- [SkillRet-Embedding-0.6B 权重](https://huggingface.co/anonymous-ed-benchmark/SKILLRET-Embedding-0.6B/tree/408aa6e2c1db2f89c791000000c70843154ed48b)，固定修订 `408aa6e2c1db2f89c791000000c70843154ed48b`。
- 截图和 JSON 来自原十题及复试八题的 A/B 平台运行。可用 `python scripts/build-evidence.py` 从两批记录重新生成静态网页。

复现验证在独立的上游源码目录进行。后端 Maven 打包成功，前端从画布重跑十题 A/B，各节点排名、最终排名和指标与留存记录一致。复跑使用已有模型权重、向量索引和依赖缓存。
