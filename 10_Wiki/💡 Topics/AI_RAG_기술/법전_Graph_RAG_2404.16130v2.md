---
id: 51436e12-e5ff-4ba8-a78f-17e4372b6873
category: "[[10_Wiki/💡 Topics/AI_RAG_기술]]"
confidence_score: 0.95
tags: ["법전", "RAG"]
last_reinforced: 2026-05-31
github_commit: "813246f85716400fdd2d832ce1d7618ea8d6e2b9"
---

# [[법전_Graph_RAG_2404.16130v2]]

## 📌 한 줄 포착 (The Karpathy Summary)
> From Local to Global: A GraphRAG Approach to Query-Focused Summarization

## 📊 구조화된 지식 (Synthesized Content)
- From Local to Global: A GraphRAG Approach to Query-Focused Summarization
- Darren Edge, Ha Trinh, Newman Cheng, Joshua Bradley, Alex Chao, Apurva Mody, Steven Truitt, Dasha Metropolitansky, Robert Osazuwa Ness, Jonathan Larson — Microsoft Research
- Abstract: The use of retrieval-augmented generation (RAG) to retrieve relevant information from an external knowledge source enables large language models (LLMs) to answer questions over private and/or previously unseen document collections. However, RAG fails on global questions directed at an entire text corpus, such as "What are the main themes in the dataset?" since this is inherently a query-focused summarization (QFS) task, rather than an explicit retrieval task.
- Prior QFS methods, meanwhile, fail to scale to the quantities of text indexed by typical RAG systems. To combine the strengths of these contrasting methods, we propose a Graph RAG approach to question answering over private text corpora that scales with both the generality of user questions and the quantity of source text to be indexed.
- GraphRAG Key Concepts:
- Community detection: Leiden algorithm applied to knowledge graph to detect node communities at multiple granularity levels
- Graph indexing: LLM-derived knowledge graph entities and relationships, summaries, and community reports
- Global search: Map-reduce approach using community summaries for global questions

## 🔗 지식 연결망 (Knowledge Connections)
- **Related Topics:** [[법전_마스터]]
- **Projects/Contexts:** 없음
- **Contradictions/Notes:** 없음

updated: 2026-05-31
