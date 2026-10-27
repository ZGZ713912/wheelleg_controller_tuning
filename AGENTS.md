# AGENTS.md - 轮腿机器人传统控制器自动调参项目

本项目使用神经网络/强化学习方法，在 Isaac Sim 仿真环境中自动优化 wheel_leg_math_clean 分支的传统控制器参数。

---

## 📋 项目概述

### 目标
在已有的稳定 Isaac Sim 仿真环境（`纯底盘_v7_flat_base107`）中，通过自动化方法优化传统控制器的参数（LQR 增益、PID 参数、外环增益等），使其在跟踪性能、稳定性、能耗等指标上达到最优。

### 背景
- **传统控制仓库**：`/home/ubuntu/RMCS_` 容器中的 `downstream/wheel_leg_math_clean` 分支
- **RL 训练仓库**：`/home/noir/Documents/workspace/isaac_wheeled_rl_train`
- **车体模型**：`纯底盘_v7_flat_base107`（已有 sim2real 轮子参数辨识）
- **仿真环境**：Isaac Sim + 已验证的轮子动力学参数

---

## 🎯 项目阶段

### 阶段 0：环境准备与代码移植（预估 1-2 周）

#### 任务 0.1：梳理传统控制器架构
- [ ] 从 `wheel_leg_math_clean` 提取完整控制流程
- [ ] 识别所有可调参数及其作用域
- [ ] 绘制控制架构图（层次、数据流、执行器分配）

**关键文件**：
```
RMCS_/rmcs_ws/src/rmcs_core/src/controller/wheelleg/
├── wheelleg_trajectory_controller.cpp  # 轨迹规划 + 外环
├── wheelleg_balance_lqr.cpp           # Pitch LQR
├── wheelleg_yaw_lqr.cpp               # Yaw LQR  
├── wheelleg_wheel_mixer.cpp           # 轮混控器
└── wheelleg_drive_bridge.cpp          # 执行器接口
```

**输出**：
- `docs/controller_architecture.md` - 控制架构文档
- `docs/tunable_parameters.json` - 可调参数列表（含默认值、范围、物理意义）

---

#### 任务 0.2：Isaac Sim 环境集成
- [ ] 在 `isaac_wheeled_rl_train` 中创建传统控制器接口
- [ ] 加载 `纯底盘_v7_flat_base107` 模型
- [ ] 应用已辨识的轮子参数（`v6_wheel_response_evidence_v1.json`）
- [ ] 实现控制器的 Python/C++ 绑定

**实现路径**：
```python
# src/wheeled_tasks/chassis/traditional_controller.py
class WheelLegTraditionalController:
    def __init__(self, params: dict):
        self.lqr_balance = BalanceLQR(params['balance_gains'])
        self.lqr_yaw = YawLQR(params['yaw_gains'])
        self.outer_loop = OuterSpeedLoop(params['outer_gains'])
        self.mixer = WheelMixer()
    
    def compute_torque(self, obs: dict) -> np.ndarray:
        # 1. 外环：速度跟踪 -> 加速度指令
        a_cmd = self.outer_loop.step(obs)
        
        # 2. 平衡环：pitch LQR -> 共模轮力矩
        tau_common = self.lqr_balance.step(obs, a_cmd)
        
        # 3. 偏航环：yaw LQR -> 差速轮力矩
        tau_diff = self.lqr_yaw.step(obs)
        
        # 4. 腿姿态规划 -> 关节目标
        joint_targets = self.plan_leg_posture(obs, a_cmd)
        
        # 5. 混控器：优先级分配
        tau_left, tau_right = self.mixer.mix(tau_common, tau_diff)
        
        return [*joint_targets, tau_left, tau_right]
```

**验证标准**：
- 控制器在仿真中能稳定站立 10 秒（无跟踪指令）
- 前进速度阶跃响应时间 < 2 秒
- 无振荡或极限环

---

#### 任务 0.3：评估指标设计
- [ ] 定义多目标优化的权重
- [ ] 实现自动化评估管线

