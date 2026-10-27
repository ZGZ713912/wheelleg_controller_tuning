# 轮腿机器人传统控制器自动调参 - 可调参数列表

本文件定义了 wheel_leg_math_clean 传统控制器中所有可调参数的默认值、搜索范围和物理意义。

---

## 📊 参数分类

### 🔴 高优先级参数（最影响性能）

这些参数直接影响稳定性和跟踪性能，是贝叶斯优化的首要目标。

#### 1. Pitch 平衡 LQR 增益

```yaml
balance_lqr:
  gain_theta:
    default: -17.6
    range: [-30.0, -5.0]
    unit: "Nm/rad"
    description: "Pitch 角度增益，控制机身俯仰稳定性"
    physical_meaning: "值越负，pitch 恢复力越强，但过大会导致振荡"
  
  gain_thetadot:
    default: -3.6
    range: [-10.0, -1.0]
    unit: "Nm/(rad/s)"
    description: "Pitch 角速度增益，提供阻尼"
    physical_meaning: "抑制 pitch 振荡，值越负阻尼越强"
  
  gain_v:
    default: -3.0
    range: [-5.0, -1.0]
    unit: "Nm/(m/s)"
    description: "前向速度增益，用于速度跟踪"
    physical_meaning: "速度偏差产生恢复力矩"
  
  gain_x:
    default: 0.0
    range: [-2.0, 2.0]
    unit: "Nm/m"
    description: "位置增益（当前禁用）"
    physical_meaning: "位置保持，通常关闭以避免漂移积累"
  
  torque_limit:
    default: 4.88
    range: [3.0, 8.0]
    unit: "Nm"
    description: "轮力矩饱和限幅"
    physical_meaning: "防止执行器过载，影响最大加速度"
```

---

#### 2. Yaw 偏航 LQR 增益

```yaml
yaw_lqr:
  gain_psi:
    default: -10.8
    range: [-15.0, -5.0]
    unit: "Nm/rad"
    description: "Yaw 角度增益，控制航向"
    physical_meaning: "航向偏差产生差速力矩"
  
  gain_psidot:
    default: -4.3
    range: [-8.0, -2.0]
    unit: "Nm/(rad/s)"
    description: "Yaw 角速度增益，提供阻尼"
    physical_meaning: "抑制转向振荡"
  
  torque_diff_limit:
    default: 8.0
    range: [4.0, 12.0]
    unit: "Nm"
    description: "差速力矩限幅"
    physical_meaning: "限制最大转向力矩，避免侧翻"
```

---

### 🟡 中优先级参数（微调性能）

#### 3. 速度外环增益

```yaml
outer_speed_loop:
  kv:
    default: 值待从代码提取
    range: [0.0, 10.0]
    unit: "m/s²/(m/s)"
    description: "速度跟踪增益"
    physical_meaning: "速度误差 -> 目标加速度，值越大响应越快"
  
  kx:
    default: 值待从代码提取
    range: [0.0, 5.0]
    unit: "m/s²/m"
    description: "位置跟踪增益"
    physical_meaning: "位置误差 -> 目标加速度，通常较小"
  
  command_accel_limit:
    default: 值待从代码提取
    range: [0.5, 3.0]
    unit: "m/s²"
    description: "加速度限制"
    physical_meaning: "限制最大加减速，影响响应速度"
  
  command_jerk_limit:
    default: 值待从代码提取
    range: [1.0, 10.0]
    unit: "m/s³"
    description: "加加速度（jerk）限制"
    physical_meaning: "S曲线规划的平滑度，越小越平滑"
```

---

#### 4. Roll 侧倾控制（当前禁用）

```yaml
roll_control:
  kp:
    default: 0.0
    range: [0.0, 5.0]
    unit: "rad/rad"
    description: "Roll 比例增益"
    physical_meaning: "侧倾误差 -> 曲柄差动，值为 0 表示关闭"
  
  kd:
    default: 0.0
    range: [0.0, 2.0]
    unit: "rad/(rad/s)"
    description: "Roll 微分增益"
    physical_meaning: "侧倾角速度阻尼"
  
  roll_bias_ff:
    default: 1.06
    range: [0.5, 1.5]
    unit: "dimensionless"
    description: "计划侧倾前馈系数"
    physical_meaning: "bank 指令的前馈缩放因子"
```

---

#### 5. 腿姿态规划

