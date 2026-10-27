"""
贝叶斯优化 - 自动调参传统控制器

使用 Optuna 进行多目标优化，搜索最优的 LQR/PID 增益。
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner
import argparse
import json
from datetime import datetime

from utils.isaac_interface import (
    TraditionalController,
    TraditionalControllerEnv,
    ControllerParams,
    evaluate_controller,
)


def objective(trial: optuna.Trial) -> tuple:
    """
    Optuna 目标函数
    
    Args:
        trial: Optuna trial 对象
    
    Returns:
        (reward, -velocity_mae, survival_time): 三个优化目标
    """
    # 1. 采样参数
    params_dict = {
        # Balance LQR (高优先级)
        'lqr_gain_theta': trial.suggest_float('lqr_gain_theta', -30.0, -5.0),
        'lqr_gain_thetadot': trial.suggest_float('lqr_gain_thetadot', -10.0, -1.0),
        'lqr_gain_v': trial.suggest_float('lqr_gain_v', -5.0, -1.0),
        
        # Yaw LQR
        'yaw_gain_psi': trial.suggest_float('yaw_gain_psi', -15.0, -5.0),
        'yaw_gain_psidot': trial.suggest_float('yaw_gain_psidot', -8.0, -2.0),
        
        # Outer loop (中优先级)
        'outer_kv': trial.suggest_float('outer_kv', 0.0, 10.0),
        'outer_kx': trial.suggest_float('outer_kx', 0.0, 5.0),
        
        # Limits
        'lqr_torque_limit': trial.suggest_float('lqr_torque_limit', 3.0, 8.0),
        'yaw_torque_diff_limit': trial.suggest_float('yaw_torque_diff_limit', 4.0, 12.0),
        
        # Leg posture (低优先级)
        'leg_motion_coupling': trial.suggest_float('leg_motion_coupling', 0.0, 0.1),
    }
    
    params = ControllerParams.from_dict(params_dict)
    
    # 2. 创建环境和控制器
    env = TraditionalControllerEnv(
        num_envs=64,
        episode_length_s=20.0,
    )
    controller = TraditionalController(params)
    
    # 3. 评估性能
    try:
        metrics = evaluate_controller(
            controller=controller,
            env=env,
            scenarios=['stand', 'forward', 'rotate', 'mixed'],
            num_episodes=3,
        )
    except Exception as e:
        print(f"[ERROR] Trial {trial.number} failed: {e}")
        env.close()
        raise optuna.TrialPruned()
    
    env.close()
    
    # 4. 早停检查
    if metrics.survival_time < 5.0 or metrics.fell:
        print(f"[PRUNE] Trial {trial.number}: survival={metrics.survival_time:.1f}s, fell={metrics.fell}")
        raise optuna.TrialPruned()
    
    # 5. 返回多目标
    reward = metrics.compute_reward()
    velocity_mae = metrics.velocity_mae
    survival_time = metrics.survival_time
    
    # 记录中间结果
    trial.set_user_attr("velocity_mae", velocity_mae)
    trial.set_user_attr("yaw_rate_mae", metrics.yaw_rate_mae)
    trial.set_user_attr("pitch_std", metrics.pitch_std)
    trial.set_user_attr("energy", metrics.energy)
    trial.set_user_attr("fell", metrics.fell)
    
    print(f"[Trial {trial.number}] reward={reward:.2f}, mae={velocity_mae:.4f}, time={survival_time:.1f}s")
    
    return reward, -velocity_mae, survival_time


def run_optimization(args):
    """运行贝叶斯优化"""
    
    print("=" * 70)
    print("Bayesian Optimization for Wheel-Leg Traditional Controller")
    print("=" * 70)
    print(f"Study name: {args.study_name}")
    print(f"Trials: {args.n_trials}")
    print(f"Parallel jobs: {args.n_jobs}")
    print(f"Storage: {args.storage}")
    print()
    
    # 创建 Optuna study
    study = optuna.create_study(
        study_name=args.study_name,
        storage=args.storage,
        load_if_exists=True,  # 允许恢复之前的优化
        directions=['maximize', 'minimize', 'maximize'],  # [reward, -mae, survival_time]
        sampler=TPESampler(
            n_startup_trials=args.n_startup_trials,
            multivariate=True,
            seed=42,
        ),
        pruner=MedianPruner(
            n_startup_trials=10,
            n_warmup_steps=5,
        ),
    )
    
    # 运行优化
    study.optimize(
        objective,
        n_trials=args.n_trials,
        n_jobs=args.n_jobs,
        show_progress_bar=True,
    )
    
    # 输出结果
    print("\n" + "=" * 70)
    print("Optimization Completed!")
    print("=" * 70)
    
    print(f"\nTotal trials: {len(study.trials)}")
    print(f"Completed trials: {len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])}")
    print(f"Pruned trials: {len([t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED])}")
    
    # 最优 trial
    if study.best_trials:
        best_trial = study.best_trials[0]
        print(f"\nBest trial (#{best_trial.number}):")
        print(f"  Reward: {best_trial.values[0]:.3f}")
        print(f"  Velocity MAE: {-best_trial.values[1]:.4f} m/s")
        print(f"  Survival time: {best_trial.values[2]:.1f} s")
        print(f"\nBest parameters:")
        for key, value in best_trial.params.items():
            print(f"  {key}: {value:.4f}")
        
        # 保存最优参数
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        best_params_file = output_dir / f"{args.study_name}_best_params.json"
        with open(best_params_file, 'w') as f:
            json.dump({
                'trial_number': best_trial.number,
                'timestamp': datetime.now().isoformat(),
                'objectives': {
                    'reward': best_trial.values[0],
                    'velocity_mae': -best_trial.values[1],
                    'survival_time': best_trial.values[2],
                },
                'parameters': best_trial.params,
                'user_attrs': best_trial.user_attrs,
            }, f, indent=2)
        
        print(f"\nBest parameters saved to: {best_params_file}")
    
    # 保存 Pareto 前沿
    if len(study.best_trials) > 1:
        print(f"\nPareto front: {len(study.best_trials)} non-dominated trials")
    
    print(f"\nVisualize results with:")
    print(f"  optuna-dashboard {args.storage}")
    print(f"or access programmatically:")
    print(f"  study = optuna.load_study(study_name='{args.study_name}', storage='{args.storage}')")


def main():
    parser = argparse.ArgumentParser(description='Bayesian optimization for traditional controller')
    
    # Optimization settings
    parser.add_argument('--study-name', type=str, default='wheelleg_tuning_v1',
                        help='Optuna study name')
    parser.add_argument('--n-trials', type=int, default=200,
                        help='Number of optimization trials')
    parser.add_argument('--n-jobs', type=int, default=1,
                        help='Number of parallel jobs (use with caution for GPU)')
    parser.add_argument('--n-startup-trials', type=int, default=20,
                        help='Number of random startup trials before TPE')
    
    # Storage
    parser.add_argument('--storage', type=str, default='sqlite:///results/optuna.db',
                        help='Optuna storage URL')
    parser.add_argument('--output-dir', type=str, default='results',
                        help='Output directory for results')
    
    args = parser.parse_args()
    
    run_optimization(args)


if __name__ == '__main__':
    main()
