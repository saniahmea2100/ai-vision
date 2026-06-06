import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import json
import traceback
import pandas as pd
import io  # Diperlukan untuk proses download Excel

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Object Analyzer | MISDEC",
    page_icon="🔍",
    layout="centered"
)

# --- HEADER ---
st.title("🔍 AI Vision: Object & Product Analyzer")
st.caption("Built for MISDEC AI Training • Cik Kiah War Room")
st.markdown("---")
st.markdown(
    "Muat naik gambar objek atau produk, dan biarkan "
    "Gemini AI mengekstrak ciri-cirinya (Jenis, Saiz, Bentuk, Warna, dll) ke dalam jadual & Excel. ✨"
)

# --- SIDEBAR: API KEY ---
with st.sidebar:
    st.header("⚙️ System Setup")
    api_key = st.text_input(
        "Enter your Gemini API Key:",
        type="password",
        help="Get it from Google AI Studio"
    )
    st.markdown(
        "🔑 [Get your API Key](https://aistudio.google.com/app/apikey)"
    )

    # --- API Key Tester Button ---
    st.divider()
    if st.button("🧪 Test API Key", use_container_width=True):
        if not api_key:
            st.error("Paste a key first")
        else:
            try:
                client = genai.Client(api_key=api_key)
                test_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=["Say hello in one word"]
                )
                st.success(f"✅ Key works! Response: {test_response.text}")
            except Exception as e:
                st.error(f"❌ RAW ERROR:\n\n{type(e).__name__}: {str(e)}")
                st.code(traceback.format_exc())

    st.divider()
    st.caption("💡 Your API key is never stored. Stays in your browser only.")
    st.divider()
    st.caption("🎓 MISDEC AI Vision Training")
    st.caption("Trainer: Muhammad Nur Aqmal bin Khatiman")

# --- MAIN: FILE UPLOAD ---
uploaded_file = st.file_uploader(
    "📁 Muat naik gambar objek/produk anda:",
    type=["jpg", "png", "jpeg", "webp"],
    help="Max 10MB. Berfungsi paling baik dengan gambar yang jelas dan terang."
)

# --- DEFAULT GENERAL PROMPT (DIKEMASKINI UNTUK OBJEK) ---
default_prompt = """Anda adalah pakar analisis imej AI. Analisis gambar yang dimuat naik dan ekstrak maklumat objek ke dalam format JSON yang berstruktur.

Respons JSON anda mesti mengikut skema yang tepat ini:
{
  "summary_fields": {
    "Penerangan Gambar": "Penerangan ringkas tentang apa yang ada dalam gambar",
    "Jenis": "Jenis atau kategori objek",
    "Saiz": "Anggaran saiz objek (cth: Kecil, Besar, 10cm x 5cm)",
    "Bentuk": "Bentuk fizikal objek",
    "Kegunaan": "Fungsi atau kegunaan utama objek tersebut",
    "Warna": "Warna-warna utama yang kelihatan",
    "Berat": "Anggaran berat objek"
  },
  "extracted_items": []
}

Arahan:
1. Dalam "summary_fields", kenal pasti dan isikan ciri-ciri objek berdasarkan gambar yang diberikan.
2. Jika mana-mata maklumat sukar dianggarkan atau tidak jelas dari gambar (seperti berat yang tepat), berikan anggaran logik atau tulis "Tidak dapat dipastikan".
3. Biarkan "extracted_items" sebagai senarai kosong [] kecuali jika terdapat komponen kecil objek yang perlu disenaraikan.
"""

# --- PROMPT EDITOR ---
st.markdown("### 🎯 AI Instruction (Prompt)")
prompt = st.text_area(
    "Edit arahan (prompt) ini jika anda mahu AI fokus pada perkara lain:",
    value=default_prompt,
    height=350,
    label_visibility="collapsed"
)

