# SkillRet 十题 RSI Flow 人工编排实验

本项目在 rsi-skill-platform 上对同一批十道 SkillRet 题运行 A/B 检索。A 用整题检索，B 保留整题检索，并为人工拆出的 2–3 项需求分别补查。两组使用同一测试语料、索引和评分口径。

## 查看结果

- [打开十题总览](pages/index.html)，从题号进入各题的证据页。页面包含原题、人工分支、A/B 排名、五项指标、失败分析和现场截图。
- [十题指标 JSON](evidence/summary.json)。[原始记录和截图](evidence/)以题号命名。静态网页读取的是已留存的实测记录，解压后可用浏览器打开。
- [人工需求分支定义](config/retrieval-cases.json)。每题一份配置，十题共用一个流程定义和一个可拖拽的现场运行页面。

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
| [frontend/](frontend/) | 复用 rsi-flow-visual 的十题共享画布、题号选择和 A/B 结果。 |
| [retrieval/](retrieval/) | 下载本次固定版本的数据与模型、构建向量索引、执行检索和评分。 |
| [config/](config/) | 十题分支定义、本地后端配置和 Maven 缓存设置。 |
| [pages/](pages/) · [evidence/](evidence/) | 十题静态网页、截图、原始排名和指标。 |

## 在 Windows 或 IDEA Terminal 复跑

运行依赖为 **JDK 8、Maven 3.9、Python 3.12、Node.js 24、Yarn 1.22.22、pnpm 11 和 Git**。准备一份独立 RSI 工作目录，以下用 `D:/rsi-demo` 举例。三个前后端仓库需在同一层。

| 上游仓库 | 验证所用提交 |
| --- | --- |
| [rsi-skill-spring-boot](https://github.com/ymxiong/rsi-skill-spring-boot) | `ff6db08d5acee0446e8074b608253a57c9916fb6` |
| [rsi-skill-platform](https://github.com/ymxiong/rsi-skill-platform) | `ff97757481f70293807f81cec78df9eea25b3119` |
| [rsi-flow-visual](https://github.com/ymxiong/rsi-flow-visual) | `43b8f53a7c77cbc6ea5f655820dfbe9336cb4452` |

Java 流程引擎通过 Maven 使用 `cc.eamon.open:flow-spring-boot-starter:0.4.14`。从零准备环境时，还需通过课程渠道取得其依赖及课程后端所需的 Maven 缓存。下方离线构建在已有课程依赖的环境中验证过。先在包的根目录执行以下命令，将源码和开发配置应用到刚准备的上游工作目录：

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

若本机用 uv 管理 Python，可用 `uv venv --seed --python 3.12 .venv` 创建环境。首次需下载约 1.2 GB 模型权重并为 6,006 条技能编码。使用支持 CUDA 的 PyTorch 时，可用 `--device cuda --batch-size 24`，与留存索引采用相同的 GPU 编码方式。CPU 也可重建，数值精度和批大小可能使个别名次不同。若已有本课程实验的 `skillret-cuda-full-1024.npz`，可复制到 `local-assets/indexes/skillret-full-1024.npz` 并跳过建索引命令。产物目录默认为 `local-assets/`，可用 `SKILLRET_ASSETS` 指向另一个同结构目录。服务打印 `Search ready on localhost:18940` 后可查询。

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

[打开本机演示](http://127.0.0.1:3400/skillret-q02592-search)。选择 `q-01364`，点击「运行 A/B」。参考实测中 A 命中 2/3，B 命中 3/3，`specs-dev` 最终排第 5。依次切换题号可以复跑其余九题。运行页面的转发规则随 Next.js 开发服务生效。

## 数据与证据来源

- [SkillRet 测试快照](https://huggingface.co/datasets/ThakiCloud/SKILLRET/tree/6583d7d2ed07644d0fb8938ed8178f3a7dc42a12)，固定修订 `6583d7d2ed07644d0fb8938ed8178f3a7dc42a12`。本包按官方公开数据核对原题和相关性标注。
- [SkillRet-Embedding-0.6B 权重](https://huggingface.co/anonymous-ed-benchmark/SKILLRET-Embedding-0.6B/tree/408aa6e2c1db2f89c791000000c70843154ed48b)，固定修订 `408aa6e2c1db2f89c791000000c70843154ed48b`。
- 截图和 JSON 来自十题 A/B 的原始平台运行。可用 `python scripts/build-evidence.py` 从这批记录重新生成静态网页。

交付验收在独立的上游源码目录进行。后端 Maven 打包成功，前端从画布重跑十题 A/B，各节点排名、最终排名和指标与留存证据一致。复跑使用已有模型权重、向量索引和依赖缓存。
