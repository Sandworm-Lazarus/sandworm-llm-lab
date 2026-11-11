# Start here: LLM Lab

[Home](../README.md) · [Tools](../TOOLS.md) · [Sources](../SOURCES.md)

Select a task, inspect the complete pinned package, then try a bounded synthetic fixture. These are reading paths and prototype ideas, not tested integrations.

## Choose a serving runtime

| Project | ใช้ทำอะไร | Evidence to collect |
| --- | --- | --- |
| [Ollama](https://github.com/ollama/ollama/tree/8a89b76cc7359805e48357ba7e5b99e845a4c211) | จัดการและเรียกโมเดลผ่าน local runtime และ REST API | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [llama.cpp](https://github.com/ggml-org/llama.cpp/tree/f3b407ca1bfeeecebf9e9ef19fcd6eed565bd70a) | รัน LLM/VLM และ quantized models บน hardware หลายชนิด | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [vLLM](https://github.com/vllm-project/vllm/tree/bafa5c6c30b8397e64fb6a73740b9ebe71a18f05) | ให้บริการโมเดลด้วย batching, KV cache และ API server | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [SGLang](https://github.com/sgl-project/sglang/tree/5fbfcc7170235064125d23feac4b64e5dbe41414) | วาง inference serving สำหรับ LLM, multimodal และ agentic workloads | Version, configuration, one task result, failure behavior and data/permission boundaries |

## Build retrieval

| Project | ใช้ทำอะไร | Evidence to collect |
| --- | --- | --- |
| [LlamaIndex](https://github.com/run-llama/llama_index/tree/18088d8f070c9212ac4a941b13f759bf417e3031) | ประกอบ ingestion, retrieval และ agentic document workflows | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [RAGFlow](https://github.com/infiniflow/ragflow/tree/5268b33a39a948931ea285a7fce8ec50461f359b) | จัด document ingestion, retrieval และ agentic context workflows | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [Qdrant](https://github.com/qdrant/qdrant/tree/222b2e44ab1c3f17e8246396ead6558e45041df7) | เก็บและค้น vectors พร้อม payload filters เพื่อ semantic retrieval | Version, configuration, one task result, failure behavior and data/permission boundaries |

## Evaluate and observe

| Project | ใช้ทำอะไร | Evidence to collect |
| --- | --- | --- |
| [Langfuse](https://github.com/langfuse/langfuse/tree/47a70342f1736561dfa157a654d011aac29db79d) | เก็บ traces, prompt versions, datasets และ Agent evaluations | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [Phoenix](https://github.com/Arize-ai/phoenix/tree/7fa410bda0483fa1e1c694f8bc11501fea2960b9) | วิเคราะห์ LLM traces, retrieval evals, datasets และ experiments | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [DeepEval](https://github.com/confident-ai/deepeval/tree/0ca198b4640277100efc28b5a862a0170d449c91) | เขียน eval สำหรับ outputs, RAG และ Agent/tool trajectories | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [Ragas](https://github.com/vibrantlabsai/ragas/tree/298b68274234c060deacab3cf5fb52aa3a20e885) | วัดคุณภาพ LLM/RAG และสร้าง test sets จากข้อมูลตัวอย่าง | Version, configuration, one task result, failure behavior and data/permission boundaries |

## Train and route models

| Project | ใช้ทำอะไร | Evidence to collect |
| --- | --- | --- |
| [Unsloth](https://github.com/unslothai/unsloth/tree/1f68ed5ea316969676fef6b988a5bc81f504eb37) | รันและ fine-tune โมเดลด้วย core package และ optional UI/workflows | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [LlamaFactory](https://github.com/hiyouga/LlamaFactory/tree/42b2a546a339b514fd8b88d63959be8fbe297485) | จัด fine-tuning ผ่าน CLI/Web UI พร้อม configs และ datasets | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [LiteLLM](https://github.com/BerriAI/litellm/tree/3616014548d40020f508566620c5cd8745721f3c) | รวม model providers ผ่าน SDK/proxy พร้อม cost/routing controls | Version, configuration, one task result, failure behavior and data/permission boundaries |

## Integrate an application

| Project | ใช้ทำอะไร | Evidence to collect |
| --- | --- | --- |
| [Vercel AI SDK](https://github.com/vercel/ai/tree/70e45d5878494be4b66e325187f865951025059e) | ต่อ text/streaming, structured outputs, tools และ UI สำหรับแอป TypeScript | Version, configuration, one task result, failure behavior and data/permission boundaries |

## Skill starting points

| Entry | Task | Review |
| --- | --- | --- |
| [llm-obs](https://github.com/elastic/agent-skills/blob/09d879dfe23436684e11391a5e5a74a2aedd6b04/skills/observability/llm-obs/SKILL.md) | สืบเหตุ latency, errors, token spend และสายการเรียก tool จาก telemetry | entry-reviewed |
| [huggingface-local-models](https://github.com/huggingface/skills/blob/25910b3d0ba31a2ba102f901cdc9e008c278a69c/skills/huggingface-local-models/SKILL.md) | ค้น GGUF, เลือก quant และตั้ง local serving ด้วย llama.cpp | entry-reviewed |
| [huggingface-llm-trainer](https://github.com/huggingface/skills/blob/25910b3d0ba31a2ba102f901cdc9e008c278a69c/skills/huggingface-llm-trainer/SKILL.md) | วาง training/fine-tuning ด้วย TRL หรือ Unsloth บน HF Jobs | entry-reviewed |