# --- ACTION BUTTON ---
if st.button("🚀 Analisis Gambar dengan AI", type="primary", use_container_width=True):

    if not api_key:
        st.error("❌ Sila masukkan Gemini API Key anda di sidebar.")
        st.stop()

    if not uploaded_file:
        st.error("❌ Sila muat naik gambar terlebih dahulu.")
        st.stop()

    if uploaded_file.size > 10 * 1024 * 1024:
        st.error("❌ Saiz fail terlalu besar. Sila muat naik imej di bawah 10MB.")
        st.stop()

    try:
        image = Image.open(uploaded_file)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📷 Gambar Anda")
            st.image(image, use_container_width=True)

        client = genai.Client(api_key=api_key)

        with col2:
            st.markdown("#### ✨ Hasil Analisis AI")
            with st.spinner("🧠 AI sedang menganalisis gambar anda..."):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt, image],
                    config=types.GenerateContentConfig(
                        temperature=0.4, # Suhu dinaikkan sedikit untuk tekaan logik pada berat/saiz
                        response_mime_type="application/json",
                        thinking_config=types.ThinkingConfig(thinking_budget=0),
                    )
                )

                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

                try:
                    parsed_json = json.loads(raw_text)
                    st.success("✅ Data berjaya diekstrak!")
                    
                    summary = parsed_json.get("summary_fields", {})
                    items = parsed_json.get("extracted_items", [])

                    # Sediakan pembolehubah DataFrame kosong untuk Excel buffer
                    df_summary = None
                    df_items = None

                    # 1. Paparkan Maklumat Ringkasan/Metadata (Jadual Pertama)
                    if summary:
                        st.markdown("##### 📋 Ciri-Ciri Objek")
                        df_summary = pd.DataFrame(list(summary.items()), columns=["Perkara (Field)", "Maklumat (Value)"])
                        st.table(df_summary)
                    else:
                        flat_data = {k: v for k, v in parsed_json.items() if not isinstance(v, (list, dict))}
                        if flat_data:
                            st.markdown("##### 📋 Ciri-Ciri Objek")
                            df_summary = pd.DataFrame(list(flat_data.items()), columns=["Perkara (Field)", "Maklumat (Value)"])
                            st.table(df_summary)

                    # 2. Paparkan Senarai Item / Jadual jika wujud (Jadual Kedua)
                    if isinstance(items, list) and len(items) > 0:
                        st.markdown("##### 📊 Komponen Tambahan (Jika Ada)")
                        df_items = pd.DataFrame(items)
                        st.table(df_items)

                    # --- JANA FAIL EXCEL (.XLSX) SECARA DINAMIK ---
                    excel_buffer = io.BytesIO()
                    
                    # Menggunakan ExcelWriter untuk buat berbilang Sheets
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        if df_summary is not None:
                            df_summary.to_excel(writer, sheet_name='Ciri-Ciri', index=False)
                        if df_items is not None:
                            df_items.to_excel(writer, sheet_name='Komponen', index=False)
                        
                        # Jika kedua-dua kosong (kes terpencil)
                        if df_summary is None and df_items is None:
                            pd.DataFrame([{"Mesej": "Tiada data diekstrak"}]).to_excel(writer, sheet_name='Empty', index=False)
                    
                    excel_buffer.seek(0)

                    # Butang Muat Turun Fail Excel
                    st.download_button(
                        label="📊 Muat Turun Excel (XLSX)",
                        data=excel_buffer,
                        file_name="hasil_analisis_objek.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                except json.JSONDecodeError:
                    st.warning("⚠️ AI mengembalikan data tetapi bukan format JSON yang tepat.")
                    st.code(raw_text, language="json")

    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg or "API_KEY" in error_msg or "401" in error_msg:
            st.error(
                "❌ API Key tidak sah. Semak semula key yang anda masukkan. "
                "Dapatkan yang baru dari [Google AI Studio](https://aistudio.google.com/app/apikey)."
            )
        elif "quota" in error_msg.lower() or "rate" in error_msg.lower() or "429" in error_msg:
            st.error(
                "❌ Had API (Rate limit) dicapai. Sila tunggu 1 minit dan cuba lagi. "
                "Ini adalah normal untuk pelan percuma."
            )
        elif "404" in error_msg or "NOT_FOUND" in error_msg:
            st.error(
                "❌ Model tidak dijumpai. Nama model mungkin telah lapuk. "
                "Sila hubungi tenaga pengajar."
            )
        else:
            st.error(f"❌ Ralat Sistem: {error_msg}")

# --- FOOTER ---
st.markdown("---")
st.caption(
    "🎓 Building AI Vision App with Gemini API • "
    "MISDEC Melaka • 06 June 2026"
)
