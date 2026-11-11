# Companion tools

[Home](README.md) · [Skill catalog](CATALOG.md) · [Sources and licenses](SOURCES.md)

These are executable tools and frameworks, counted separately from agent skills. Their README/source overviews were inspected; this repository has not installed or run them. Links point to the recorded revision.

**15 tools and frameworks in 7 groups.** See [start here](docs/start-here.md) for task-oriented selections.

| Group | Tools |
| --- | ---: |
| [Local inference](#local-inference) | 4 |
| [RAG & vector search](#rag-vector-search) | 3 |
| [Training & fine-tuning](#training-fine-tuning) | 2 |
| [Observability](#observability) | 2 |
| [Model gateways](#model-gateways) | 1 |
| [AI evaluation](#ai-evaluation) | 2 |
| [AI application SDKs](#ai-application-sdks) | 1 |

<a id="local-inference"></a>

## Local inference

| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |
| --- | --- | --- |
| [Ollama](https://github.com/ollama/ollama/tree/8a89b76cc7359805e48357ba7e5b99e845a4c211) | จัดการและเรียกโมเดลผ่าน local runtime และ REST API | Model artifacts และ CPU/GPU/RAM ที่เหมาะกับโมเดล. เลือก local/cloud backend ให้ชัด; MIT ของ runtime ไม่ใช่สิทธิ์ของ model weights ทุกตัว |
| [llama.cpp](https://github.com/ggml-org/llama.cpp/tree/f3b407ca1bfeeecebf9e9ef19fcd6eed565bd70a) | รัน LLM/VLM และ quantized models บน hardware หลายชนิด | Binary/build backend และ model format ที่รองรับ. เหมาะสำรวจ CPU/GPU hybrid และ GGUF; วัด latency/VRAM กับโมเดลจริง |
| [vLLM](https://github.com/vllm-project/vllm/tree/bafa5c6c30b8397e64fb6a73740b9ebe71a18f05) | ให้บริการโมเดลด้วย batching, KV cache และ API server | Supported model/backend และ hardware/runtime ตามรุ่น. เหมาะเทียบ serving throughput; concurrency และ context มีผลต่อ memory และ latency |
| [SGLang](https://github.com/sgl-project/sglang/tree/5fbfcc7170235064125d23feac4b64e5dbe41414) | วาง inference serving สำหรับ LLM, multimodal และ agentic workloads | Model/backend และ hardware ที่ cookbook รองรับ. ตรวจ engine/model compatibility; ไม่ใช้ตัวเลขเร็วที่สุดจาก marketing เป็นผลทดสอบของคลัง |

<a id="rag-vector-search"></a>

## RAG & vector search

| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |
| --- | --- | --- |
| [LlamaIndex](https://github.com/run-llama/llama_index/tree/18088d8f070c9212ac4a941b13f759bf417e3031) | ประกอบ ingestion, retrieval และ agentic document workflows | Python core/integrations และ model/vector backends. README ระบุ focus ของบริษัทไป LlamaParse; แยก OSS framework จาก hosted parsing products |
| [RAGFlow](https://github.com/infiniflow/ragflow/tree/5268b33a39a948931ea285a7fce8ec50461f359b) | จัด document ingestion, retrieval และ agentic context workflows | Self-hosted service stack และ model/storage backends. ประเมินความต้องการ RAM/storage จาก deployment docs; ไม่อนุมานว่าเหมาะกับ VPS เล็กทุกเครื่อง |
| [Qdrant](https://github.com/qdrant/qdrant/tree/222b2e44ab1c3f17e8246396ead6558e45041df7) | เก็บและค้น vectors พร้อม payload filters เพื่อ semantic retrieval | Qdrant server/embedded option และ embedding model. Quickstart container ไม่ใช่ production security config; แยก auth, exposure และ tenant controls |

<a id="training-fine-tuning"></a>

## Training & fine-tuning

| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |
| --- | --- | --- |
| [Unsloth](https://github.com/unslothai/unsloth/tree/1f68ed5ea316969676fef6b988a5bc81f504eb37) | รันและ fine-tune โมเดลด้วย core package และ optional UI/workflows | Model/dataset และ hardware/runtime ที่รองรับ. README แบ่ง Apache core กับ AGPL optional components; ตรวจ file scope และ model/dataset licenses |
| [LlamaFactory](https://github.com/hiyouga/LlamaFactory/tree/42b2a546a339b514fd8b88d63959be8fbe297485) | จัด fine-tuning ผ่าน CLI/Web UI พร้อม configs และ datasets | Python, supported model และ training hardware/backend. ประเมิน VRAM/compute จาก sequence length และวิธีฝึกจริง; ไม่รับรอง savings ที่ยังไม่วัด |

<a id="observability"></a>

## Observability

| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |
| --- | --- | --- |
| [Langfuse](https://github.com/langfuse/langfuse/tree/47a70342f1736561dfa157a654d011aac29db79d) | เก็บ traces, prompt versions, datasets และ Agent evaluations | SDK instrumentation และ Cloud/self-hosted stack. MIT สำหรับส่วนที่ระบุ; ee directories มีสิทธิ์แยก และ traces อาจมี prompts/ข้อมูลผู้ใช้ |
| [Phoenix](https://github.com/Arize-ai/phoenix/tree/7fa410bda0483fa1e1c694f8bc11501fea2960b9) | วิเคราะห์ LLM traces, retrieval evals, datasets และ experiments | Instrumentation และ local/container/cloud backend. Root LICENSE เป็น ELv2; ไม่ติดป้าย Apache/MIT และต้องตรวจข้อจำกัด hosted service |

<a id="model-gateways"></a>

## Model gateways

| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |
| --- | --- | --- |
| [LiteLLM](https://github.com/BerriAI/litellm/tree/3616014548d40020f508566620c5cd8745721f3c) | รวม model providers ผ่าน SDK/proxy พร้อม cost/routing controls | Provider credentials และ SDK/proxy runtime ตาม mode. MIT scope แยก enterprise directory; gateway ไม่เพิ่มสิทธิ์หรือโควตาจาก model provider |

<a id="ai-evaluation"></a>

## AI evaluation

| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |
| --- | --- | --- |
| [DeepEval](https://github.com/confident-ai/deepeval/tree/0ca198b4640277100efc28b5a862a0170d449c91) | เขียน eval สำหรับ outputs, RAG และ Agent/tool trajectories | Python, task fixtures และ judge/model backend ตาม metric. LLM judges มีต้นทุนและความคลาดเคลื่อน; รักษา acceptance checks ที่ตรวจได้อิสระ |
| [Ragas](https://github.com/vibrantlabsai/ragas/tree/298b68274234c060deacab3cf5fb52aa3a20e885) | วัดคุณภาพ LLM/RAG และสร้าง test sets จากข้อมูลตัวอย่าง | Python, dataset และ LLM/embedding backend ตาม metric. Synthetic tests และ judge scores ต้องตรวจ bias/coverage ก่อนตัดสินระบบจริง |

<a id="ai-application-sdks"></a>

## AI application SDKs

| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |
| --- | --- | --- |
| [Vercel AI SDK](https://github.com/vercel/ai/tree/70e45d5878494be4b66e325187f865951025059e) | ต่อ text/streaming, structured outputs, tools และ UI สำหรับแอป TypeScript | Node 22+ ตาม README ที่อ่าน, provider adapter หรือ gateway และ UI integration ตามงาน. String model ID อาจเลือก Vercel AI Gateway; adapter โดยตรงเป็นอีกเส้นทาง ต้องบันทึก provider/billing route |
