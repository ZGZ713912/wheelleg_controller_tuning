# 轮腿机器人传统控制器自动调参 - 待办事项

## 🚧 当前阶段：阶段 0 - 环境准备与代码移植

---

## ✅ 已完成

- [x] 项目规划和目录结构设计 (2026-10-27)
- [x] 编写 AGENTS.md 详细开发计划
- [x] 创建 README.md 项目说明
- [x] 定义可调参数列表 (`docs/tunable_parameters.md`)
- [x] 实现 Isaac Sim 接口框架 (`src/utils/isaac_interface.py`)
- [x] 实现贝叶斯优化脚本框架 (`scripts/02_run_bayesian_opt.py`)

---

## 📋 待办任务

### 阶段 0.1: 梳理传统控制器架构 (优先级: 🔴 高)

- [ ] **任务 0.1.1**: 从 RMCS 容器提取 wheel_leg_math_clean 分支代码
  ```bash
  # 在容器中
  cd ~/RMCS_
  git archive --format=tar downstream/wheel_leg_math_clean rmcs_ws/src/rmcs_core/src/controller/wheelleg | \
    tar -x -C /tmp/wheelleg_export
  
  # 复制到宿主机
  docker cp <container>:/tmp/wheelleg_export ~/Documents/workspace/wheelleg_controller_tuning/reference/
  ```

- [ ] **任务 0.1.2**: 识别所有可调参数的**确切默认值**
  - 从以下文件提取：
    - `wheelleg_balance_lqr.cpp` - Balance LQR 增益
    - `wheelleg_yaw_lqr.cpp` - Yaw LQR 增益
    - `wheelleg_trajectory_controller.cpp` - 外环增益、腿姿态参数
    - `wheelleg_wheel_mixer.cpp` - 混控器限幅
  - 更新 `docs/tunable_parameters.md` 中的 default 值

- [ ] **任务 0.1.3**: 绘制控制架构图
  - 工具：draw.io / Mermaid / PlantUML
  - 内容：
    - 数据流：命令 → 各层控制器 → 执行器
    - 控制频率：哪些是 200Hz，哪些是 50Hz
    - 优先级分配：轮混控器的逻辑
  - 输出：`docs/controller_architecture.png` + 说明文档

---

### 阶段 0.2: Isaac Sim 环境集成 (优先级: 🔴 高)

- [ ] **任务 0.2.1**: 理解 isaac_wheeled_rl_train 的资产加载流程
  - 阅读 `src/wheeled_tasks/chassis/*.py`
  - 找到车体加载、物理参数设置的入口
  - 识别轮子参数应用位置（`actuator_response.py`）

- [ ] **任务 0.2.2**: 实现 `TraditionalControllerEnv` 的完整功能
  - 加载 `纯底盘_v7_flat_base107` URDF
  - 应用 `v6_wheel_response_evidence_v1.json` 的参数：
    - `armature`: [0.0, 0.0, 0.00387, 0.0, 0.0, 0.00382]
    - `frictionloss`: [0.0, 0.0, 0.0495, 0.0, 0.0, 0.0696]
    - `damping`: [0.0, 0.0, 0.00061, 0.0, 0.0, 0.00034]
  - 实现 `_get_observations()` 读取真实状态
  - 实现 `_check_termination()` 判断摔倒条件

- [ ] **任务 0.2.3**: 实现 `TraditionalController` 的核心逻辑
  - **S-curve 速度规划**：
    ```python
    accel_ref += clamp(a_des - accel_ref, -jerk*dt, jerk*dt)
    velocity_ref += accel_ref * dt
    ```
  - **外环**：速度跟踪 → 目标加速度
    ```python
    a_outer = outer_kv * (v_cmd - v_meas) + outer_kx * (x_ref - x_meas)
    a_cmd = a_planned + a_outer
    ```
  - **Balance LQR**：
    ```python
    tau_common = clamp(
        g_θ*theta + g_θ̇*thetadot + g_v*v + g_x*x,
        -torque_limit, torque_limit
    )
    ```
  - **Yaw LQR**：
    ```python
    tau_diff = clamp(
        g_ψ*(psi - psi_cmd) + g_ψ̇*psidot,
        -torque_diff_limit, torque_diff_limit
    )
    ```
  - **轮混控器**：优先级分配
    ```python
    common = clamp(tau_common, -L, L)
    headroom = L - abs(common)
    diff = clamp(tau_diff, -headroom, headroom)
    tau_left = common + diff
    tau_right = common - diff
    ```
  - **腿姿态规划**：五连杆逆运动学（可先用简化版）

