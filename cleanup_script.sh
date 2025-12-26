#!/bin/bash
# VisualSketchpad 清理脚本
# 生成时间: 2025-12-26

set -e  # 遇到错误时退出

echo "======================================"
echo "🧹 VisualSketchpad 清理脚本"
echo "======================================"
echo ""

cd "$(dirname "$0")"

# 询问用户确认
echo "此脚本将删除以下内容:"
echo "  - 调试文档 (6 个)"
echo "  - 调试脚本 (8 个)"
echo "  - 日志文件 (5+ 个)"
echo "  - 临时文件"
echo "  - 测试输出目录"
echo ""
read -p "是否继续? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 1
fi

echo ""
echo "🗑️  开始清理..."
echo ""

# 1. 删除调试文档
echo "📄 删除调试文档..."
rm -f agent/CHANGES_SUMMARY.md
rm -f agent/DEBUGGING_TOOLS_README.md
rm -f agent/DEBUG_VISION_TOOLS.md
rm -f agent/NEXT_STEPS.md
rm -f agent/QUICK_DEBUG_GUIDE.md
rm -f agent/WHAT_CHANGED.md
echo "   ✅ 完成"

# 2. 删除调试脚本
echo "🔧 删除调试脚本..."
rm -f agent/debug_server_response.py
rm -f agent/run_diagnosis.py
rm -f agent/test_json_structure.py
rm -f agent/test_server_json.py
rm -f agent/test_vision_tools.py
rm -f agent/tools_with_error_handling.py
echo "   ✅ 完成"

# 3. 删除日志文件
echo "📋 删除日志文件..."
rm -f agent/jupyter_gateway.log*
rm -f agent/run.log
rm -f agent/run_example1.log
rm -f agent/run_mmsb_all.log
rm -f run.log
rm -f formatted_output.txt
echo "   ✅ 完成"

# 4. 删除临时文件
echo "🖼️  删除临时文件..."
rm -f agent/temp_image.png
echo "   ✅ 完成"

# 5. 删除测试输出
echo "📁 删除测试输出目录..."
rm -rf agent/output/
echo "   ✅ 完成"

# 6. 删除输出中的临时图片
echo "🖼️  删除输出中的临时图片..."
rm -f outputs/blink_spatial/val_Spatial_Relation_1/*.png 2>/dev/null || true
rm -f outputs/geometry/2079/*.png 2>/dev/null || true
rm -f outputs/graph_max_flow/5/*.png 2>/dev/null || true
echo "   ✅ 完成"

# 7. 删除测试输出目录
echo "📁 删除测试任务输出..."
rm -rf outputs/mm-safetybench/ 2>/dev/null || true
rm -rf outputs/mmsb-tasks/ 2>/dev/null || true
rm -rf outputs/test_geo/ 2>/dev/null || true
echo "   ✅ 完成"

echo ""
echo "======================================"
echo "✅ 清理完成!"
echo "======================================"
echo ""
echo "统计信息:"
echo "  - 已删除: ~22 个文件"
echo "  - 已删除: ~4 个目录"
echo ""
echo "⚠️  注意: 以下文件需要手动处理:"
echo "  - agent/config.py (包含 API key，需要清理)"
echo "  - agent/tools.py (已简化，如需恢复: git restore agent/tools.py)"
echo "  - agent/batch_process.py (确认后可删除)"
echo "  - agent/convert_jsonl_to_tasks.py (确认后可删除)"
echo "  - agent/run_mmsb_tasks.py (确认后可删除)"
echo ""
echo "下一步建议:"
echo "  1. 查看 GIT_CHANGES_REPORT.md 了解详细改动"
echo "  2. 运行 git status 查看剩余改动"
echo "  3. 编辑 agent/config.py 移除 API key"
echo "  4. 决定是否恢复 agent/tools.py"
echo ""