```yaml
leg_posture:
  nominal_leg_length:
    default: 0.305
    range: [0.25, 0.40]
    unit: "m"
    description: "标称腿长"
    physical_meaning: "站立时的默认腿长，影响稳定性和能耗"
  
  leg_motion_coupling:
    default: 值待从代码提取
    range: [0.0, 0.1]
    unit: "m/(m/s)"
    description: "腿长-速度耦合系数"
    physical_meaning: "前进时缩腿，v * coupling -> ΔL"
  
  posture_gate_enabled:
    default: false
    type: bool
    description: "转向时是否软化步态"
    physical_meaning: "转向时降低姿态调整幅度"
  
  posture_yaw_scale:
    default: 值待从代码提取
    range: [0.5, 2.0]
    unit: "rad/s"
    description: "转向软化尺度"
    physical_meaning: "yaw_rate / scale 决定软化程度"
```

---

### 🟢 低优先级参数（边缘情况）

#### 6. 启动和过渡

```yaml
startup:
  settle_time:
    default: 值待从代码提取
    range: [0.0, 1.0]
    unit: "s"
    description: "启动稳定时间"
    physical_meaning: "使能后保持当前姿态的时间，避免初始冲击"

trajectory_transition:
  pitch_transition_time:
    default: 0.15
    range: [0.05, 0.5]
    unit: "s"
    description: "Pitch 过渡时间"
    physical_meaning: "Pitch 五次多项式过渡的时长"
  
  shank_knee_transition_time:
    default: 1.5  # 仿真中为 4.0
    range: [0.5, 4.0]
    unit: "s"
    description: "小腿/膝盖过渡时间"
    physical_meaning: "姿态变化的时长，越长越平滑"
```

---

#### 7. 恢复模式（Recovery）

```yaml
recovery:
  blend_enabled:
    default: true
    type: bool
    description: "是否启用平衡/恢复混合"
    physical_meaning: "倒地后使用外部恢复姿态"
  
  default_recovery_alpha:
    default: 1.0
    range: [0.0, 1.0]
    unit: "dimensionless"
    description: "默认恢复混合系数"
    physical_meaning: "1=平衡模式, 0=恢复模式"
```

---

## 🎯 贝叶斯优化推荐配置

### Phase 1: 核心稳定性（5 参数）
```yaml
core_stability:
  - balance_lqr.gain_theta
  - balance_lqr.gain_thetadot
  - balance_lqr.gain_v
  - yaw_lqr.gain_psi
  - yaw_lqr.gain_psidot
```

### Phase 2: 扩展优化（+5 参数）
```yaml
extended:
  - outer_speed_loop.kv
  - outer_speed_loop.kx
  - leg_posture.leg_motion_coupling
  - balance_lqr.torque_limit
  - yaw_lqr.torque_diff_limit
```

### Phase 3: 全参数精调（+5 参数）
```yaml
full:
  - leg_posture.nominal_leg_length
  - outer_speed_loop.command_accel_limit
  - outer_speed_loop.command_jerk_limit
  - startup.settle_time
  - trajectory_transition.shank_knee_transition_time
```

---

## 📝 参数来源

| 参数组 | 源文件 | 行号范围 |
|--------|--------|----------|
| Balance LQR | `wheelleg_balance_lqr.cpp` | 待确认 |
| Yaw LQR | `wheelleg_yaw_lqr.cpp` | 待确认 |
| 外环增益 | `wheelleg_trajectory_controller.cpp` | 待确认 |
| 腿姿态 | `wheelleg_trajectory_controller.cpp` | 待确认 |
| Roll PD | `wheelleg_trajectory_controller.cpp` | 待确认 |

---

## 🔄 参数更新记录

- **2026-10-27**: 初始版本，基于代码审查和文档分析
- **待更新**: 从实际代码提取确切默认值

---

## ⚠️ 注意事项

1. **物理约束**：
   - LQR 增益必须为负（恢复力方向）
   - 力矩限幅不能超过电机额定值
   - 腿长范围受机械限位约束 [0.22, 0.45] m

2. **稳定性考虑**：
   - 增益过大会导致振荡或极限环
   - 限幅过小会导致响应不足
   - 过渡时间过短会引起冲击

3. **优化顺序**：
   - 先优化平衡增益（最关键）
   - 再优化外环（速度跟踪）
   - 最后微调边缘参数
