#!/bin/bash
# TradingAgents-Astock 快速启动脚本
# 作者: Senior Developer (高级开发工程师)

echo "==================================================="
echo "   TradingAgents-Astock 快速启动"
echo "==================================================="

# 检查 Python 版本
echo ""
echo "📌 步骤 1/6: 检查 Python 版本..."
python --version

# 检查是否已配置 .env
echo ""
echo "📌 步骤 2/6: 检查环境配置..."
if [ -f ".env" ]; then
    if grep -q "sk-xxx" .env || grep -q "your_key_here" .env; then
        echo "⚠️  .env 文件包含示例 API Key，请编辑 .env 填入真实的 Key"
        echo "   推荐使用 MiniMax: https://platform.minimaxi.com/"
    else
        echo "✅ .env 文件已配置"
    fi
else
    echo "❌ .env 文件不存在，正在创建..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件，填入真实的 API Key"
fi

# 检查依赖是否正确安装
echo ""
echo "📌 步骤 3/6: 检查依赖安装..."
python -c "import tradingagents; print('✅ tradingagents 已安装')" 2>/dev/null || echo "❌ tradingagents 未安装，请运行: pip install -e ."

# 运行安装验证测试
echo ""
echo "📌 步骤 4/6: 运行安装验证测试..."
python test_installation.py

# 检查 pre-commit 是否安装
echo ""
echo "📌 步骤 5/6: 检查代码质量工具..."
if command -v pre-commit &> /dev/null; then
    echo "✅ pre-commit 已安装"
    if [ -d ".git/hooks" ] && [ -f ".git/hooks/pre-commit" ]; then
        echo "✅ pre-commit hooks 已安装"
    else
        echo "⚠️  pre-commit hooks 未安装，正在安装..."
        python -m pre_commit install 2>/dev/null || echo "请手动运行: python -m pre_commit install"
    fi
else
    echo "⚠️  pre-commit 未安装，请运行: pip install pre-commit"
fi

# 提供下一步指导
echo ""
echo "==================================================="
echo "   下一步操作指南"
echo "==================================================="
echo ""
echo "1️⃣  配置 API Key（必须）:"
echo "   a. 编辑 .env 文件"
echo "   b. 填入真实的 MINIMAX_API_KEY 或 DEEPSEEK_API_KEY"
echo ""
echo "2️⃣  安装 pre-commit hooks（推荐）:"
echo "   python -m pre_commit install"
echo ""
echo "3️⃣  运行代码质量检查（推荐）:"
echo "   pre-commit run --all-files"
echo ""
echo "4️⃣  尝试 CLI:"
echo "   python -m cli.main"
echo ""
echo "5️⃣  启动 Web UI:"
echo "   streamlit run web/app.py"
echo ""
echo "6️⃣  阅读团队技术提升指南:"
echo "   打开 TEAM_GUIDE.md"
echo ""
echo "==================================================="
echo "   技术支持"
echo "==================================================="
echo "如有问题，请联系 Senior Developer (高级开发工程师)"
echo "项目文档: TEAM_GUIDE.md"
echo "安装报告: INSTALL_REPORT.md"
echo "==================================================="
