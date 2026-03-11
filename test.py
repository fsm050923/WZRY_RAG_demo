from sentence_transformers import SentenceTransformer

model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # 替换为你的实际模型名
try:
    model = SentenceTransformer(model_name, local_files_only=True)
    print("✅ 模型已存在于本地缓存！")
except Exception as e:
    print("❌ 模型不存在于本地缓存：", e)