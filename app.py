import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import json
import traceback
import pandas as pd
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Live Camera Analyzer | MISDEC",
    page_icon="📸",
    layout="centered"
)

# --- HEADER ---
st.title("📸 AI Live Vision: Object & Product")
st.caption("Built for MISDEC AI Training • Cik Kiah War Room")
st.markdown("---")

# --- SIDEBAR: API KEY ---
with st.sidebar:
    st.header("⚙️ System Setup")
    api_key = st.text_input("Enter your Gemini API Key:", type="password")
    st.markdown("🔑 [Get your API Key](https://aistudio.google.com/app/apikey)")
    st.divider()
    st.caption("🎓 MISDEC AI Vision Training")

# --- MAIN: CAMERA INPUT ---
st.markdown("### 📷 Ambil Gambar Objek")
# st.camera_input menggantikan st.file_uploader
camera_image = st.camera_input("Klik butang di bawah untuk ambil gambar:")

# --- DEFAULT PROMPT ---
default_prompt = """Anda adalah pakar analisis imej AI. Analisis gambar yang diambil terus dari kamera dan ekstrak maklumat objek ke dalam format JSON.

{
  "summary_fields": {
    "Penerangan": "Penerangan ringkas",
    "Jenis": "Jenis objek",
    "Saiz": "Anggaran saiz",
    "Bentuk": "Bentuk fizikal",
    "Kegunaan": "Fungsi utama",
    "Warna": "Warna utama",
    "Berat": "Anggaran berat"
  },
  "extracted_items": []
}
"""

# --- ACTION BUTTON ---
if camera_image:
    # Papar gambar yang diambil
    image = Image.open(camera_image)
    st.image(image, caption="Gambar yang baru diambil", use_container_width=True)
    
    if st.button("🚀 Analisis Gambar Terus", type="primary", use_container_width=True):
        if not api_key:
            st.error("❌ Sila masukkan API Key di sidebar.")
            st.stop()

        try:
            client = genai.Client(api_key=api_key)
            with st.spinner("🧠 AI sedang menganalisis gambar kamera..."):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[default_prompt, image],
                    config=types.GenerateContentConfig(
                        temperature=0.4,
                        response_mime_type="application/json"
                    )
                )

                raw_text = response.text.replace('```json', '').replace('```', '').strip()
                parsed_json = json.loads(raw_text)
                
                # Papar Hasil
                summary = parsed_json.get("summary_fields", {})
                st.markdown("##### 📋 Hasil Analisis")
                df_summary = pd.DataFrame(list(summary.items()), columns=["Perkara", "Maklumat"])
                st.table(df_summary)

                # Excel Download
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df_summary.to_excel(writer, sheet_name='Ciri-Ciri', index=False)
                
                excel_buffer.seek(0)
                st.download_button(
                    label="📊 Muat Turun Excel",
                    data=excel_buffer,
                    file_name="hasil_analisis_kamera.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"❌ Ralat: {str(e)}")