**评估指标**：
```python
class PerformanceMetrics:
    def __init__(self):
        self.survival_time = 0.0          # 存活时间 (s)
        self.velocity_mae = 0.0           # 速度跟踪误差 (m/s)
        self.yaw_rate_mae = 0.0           # 角速度跟踪误差 (rad/s)
        self.pitch_std = 0.0              # Pitch 稳定性 (rad)
        self.energy = 0.0                 # 能耗 (J)
        self.torque_smoothness = 0.0      # 力矩平滑度
    
    def compute_reward(self) -> float:
        # 多目标加权求和
        return (
            + 1.0 * self.survival_time
            - 10.0 * self.velocity_mae
            - 5.0 * self.yaw_rate_mae
            - 2.0 * self.pitch_std
            - 0.01 * self.energy
            - 100.0 * (1 if self.fell else 0)
        )
```

**测试场景**：
1. **站立保持**：无指令，保持 20 秒
2. **速度跟踪**：阶跃 0 → 0.5 m/s，保持 10 秒
3. **速度反向**：0.5 → -0.5 m/s
4. **原地转向**：1 rad/s 角速度
5. **混合运动**：前进 + 转向
6. **鲁棒性测试**：质量扰动 ±20%，摩擦系数 0.5-1.2

---

### 阶段 1：贝叶斯优化单参数调优（预估 2-3 周）

#### 任务 1.1：参数空间设计
- [ ] 选择最关键的 10-15 个参数
- [ ] 设置合理的搜索范围（基于物理约束和经验值）

**参数优先级**：
```python
# 高优先级（最影响性能）
HIGH_PRIORITY = {
    'lqr_gain_theta': (-30, -5),         # Pitch LQR - θ
    'lqr_gain_thetadot': (-10, -1),      # Pitch LQR - θ̇
    'lqr_gain_v': (-5, -1),              # Pitch LQR - v
    'lqr_yaw_gain_psi': (-15, -5),       # Yaw LQR - ψ
    'lqr_yaw_gain_psidot': (-8, -2),     # Yaw LQR - ψ̇
}

# 中优先级
MEDIUM_PRIORITY = {
    'outer_kv': (0, 10),                 # 速度外环增益
    'outer_kx': (0, 5),                  # 位置外环增益
    'roll_kp': (0, 5),                   # Roll PD - Kp
    'roll_kd': (0, 2),                   # Roll PD - Kd
    'leg_motion_coupling': (0, 0.1),     # 腿长-速度耦合
}

# 低优先级（微调用）
LOW_PRIORITY = {
    'startup_settle_s': (0, 1.0),        # 启动稳定时间
    'posture_gate_enabled': [True, False],
    'command_accel_limit': (0.5, 3.0),
    'command_jerk_limit': (1.0, 10.0),
}
```

---

#### 任务 1.2：贝叶斯优化实现
- [ ] 使用 Optuna/BoTorch 实现多目标优化
- [ ] 设置并行评估（多进程/多 GPU）
- [ ] 实现中间结果保存和恢复

**实现框架**：
```python
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner

def objective(trial):
    # 1. 采样参数
    params = {
        'lqr_gain_theta': trial.suggest_float('lqr_gain_theta', -30, -5),
        'lqr_gain_thetadot': trial.suggest_float('lqr_gain_thetadot', -10, -1),
        'lqr_gain_v': trial.suggest_float('lqr_gain_v', -5, -1),
        'lqr_yaw_gain_psi': trial.suggest_float('lqr_yaw_gain_psi', -15, -5),
        'lqr_yaw_gain_psidot': trial.suggest_float('lqr_yaw_gain_psidot', -8, -2),
        'outer_kv': trial.suggest_float('outer_kv', 0, 10),
        'outer_kx': trial.suggest_float('outer_kx', 0, 5),
    }
    
    # 2. 在 Isaac Sim 中评估
    controller = WheelLegTraditionalController(params)
    metrics = evaluate_controller(
        controller=controller,
        scenarios=['stand', 'forward', 'rotate', 'mixed'],
        num_envs=64,
        episode_length=20.0,
    )
    
    # 3. 早停检查（如果太差直接剪枝）
    if metrics.survival_time < 5.0:
        raise optuna.TrialPruned()
    
    # 4. 返回多目标
    return (
        metrics.compute_reward(),        # 主目标：综合奖励
        -metrics.velocity_mae,           # 次目标 1：跟踪误差
        metrics.survival_time,           # 次目标 2：存活时间
    )

# 创建多目标优化研究
study = optuna.create_study(
    study_name='wheelleg_controller_tuning',
    storage='sqlite:///results/optuna.db',  # 持久化
    directions=['maximize', 'minimize', 'maximize'],
    sampler=TPESampler(n_startup_trials=20),
    pruner=MedianPruner(n_startup_trials=10, n_warmup_steps=5),
)

# 运行优化（200 次评估约需 2-4 小时，取决于硬件）
study.optimize(objective, n_trials=200, n_jobs=4)

# 导出结果
best_trial = study.best_trials[0]
best_params = best_trial.params
print(f"最优参数: {best_params}")
print(f"最优性能: reward={best_trial.values[0]:.3f}, mae={-best_trial.values[1]:.4f}")
```

