"""
LLM提供商基类

定义所有LLM提供商的统一接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import time


@dataclass
class LLMResponse:
    """LLM响应数据类"""
    text: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    latency: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """
    LLM提供商基类
    
    所有LLM提供商都应该继承此类并实现相关方法
    """
    
    def __init__(
        self,
        api_key: str,
        model_name: str,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs
    ):
        """
        初始化LLM提供商
        
        Args:
            api_key: API密钥
            model_name: 模型名称
            base_url: API基础URL（可选）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            **kwargs: 其他配置参数
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.extra_config = kwargs
    
    @abstractmethod
    async def acall(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """
        异步调用LLM
        
        Args:
            prompt: 输入提示词
            temperature: 温度参数
            max_tokens: 最大生成token数
            **kwargs: 其他模型参数
            
        Returns:
            LLMResponse: LLM响应
        """
        pass
    
    def call(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """
        同步调用LLM
        
        Args:
            prompt: 输入提示词
            temperature: 温度参数
            max_tokens: 最大生成token数
            **kwargs: 其他模型参数
            
        Returns:
            LLMResponse: LLM响应
        """
        import asyncio
        return asyncio.run(self.acall(prompt, temperature, max_tokens, **kwargs))
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        pass
    
    def _measure_latency(self, func):
        """测量函数执行延迟的装饰器"""
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            latency = time.time() - start_time
            if isinstance(result, LLMResponse):
                result.latency = latency
            return result
        return wrapper
    
    async def _retry_call(self, func, *args, **kwargs):
        """带重试机制的调用"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # 指数退避
                    wait_time = 2 ** attempt
                    print(f"调用失败，{wait_time}秒后重试... (尝试 {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"调用失败，已达到最大重试次数")
        
        raise last_exception
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        if not self.api_key:
            raise ValueError(f"{self.get_provider_name()}: API密钥不能为空")
        if not self.model_name:
            raise ValueError(f"{self.get_provider_name()}: 模型名称不能为空")
        return True


import asyncio

