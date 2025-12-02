"""
LLM提供商工厂

统一管理和创建各种LLM提供商实例
"""

import os
from typing import Optional, Dict, Any
from .base_provider import BaseLLMProvider
from .doubao_provider import DoubaoProvider
from .deepseek_provider import DeepSeekProvider


class LLMProviderFactory:
    """
    LLM提供商工厂类
    
    负责根据配置创建合适的LLM提供商实例
    """
    
    # 注册的提供商类
    _providers = {
        "doubao": DoubaoProvider,
        "deepseek": DeepSeekProvider,
    }
    
    @classmethod
    def create(
        cls,
        provider_name: str,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """
        创建LLM提供商实例
        
        Args:
            provider_name: 提供商名称 (doubao, deepseek等)
            api_key: API密钥（可选，默认从环境变量读取）
            model_name: 模型名称（可选，默认从环境变量读取）
            base_url: API基础URL（可选）
            **kwargs: 其他配置参数
            
        Returns:
            BaseLLMProvider: LLM提供商实例
            
        Raises:
            ValueError: 不支持的提供商名称
        """
        provider_name = provider_name.lower()
        
        if provider_name not in cls._providers:
            raise ValueError(
                f"不支持的LLM提供商: {provider_name}. "
                f"支持的提供商: {', '.join(cls._providers.keys())}"
            )
        
        # 从环境变量读取配置（如果未提供）
        if api_key is None:
            api_key = cls._get_api_key_from_env(provider_name)
        
        if model_name is None:
            model_name = cls._get_model_name_from_env(provider_name)
        
        if base_url is None:
            base_url = cls._get_base_url_from_env(provider_name)
        
        # 创建提供商实例
        provider_class = cls._providers[provider_name]
        return provider_class(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            **kwargs
        )
    
    @classmethod
    def create_evaluator_llm(cls, **kwargs) -> BaseLLMProvider:
        """
        创建评估器LLM（裁判LLM）
        
        从环境变量EVALUATOR_PROVIDER等读取配置
        
        Returns:
            BaseLLMProvider: 评估器LLM实例
        """
        provider = os.getenv("EVALUATOR_PROVIDER", "doubao")
        api_key = os.getenv("EVALUATOR_API_KEY")
        model_name = os.getenv("EVALUATOR_MODEL_NAME")
        
        return cls.create(
            provider_name=provider,
            api_key=api_key,
            model_name=model_name,
            **kwargs
        )
    
    @classmethod
    def create_evaluated_llm(cls, **kwargs) -> BaseLLMProvider:
        """
        创建被评估LLM（参评LLM）
        
        从环境变量EVALUATED_PROVIDER等读取配置
        
        Returns:
            BaseLLMProvider: 被评估LLM实例
        """
        provider = os.getenv("EVALUATED_PROVIDER", "deepseek")
        api_key = os.getenv("EVALUATED_API_KEY")
        model_name = os.getenv("EVALUATED_MODEL_NAME")
        
        return cls.create(
            provider_name=provider,
            api_key=api_key,
            model_name=model_name,
            **kwargs
        )
    
    @classmethod
    def _get_api_key_from_env(cls, provider_name: str) -> str:
        """从环境变量获取API密钥"""
        env_var_map = {
            "doubao": "DOUBAO_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }
        
        env_var = env_var_map.get(provider_name)
        if not env_var:
            raise ValueError(f"未知的提供商: {provider_name}")
        
        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(
                f"未找到{provider_name}的API密钥。请设置环境变量: {env_var}"
            )
        
        return api_key
    
    @classmethod
    def _get_model_name_from_env(cls, provider_name: str) -> str:
        """从环境变量获取模型名称"""
        env_var_map = {
            "doubao": "DOUBAO_MODEL_NAME",
            "deepseek": "DEEPSEEK_MODEL_NAME",
        }
        
        env_var = env_var_map.get(provider_name)
        if not env_var:
            raise ValueError(f"未知的提供商: {provider_name}")
        
        model_name = os.getenv(env_var)
        if not model_name:
            # 使用默认模型名称
            default_models = {
                "doubao": "ep-20250614210935-8mthr",
                "deepseek": "deepseek-chat",
            }
            model_name = default_models.get(provider_name)
        
        return model_name
    
    @classmethod
    def _get_base_url_from_env(cls, provider_name: str) -> Optional[str]:
        """从环境变量获取基础URL"""
        env_var_map = {
            "doubao": "DOUBAO_BASE_URL",
            "deepseek": "DEEPSEEK_BASE_URL",
        }
        
        env_var = env_var_map.get(provider_name)
        if env_var:
            return os.getenv(env_var)
        
        return None
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """
        注册新的LLM提供商
        
        Args:
            name: 提供商名称
            provider_class: 提供商类（必须继承BaseLLMProvider）
        """
        if not issubclass(provider_class, BaseLLMProvider):
            raise ValueError(
                f"提供商类必须继承BaseLLMProvider"
            )
        
        cls._providers[name.lower()] = provider_class
    
    @classmethod
    def list_providers(cls) -> list:
        """
        列出所有已注册的提供商
        
        Returns:
            list: 提供商名称列表
        """
        return list(cls._providers.keys())