---

#### 任务 1.3：结果分析与验证
- [ ] Pareto 前沿可视化
- [ ] 参数敏感性分析（哪些参数最关键）
- [ ] 在测试集上验证泛化性能

**分析工具**：
```python
# Pareto 前沿
optuna.visualization.plot_pareto_front(study)

# 参数重要性
optuna.visualization.plot_param_importances(study)

# 优化历史
optuna.visualization.plot_optimization_history(study)

# 参数关系
optuna.visualization.plot_slice(study, params=['lqr_gain_theta', 'outer_kv'])
```

**验证流程**：
1. 在训练场景中验证（应该表现最好）
2. 在未见过的场景中测试（速度/转向组合、地形变化）
3. 鲁棒性测试（质量 ±30%，摩擦 ±50%）
4. 对比优化前后的性能提升

---

### 阶段 2：增益调度学习（预估 3-4 周，可选）

#### 任务 2.1：状态依赖增益策略
- [ ] 设计增益调度网络
- [ ] 用 RL（PPO）学习策略
- [ ] 对比固定增益 vs 自适应增益

**架构设计**：
```python
class GainSchedulingPolicy(nn.Module):
    def __init__(self, obs_dim=30, gain_dim=7):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(obs_dim, 256),
            nn.ELU(),
            nn.Linear(256, 128),
            nn.ELU(),
            nn.Linear(128, gain_dim),
        )
        
        # 初始化为接近零，这样初始策略 ≈ 固定增益
        nn.init.orthogonal_(self.mlp[-1].weight, gain=0.01)
    
    def forward(self, obs, nominal_gains):
        # 输出增益调整量 Δg
        delta_gains = self.mlp(obs)
        
        # 限制调整幅度（避免爆炸）
        delta_gains = torch.tanh(delta_gains) * 0.3 * nominal_gains
        
        return nominal_gains + delta_gains
```

**观测空间设计**（增益调度需要的额外信息）：
```python
obs = [
    # 基础状态（已有）
    *base_velocity,           # 3D
    *base_angular_velocity,   # 3D
    *projected_gravity,       # 3D
    *joint_positions,         # 6D
    *joint_velocities,        # 6D
    *last_action,             # 6D
    
    # 增益调度额外需要
    *command,                 # 3D (v_x, v_y, ω_z)
    tracking_error_v,         # 1D
    tracking_error_omega,     # 1D
    terrain_roughness,        # 1D (可选)
    load_estimation,          # 1D (可选)
]
```

**训练配置**：
```python
ppo_config = {
    'num_envs': 512,
    'num_steps_per_env': 96,
    'num_learning_epochs': 5,
    'learning_rate': 3e-4,
    'gamma': 0.99,
    'lam': 0.95,
    'entropy_coef': 0.01,
    'max_grad_norm': 1.0,
}

# 奖励设计（强调平滑和保守）
reward = (
    + 1.0 * survival_bonus
    - 5.0 * velocity_tracking_error
    - 2.0 * yaw_tracking_error
    - 0.1 * gain_change_penalty     # 惩罚增益剧烈变化
    - 0.01 * energy
)
```

---

#### 任务 2.2：性能对比实验
- [ ] 固定增益（贝叶斯优化结果）
- [ ] 增益调度（RL 学习）
- [ ] 在不同场景/扰动下的鲁棒性对比

**对比维度**：
| 场景 | 固定增益 | 增益调度 | 提升 |
|------|----------|----------|------|
| 标准站立 | ✓ | ✓ | - |
| 速度跟踪 | ✓ | ✓✓ | +15% |
| 急转弯 | ✓ | ✓✓ | +20% |
| 负载变化 | ✓ | ✓✓✓ | +35% |
| 低摩擦地面 | ✓ | ✓✓✓ | +40% |

---

