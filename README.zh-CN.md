# 数字人交互效果评测

[English](README.md) | [简体中文](README.zh-CN.md)

**英文名称：** Digital Human Interaction Evaluation · **仓库及包名称：** `digital-human-interaction-evaluation` · **软件许可证：** [MIT](LICENSE)

本项目使用 Python 分析人机交互中的问卷回答与面部动作单元（Action Unit，AU）测量数据。流程包括构建问卷维度、将面部测量与打断事件对齐，以及使用线性混合效应模型估计交互条件效应和人格与条件的交互效应。

项目对应的研究使用西交利物浦大学的 Wizard-of-Oz 数字人，即由研究人员在幕后控制的数字人。本仓库提供评测与分析工具，不包含数字人渲染平台、自主 LLM 智能体、模型训练或参与者录像。

**发布状态：** 本地公开候选版本，已按维护者要求加入 MIT 许可证。原团队代码的共同权属及再分发授权仍待确认，详见 [发布状态](docs/release-status.md)。当前实现的 `archived_notebooks` 分析口径遵循现存研究 Notebook，与论文方法描述的差异记录在 [方法说明](docs/methods.md)。合成示例用于展示软件行为，不代表论文实测结果。

## 运行合成示例

使用 Python 3.11 或更新版本，先创建隔离环境：

```sh
python -m venv .venv
```

在 Windows PowerShell 中执行 `.\.venv\Scripts\Activate.ps1` 激活环境；在 macOS/Linux 中执行 `source .venv/bin/activate`。随后安装项目、运行示例及测试：

```sh
python -m pip install -e .
python -m hci_eval demo --out results/demo
python -m unittest discover -s tests -v
```

后续运行请指定一个新的空输出目录。演示独立生成虚构参与者、问卷回答、面部测量和打断事件，不使用真实参与者记录。默认随机种子固定，也可以通过 `--seed` 指定其他种子以获得可重复的演示。

输出包括问卷维度分数、合并计算的问卷信度、AU 会话均值、条件与人格效应、原始及校正后的 p 值、拟合诊断和森林图。`run_report.json` 记录分析口径及数据是否由演示生成。解释任何估计值前，都应检查拟合诊断；未收敛、奇异性及协方差警告会被保留。

## 已验证的示例输出

在已测试的 Windows/Python 3.12 环境中，16 项测试全部通过，安装后的包完成了完整合成流程，拟合 156 个模型并生成三张图。72 个 AU 模型均有参数边界警告，其中 5 个未收敛；相关效应保留复核标记。软件成功执行不代表这些估计值已经通过统计解释验证，也不代表论文结论已复现。

示例见 [模型输出说明](examples/model-output/README.md)，检查记录见 [验证文档](docs/validation.md)。若要在相同的 Python 3.12 环境中使用已验证的依赖版本，可先安装 `requirements-tested.txt`，再安装本项目：

```sh
python -m pip install -r requirements-tested.txt
python -m pip install -e .
```

![合成数据的问卷条件效应](examples/model-output/questionnaire_condition.png)

## 分析自己的本地数据

按照 [输入数据格式](docs/data-schema.md) 准备三份标准 CSV：

```sh
python -m hci_eval run --questionnaire private_data/questionnaire.csv --frames private_data/frames.csv --events private_data/events.csv --out results/local
```

输入文件只读，结果写入专用输出目录。真实参与者数据应保留在公开仓库之外；Git 已忽略 `private_data/` 和 `results/` 路径。`.gitignore` 有助于减少误上传，但不能替代发布前的文件审查。

## 分析流程

1. 检查记录键、分数范围和参与者层面的信息一致性。
2. 保留问卷原始分数，应用原 Notebook 的题目计分规则，并仅使用组成题目完整的记录构建维度分数。
3. 按去重后的参与者计算五大人格的均值，并进行中心化。
4. 根据原研究阶段，在完整会话或打断事件窗口的并集内聚合四种面部 AU。
5. 拟合条件效应与人格调节效应的混合模型，同时纳入年龄、性别和条件呈现顺序。
6. 使用明确记录的多重比较校正范围，导出结果、拟合诊断和图表。

