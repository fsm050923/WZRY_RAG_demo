import os
import torch
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from config import KNOWLEDGE_PATH, EMBEDDING_MODEL, HF_ENDPOINT, FAISS_INDEX_PATH

# 设置 Hugging Face 镜像（必须最先设置）
os.environ['HF_ENDPOINT'] = HF_ENDPOINT

def load_and_split_documents(chunk_size=500, chunk_overlap=0):
    """加载知识库文档并按装备块分割"""
    loader = DirectoryLoader(
        KNOWLEDGE_PATH,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'}
    )
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        separators=[
            "\n--------------------------------------------------\n",  # 装备分隔符
            "\n\n",
            "\n",
            "。", "！", "？", "；",
            " ",
            ""
        ],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(documents)
    return chunks

def load_or_create_vectorstore(chunks):
    """
    如果存在本地索引文件则加载，否则创建并保存。
    返回 (vectorstore, embedding_model)
    """
    # 自动选择设备：有 GPU 用 cuda，否则用 cpu
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    embedding = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': device},
        encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
    )
    # 检查索引文件是否存在（而不是仅检查目录）
    index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
    if os.path.exists(index_file):
        print(f"加载本地索引: {FAISS_INDEX_PATH}")
        vectorstore = FAISS.load_local(
            FAISS_INDEX_PATH,
            embedding,
            allow_dangerous_deserialization=True
        )
    else:
        print("创建新索引...")
        vectorstore = FAISS.from_documents(chunks, embedding)
        # 确保保存目录存在
        os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
        print(f"保存索引到: {FAISS_INDEX_PATH}")
        vectorstore.save_local(FAISS_INDEX_PATH)

    return vectorstore, embedding