### 阶段 3：混合控制架构（预估 2-3 周，可选）

#### 任务 3.1：残差力矩学习
- [ ] 保留传统控制器作为基线
- [ ] 用 RL 学习残差修正

**架构**：
```python
class HybridController:
    def __init__(self, traditional_controller, residual_policy):
        self.trad = traditional_controller
        self.policy = residual_policy
        self.alpha = 0.3  # 残差权重
    
    def compute_torque(self, obs):
        # 1. 传统控制器输出
        tau_base = self.trad.compute_torque(obs)
        
        # 2. RL 残差修正
        tau_residual = self.policy(obs)
        
        # 3. 混合输出（带安全限幅）
        tau_final = tau_base + self.alpha * tau_residual
        tau_final = torch.clamp(tau_final, -effort_limit, effort_limit)
        
        return tau_final
```

**优势**：
- 保留传统控制器的稳定性和可解释性
- RL 只需学习小的修正量，样本效率高
- 可以平滑调整 `alpha` 来权衡安全性和性能

---

## 📁 项目目录结构

```
wheelleg_controller_tuning/
├── AGENTS.md                          # 本文件
├── README.md                          # 项目说明
├── docs/
│   ├── controller_architecture.md     # 控制架构文档
│   ├── tunable_parameters.json        # 参数列表
│   └── literature_review.md           # 相关论文综述
├── src/
│   ├── controller/                    # 传统控制器实现
│   │   ├── balance_lqr.py
│   │   ├── yaw_lqr.py
│   │   ├── outer_loop.py
│   │   ├── wheel_mixer.py
│   │   └── traditional_controller.py
│   ├── optimization/                  # 优化算法
│   │   ├── bayesian_tuning.py
│   │   ├── gain_scheduling.py
│   │   └── hybrid_controller.py
│   ├── evaluation/                    # 评估指标
│   │   ├── metrics.py
│   │   ├── scenarios.py
│   │   └── visualization.py
│   └── utils/
│       ├── isaac_interface.py         # Isaac Sim 接口
│       └── logger.py
├── configs/
│   ├── default_params.yaml            # 默认参数
│   ├── search_space.yaml              # 贝叶斯优化搜索空间
│   └── ppo_config.yaml                # RL 训练配置
├── scripts/
│   ├── 01_extract_controller.sh       # 从 RMCS 提取控制器
│   ├── 02_run_bayesian_opt.py         # 运行贝叶斯优化
│   ├── 03_train_gain_scheduling.py    # 训练增益调度
│   ├── 04_evaluate_comparison.py      # 性能对比
│   └── 05_export_to_rmcs.py           # 导出参数到 RMCS
├── results/
│   ├── optuna.db                      # Optuna 数据库
│   ├── best_params.json               # 最优参数
│   ├── pareto_front.png               # Pareto 前沿图
│   └── comparison_report.pdf          # 性能对比报告
└── tests/
    ├── test_controller.py             # 控制器单元测试
    ├── test_optimization.py           # 优化流程测试
    └── test_isaac_interface.py        # 仿真接口测试
```

---

## 🔧 环境依赖

### Isaac Sim 环境
```bash
# 已有的 RL 训练环境
cd /home/noir/Documents/workspace/isaac_wheeled_rl_train
source venv/bin/activate  # 或你的虚拟环境
```

### 额外依赖
```bash
pip install optuna optuna-dashboard
pip install botorch gpytorch  # 可选：用 BoTorch 替代 Optuna
pip install plotly kaleido    # 可视化
pip install tensorboard       # RL 训练监控
```

---

## 📊 预期成果

### 量化指标
- **速度跟踪误差**：< 0.05 m/s MAE（当前基线待测）
- **角速度跟踪误差**：< 0.1 rad/s MAE
- **稳定性**：Pitch 标准差 < 5°
- **存活率**：> 99% 在标准场景
- **鲁棒性**：质量 ±30%、摩擦 ±50% 扰动下仍稳定

### 交付物
1. **优化后的参数文件**：`best_params.json`（可直接用于 RMCS）
2. **性能对比报告**：优化前后的定量对比
3. **可视化仪表盘**：Optuna Dashboard + TensorBoard
4. **开源代码**：完整的优化管线和评估工具

---

## 🎓 参考文献

