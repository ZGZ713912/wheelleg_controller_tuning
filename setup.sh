#!/bin/bash
# 快速启动脚本 - 轮腿机器人传统控制器自动调参

set -e

echo "========================================"
echo "Wheel-Leg Controller Auto-Tuning Setup"
echo "========================================"
echo

# 检查是否在正确的目录
if [[ ! -f "AGENTS.md" ]]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# 创建必要的目录
echo "[1/5] Creating directories..."
mkdir -p results logs reference/{code,docs}

# 检查 Python 环境
echo "[2/5] Checking Python environment..."
if ! command -v python &> /dev/null; then
    echo "Error: Python not found. Please install Python 3.8+"
    exit 1
fi

python_version=$(python --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "  Found Python $python_version"

# 安装依赖（可选）
read -p "[3/5] Install Python dependencies? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  Installing optuna, plotly, kaleido..."
    pip install optuna optuna-dashboard plotly kaleido -q
    echo "  ✓ Dependencies installed"
else
    echo "  Skipped. Install manually with:"
    echo "    pip install optuna optuna-dashboard plotly kaleido"
fi

# 提示下一步
echo
echo "[4/5] Next steps:"
echo "  1. Extract controller code from RMCS:"
echo "     # In RMCS container:"
echo "     cd ~/RMCS_"
echo "     git archive --format=tar downstream/wheel_leg_math_clean \\"
echo "       rmcs_ws/src/rmcs_core/src/controller/wheelleg | \\"
echo "       tar -x -C reference/code"
echo
echo "  2. Update default parameters in:"
echo "     configs/default_params.yaml"
echo
echo "  3. Implement Isaac Sim interface in:"
echo "     src/utils/isaac_interface.py"
echo

echo "[5/5] Quick test (placeholder):"
echo "  python src/utils/isaac_interface.py"
echo

echo "========================================"
echo "Setup completed! See TODO.md for tasks."
echo "========================================"
