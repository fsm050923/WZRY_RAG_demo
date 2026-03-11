import torch
import logging
from typing import List, Optional, Any
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from pydantic import Field
from sentence_transformers import CrossEncoder
from config import THRESHOLD

logger = logging.getLogger(__name__)

class HyDERetriever(BaseRetriever):
    """
    Hypothetical Document Embeddings 检索器。
    先用大语言模型生成假设性回答，再用该回答检索。
    """
    llm: Any = Field(description="大语言模型实例")
    vectorstore: Any = Field(description="向量库")
    base_retriever: Any = Field(description="基础检索器")
    base_kwargs: Optional[dict] = Field(default=None)

    def __init__(self, llm, vectorstore, base_kwargs=None, **kwargs):
        base = vectorstore.as_retriever(**(base_kwargs or {}))
        super().__init__(llm=llm, vectorstore=vectorstore, base_retriever=base, base_kwargs=base_kwargs, **kwargs)

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        hyde_prompt = f"请根据问题生成一段假设性回答（只输出内容）：\n问题：{query}\n假设回答："
        try:
            hyp = self.llm.invoke(hyde_prompt)
            hyp = hyp.content if hasattr(hyp, 'content') else hyp
        except Exception as e:
            logger.warning(f"HyDE 生成失败，回退到原始查询: {e}")
            hyp = query
        run_manager.on_text(f"HyDE 假设回答：\n{hyp}\n", color="yellow")
        return self.base_retriever.invoke(hyp)


class RerankRetriever(BaseRetriever):
    """
    带重排序和阈值过滤的检索器。
    先用基础检索器召回候选文档，然后用交叉编码器重排序，
    最后根据阈值过滤，返回前 final_k 个文档。
    """
    base: Any = Field(description="基础检索器")
    reranker: Any = Field(description="重排序模型")
    initial_k: int = Field(default=20)   # 此参数仅用于说明，实际由基础检索器控制
    final_k: int = Field(default=5)

    def __init__(self, base, model_name="BAAI/bge-reranker-v2-m3", initial_k=20, final_k=5, **kwargs):
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        reranker = CrossEncoder(model_name, device=device)
        super().__init__(base=base, reranker=reranker, initial_k=initial_k, final_k=final_k, **kwargs)

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        candidates = self.base.invoke(query) or []
        if not candidates:
            return []

        # 构造 (query, doc) 对并计算分数
        pairs = [(query, doc.page_content) for doc in candidates]
        scores = list(self.reranker.predict(pairs))

        # 按分数降序排序
        scored = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)

        # 阈值过滤：如果最高分低于阈值，返回空列表
        if scored and scored[0][1] < THRESHOLD:
            return []

        # 返回前 final_k 个文档
        return [doc for doc, _ in scored[:self.final_k]]