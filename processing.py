import os
import config
import numpy as np
from mistralai.client import Mistral

# 1. Inisialisasi Client dari config.py
client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))

# 2. Baca teks dari file output.md secara lokal
file_path = "./output.md"
try:
    with open(file_path, "r", encoding="utf-8") as f:
        document_text = f.read()
except FileNotFoundError:
    print(f"Error: File '{file_path}' tidak ditemukan. Jalankan parse.py terlebih dahulu.")
    exit()

def chunk_text(text, chunk_size=1500, overlap=200):
    """Membagi teks panjang menjadi potongan-potongan (chunks) yang lebih kecil."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

query = "Kondisi perusahaan saat ini?"

print("Membagi dokumen menjadi chunks...")
chunks = chunk_text(document_text, chunk_size=2000, overlap=200)
print(f"Total chunks: {len(chunks)}")

# Ambil embedding untuk query
print("Mengambil embedding untuk query...")
query_embedding = client.embeddings.create(
    inputs=[query],
    model="mistral-embed"
).data[0].embedding

# Jika chunk terlalu banyak, kita bisa mengambil sample/batch embedding untuk pencarian teratas
# Untuk performa & kuota API yang efisien, ambil hingga 30 chunks pertama atau paling relevan
print("Mencari chunk paling relevan...")
chunk_embeddings = []
batch_size = 20
sample_chunks = chunks[:50] # Mengambil hingga 50 chunk pertama untuk efisiensi

embeddings_res = client.embeddings.create(
    inputs=sample_chunks,
    model="mistral-embed"
)
chunk_embeddings = [item.embedding for item in embeddings_res.data]

# Hitung skor kemiripan (similarity)
scores = [cosine_similarity(query_embedding, emb) for emb in chunk_embeddings]

# Ambil Top-5 chunk terbaik
top_indices = np.argsort(scores)[-5:][::-1]
relevant_chunks = [sample_chunks[i] for i in top_indices]

context = "\n\n--- CHUNK ---\n\n".join(relevant_chunks)

# 3. Susun Prompt dengan Konteks Hasil Retrieval
prompt = f"Berdasarkan potongan dokumen di bawah ini, tolong jawab pertanyaan berikut secara rinci.\n\n=== KONTEKS DOKUMEN ===\n{context}\n\n=== PERTANYAAN ===\n{query}"

print("Mengirimkan konteks relevan ke Mistral AI...")
# 4. Kirim ke Mistral AI
response = client.chat.complete(
    model="mistral-medium-latest",
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ]
)

# 5. Cetak Hasil Response
print("\n=== JAWABAN ===")
print(response.choices[0].message.content)
