import streamlit as st
import os
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
        # Display smaller image preview
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", width=300)
        
        if st.button("Process Image"):
            with st.spinner("Processing..."):
                try:
                    data = process_image(uploaded_file)
                    
                    paragraph_data = [text for _, text, _ in data]
                    confidences = [conf for _, _, conf in data]
                    
                    # Create DataFrame for display
                    df = pd.DataFrame({
                        "Text": paragraph_data,
                        "Confidence": confidences
                    })
                    
                    # Display with confidence highlighting
                    st.subheader("Extracted Text")
                    for text, conf in zip(paragraph_data, confidences):
                        st.markdown(
                            f'<div style="background-color: {get_color(conf)}; padding: 10px; border-radius: 5px; margin: 5px 0;">{text}</div>',
                            unsafe_allow_html=True
                        )
                    
                    # Editable version
                    st.subheader("Editable Text")
                    edited_df = st.data_editor(df[["Text"]], hide_index=True)
                    
                    # Join text for download
                    full_text = "\n".join(edited_df["Text"].tolist())
                    
                    # Download button
                    st.download_button(
                        "Download as TXT",
                        full_text,
                        file_name="extracted_text.txt"
                    )
                    
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
        # Display smaller image preview
        image = Image.open(uploaded_file)
        st.image(image, caption=f"Uploaded Image for {data_columns[col_index]}", width=300)
        
        if st.button("Process Column"):
            with st.spinner("Processing..."):
                try:
                    column = process_image(uploaded_file)
                    st.session_state.column_data[col_index] = column
                    st.success(f"Column {data_columns[col_index]} processed successfully!")
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")

    # Show the current table state
    if any(len(col) > 0 for col in st.session_state.column_data):
        st.subheader("Current Table State")
        
        # Create table data with confidence coloring
        max_rows = max([len(col) for col in st.session_state.column_data], default=0)
        table_html = "<table style='width:100%; border-collapse: collapse;'>"
        
        # Table headers
        table_html += "<tr style='background-color: #f2f2f2;'>"
        for col in data_columns:
            table_html += f"<th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>{col}</th>"
        table_html += "</tr>"
        
        # Table rows
        for i in range(max_rows):
            table_html += "<tr>"
            for j in range(len(data_columns)):
                if j < len(st.session_state.column_data) and i < len(st.session_state.column_data[j]):
                    text = st.session_state.column_data[j][i][1]
                    conf = st.session_state.column_data[j][i][2]
                    color = get_color(conf)
                else:
                    text = ""
                    color = "white"
                
                table_html += f"<td style='border: 1px solid #ddd; padding: 8px; background-color: {color}'>{text}</td>"
            table_html += "</tr>"
        table_html += "</table>"
        
        st.markdown(table_html, unsafe_allow_html=True)
        
        # Create DataFrame for download
        table_data = []
        for i in range(max_rows):
            row = []
            for j in range(len(data_columns)):
                if j < len(st.session_state.column_data) and i < len(st.session_state.column_data[j]):
                    row.append(st.session_state.column_data[j][i][1])
                else:
                    row.append("")
            table_data.append(row)
        
        df = pd.DataFrame(table_data, columns=data_columns)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            "Download as CSV",
            csv,
            file_name="extracted_table.csv"
        )

        if st.button("Clear Table"):
            st.session_state.column_data = [[] for _ in data_columns]
            st.rerun()
