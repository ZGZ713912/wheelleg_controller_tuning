# Wheel-Leg Traditional Controller Auto-Tuning

🤖 使用贝叶斯优化和强化学习在 Isaac Sim 中自动调参轮腿机器人传统控制器

---

## 🎯 项目目标

在已有的 Isaac Sim 仿真环境（`纯底盘_v7_flat_base107`）中，通过自动化方法优化传统控制器参数（LQR 增益、PID 参数等），使其在跟踪性能、稳定性、能耗等指标上达到最优。

## ✨ 核心特性

- 🔧 **保留物理意义**：基于传统控制器架构，参数有明确物理解释
- ⚡ **样本效率高**：贝叶斯优化 200 次评估即可收敛（相比 RL 百万步）
- 🎛️ **多目标优化**：同时优化跟踪误差、稳定性、能耗
- 🔬 **Sim2Real 友好**：优化后的参数可直接部署到 RMCS 真机
- 📊 **可视化丰富**：Optuna Dashboard + Pareto 前沿分析

## 📦 快速开始

### 环境准备

```bash
cd /home/noir/Documents/workspace/wheelleg_controller_tuning

# 使用 Isaac RL 训练环境
cd ../isaac_wheeled_rl_train
source venv/bin/activate  # 或你的虚拟环境
cd ../wheelleg_controller_tuning

# 安装额外依赖
pip install optuna optuna-dashboard plotly kaleido
```

### 运行优化

```bash
# 1. 评估基线性能
python scripts/evaluate_baseline.py \
    --config configs/default_params.yaml \
    --output results/baseline.json

# 2. 启动贝叶斯优化
python scripts/02_run_bayesian_opt.py \
    --n-trials 200 \
    --n-jobs 4 \
    --study-name wheelleg_v1

# 3. 实时监控（另一个终端）
optuna-dashboard sqlite:///results/optuna.db
# 访问 http://localhost:8080

# 4. 导出最优参数
python scripts/export_best_params.py \
    --study-name wheelleg_v1 \
    --output results/best_params.json
```

## 📊 项目结构

```
wheelleg_controller_tuning/
├── AGENTS.md              # 详细开发计划
├── README.md              # 本文件
├── docs/                  # 文档
├── src/                   # 源代码
│   ├── controller/        # 传统控制器实现
│   ├── optimization/      # 优化算法
│   └── evaluation/        # 评估指标
├── configs/               # 配置文件
├── scripts/               # 执行脚本
└── results/               # 结果输出
```

## 🔗 相关项目

- **传统控制器源码**：`/home/ubuntu/RMCS_` 容器中的 `downstream/wheel_leg_math_clean` 分支
- **RL 训练仓库**：`/home/noir/Documents/workspace/isaac_wheeled_rl_train`
- **车体模型**：`纯底盘_v7_flat_base107`（已有轮子参数辨识）

## 📚 方法论

### 阶段 1：贝叶斯优化（推荐优先使用）

- **输入**：LQR/PID 增益等 10-15 个关键参数
- **输出**：Pareto 最优参数组合
- **时间**：200 次评估约 30-60 分钟（4 进程并行）
- **优势**：样本效率高、可解释性强、直接部署

### 阶段 2：增益调度学习（可选）

- **方法**：用 RL（PPO）学习状态依赖的增益策略
- **优势**：适应不同场景（负载变化、地形变化）
- **劣势**：需要更多训练时间，sim2real 难度更高

### 阶段 3：混合控制（可选）

- **架构**：传统控制器 + RL 残差修正
- **优势**：保留稳定性 + 提升性能
- **适用**：需要极致性能的场景

## 📈 预期成果

| 指标 | 基线（待测） | 优化目标 |
|------|--------------|----------|
| 速度跟踪误差 | - | < 0.05 m/s |
| 角速度跟踪误差 | - | < 0.1 rad/s |
| Pitch 稳定性 | - | < 5° std |
| 存活率 | - | > 99% |
| 质量鲁棒性 | - | ±30% 仍稳定 |

## 🛠️ 开发路线

- [x] 项目规划和文档（2026-10-27）
- [ ] 提取传统控制器代码
- [ ] Isaac Sim 环境集成
- [ ] 实现贝叶斯优化管线
- [ ] 性能评估和报告生成
- [ ] （可选）增益调度学习
- [ ] （可选）混合控制架构

详细计划见 [AGENTS.md](./AGENTS.md)

## 📄 许可证

本项目用于研究和学习目的。

## 🙏 致谢

- RMCS 团队提供的传统控制器实现
- Isaac Sim RL 训练环境和车体模型
- Optuna 贝叶斯优化框架