### 核心论文
1. **"Learning Robust Perceptive Locomotion for Quadrupedal Robots in the Wild"** (2022)  
   - ANYbotics, CoRL 2022
   - 混合传统控制 + RL 残差的经典案例

2. **"Sample Efficient Optimization for Learning Controllers for Bipedal Locomotion"** (2021)  
   - Berkeley, RSS 2021
   - 贝叶斯优化在双足机器人上的应用

3. **"Bayesian Optimization for Policy Search via Online-Offline Experimentation"** (2019)  
   - Berkeley, ICML 2019
   - 理论基础：高斯过程 + 采集函数

### 方法论参考
4. **Optuna 官方文档**：https://optuna.readthedocs.io/
5. **BoTorch 教程**：https://botorch.org/tutorials/
6. **Isaac Gym 文档**：https://developer.nvidia.com/isaac-gym

---

## 🚀 快速开始

### 第一步：验证环境
```bash
cd /home/noir/Documents/workspace/wheelleg_controller_tuning

# 测试 Isaac Sim 能否加载模型
python scripts/test_isaac_env.py

# 测试传统控制器能否运行
python tests/test_controller.py
```

### 第二步：运行基线评估
```bash
# 用默认参数评估性能（建立基线）
python scripts/evaluate_baseline.py \
    --config configs/default_params.yaml \
    --scenarios stand,forward,rotate \
    --output results/baseline_metrics.json
```

### 第三步：启动优化
```bash
# 贝叶斯优化（推荐先运行这个）
python scripts/02_run_bayesian_opt.py \
    --n-trials 200 \
    --n-jobs 4 \
    --study-name wheelleg_tuning_v1 \
    --storage sqlite:///results/optuna.db

# 实时监控（另一个终端）
optuna-dashboard sqlite:///results/optuna.db --port 8080
```

### 第四步：查看结果
```bash
# 生成报告
python scripts/generate_report.py \
    --study-name wheelleg_tuning_v1 \
    --output results/report_v1.pdf

# 导出最优参数
python scripts/export_best_params.py \
    --study-name wheelleg_tuning_v1 \
    --output results/best_params.json
```

---

## 📝 工作日志

### 2026-10-27
- [x] 创建项目目录
- [x] 编写 AGENTS.md 规划文档
- [ ] 从 wheel_leg_math_clean 提取控制器代码
- [ ] 设计 Isaac Sim 接口

---

## 🤝 协作指南

本项目涉及三个代码库：
1. **RMCS 传统控制器**：`/home/ubuntu/RMCS_` 容器中
2. **Isaac Sim RL 环境**：`/home/noir/Documents/workspace/isaac_wheeled_rl_train`
3. **本优化项目**：`/home/noir/Documents/workspace/wheelleg_controller_tuning`

**开发流程**：
- 控制器代码从 RMCS 提取后，维护在本项目中
- Isaac Sim 接口复用 RL 训练仓库的资产和配置
- 优化结果导出后，可回馈到 RMCS 进行真机验证

---

## ❓ 常见问题

### Q1: 为什么不直接用 RL 训练策略？
A: 传统控制器有明确的物理意义和理论保证，参数少、可解释性强。用自动化方法调参结合了两者优势：
- 保留传统控制的稳定性
- 避免从头训练 RL 的样本低效
- 最终参数可以直接部署到 RMCS，无需 sim2real

### Q2: 优化需要多久？
A: 取决于硬件和并行度：
- 单次评估：10-30 秒（取决于场景复杂度）
- 200 次评估：
  - 单进程：约 1-2 小时
  - 4 进程并行：约 30-60 分钟
  - 增益调度 RL 训练：约 2-4 小时

### Q3: 优化后的参数能直接用到真机吗？
A: 需要真机验证，但风险较低：
1. 轮子参数已经过辨识验证（sim2real gap 小）
2. 传统控制器本身就是物理建模的
3. 优化只是在物理合理范围内搜索

建议：先在仿真中充分测试鲁棒性，再逐步迁移到真机。

### Q4: 如果优化结果不好怎么办？
A: 排查顺序：
1. 检查控制器实现是否正确（对比 RMCS 原版）
2. 检查评估指标设计是否合理
3. 扩大搜索空间或调整先验范围
4. 检查仿真参数是否匹配真机（特别是轮子动力学）

---

## 📧 联系与支持

有问题或建议，请在本项目目录下创建 `TODO.md` 或直接修改本文件。
