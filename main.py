import streamlit as st
from streamlit_chat import message
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

import tempfile
import os

st.set_page_config(layout="wide", page_title="🤖💬 AI Chatbot")

st.sidebar.image("logo1.png", width = 80)
st.sidebar.write(" ### CSV파일을 업로드 하세요")



# col1: 이미지 표시
col1, col2, col3 = st.columns([2,4,1])
with col2:
    st.image('logo.png', width = 300)

# col2: 제목 표시
    st.title("밀양시 :blue[단디교통봇🤖💬]")
    st.caption('예시1) xxxx년 xx월 xx동의 교통사고 위험지수는 몇이야?  예시2) xx동의 위험지수를 낮추는 방법은 뭐가 있을까?')

col4, col5, col6 = st.columns([1,4,1])
with col5:
    

    uploaded_file = st.sidebar.file_uploader("upload", type="csv")


    if uploaded_file :
    #use tempfile because CSVLoader only accepts a file_path
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        loader = CSVLoader(file_path=tmp_file_path, encoding="utf-8", csv_args={'delimiter': ','})
        
        data = loader.load_and_split()
        
        text_splitter = RecursiveCharacterTextSplitter(
            # Set a really small chunk size, just to show.
            chunk_size = 100,
            chunk_overlap  = 20,
            length_function = len,
            is_separator_regex = False,
            )
        
        texts = text_splitter.split_documents(data)
        
        embeddings = OpenAIEmbeddings()
        vectorstore = Chroma.from_documents(texts, embeddings)
        

        chain = ConversationalRetrievalChain.from_llm(llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo'), 
                                                    retriever=vectorstore.as_retriever(), verbose=True)

        def conversational_chat(query):
            
            result = chain({"question": query, "chat_history": st.session_state['history']})
            #st.session_state['history'].append((query, result["answer"]))
            
            MAX_HISTORY_LENGTH = 4097

            if len(st.session_state['history']) >= MAX_HISTORY_LENGTH:
                st.session_state['history'].append((query, result["answer"]))
                st.session_state['history'] = st.session_state['history'][-MAX_HISTORY_LENGTH:]
            
            return result["answer"]

        if 'history' not in st.session_state:
            st.session_state['history'] = []

        if 'generated' not in st.session_state: 
            st.session_state['generated'] = ["안녕하세요🤗 밀양 단디교통 봇입니다~~ " + uploaded_file.name + "을 바탕으로 정보를 알려드릴게요! "]

        if 'past' not in st.session_state:
            st.session_state['past'] = ["안녕? 👋"]
            
        #container for the chat history
        response_container = st.container()
        #container for the user's text input
        container = st.container() 
        
        with container:
            
            with st.form(key='my_form', clear_on_submit=True):
                
                user_input = st.text_input("You:", placeholder="텍스트를 입력하세요 ", key='input')
                submit_button = st.form_submit_button(label='전송')
                
            if submit_button and user_input:
                with st.spinner("Wait for it..."):
                    output = conversational_chat(user_input)
                
                    st.session_state['past'].append(user_input)
                    st.session_state['generated'].append(output)
            
        if st.session_state['generated']:
            with response_container:
                for i in range(len(st.session_state['generated'])):
                    message(st.session_state["past"][i], is_user=True, key=str(i) + '_user', avatar_style="fun-emoji", seed = 'Ginger')
                    message(st.session_state["generated"][i], key=str(i), avatar_style="bottts", seed = 'Dusty')
