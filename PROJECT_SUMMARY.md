# 项目创建总结

## ✅ 已完成的工作

### 1. 项目规划文档
- **AGENTS.md** - 详细的开发计划（3个阶段，10+任务）
- **README.md** - 项目说明和快速开始指南
- **TODO.md** - 待办事项跟踪
- **docs/tunable_parameters.md** - 可调参数完整列表

### 2. 代码框架
- **src/utils/isaac_interface.py** - Isaac Sim 环境接口（框架）
  - `ControllerParams` - 参数数据类
  - `PerformanceMetrics` - 评估指标
  - `TraditionalControllerEnv` - 环境包装器
  - `TraditionalController` - 控制器实现框架
  - `evaluate_controller()` - 评估函数

- **scripts/02_run_bayesian_opt.py** - 贝叶斯优化脚本
  - 使用 Optuna 进行多目标优化
  - 支持并行评估
  - 自动保存最优参数

### 3. 配置文件
- **configs/default_params.yaml** - 默认控制器参数
- **configs/search_space.yaml** - 贝叶斯优化搜索空间

### 4. 工具脚本
- **setup.sh** - 快速启动脚本

---

## 📁 项目目录结构

```
wheelleg_controller_tuning/
├── AGENTS.md                      # 详细开发计划
├── README.md                      # 项目说明
├── TODO.md                        # 待办事项
├── setup.sh                       # 快速启动脚本
├── configs/                       # 配置文件
│   ├── default_params.yaml        # 默认参数
│   └── search_space.yaml          # 搜索空间
├── docs/                          # 文档
│   └── tunable_parameters.md      # 参数列表
├── src/                           # 源代码
│   ├── controller/                # 控制器实现
│   ├── optimization/              # 优化算法
│   ├── evaluation/                # 评估指标
│   └── utils/
│       └── isaac_interface.py     # Isaac Sim 接口
├── scripts/                       # 执行脚本
│   └── 02_run_bayesian_opt.py     # 贝叶斯优化
├── reference/                     # 参考资料
├── results/                       # 结果输出
└── tests/                         # 单元测试
```

---

## 🎯 下一步行动（优先级排序）

### 立即执行（今天/明天）
1. **提取 RMCS 控制器代码**
   ```bash
   # 在 RMCS 容器中
   cd ~/RMCS_
   git checkout downstream/wheel_leg_math_clean
   
   # 导出代码
   mkdir -p /tmp/wheelleg_export
   cp -r rmcs_ws/src/rmcs_core/src/controller/wheelleg /tmp/wheelleg_export/
   cp -r rmcs_ws/src/rmcs_core/include/rmcs_core/controller/wheelleg /tmp/wheelleg_export/include
   
   # 复制到宿主机（在宿主机执行）
   docker cp <container_name>:/tmp/wheelleg_export ~/Documents/workspace/wheelleg_controller_tuning/reference/code
   ```

2. **从代码中提取确切的默认参数值**
   - 更新 `configs/default_params.yaml`
   - 特别关注：
     - `outer_kv`, `outer_kx` (速度外环增益)
     - `leg_motion_coupling` (腿长-速度耦合)
     - 过渡时间、启动参数

### 本周内完成
3. **实现 Isaac Sim 环境集成**
   - 参考 `isaac_wheeled_rl_train/src/wheeled_tasks/chassis/*.py`
   - 实现 `TraditionalControllerEnv` 的：
     - 模型加载（`纯底盘_v7_flat_base107`）
     - 轮子参数应用
     - 状态观测
     - 终止条件检测

4. **实现传统控制器核心逻辑**
   - Balance LQR
   - Yaw LQR
   - 外环控制
   - 轮混控器
   - 腿姿态规划（可先简化）

5. **基线测试**
   - 站立保持 10 秒
   - 速度跟踪 0 → 0.5 m/s
   - 原地转向

