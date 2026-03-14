"""LLM服务模块"""

from src.llm import AgentsLLM
# from src.config import get_settings

# 全局LLM实例
_llm_instance = None


def get_llm(        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None) -> AgentsLLM:
    """
    获取LLM实例(单例模式)
    
    Returns:
        AgentsLLM实例
    """
    global _llm_instance
    
    if _llm_instance is None:
        # settings = get_settings()
        
        # AgentsLLM会自动从环境变量读取配置
        # 包括OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL等
        _llm_instance = AgentsLLM( model = model,
        api_key = api_key,
        base_url = base_url)
        
        print(f"✅ LLM服务初始化成功")
        # print(f"   提供商: {_llm_instance.provider}")
        print(f"   模型: {_llm_instance.model}")
    
    return _llm_instance


def reset_llm():
    """重置LLM实例(用于测试或重新配置)"""
    global _llm_instance
    _llm_instance = None

