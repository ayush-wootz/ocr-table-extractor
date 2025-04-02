import streamlit as st
import os
import cv2
import numpy as np
from paddleocr import PaddleOCR
import pandas as pd
import base64
from PIL import Image
import io

st.set_page_config(page_title="OCR Table Extractor", layout="wide")


# Initialize OCR
@st.cache_resource
def load_ocr():
    return PaddleOCR(use_angle_cls=True, lang='en')

ocr = load_ocr()

# --- OCR Processing ---
def process_image(uploaded_image):
    # Convert uploaded file to image
    image_bytes = uploaded_image.getvalue()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Process with OCR (same as your original code)
    results = ocr.ocr(image_rgb, cls=True)
    cells = []
    for box, (text, confidence) in results[0]:
        if text.strip():
            y_center = int((box[0][1] + box[2][1]) / 2)
            cells.append((y_center, text.strip(), confidence))
    cells.sort(key=lambda c: c[0])
    return cells

# Helper functions for file downloads
def get_table_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">{text}</a>'
    return href

def get_text_download_link(text_content, filename, link_text):
    b64 = base64.b64encode(text_content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}.txt">{link_text}</a>'
    return href

# --- Main Application ---
st.set_page_config(page_title="OCR Table Extractor", layout="wide")

# App title
st.title("OCR Table Extractor")

# Add debugging option
debug_mode = st.sidebar.checkbox("Debug Mode")
if debug_mode:
    st.sidebar.write("Python Path:", sys.path)
    st.sidebar.write("OpenCV Version:", cv2.__version__)
    st.sidebar.write("Available in Environment:", os.environ)

# Mode selection
mode = st.radio("Choose a mode:", ["Quick Text Copy (Paragraph)", "Column-by-Column Table Extract"])

if mode == "Quick Text Copy (Paragraph)":
    st.subheader("Upload an image for Paragraph OCR")
    
    uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"], key="paragraph_uploader")
    
    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        # Process the image on button click
        if st.button("Process Image"):
            with st.spinner("Processing..."):
                try:
                    data = process_image(uploaded_file)
                    
                    # Extract text and confidence
                    paragraph_data = [text for _, text, _ in data]
                    paragraph_confidence = [conf for _, _, conf in data]
                    
                    # Create a DataFrame for display
                    df = pd.DataFrame({
                        "Text": paragraph_data,
                        "Confidence": paragraph_confidence
                    })
                    
                    # Display the editable DataFrame
                    st.subheader("Extracted Text (editable)")
                    edited_df = st.data_editor(df, hide_index=True)
                    
                    # Join the text for clipboard and download
                    full_text = "\n".join(edited_df["Text"].tolist())
                    
                    # Text area for copying
                    st.subheader("Copy this text:")
                    st.text_area("", full_text, height=150)
                    
                    # Download as txt
                    st.markdown(get_text_download_link(full_text, "extracted_text", "Download as TXT"), unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")
                    if debug_mode:
                        st.exception(e)

elif mode == "Column-by-Column Table Extract":
    st.subheader("Column-by-Column Table Extract")
    
    # Define column names (same as original)
    data_columns = ["BO Code", "BO Name", "BO Qty", "Material/Spec"]
    
    # Create a session state to store the columns data
    if 'column_data' not in st.session_state:
        st.session_state.column_data = [[] for _ in data_columns]
    
    # Column selection
    col_index = st.selectbox("Select column to process:", 
                             range(len(data_columns)), 
                             format_func=lambda x: data_columns[x])
    
    # File uploader for the selected column
    uploaded_file = st.file_uploader(f"Upload image for {data_columns[col_index]}", 
                                      type=["jpg", "jpeg", "png"],
                                      key=f"column_{col_index}")
    
    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption=f"Uploaded Image for {data_columns[col_index]}", use_column_width=True)
        
        # Process the column on button click
        if st.button("Process Column"):
            with st.spinner("Processing..."):
                try:
                    column = process_image(uploaded_file)
                    st.session_state.column_data[col_index] = column
                    st.success(f"Column {data_columns[col_index]} processed successfully!")
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")
                    if debug_mode:
                        st.exception(e)
    
    # Show the current table state
    if any(len(col) > 0 for col in st.session_state.column_data):
        st.subheader("Current Table State")
        
        # Create table data
        max_rows = max([len(col) for col in st.session_state.column_data], default=0)
        table_data = []
        
        for i in range(max_rows):
            row = []
            for j in range(len(data_columns)):
                if j < len(st.session_state.column_data) and i < len(st.session_state.column_data[j]):
                    val = st.session_state.column_data[j][i][1]
                    row.append(val)
                else:
                    row.append("")
            table_data.append(row)
        
        # Create and display the table
        if table_data:
            df = pd.DataFrame(table_data, columns=data_columns)
            edited_df = st.data_editor(df, hide_index=True)
            
            # Download as CSV
            st.markdown(get_table_download_link(edited_df, "extracted_table", "Download as CSV"), unsafe_allow_html=True)
            
            # Clear table button
            if st.button("Clear Table"):
                st.session_state.column_data = [[] for _ in data_columns]
                st.experimental_rerun()
