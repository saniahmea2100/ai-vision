# ==========================================
# CELL 2: BUILD THE AI VISION APP (app.py)
# FIXED: Download output as Excel (.xlsx)
# ==========================================


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
    page_title="Vision AI Data Extractor | MISDEC",
    page_icon="🤖",
    layout="centered"
)

# --- HEADER ---
st.title("📄 AI Vision: General Document Extractor")
st.caption("Built for MISDEC AI Training • Cik Kiah War Room")
st.markdown("---")
st.markdown(
    "Upload any document image (form, certificate, letter, receipt, report) and watch "
    "Gemini AI extract structured data into clean tables & Excel. ✨"
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
    "📁 Upload your document image:",
    type=["jpg", "png", "jpeg", "webp"],
    help="Max 10MB. Works best with clear, well-lit images."
)

# --- DEFAULT GENERAL PROMPT ---
default_prompt = """You are an expert document AI analyzer. Extract all relevant and important information from this document into a structured JSON format.

Your JSON response must follow this exact schema:
{
  "summary_fields": {
    "field_name_1": "value_1",
    "field_name_2": "value_2"
  },
  "extracted_items": [
    {
      "column_1": "value",
      "column_2": "value"
    }
  ]
}

Instructions:
1. In "summary_fields", extract all key metadata, headings, or individual values found in the document (e.g., Title, Date, Name, Reference Number, Status, Total, etc.). Use descriptive and clear keys.
2. In "extracted_items", if the document contains any table, itemized list, or repeated rows of data, extract them as a list of objects. If there are no line items or tables, return an empty list [].
3. Do not assume, guess, or extrapolate any information. Only extract what is clearly visible in the image.
"""

# --- PROMPT EDITOR ---
st.markdown("### 🎯 AI Instruction (Prompt)")
prompt = st.text_area(
    "Edit the prompt to customize what you want to extract:",
    value=default_prompt,
    height=300,
    label_visibility="collapsed"
)

# --- ACTION BUTTON ---
if st.button("🚀 Extract Data with AI", type="primary", use_container_width=True):

    if not api_key:
        st.error("❌ Please enter your Gemini API Key in the sidebar.")
        st.stop()

    if not uploaded_file:
        st.error("❌ Please upload a document image first.")
        st.stop()

    if uploaded_file.size > 10 * 1024 * 1024:
        st.error("❌ File too large. Please upload an image under 10MB.")
        st.stop()

    try:
        image = Image.open(uploaded_file)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📷 Your Document")
            st.image(image, use_container_width=True)

        client = genai.Client(api_key=api_key)

        with col2:
            st.markdown("#### ✨ AI Extraction Result")
            with st.spinner("🧠 AI is analyzing your document..."):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt, image],
                    config=types.GenerateContentConfig(
                        temperature=0.1,
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
                    st.success("✅ Data extracted successfully!")
                    
                    summary = parsed_json.get("summary_fields", {})
                    items = parsed_json.get("extracted_items", [])

                    # Sediakan pembolehubah DataFrame kosong untuk Excel bunder
                    df_summary = None
                    df_items = None

                    # 1. Paparkan Maklumat Ringkasan/Metadata (Jadual Pertama)
                    if summary:
                        st.markdown("##### 📋 Maklumat Ringkasan (Summary)")
                        df_summary = pd.DataFrame(list(summary.items()), columns=["Perkara (Field)", "Maklumat (Value)"])
                        st.table(df_summary)
                    else:
                        flat_data = {k: v for k, v in parsed_json.items() if not isinstance(v, (list, dict))}
                        if flat_data:
                            st.markdown("##### 📋 Maklumat Dokumen")
                            df_summary = pd.DataFrame(list(flat_data.items()), columns=["Perkara (Field)", "Maklumat (Value)"])
                            st.table(df_summary)

                    # 2. Paparkan Senarai Item / Jadual jika wujud (Jadual Kedua)
                    if isinstance(items, list) and len(items) > 0:
                        st.markdown("##### 📊 Senarai Item / Jadual Dokumen")
                        df_items = pd.DataFrame(items)
                        st.table(df_items)
                    elif "key_items" in parsed_json: 
                        old_items = parsed_json.get("key_items", [])
                        if old_items:
                            st.markdown("##### 📊 Senarai Item")
                            df_items = pd.DataFrame(old_items)
                            st.table(df_items)

                    # --- JANA FAIL EXCEL (.XLSX) SECARA DINAMIK ---
                    excel_buffer = io.BytesIO()
                    
                    # Menggunakan ExcelWriter untuk buat berbilang Sheets
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        if df_summary is not None:
                            df_summary.to_excel(writer, sheet_name='Summary', index=False)
                        if df_items is not None:
                            df_items.to_excel(writer, sheet_name='Items', index=False)
                        
                        # Jika kedua-dua kosong (kes terpencil)
                        if df_summary is None and df_items is None:
                            pd.DataFrame([{"Mesej": "Tiada data diekstrak"}]).to_excel(writer, sheet_name='Empty', index=False)
                    
                    excel_buffer.seek(0)

                    # Butang Muat Turun Fail Excel
                    st.download_button(
                        label="Excel_Muat_Turun 📊 Download Excel (XLSX)",
                        data=excel_buffer,
                        file_name="extracted_document_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                except json.JSONDecodeError:
                    st.warning("⚠️ AI returned data but not strict JSON.")
                    st.code(raw_text, language="json")

    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg or "API_KEY" in error_msg or "401" in error_msg:
            st.error(
                "❌ Invalid API Key. Double-check the key you pasted. "
                "Get a new one from [Google AI Studio](https://aistudio.google.com/app/apikey)."
            )
        elif "quota" in error_msg.lower() or "rate" in error_msg.lower() or "429" in error_msg:
            st.error(
                "❌ Rate limit hit. Wait 1 minute and try again. "
                "Free tier has limits — that's normal."
            )
        elif "404" in error_msg or "NOT_FOUND" in error_msg:
            st.error(
                "❌ Model not found. The model name might be outdated. "
                "Contact trainer for assistance."
            )
        else:
            st.error(f"❌ System Error: {error_msg}")

# --- FOOTER ---
st.markdown("---")
st.caption(
    "🎓 Building AI Vision App with Gemini API • "
    "MISDEC Melaka • 06 June 2026"
)