问卷与 AU 结果分别建模，共享参与者信息。仓库没有实现经过训练的多模态融合模型，也不包含访谈转录或定性编码记录。

## 仓库结构

| 路径 | 用途 |
| --- | --- |
| `src/hci_eval/questionnaire.py` | 原始题目映射、计分、维度构建和信度计算 |
| `src/hci_eval/openface.py` | 事件合并、最近帧对齐和 AU 聚合 |
| `src/hci_eval/statistics.py` | BH/Holm 校正、Wald 对比及带诊断的混合模型拟合 |
| `src/hci_eval/modeling.py` | 条件模型、人格交互模型及多重比较校正范围 |
| `src/hci_eval/validation.py`、`qc.py` | 输入格式校验、参与者信息一致性及数据质量统计 |
| `src/hci_eval/data.py` | 不修改原数据的参与者名单筛选 |
| `src/hci_eval/pipeline.py`、`__main__.py` | CSV 分析流程和命令行入口 |
| `src/hci_eval/plotting.py` | 展示校正后显著性及拟合复核标记的森林图 |
| `src/hci_eval/synthetic.py`、`data/demo/` | 独立合成数据生成器及示例输入 |
| `examples/analysis_walkthrough.ipynb` | 分步预处理示例，不保留运行输出 |
| `examples/preprocessing-output/` | 合成数据的问卷维度、AU 聚合、信度和质量报告 |
| `examples/model-output/` | 合成模型结果表、森林图和运行报告 |
| `tests/` | 计分、时间边界、统计校正和拟合诊断测试 |
| `docs/` | 方法、数据格式、代码来源和发布限制 |
| `pyproject.toml`、`requirements-tested.txt` | Python 包配置及已验证依赖版本 |
| `CITATION.cff`、`LICENSE` | 研究引用信息及 MIT 许可证 |

## 研究背景与贡献归属

研究由团队共同完成。Jingyu Ye 与 Xichun Xu 对 ECSCW 论文贡献相同；数字人平台由其他团队成员开发。原 Notebook 的作者归属及软件再分发授权仍在核对，论文作者排序不能证明代码由一人独立完成。本仓库是 2026 年在 AI 协助下整理的分析软件版本，应与原研究工作分别记录贡献。

相关论文：

- Ye 等（2026）。*“Because I Know It Is an AI”: How User Personality and AI-Schema Shape the Social Contract of Digital Humans*。[ECSCW 论文](https://doi.org/10.48340/ecscw2026_108)。
- *Evaluating User Preferences for Gender and Embodiment Scope in Human-Agent Interaction Systems*。[ICHEC 论文](https://doi.org/10.1145/3786995.3787057)。
- *When Virtual Eyes Meet Human Personality: An Empirical Study On How Personality Shapes Gaze Perception*。[ICHEC 论文](https://doi.org/10.1145/3786995.3787058)。

两篇 ICHEC 论文提供相关研究背景，其完整分析流程没有纳入本仓库主线。论文许可证不自动覆盖每一份代码或数据。

## 许可证

本候选版本的软件与配套文档采用 [MIT 许可证](LICENSE)，版权行使用项目贡献者集体署名。MIT 允许使用、修改、分发及商业使用，要求保留版权和许可声明，并且不提供质量担保。选择许可证不代表原团队代码的权属或贡献者授权已经核实；这些来源事项继续记录在 [发布状态](docs/release-status.md) 中。

此声明不改变相关论文、原始参与者数据、录像、外部 OpenFace 软件或其他第三方材料的许可，这些材料均未打包进本仓库。已提交的合成输入与生成的演示输出属于本候选版本的分发内容。

完整英文说明见 [English README](README.md)，软件检查结果见 [验证文档](docs/validation.md)。
