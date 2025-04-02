import streamlit as st
import cv2
import numpy as np
from paddleocr import PaddleOCR
import pandas as pd
from PIL import Image

# --- MUST BE FIRST STREAMLIT COMMAND ---
st.set_page_config(page_title="OCR Table Extractor", layout="wide")

# Initialize OCR
@st.cache_resource
def load_ocr():
    return PaddleOCR(use_angle_cls=True, lang='en')

ocr = load_ocr()

# --- OCR Processing ---
def process_image(uploaded_image):
    image_bytes = uploaded_image.getvalue()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    results = ocr.ocr(image_rgb, cls=True)
    cells = []
    for box, (text, confidence) in results[0]:
        if text.strip():
            y_center = int((box[0][1] + box[2][1]) / 2)
            cells.append((y_center, text.strip(), confidence))
    cells.sort(key=lambda c: c[0])
    return cells

# Confidence level indicator
def confidence_indicator(confidence):
    if confidence >= 0.9:
        return "🟢 High"
    elif confidence >= 0.8:
        return "🟠 Medium"
    else:
        return "🔴 Low"

# --- Main Application ---
st.title("OCR Table Extractor")
mode = st.radio("Choose a mode:", ["Quick Text Copy (Paragraph)", "Column-by-Column Table Extract"])

if mode == "Quick Text Copy (Paragraph)":
    st.subheader("Upload an image for Paragraph OCR")
    
    uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", width=300)
        
        if st.button("Process Image"):
            with st.spinner("Processing..."):
                try:
                    data = process_image(uploaded_file)
                    df = pd.DataFrame({
                        "Text": [text for _, text, _ in data],
                        "Confidence": [confidence_indicator(conf) for _, _, conf in data]
                    })
                    
                    st.data_editor(df, use_container_width=True, num_rows="dynamic")

                    full_text = "\n".join(df["Text"])
                    st.download_button("Download as TXT", full_text, file_name="extracted_text.txt")
                    
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")

elif mode == "Column-by-Column Table Extract":
    st.subheader("Column-by-Column Table Extract")
    data_columns = ["BO Code", "BO Name", "BO Qty", "Material/Spec"]
    
    if 'column_data' not in st.session_state:
        st.session_state.column_data = [[] for _ in data_columns]
    
    col_index = st.selectbox("Select column to process:", 
                             range(len(data_columns)), 
                             format_func=lambda x: data_columns[x])
    
    uploaded_file = st.file_uploader(f"Upload image for {data_columns[col_index]}", 
                                     type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption=f"Uploaded Image for {data_columns[col_index]}", width=300)
        
        if st.button("Process Column"):
            with st.spinner("Processing..."):
                try:
                    column = process_image(uploaded_file)
                    st.session_state.column_data[col_index] = column
                    st.success(f"Column '{data_columns[col_index]}' processed successfully!")
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")

    # Display editable spreadsheet with confidence indicators
    if any(len(col) > 0 for col in st.session_state.column_data):
        st.subheader("Extracted Table (Editable)")

        max_rows = max(len(col) for col in st.session_state.column_data)
        table_data = []
        
        for i in range(max_rows):
            row = []
            for col in st.session_state.column_data:
                if i < len(col):
                    text, conf = col[i][1], confidence_indicator(col[i][2])
                else:
                    text, conf = "", ""
                row.extend([text, conf])
            table_data.append(row)

        # Create DataFrame with alternating columns for text and confidence
        expanded_columns = []
        for col in data_columns:
            expanded_columns.extend([col, f"{col} Confidence"])
        
        df = pd.DataFrame(table_data, columns=expanded_columns)

        edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

        # Download CSV
        edited_csv = edited_df.to_csv(index=False)
        st.download_button(
            "Download as CSV",
            edited_csv,
            file_name="extracted_table.csv",
            mime="text/csv"
        )

        if st.button("Clear Table"):
            st.session_state.column_data = [[] for _ in data_columns]
            st.rerun()
