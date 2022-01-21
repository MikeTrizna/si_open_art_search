import streamlit as st
from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer
import json
from PIL import Image
import os
import urllib

st.set_page_config(
     page_title="Smithsonian Open Access Art Search",
     page_icon="🖼️",
     layout="wide"
)

@st.cache(allow_output_mutation=True)
def load_clip_model():
    return SentenceTransformer('clip-ViT-B-32')

@st.cache(allow_output_mutation=True)
def load_annoy_index():
    annoy_index = AnnoyIndex(512, metric='angular')
    annoy_index.load('art_index.annoy')
    return annoy_index

@st.cache(allow_output_mutation=True)
def load_file_data():
    with open('art_file_info.json') as json_in:
        art_file_info = json.load(json_in)
    return art_file_info

def art_annoy_search(mode, query, k=5):
    if mode == 'id':
        for idx, row in enumerate(art_records):
            if str(row['id']) == query:
                matching_row = idx
        neighbors = art_index.get_nns_by_item(matching_row, k,
                                            include_distances=True)
    elif mode == 'text':
        query_emb = model.encode([query], show_progress_bar=False)
        neighbors = art_index.get_nns_by_vector(query_emb[0], k,
                                            include_distances=True)
    elif mode == 'image':
        query_emb = model.encode([query], show_progress_bar=False)
        neighbors = art_index.get_nns_by_vector(query_emb[0], k,
                                            include_distances=True)
    return neighbors

DEPLOY_MODE = 'streamlit_share'
#DEPLOY_MODE = 'localhost'

if DEPLOY_MODE == 'localhost':
    BASE_URL = 'http://localhost:8501/'
elif DEPLOY_MODE == 'streamlit_share':
    BASE_URL = 'https://share.streamlit.io/miketrizna/si_open_art_search'

if __name__ == "__main__":
    st.markdown("# Smithsonian Open Access Art Search")
    with open('explanation.md','r') as md_file:
        explanation_text = md_file.read()
        st.markdown(explanation_text)

    st.sidebar.markdown('### Search Mode')

    query_params = st.experimental_get_query_params()
    mode_index = 0
    if 'mode' in query_params:
        if query_params['mode'][0] == 'text_search':
            mode_index = 0
        elif query_params['mode'][0] == 'edan_id':
            mode_index = 2

    app_mode = st.sidebar.radio("How would you like to search?",
                        ['Text search','Upload Image', 'EDAN ID'],
                        index = mode_index)

    model = load_clip_model()
    art_index = load_annoy_index()
    art_records = load_file_data()

    if app_mode == 'Text search':
        search_text = 'a watercolor painting of a landscape with mountains'
        if 'mode' in query_params:
            if query_params['mode'][0] == 'text_search':
                if 'query' in query_params:
                    search_text = query_params['query'][0]
            else:
                st.experimental_set_query_params()
        query = st.text_input('Text query',search_text) 
        search_mode = 'text'
        #closest_k_idx, closest_k_dist = bhl_text_search(text_query, 100)

    elif app_mode == 'EDAN ID':
        search_id = 'edanmdm-chndm_2009-6-51'
        if 'mode' in st.experimental_get_query_params():
            if st.experimental_get_query_params()['mode'][0] == 'edan_id':
                if 'query' in st.experimental_get_query_params():
                    search_id = st.experimental_get_query_params()['query'][0]
            else:
                st.experimental_set_query_params()
        query = st.text_input('Query ID', search_id)
        search_mode = 'id'
        #closest_k_idx, closest_k_dist = bhl_id_search(id_query, 100)
    
    elif app_mode == 'Upload Image':
        st.experimental_set_query_params()
        query = None
        image_file = st.file_uploader("Upload Image", type=["png","jpg","jpeg"])
        search_mode = 'image'
        #closest_k_idx = []
        if image_file is not None:
            query = Image.open(image_file)
            st.image(query,width=100,caption='Query image')
            #closest_k_idx, closest_k_dist = bhl_image_search(img, 100)

    if query:
        closest_k_idx, closest_k_dist = art_annoy_search(search_mode, query, 100)

        cols = 3
        col_list = st.columns(cols)

        if len(closest_k_idx):
            for idx, annoy_idx in enumerate(closest_k_idx):
                art_info = art_records[annoy_idx]
                image_url = art_info['ids_url']
                col_list[idx%cols].image(image_url, use_column_width=True)
                si_url = art_info['record_link']
                col_list[idx%cols].markdown(f"*{art_info['title']}*")
                col_list[idx%cols].markdown(f"from {art_info['unitCode']}")
                neighbors_url = f"{BASE_URL}?mode=edan_id&query={art_info['id']}"
                link_html = f'📎<a href="{si_url}" target="_blank">SI Record Link</a> | 🖇️<a href="{neighbors_url}">Nearest Neighbors</a>'
                col_list[idx%cols].markdown(link_html, unsafe_allow_html=True)
                col_list[idx%cols].markdown("---")


