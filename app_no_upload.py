# import streamlit as st
# import sqlite3
# from io import BytesIO
# from PIL import Image
# from byaldi import RAGMultiModalModel

# # --- Configuration ---
# DB_PATH = "pdf_images_completed.db"
# INDEX_NAME = "image_index_full"

# # --- Load Colpali model from existing index ---
# @st.cache_resource
# def load_indexed_model():
#     return RAGMultiModalModel.from_index(INDEX_NAME)

# # --- Load images from SQLite DB ---
# @st.cache_data
# def load_images_from_db(doc_id, k=3, db_path=DB_PATH):
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()
#     cursor.execute('''
#         SELECT page_num, image FROM images
#         WHERE doc_id = ?
#         ORDER BY page_num ASC
#         LIMIT ?
#     ''', (doc_id, k))
#     rows = cursor.fetchall()
#     conn.close()

#     results = []
#     for page_num, img_blob in rows:
#         img = Image.open(BytesIO(img_blob))
#         results.append((page_num, img))
#     return results

# # --- Search Query and Fetch Images from DB ---
# def search_and_get_images(query, model):
#     results = model.search(query, k=3)

#     final_images = []
#     for res in results:
#         doc_id = res['doc_id']
#         page_num = res['page_num']

#         # Load image from DB
#         conn = sqlite3.connect(DB_PATH)
#         cursor = conn.cursor()
#         cursor.execute('''
#             SELECT image FROM images
#             WHERE doc_id = ? AND page_num = ?
#         ''', (doc_id, page_num))
#         row = cursor.fetchone()
#         conn.close()

#         if row:
#             img = Image.open(BytesIO(row[0]))
#             final_images.append((doc_id, page_num, img))

#     return final_images

# # --- UI Setup ---
# st.set_page_config(page_title="PDF Semantic Search", layout="wide")
# st.markdown("## ⚡ LLM For Electrical Engineering")
# st.markdown("Use semantic queries to retrieve PDF pages indexed by AI and stored efficiently in a database.")

# # --- Load Model from Disk ---
# with st.spinner("⚙️ Loading AI model and index..."):
#     colpali_model = load_indexed_model()

# st.success("✅ System ready for semantic search!")

# # --- Search Interface ---
# st.markdown("### 🧠 Retrieve any information")
# query = st.text_input("Example: 'opamp formula every types in table'", placeholder="Type your semantic question here")

# if query:
#     with st.spinner("🔍 Searching the indexed dataset..."):
#         result_images = search_and_get_images(query, colpali_model)

#     if not result_images:
#         st.warning("No matching results found. Try rewording your query.")
#     else:
#         st.markdown("### 🖼️ Top Matching Pages")
#         cols = st.columns(len(result_images))
#         for idx, (doc_id, page_num, img) in enumerate(result_images):
#             with cols[idx]:
#                 st.image(img, caption=f"📄 Doc {doc_id} - Page {page_num}", use_container_width=True)
#                 st.markdown("<div style='text-align: center;'>🎯 AI Match</div>", unsafe_allow_html=True)

import streamlit as st
import sqlite3
from io import BytesIO
from PIL import Image
from byaldi import RAGMultiModalModel

# --- Configuration ---
DB_PATH = "pdf_images_completed.db"
INDEX_NAME = "image_index_full"

# --- Load Colpali model from existing index ---
@st.cache_resource
def load_indexed_model():
    return RAGMultiModalModel.from_index(INDEX_NAME)

# --- Load images from SQLite DB ---
@st.cache_data
def load_images_from_db(doc_id, start_page, end_page, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT page_num, image FROM images
        WHERE doc_id = ? AND page_num BETWEEN ? AND ?
        ORDER BY page_num ASC
    ''', (doc_id, start_page, end_page))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for page_num, img_blob in rows:
        img = Image.open(BytesIO(img_blob))
        results.append((page_num, img))
    return results

# --- Search Query and Fetch Images from DB ---
def search_and_get_images(query, model):
    results = model.search(query, k=3)

    final_images = []
    document_pages = {}
    for res in results:
        doc_id = res['doc_id']
        page_num = res['page_num']

        if doc_id not in document_pages:
            document_pages[doc_id] = []

        document_pages[doc_id].append(page_num)

        # Load image from DB
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT image FROM images
            WHERE doc_id = ? AND page_num = ?
        ''', (doc_id, page_num))
        row = cursor.fetchone()
        conn.close()

        if row:
            img = Image.open(BytesIO(row[0]))
            final_images.append((doc_id, page_num, img))

    return final_images, document_pages

# --- UI Setup ---
st.set_page_config(page_title="PDF Semantic Search", layout="wide")
st.markdown("## ⚡ LLM For Electrical Engineering")
st.markdown("Use semantic queries to retrieve PDF pages indexed by AI and stored efficiently in a database.")

# --- Load Model from Disk ---
with st.spinner("⚙️ Loading AI model and index..."):
    colpali_model = load_indexed_model()

st.success("✅ System ready for semantic search!")

# --- Search Interface ---
st.markdown("### 🧠 Retrieve any information")
query = st.text_input("Example: 'opamp formula every types in table'", placeholder="Type your semantic question here")

if query:
    with st.spinner("🔍 Searching the indexed dataset..."):
        result_images, document_pages = search_and_get_images(query, colpali_model)

    if not result_images:
        st.warning("No matching results found. Try rewording your query.")
    else:
        st.markdown("### 🖼️ Top Matching Pages")
        cols = st.columns(len(result_images))
        
        for idx, (doc_id, page_num, img) in enumerate(result_images):
            with cols[idx]:
                st.image(img, caption=f"📄 Doc {doc_id} - Page {page_num}", use_container_width=True)
                st.markdown("<div style='text-align: center;'>🎯 AI Match</div>", unsafe_allow_html=True)
        
        # --- Filter Pages Based on Predicted Document ---
        st.markdown("### 🔍 Filter Pages by Document and Range")

        # Create a dropdown for document selection
        selected_doc_id = st.selectbox("Select Document to View", list(document_pages.keys()))

        # Get pages for the selected document
        pages = document_pages[selected_doc_id]
        start_page, end_page = min(pages), max(pages)

        # Input for the start and end page range (no limits)
        start_page = st.number_input("Start page", min_value=1, value=start_page)
        end_page = st.number_input("End page", min_value=1, value=end_page)

        # Ensure the end page is not before the start page
        if end_page < start_page:
            end_page = start_page

        # Load images based on the selected document and filtered page range
        filtered_images = load_images_from_db(selected_doc_id, start_page, end_page)

        # Display the filtered images
        if filtered_images:
            st.markdown(f"### 📄 Viewing Pages {start_page} to {end_page} of Doc {selected_doc_id}")
            cols = st.columns(len(filtered_images))
            for idx, (page_num, img) in enumerate(filtered_images):
                with cols[idx]:
                    st.image(img, caption=f"📄 Doc {selected_doc_id} - Page {page_num}", use_container_width=True)
        else:
            st.warning("No pages found in the selected range.")
