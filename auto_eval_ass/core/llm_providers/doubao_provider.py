"""
Doubao (豆包) LLM提供商

火山引擎豆包大模型接入实现
"""

import json
import aiohttp
from typing import Optional, Dict, Any
from .base_provider import BaseLLMProvider, LLMResponse


class DoubaoProvider(BaseLLMProvider):
    """
    Doubao LLM提供商
    
    支持火山引擎豆包大模型的调用
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
        初始化Doubao提供商
        
        Args:
            api_key: 火山引擎API密钥
            model_name: 模型endpoint ID (例如: ep-20250614210935-8mthr)
            base_url: API基础URL（可选，默认使用火山引擎地址）
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        if base_url is None:
            base_url = "https://ark.cn-beijing.volces.com/api/v3"
        
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
        return "doubao"
    
    async def acall(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """
        异步调用Doubao模型
        
        Args:
            prompt: 输入提示词
            temperature: 温度参数 (0.0-1.0)
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
            
            # 构建请求数据
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
            if "stream" in kwargs:
                data["stream"] = kwargs["stream"]
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Doubao API调用失败 (状态码: {response.status}): {error_text}"
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
                            "request_id": result.get("id")
                        }
                    )
        
        # 使用重试机制调用
        return await self._retry_call(_call)
    
    def validate_config(self) -> bool:
        """验证配置"""
        super().validate_config()
        
        # 验证模型名称格式（应该是endpoint ID）
        if not self.model_name.startswith("ep-"):
            print(f"警告: Doubao模型名称 '{self.model_name}' 不是标准的endpoint ID格式 (ep-xxxxx)")
        
        return True

