import os

# 基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_PATH = os.path.join(BASE_DIR, "王者知识库")
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "faiss_index")

# 检索参数
TOP_K = 5               # 最终返回文档数
HYDE_K = 20             # HyDE 召回候选数
INITIAL_K = 30          # 重排序初始候选数
THRESHOLD = 0.5         # 重排序相关性阈值（低于此值则返回空）

# 模型配置
EMBEDDING_MODEL = "BAAI/bge-m3"
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
LLM_MODEL = "deepseek-chat"
TEMPERATURE = 0.3
MAX_TOKENS = 200

# API密钥（从环境变量读取，更安全）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-f7f5376ccbe04050b657309a9eccab15")

# Hugging Face 镜像
HF_ENDPOINT = "https://hf-mirror.com"