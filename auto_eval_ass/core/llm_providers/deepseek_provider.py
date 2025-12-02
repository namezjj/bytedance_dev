"""
DeepSeek LLM提供商

DeepSeek大模型接入实现
"""

import json
import aiohttp
from typing import Optional, Dict, Any
from .base_provider import BaseLLMProvider, LLMResponse


class DeepSeekProvider(BaseLLMProvider):
    """
    DeepSeek LLM提供商
    
    支持DeepSeek大模型的调用
    """
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "deepseek-chat",
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs
    ):
        """
        初始化DeepSeek提供商
        
        Args:
            api_key: DeepSeek API密钥
            model_name: 模型名称 (默认: deepseek-chat)
            base_url: API基础URL（可选）
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        if base_url is None:
            base_url = "https://api.deepseek.com"
        
        super().__init__(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs
        )
        
        self.validate_config()
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "deepseek"
    
    async def acall(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """
        异步调用DeepSeek模型
        
        Args:
            prompt: 输入提示词
            temperature: 温度参数 (0.0-2.0)
            max_tokens: 最大生成token数
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 模型响应
        """
        
        async def _call():
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 构建请求数据（兼容OpenAI格式）
            data = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # 添加其他可选参数
            if "top_p" in kwargs:
                data["top_p"] = kwargs["top_p"]
            if "frequency_penalty" in kwargs:
                data["frequency_penalty"] = kwargs["frequency_penalty"]
            if "presence_penalty" in kwargs:
                data["presence_penalty"] = kwargs["presence_penalty"]
            if "stream" in kwargs:
                data["stream"] = kwargs["stream"]
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"DeepSeek API调用失败 (状态码: {response.status}): {error_text}"
                        )
                    
                    result = await response.json()
                    
                    # 解析响应
                    text = result["choices"][0]["message"]["content"]
                    usage = result.get("usage", {})
                    
                    return LLMResponse(
                        text=text,
                        model=self.model_name,
                        provider=self.get_provider_name(),
                        usage={
                            "prompt_tokens": usage.get("prompt_tokens", 0),
                            "completion_tokens": usage.get("completion_tokens", 0),
                            "total_tokens": usage.get("total_tokens", 0)
                        },
                        metadata={
                            "finish_reason": result["choices"][0].get("finish_reason"),
                            "request_id": result.get("id"),
                            "system_fingerprint": result.get("system_fingerprint")
                        }
                    )
        
        # 使用重试机制调用
        return await self._retry_call(_call)
    
    def validate_config(self) -> bool:
        """验证配置"""
        super().validate_config()
        
        # DeepSeek支持的模型列表
        supported_models = [
            "deepseek-chat",
            "deepseek-coder",
            "deepseek-reasoner"
        ]
        
        if self.model_name not in supported_models:
            print(f"警告: 模型 '{self.model_name}' 可能不被DeepSeek官方支持")
            print(f"支持的模型: {', '.join(supported_models)}")
        
        return True

