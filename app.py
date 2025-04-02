import streamlit as st
from PIL import Image
import io
import cv2
import numpy as np
from paddleocr import PaddleOCR
import pandas as pd
import base64
import os

# Set page configuration
st.set_page_config(
    page_title="OCR Table Extractor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar for instructions and info
with st.sidebar:
    st.title("OCR Table Extractor")
    st.write("This application helps you extract text from images.")
    
    # Try to load logo if available
    try:
        if os.path.exists("logo.jpeg"):
            st.image("logo.jpeg", width=80)
    except:
        pass
    
    st.markdown("### Instructions")
    st.markdown("""
    **Paragraph Mode:**
    1. Upload an image containing text
    2. Click 'Process Image'
    3. Edit the extracted text if needed
    4. Copy or download the results
    
    **Table Mode:**
    1. Select a column to process
    2. Upload an image for that column
    3. Process each column one by one
    4. The table will be built as you add columns
    5. Edit and download when complete
    """)

# App title
st.title("OCR Table Extractor")
st.subheader("Extract text and tables from images")

# Initialize OCR (with caching to avoid reloading)
@st.cache_resource
def load_ocr():
    return PaddleOCR(use_angle_cls=True, lang='en')

ocr = load_ocr()

# OCR Processing Function
def process_image(uploaded_image):
    """Process an uploaded image with OCR"""
    # Convert the uploaded image to an OpenCV image
    image_bytes = uploaded_image.getvalue()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Perform OCR
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
    """Generates a link allowing the data in a DataFrame to be downloaded as a CSV file"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">{text}</a>'
    return href

def get_text_download_link(text_content, filename, link_text):
    """Generates a link allowing the text to be downloaded as a TXT file"""
    b64 = base64.b64encode(text_content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}.txt">{link_text}</a>'
    return href

# Main app logic
# Mode selection
mode = st.radio("Choose a mode:", ["Quick Text Copy (Paragraph)", "Column-by-Column Table Extract"])

if mode == "Quick Text Copy (Paragraph)":
    st.subheader("Paragraph Mode")
    st.write("Upload an image containing text to extract")
    
    # File uploader for paragraph mode
    uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"], key="paragraph_uploader")
    
    # Display and process content when file is uploaded
    if uploaded_file is not None:
        # Show the uploaded image
        st.image(Image.open(uploaded_file), caption="Uploaded Image", use_column_width=True)
        
        # Process button
        if st.button("Process Image"):
            with st.spinner("Processing..."):
                # Process the image with OCR
                processed_data = process_image(uploaded_file)
                
                # Display results
                st.success("Processing complete!")
                st.subheader("Extracted Text")
                
                # Extract text and confidence
                paragraph_data = [text for _, text, _ in processed_data]
                paragraph_confidence = [conf for _, _, conf in processed_data]
                
                # Create a DataFrame for display
                df = pd.DataFrame({
                    "Text": paragraph_data,
                    "Confidence": paragraph_confidence
                })
                
                # Create a styled DataFrame - highlight cells based on confidence
                def color_confidence(val):
                    if val > 0.9:
                        color = '#d4fcd4'  # Light green
                    elif val > 0.8:
                        color = '#fff3cd'  # Light yellow
                    else:
                        color = '#f8d7da'  # Light red
                    return f'background-color: {color}'
                
                # Apply styling to confidence column
                styled_df = df.style.applymap(color_confidence, subset=['Confidence'])
                
                # Display the data in an editable form
                edited_df = st.data_editor(
                    df,
                    column_config={
                        "Text": st.column_config.TextColumn("Text"),
                        "Confidence": st.column_config.NumberColumn("Confidence", format="%.2f")
                    },
                    hide_index=True
                )
                
                # Join the text for clipboard and download
                full_text = "\n".join(edited_df["Text"].tolist())
                
                # Show text in a copyable text area
                st.subheader("Copy Text")
                st.text_area("Copy this text:", full_text, height=150)
                
                # Provide download link
                st.markdown(
                    get_text_download_link(full_text, "extracted_text", "Download as TXT"), 
                    unsafe_allow_html=True
                )

elif mode == "Column-by-Column Table Extract":
    st.subheader("Table Mode")
    st.write("Upload images for each column of your table")
    
    # Define column names
    data_columns = ["BO Code", "BO Name", "BO Qty", "Material/Spec"]
    
    # Initialize session state for storing column data
    if 'column_data' not in st.session_state:
        st.session_state.column_data = [[] for _ in data_columns]
    
    # Column selection
    col_index = st.selectbox(
        "Select column to process:", 
        range(len(data_columns)), 
        format_func=lambda x: data_columns[x]
    )
    
    # File uploader for the selected column
    uploaded_file = st.file_uploader(
        f"Upload image for {data_columns[col_index]}", 
        type=["jpg", "jpeg", "png"],
        key=f"column_{col_index}"
    )
    
    if uploaded_file is not None:
        # Display the uploaded image
        st.image(Image.open(uploaded_file), caption=f"Image for {data_columns[col_index]}", use_column_width=True)
        
        # Process the column on button click
        if st.button("Process Column"):
            with st.spinner("Processing..."):
                column_data = process_image(uploaded_file)
                st.session_state.column_data[col_index] = column_data
                st.success(f"Column {data_columns[col_index]} processed successfully!")
    
    # Display current table state
    if any(len(col) > 0 for col in st.session_state.column_data):
        st.subheader("Current Table State")
        
        # Create table data
        max_rows = max([len(col) for col in st.session_state.column_data], default=0)
        table_data = []
        
        for i in range(max_rows):
            row = []
            for j in range(len(data_columns)):
                if j < len(st.session_state.column_data) and i < len(st.session_state.column_data[j]):
                    # Get text value from the processed data
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
            st.markdown(
                get_table_download_link(edited_df, "extracted_table", "Download as CSV"), 
                unsafe_allow_html=True
            )
            
            # Clear table button
            if st.button("Clear Table"):
                st.session_state.column_data = [[] for _ in data_columns]
                st.experimental_rerun()

# Run the app with: streamlit run app.py

