import json
import time
from typing import Dict, List, Any
from pathlib import Path
from mistralai.client import Mistral
import config
from src.rag.engine import RAGEngine
from src.rag.nashta_pillars import PILLAR_DICT

class RAGEvaluator:
    """Automated RAG evaluation framework using LLM-as-a-Judge (G-Eval / RAG Triad standard)."""

    def __init__(self):
        self.engine = RAGEngine()
        self.judge_client = Mistral(api_key=config.MISTRAL_API_KEY)
        self.judge_model = config.MISTRAL_CHAT_MODEL

    def evaluate_test_case(self, emiten_code: str, pillar_id: str) -> Dict[str, Any]:
        """Evaluates a single pillar analysis test case for an emiten."""
        emiten_code = emiten_code.upper()
        pillar = PILLAR_DICT[pillar_id]

        start_time = time.time()

        # 1. Retrieve Context from Vector Store
        queries = pillar["search_queries"]
        all_chunks = []
        seen_texts = set()
        for q in queries:
            matched = self.engine.vector_store.query(q, emiten_code=emiten_code, top_k=3)
            for m in matched:
                if m["text"] not in seen_texts:
                    seen_texts.add(m["text"])
                    all_chunks.append(m)

        context_parts = []
        for c in all_chunks[:5]:
            meta = c["metadata"]
            header = f"[Dokumen: {meta.get('doc_name', '')} | Halaman: {meta.get('page_number', '')} | Bagian: {meta.get('section_header', '')}]"
            context_parts.append(f"{header}\n{c['text']}")
        context_str = "\n\n---\n\n".join(context_parts) if context_parts else "Tidak ada dokumen."

        # 2. Run RAG Generation
        rag_output = self.engine.analyze_single_pillar(emiten_code, pillar_id, force_refresh=True)
        latency = round(time.time() - start_time, 2)

        # 3. LLM-as-a-Judge Evaluation Prompt
        judge_prompt = f"""Anda adalah AI Evaluator independen yang bertugas menilai kualitas sistem RAG (Retrieval-Augmented Generation) di bidang konsultasi TI korporasi.

TUGAS EVALUASI:
Nilai hasil RAG berikut berdasarkan 4 dimensi standar RAG Triad.

EMITEN: {emiten_code}
PILAR YANG DIUJI: {pillar['name']} ({pillar['description']})

--- KONTEKS DOKUMEN YANG DIAMBIL (RETRIEVED CONTEXT) ---
{context_str}

--- HASIL GENERASI RAG (YANG DINILAI) ---
1. KESIMPULAN MASALAH:
{rag_output.get('problem_summary', '')}

2. CITATION (SUMBER):
- Dokumen: {rag_output.get('citation_doc', '')}
- Lokasi: {rag_output.get('citation_location', '')}
- Kutipan: {rag_output.get('citation_quote', '')}

3. REKOMENDASI SOLUSI NASHTA:
{json.dumps(rag_output.get('solutions', []), ensure_ascii=False, indent=2)}

--- KRITERIA PENILAIAN (Skor 0.0 sampai 1.0) ---
1. **context_relevance** (0.0 - 1.0): Apakah potongan teks konteks yang diambil dari dokumen relevan dengan topik pilar "{pillar['name']}"?
2. **faithfulness** (0.0 - 1.0): Apakah kesimpulan masalah 100% berdasar dari fakta yang ada di konteks dokumen tanpa halusinasi/mengarang?
3. **citation_accuracy** (0.0 - 1.0): Apakah kutipan teks dan lokasi halaman/bagian benar-benar dapat diverifikasi pada potongan dokumen?
4. **solution_relevance** (0.0 - 1.0): Apakah solusi yang direkomendasikan relevan mengatasi masalah yang ditemukan dan sesuai dengan kapabilitas Nashta pada pilar "{pillar['name']}"?

FORMAT OUTPUT WAJIB:
Kembalikan HANYA format JSON valid berikut tanpa teks pengantar:
{{
  "context_relevance_score": 0.95,
  "faithfulness_score": 0.95,
  "citation_accuracy_score": 0.90,
  "solution_relevance_score": 0.95,
  "feedback": "Penjelasan singkat (1-2 kalimat) mengenai kekuatan atau catatan perbaikan pada hasil ini."
}}
"""

        try:
            resp = self.judge_client.chat.complete(
                model=self.judge_model,
                messages=[{"role": "user", "content": judge_prompt}],
                response_format={"type": "json_object"}
            )
            eval_result = json.loads(resp.choices[0].message.content)

            cr = float(eval_result.get("context_relevance_score", 0.0))
            fa = float(eval_result.get("faithfulness_score", 0.0))
            ca = float(eval_result.get("citation_accuracy_score", 0.0))
            sr = float(eval_result.get("solution_relevance_score", 0.0))
            overall = round((cr + fa + ca + sr) / 4.0, 3)

            return {
                "emiten": emiten_code,
                "pillar_id": pillar_id,
                "pillar_name": pillar["name"],
                "latency_sec": latency,
                "context_relevance": cr,
                "faithfulness": fa,
                "citation_accuracy": ca,
                "solution_relevance": sr,
                "overall_score": overall,
                "feedback": eval_result.get("feedback", ""),
                "rag_output": rag_output
            }
        except Exception as e:
            return {
                "emiten": emiten_code,
                "pillar_id": pillar_id,
                "pillar_name": pillar["name"],
                "latency_sec": latency,
                "context_relevance": 0.0,
                "faithfulness": 0.0,
                "citation_accuracy": 0.0,
                "solution_relevance": 0.0,
                "overall_score": 0.0,
                "feedback": f"Evaluation error: {e}",
                "rag_output": rag_output
            }

    def run_benchmark(self, test_cases: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Runs a benchmark suite across multiple emitens and pillars."""
        if not test_cases:
            test_cases = [
                {"emiten": "KLBF", "pillar": "cyber_security"},
                {"emiten": "KLBF", "pillar": "data_ai"},
                {"emiten": "PDSB", "pillar": "managed_service"},
                {"emiten": "PDSB", "pillar": "cloud_services"},
                {"emiten": "SIDO", "pillar": "business_app"},
                {"emiten": "SIDO", "pillar": "iot_edge"},
                {"emiten": "BANK", "pillar": "consulting_advisory"},
                {"emiten": "CARE", "pillar": "hybrid_infra"}
            ]

        print(f"=== Starting RAG Evaluation Benchmark ({len(test_cases)} Test Cases) ===")
        results = []
        for idx, tc in enumerate(test_cases, 1):
            emiten = tc["emiten"]
            pillar = tc["pillar"]
            print(f"[{idx}/{len(test_cases)}] Evaluating {emiten} -> Pillar: {pillar}...")
            res = self.evaluate_test_case(emiten, pillar)
            results.append(res)
            print(f"    Overall Score: {res['overall_score']*100:.1f}% | Faithfulness: {res['faithfulness']*100:.0f}% | Citation: {res['citation_accuracy']*100:.0f}% | Solution: {res['solution_relevance']*100:.0f}% | Latency: {res['latency_sec']}s")

        avg_cr = round(sum(r["context_relevance"] for r in results) / len(results), 3)
        avg_fa = round(sum(r["faithfulness"] for r in results) / len(results), 3)
        avg_ca = round(sum(r["citation_accuracy"] for r in results) / len(results), 3)
        avg_sr = round(sum(r["solution_relevance"] for r in results) / len(results), 3)
        avg_overall = round(sum(r["overall_score"] for r in results) / len(results), 3)
        avg_latency = round(sum(r["latency_sec"] for r in results) / len(results), 2)

        summary = {
            "total_test_cases": len(results),
            "average_overall_score": avg_overall,
            "average_context_relevance": avg_cr,
            "average_faithfulness": avg_fa,
            "average_citation_accuracy": avg_ca,
            "average_solution_relevance": avg_sr,
            "average_latency_sec": avg_latency,
            "details": results
        }

        report_path = config.DATA_DIR / "eval_report.json"
        report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nEvaluation complete! Full report saved to {report_path}")

        return summary

if __name__ == "__main__":
    evaluator = RAGEvaluator()
    summary = evaluator.run_benchmark()
    print("\n" + "="*50)
    print("🏆 SUMMARY BENCHMARK EVALUATION RESULT")
    print("="*50)
    print(f"⭐ Overall RAG Accuracy Score: {summary['average_overall_score']*100:.1f}%")
    print(f"• Context Relevance (Retrieval)  : {summary['average_context_relevance']*100:.1f}%")
    print(f"• Faithfulness (Anti-Hallucinate): {summary['average_faithfulness']*100:.1f}%")
    print(f"• Citation Accuracy (Veracity)   : {summary['average_citation_accuracy']*100:.1f}%")
    print(f"• Solution Relevance (Nashta Fit): {summary['average_solution_relevance']*100:.1f}%")
    print(f"• Average Generation Latency     : {summary['average_latency_sec']} seconds")
    print("="*50)
