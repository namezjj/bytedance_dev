"""
配置测试脚本

用于验证Doubao和DeepSeek的配置是否正确
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv


def check_env_vars():
    """检查环境变量配置"""
    print("="*80)
    print("检查环境变量配置")
    print("="*80)
    
    # 加载.env文件
    env_path = project_root / ".env"
    if not env_path.exists():
        print(f"❌ .env文件不存在: {env_path}")
        print("请创建.env文件并配置必要的环境变量")
        return False
    
    load_dotenv(env_path)
    print(f"✓ .env文件加载成功: {env_path}\n")
    
    # 必需的环境变量
    required_vars = {
        "Doubao配置": [
            "DOUBAO_API_KEY",
            "DOUBAO_MODEL_NAME"
        ],
        "DeepSeek配置": [
            "DEEPSEEK_API_KEY",
            "DEEPSEEK_MODEL_NAME"
        ],
        "评估器配置": [
            "EVALUATOR_PROVIDER",
            "EVALUATOR_MODEL_NAME",
            "EVALUATOR_API_KEY"
        ],
        "被评估模型配置": [
            "EVALUATED_PROVIDER",
            "EVALUATED_MODEL_NAME",
            "EVALUATED_API_KEY"
        ]
    }
    
    all_ok = True
    
    for category, vars_list in required_vars.items():
        print(f"{category}:")
        for var in vars_list:
            value = os.getenv(var)
            if value:
                # 隐藏API密钥的大部分内容
                if "API_KEY" in var:
                    display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                else:
                    display_value = value
                print(f"  ✓ {var}: {display_value}")
            else:
                print(f"  ❌ {var}: 未设置")
                all_ok = False
        print()
    
    return all_ok


def check_project_structure():
    """检查项目结构"""
    print("="*80)
    print("检查项目结构")
    print("="*80)
    
    required_paths = {
        "核心模块": [
            "core/llm_providers/__init__.py",
            "core/llm_providers/base_provider.py",
            "core/llm_providers/doubao_provider.py",
            "core/llm_providers/deepseek_provider.py",
            "core/llm_providers/provider_factory.py"
        ],
        "配置文件": [
            "config/evaluation_config.py",
            "config/model_configs/doubao_config.json",
            "config/model_configs/deepseek_config.json"
        ],
        "示例文件": [
            "examples/doubao_deepseek_evaluation.py"
        ],
        "文档": [
            "docs/QUICKSTART_DOUBAO_DEEPSEEK.md"
        ]
    }
    
    all_ok = True
    
    for category, paths in required_paths.items():
        print(f"{category}:")
        for path in paths:
            full_path = project_root / path
            if full_path.exists():
                print(f"  ✓ {path}")
            else:
                print(f"  ❌ {path} (不存在)")
                all_ok = False
        print()
    
    return all_ok


def check_dependencies():
    """检查依赖安装"""
    print("="*80)
    print("检查依赖包")
    print("="*80)
    
    required_packages = [
        "aiohttp",
        "dotenv",
        "asyncio"
    ]
    
    all_ok = True
    
    for package in required_packages:
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ❌ {package} (未安装)")
            all_ok = False
    
    print()
    
    if not all_ok:
        print("请运行以下命令安装依赖:")
        print("  pip install -r requirements.txt")
        print()
    
    return all_ok


def test_imports():
    """测试模块导入"""
    print("="*80)
    print("测试模块导入")
    print("="*80)
    
    all_ok = True
    
    try:
        from core.llm_providers import (
            BaseLLMProvider,
            LLMResponse,
            DoubaoProvider,
            DeepSeekProvider,
            LLMProviderFactory
        )
        print("  ✓ core.llm_providers 导入成功")
    except Exception as e:
        print(f"  ❌ core.llm_providers 导入失败: {e}")
        all_ok = False
    
    try:
        from config.evaluation_config import (
            EvaluationConfig,
            ConfigManager,
            ModelProvider
        )
        print("  ✓ config.evaluation_config 导入成功")
    except Exception as e:
        print(f"  ❌ config.evaluation_config 导入失败: {e}")
        all_ok = False
    
    print()
    return all_ok


def show_usage_example():
    """显示使用示例"""
    print("="*80)
    print("快速开始示例")
    print("="*80)
    print("""
要开始使用，请运行以下命令：

1. 测试基本功能：
   python examples/doubao_deepseek_evaluation.py

2. 在Python代码中使用：
   
   import asyncio
   from core.llm_providers import LLMProviderFactory
   
   async def main():
       # 创建评估器（Doubao）
       evaluator = LLMProviderFactory.create_evaluator_llm()
       
       # 创建被评估模型（DeepSeek）
       evaluated = LLMProviderFactory.create_evaluated_llm()
       
       # 使用
       response = await evaluated.acall("你好")
       print(response.text)
   
   asyncio.run(main())

3. 查看完整文档：
   docs/QUICKSTART_DOUBAO_DEEPSEEK.md
""")


def main():
    """主函数"""
    print("\n🚀 Doubao + DeepSeek 配置检查工具\n")
    
    results = []
    
    # 1. 检查项目结构
    results.append(("项目结构", check_project_structure()))
    
    # 2. 检查依赖
    results.append(("依赖包", check_dependencies()))
    
    # 3. 检查环境变量
    results.append(("环境变量", check_env_vars()))
    
    # 4. 测试导入
    results.append(("模块导入", test_imports()))
    
    # 显示总结
    print("="*80)
    print("检查总结")
    print("="*80)
    
    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    
    if all_passed:
        print("🎉 所有检查通过！系统配置正确。")
        show_usage_example()
    else:
        print("⚠️  部分检查失败，请根据上述提示修复问题。")
        print("\n常见问题解决：")
        print("1. 如果依赖包缺失: pip install -r requirements.txt")
        print("2. 如果环境变量未设置: 编辑 .env 文件")
        print("3. 如果文件缺失: 确保所有文件都已创建")
    
    print("\n" + "="*80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