### 两周内完成
6. **运行首次贝叶斯优化**
   ```bash
   python scripts/02_run_bayesian_opt.py \
       --n-trials 50 \
       --n-jobs 2 \
       --study-name wheelleg_pilot
   ```

7. **分析结果**
   - Pareto 前沿可视化
   - 参数敏感性分析
   - 性能提升评估

---

## 📊 预期时间线

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| **阶段 0** | 环境准备与代码移植 | 1-2 周 |
| - 提取代码 | - | 1 天 |
| - Isaac Sim 集成 | - | 3-5 天 |
| - 控制器实现 | - | 5-7 天 |
| - 基线测试 | - | 2 天 |
| **阶段 1** | 贝叶斯优化 | 2-3 周 |
| - 首次优化（50 trials） | - | 1-2 小时 |
| - 完整优化（200 trials） | - | 4-8 小时 |
| - 结果分析 | - | 2-3 天 |
| - 鲁棒性测试 | - | 3-5 天 |
| **阶段 2** | 增益调度（可选） | 3-4 周 |
| **阶段 3** | 混合控制（可选） | 2-3 周 |

---

## 🔑 关键设计决策

### 1. 为什么用贝叶斯优化而不是 RL？
- **样本效率**：200 次评估 vs 数百万步
- **可解释性**：得到明确的参数值
- **Sim2Real**：传统控制器本身就是物理建模的，参数可直接部署

### 2. 为什么分三个阶段？
- **阶段 1（贝叶斯优化）**：快速、可靠、可解释
- **阶段 2（增益调度）**：适应不同场景，但需要更多训练
- **阶段 3（混合控制）**：极致性能，但复杂度高

### 3. 优化目标设计
- **多目标优化**：同时考虑性能、稳定性、能耗
- **Pareto 最优**：给出多个非支配解，用户可根据需求选择

---

## 📚 关键参考资料

### 代码库
1. **RMCS 传统控制器**：`/home/ubuntu/RMCS_/rmcs_ws/src/rmcs_core/src/controller/wheelleg`
2. **Isaac RL 训练环境**：`/home/noir/Documents/workspace/isaac_wheeled_rl_train`
3. **车体模型**：`纯底盘_v7_flat_base107/urdf`
4. **轮子参数**：`contracts/v6_wheel_response_evidence_v1.json`

### 论文
1. Learning Robust Perceptive Locomotion (ANYmal, 2022)
2. Sample Efficient Optimization for Bipedal Locomotion (Berkeley, 2021)
3. Bayesian Optimization for Policy Search (2019)

### 工具
1. Optuna: https://optuna.readthedocs.io/
2. Isaac Gym: https://developer.nvidia.com/isaac-gym
3. BoTorch (可选): https://botorch.org/

---

## ⚠️ 注意事项

1. **GPU 内存管理**
   - 并行评估时注意显存占用
   - 可能需要减少 `num_envs` 或 `n_jobs`

2. **参数约束**
   - LQR 增益必须为负（恢复力方向）
   - 力矩限幅不能超过电机额定值
   - 腿长范围受机械限位约束

3. **安全性**
   - 先在仿真中充分测试
   - 真机验证时从保守参数开始
   - 准备紧急停止机制

---

## 🎉 成果

完成后你将拥有：
1. ✅ **优化后的控制器参数**（可直接用于 RMCS）
2. ✅ **性能对比报告**（优化前后定量对比）
3. ✅ **可视化仪表盘**（Optuna Dashboard + Pareto 前沿）
4. ✅ **完整的优化管线**（可复用于其他机器人）
5. ✅ **（可选）增益调度策略**（适应不同场景）

---

## 📧 需要帮助？

遇到问题时：
1. 查看 `TODO.md` 中的"需要帮助的地方"
2. 查阅 `AGENTS.md` 中的常见问题
3. 在项目目录下创建 `NOTES.md` 记录疑问

---

**项目创建时间**：2026-10-27  
**当前状态**：✅ 框架完成，待实现  
**下一步**：提取 RMCS 控制器代码
