app.py

import streamlit as st
import os
import cv2
import numpy as np
from paddleocr import PaddleOCR
import pandas as pd
import base64
from PIL import Image
import io

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

# Confidence color coding
def get_color(confidence):
    if confidence > 0.9:
        return '#d4fcd4'  # Green
    elif confidence > 0.8:
        return '#fff3cd'  # Orange
    else:
        return '#f8d7da'  # Red

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
                data = process_image(uploaded_file)
                
                paragraph_data = [text for _, text, _ in data]
                confidences = [conf for _, _, conf in data]
                
                # Display with confidence colors
                df = pd.DataFrame({"Text": paragraph_data, "Confidence": confidences})
                st.subheader("Extracted Text (editable)")
                
                # Create styled text display
                styled_text = []
                for text, conf in zip(paragraph_data, confidences):
                    styled_text.append(f'<div style="background-color: {get_color(conf)}; padding: 5px; margin: 2px;">{text}</div>')
                st.markdown("".join(styled_text), unsafe_allow_html=True)
                
                # Editable version
                edited_df = st.data_editor(df[["Text"]], hide_index=True)
                full_text = "\n".join(edited_df["Text"].tolist())
                
                st.download_button("Download as TXT", full_text, file_name="extracted_text.txt")

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
                column = process_image(uploaded_file)
                st.session_state.column_data[col_index] = column
                st.success(f"Column {data_columns[col_index]} processed!")

    if any(len(col) > 0 for col in st.session_state.column_data):
        st.subheader("Current Table State")
        
        max_rows = max(len(col) for col in st.session_state.column_data)
        table_html = "<table style='border-collapse: collapse; width: 100%;'>"
        
        # Header
        table_html += "<tr>"
        for col in data_columns:
            table_html += f"<th style='border: 1px solid black; padding: 8px;'>{col}</th>"
        table_html += "</tr>"
        
        # Rows
        for i in range(max_rows):
            table_html += "<tr>"
            for j in range(len(data_columns)):
                if j < len(st.session_state.column_data) and i < len(st.session_state.column_data[j]):
                    text = st.session_state.column_data[j][i][1]
                    conf = st.session_state.column_data[j][i][2]
                else:
                    text = ""
                    conf = 1.0
                table_html += f"<td style='border: 1px solid black; padding: 8px; background-color: {get_color(conf)}'>{text}</td>"
            table_html += "</tr>"
        
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)
        
        # CSV Download
        csv_data = []
        for i in range(max_rows):
            row = []
            for j in range(len(data_columns)):
                row.append(st.session_state.column_data[j][i][1] if j < len(st.session_state.column_data) and i < len(st.session_state.column_data[j]) else "")
            csv_data.append(row)
        
        df = pd.DataFrame(csv_data, columns=data_columns)
        csv = df.to_csv(index=False)
        st.download_button("Download as CSV", csv, file_name="extracted_table.csv")

        if st.button("Clear Table"):
            st.session_state.column_data = [[] for _ in data_columns]
            st.rerun()  # Updated from experimental_rerun
