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
                if raw_text.startswith("
                    raw_text = raw_text[7:]
                if raw_text.startswith("
"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("`"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

                try:
                    parsed_json = json.loads(raw_text)
                    st.success("✅ Data extracted successfully!")
                    st.json(parsed_json)

                    json_str = json.dumps(parsed_json, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="⬇️ Download JSON",
                        data=json_str,
                        file_name="extracted_data.json",
                        mime="application/json",
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
