import streamlit as st
import os
import re
from langchain_classic.retrievers import BM25Retriever, EnsembleRetriever
from langchain_classic.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from config import (
    KNOWLEDGE_PATH, TOP_K, HYDE_K, INITIAL_K,
    DEEPSEEK_API_KEY, LLM_MODEL, TEMPERATURE, MAX_TOKENS, HF_ENDPOINT
)
from utils import load_and_split_documents, load_or_create_vectorstore
from retrievers import HyDERetriever, RerankRetriever

# 设置 Hugging Face 镜像
os.environ['HF_ENDPOINT'] = HF_ENDPOINT

st.set_page_config(page_title="王者荣耀知识问答", page_icon="🎮", layout="wide")
st.title("🎮 王者荣耀知识问答机器人")
st.markdown("基于装备数据的智能问答助手，可回答装备属性、效果等问题。")

if "qa_chain" not in st.session_state:
    with st.spinner("加载知识库和模型中..."):
        # 1. 加载并分割文档
        chunks = load_and_split_documents()

        # 2. 创建或加载向量库
        vectorstore, embed_model = load_or_create_vectorstore(chunks)

        # 3. 创建混合检索器（BM25 + 向量）
        bm25 = BM25Retriever.from_documents(chunks)
        bm25.k = TOP_K
        vector_retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
        ensemble = EnsembleRetriever(retrievers=[bm25, vector_retriever], weights=[0.3, 0.7])

        # 4. 配置 DeepSeek API
        if not DEEPSEEK_API_KEY:
            st.error("请设置环境变量 DEEPSEEK_API_KEY")
            st.stop()
        llm = ChatOpenAI(
            openai_api_key=DEEPSEEK_API_KEY,
            openai_api_base="https://api.deepseek.com/v1",
            model=LLM_MODEL,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )

        # 5. HyDE 检索器
        hyde = HyDERetriever(llm=llm, vectorstore=vectorstore, base_kwargs={"search_kwargs": {"k": HYDE_K}})

        # 6. 重排序检索器
        rerank = RerankRetriever(base=hyde, initial_k=INITIAL_K, final_k=TOP_K)

        # 7. 提示模板
        prompt = PromptTemplate.from_template("""你是一名王者荣耀装备专家，基于以下信息回答问题，若不知道则说不知道。

信息：
{context}

问题：{question}
回答：""")

        # 8. 构建问答链
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=rerank,
            return_source_documents=True,
            verbose=False,
            chain_type_kwargs={"prompt": prompt}
        )
        st.session_state.qa_chain = qa_chain

# ========== 聊天界面 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if query := st.chat_input("输入你的问题"):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            result = st.session_state.qa_chain.invoke({"query": query})
            answer = result['result']

            if src := result.get('source_documents'):
                answer += "\n\n📚 **参考资料**："
                for i, doc in enumerate(src[:TOP_K]):
                    name_match = re.search(r'【装备名称】(.*?)(\n|$)', doc.page_content)
                    if name_match:
                        preview = name_match.group(1).strip()
                    else:
                        preview = doc.page_content[:60].replace('\n', ' ') + "..."
                    answer += f"\n{i+1}. {preview}"
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})