- [ ] **任务 0.2.4**: 单元测试
  - 测试场景 1：站立保持 10 秒
  - 测试场景 2：速度阶跃 0 → 0.5 m/s
  - 测试场景 3：原地转向
  - 验证标准：无振荡、无摔倒、跟踪误差合理

---

### 阶段 0.3: 评估指标设计 (优先级: 🟡 中)

- [ ] **任务 0.3.1**: 实现 `PerformanceMetrics` 的计算逻辑
  - `survival_time`: 记录直到摔倒或超时的时间
  - `velocity_mae`: 计算速度跟踪的平均绝对误差
  - `yaw_rate_mae`: 角速度跟踪误差
  - `pitch_std`: Pitch 角的标准差（稳定性指标）
  - `energy`: 累积力矩 × 角速度的积分
  - `fell`: 检测条件（pitch > 45°, roll > 30°, height < 0.15m）

- [ ] **任务 0.3.2**: 设计测试场景库
  - `stand_230mm`: 站立在最低腿长
  - `stand_305mm`: 站立在标称腿长
  - `stand_430mm`: 站立在最高腿长
  - `forward_05`: 前进 0.5 m/s
  - `backward_05`: 后退 0.5 m/s
  - `rotate_1`: 原地转向 1 rad/s
  - `mixed`: 前进 + 转向组合
  - `ramp`: 速度斜坡 0 → 1 m/s

- [ ] **任务 0.3.3**: 实现鲁棒性测试
  - 质量扰动：base ±20%, leg ±10%, wheel ±10%
  - 摩擦系数：0.5 ~ 1.2（随机）
  - CoM 偏移：±3 cm
  - 初始状态扰动：pitch ±10°, height ±5 cm

---

## 🎯 里程碑

### Milestone 0: 环境就绪 (预计完成: 2026-11-10)
- [x] 项目框架搭建
- [ ] 控制器代码移植完成
- [ ] Isaac Sim 环境能运行传统控制器
- [ ] 基线性能测试通过

### Milestone 1: 优化完成 (预计完成: 2026-11-24)
- [ ] 贝叶斯优化收敛（200 trials）
- [ ] 性能提升 > 20%
- [ ] Pareto 前沿分析完成

### Milestone 2: 交付 (预计完成: 2026-12-01)
- [ ] 最优参数导出到 RMCS 格式
- [ ] 性能对比报告生成
- [ ] （可选）增益调度学习完成

---

## 🐛 已知问题

### 问题列表
1. **wheel_leg_math_clean 代码访问**：需要在 RMCS 容器中提取
2. **Isaac Sim 接口**：当前是 placeholder，需要对接实际 API
3. **五连杆运动学**：复杂度高，可能需要先用简化模型验证流程

---

## 💡 优化想法

### 性能优化
- [ ] 使用 GPU 并行评估多个参数组合
- [ ] 实现检查点保存/恢复（长时间优化容错）
- [ ] 早停机制：前 5 秒就摔倒的 trial 直接剪枝

### 工具改进
- [ ] 实时可视化：TensorBoard 集成
- [ ] 参数敏感性分析：哪些参数最关键
- [ ] 自动生成优化报告（PDF/HTML）

---

## 📝 日志

### 2026-10-27
- 创建项目目录和文档
- 完成框架代码（placeholder）
- 下一步：从 RMCS 提取控制器源码

---

## 🤝 需要帮助的地方

如果遇到以下问题，请记录在此：
1. Isaac Sim API 不熟悉 → 查阅 `isaac_wheeled_rl_train` 的已有代码
2. 五连杆运动学太复杂 → 先用简化的腿长-关节映射
3. 优化不收敛 → 检查搜索空间、调整 TPE 参数
4. 真机验证需求 → 联系 RMCS 团队

---

更新本文件时请保持格式清晰，标记完成的任务为 `[x]`。
