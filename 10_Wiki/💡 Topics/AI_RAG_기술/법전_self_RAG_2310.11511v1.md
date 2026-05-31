---
id: 2a5cf50b-4c01-4d3f-b257-a38d5e1d3577
category: "[[10_Wiki/💡 Topics/AI_RAG_기술]]"
confidence_score: 0.95
tags: ["법전", "RAG"]
last_reinforced: 2026-05-31
github_commit: "813246f85716400fdd2d832ce1d7618ea8d6e2b9"
---

# [[법전_self_RAG_2310.11511v1]]

## 📌 한 줄 포착 (The Karpathy Summary)
> SELF-RAG: LEARNING TO RETRIEVE, GENERATE, AND CRITIQUE THROUGH SELF-REFLECTION

## 📊 구조화된 지식 (Synthesized Content)
- SELF-RAG: LEARNING TO RETRIEVE, GENERATE, AND CRITIQUE THROUGH SELF-REFLECTION
- Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, Hannaneh Hajishirzi — University of Washington, IBM Research AI
- Abstract: Despite their remarkable capabilities, large language models (LLMs) often produce responses containing factual inaccuracies due to their sole reliance on the parametric knowledge they encapsulate. Retrieval-Augmented Generation (RAG), an ad hoc approach that augments LMs with retrieval of relevant knowledge, decreases such issues.
- However, indiscriminately retrieving and incorporating a fixed number of retrieved passages, regardless of whether retrieval is necessary, or passages are relevant, diminishes LM versatility or can lead to unhelpful responses.
- Self-RAG Framework:
- Adaptive retrieval: Retrieves on demand, when retrieval is necessary
- ISREL (Is Relevant): Assesses if retrieved passage is relevant to query
- ISSUP (Is Supported): Evaluates if output is supported by retrieved passage

## 🔗 지식 연결망 (Knowledge Connections)
- **Related Topics:** [[법전_마스터]]
- **Projects/Contexts:** 없음
- **Contradictions/Notes:** 없음

updated: 2026-05-31
