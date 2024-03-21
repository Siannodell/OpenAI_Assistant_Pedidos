import base64

import openai
import streamlit as st
from bs4 import BeautifulSoup
from faker.decode import unidecode
from streamlit.components.v1 import html
import requests
import pdfkit
import time
import os
from dotenv import load_dotenv
from openpyxl import load_workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from PIL import Image
import urllib
import pandas as pd
import threading

def verificar_id(array, id_procurado):
    # Itera sobre os elementos do array
    for item in array:
        # Verifica se o ID do item atual é igual ao ID procurado
        if item['id'] == id_procurado:
            return True  # Se encontrado, retorna True
    return False  # Se não encontrado, retorna False


def process_message_with_citations(message):
    """Extract content and annotations from the message and format citations as footnotes."""
    message_content = message.text
    annotations = message_content.annotations if hasattr(message_content, 'annotations') else []
    citations = []

    # for nas annotations
    for index, annotation in enumerate(annotations):
        # substitui o texto da mensagem
        message_content.value = message_content.value.replace(annotation.text, f' [{index + 1}]')

        if (file_citation := getattr(annotation, 'file_citation', None)):
            cited_file = {'filename': 'cited_document.pdf'}  # Substituído pelo arquivo retornado
            citations.append(f'[{index + 1}] {file_citation.quote} from {cited_file["filename"]}')
        elif (file_path := getattr(annotation, 'file_path', None)):
            # Placeholder for file download citation
            cited_file = {'filename': 'downloaded_document.pdf'}  # Substituído pelo arquivo retornado
            citations.append(f'[{index + 1}] Click [here](#) to download {cited_file["filename"]}')  # Link de download substituído pelo caminho do arquivo

    # Adiciona notas no final da mensgaem (talvez tirar)
    full_response = message_content.value
    return full_response


def getImage(file_id) :
    image_file_id = file_id
    image_file = openai.files.content(image_file_id)
    bites = BytesIO(base64.b64decode(image_file.content))
    aux_im = Image.open(BytesIO(image_file.content))
    return aux_im

def chat_openai(pergunta_,client, assistant_id):
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4-turbo-preview"
    if "messages" not in st.session_state:
        st.session_state.messages = []

        # Mostra mensagens anteriores
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["typeFile"] == "text":
                st.markdown(message["content"], unsafe_allow_html=True)

            if message["typeFile"] == "image":
                image = getImage(message["content"])
                st.image(image)

    prompt_ = st.chat_input("Faça uma pergunta!", disabled=st.session_state.is_running)
    if st.session_state.is_running:
        st.status("Estamos analisando...")

    if pergunta_:
        prompt = pergunta_

    if not pergunta_:
        prompt = prompt_

    # Campo pro usuário escrever
    if prompt:
        st.session_state.is_running = True
        # Adiciona as mensagens do usuário e mostra no chat
        st.session_state.messages.append({"role": "user", "content": prompt, "typeFile": "text", "id": ""})
        with st.chat_message("user"):
            st.markdown(prompt, unsafe_allow_html=True)

        # Adiciona as mensagens criadas na thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt + " Obs. Toda vez que você se referir ao arquivo, fale que é a base de dados (o cliente não precisa saber que o arquivo foi enviado), não fale que irá 'analisar o arquivo' e sim a base",
            file_ids=st.session_state.file_id_list,
        )

        # Cria a requisição com mais instruções
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
        )

        # Pedido para finalizar a requisição e retornar as mensagens do assistente
        while run.status != 'completed':
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
            # Processa e mostra as mensagens do assistente
            assistant_messages_for_run = [
                message for message in messages
                if message.run_id == run.id and message.role == "assistant" and len(message.content) > 0
            ]

            print(assistant_messages_for_run)

            for message in assistant_messages_for_run[::-1]:
                if not verificar_id(st.session_state.messages, message.id):
                    for messageInt in message.content:
                        # print(message)
                        if messageInt.type == "text":
                            full_response = process_message_with_citations(messageInt)
                            st.session_state.messages.append(
                                {"role": "assistant", "content": full_response, "typeFile": "text", "id": message.id})

                            with st.chat_message("assistant"):
                                st.markdown(full_response, unsafe_allow_html=True)

                        if messageInt.type == "image_file":
                            image = getImage(messageInt.image_file.file_id)
                            if image:
                                st.session_state.messages.append(
                                    {"role": "assistant", "content": messageInt.image_file.file_id, "typeFile": "image",
                                     "id": message.id})
                                with st.chat_message("assistant"):
                                    st.image(getImage(messageInt.image_file.file_id))
                        st.spinner(text="In progress...")
        # Retorna as mensagens do assistente
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # Processa e mostra as mensagens do assistente
        assistant_messages_for_run = [
            message for message in messages
            if message.run_id == run.id and message.role == "assistant"
        ]

        for message in assistant_messages_for_run[::-1]:
            if not verificar_id(st.session_state.messages, message.id):
                for messageInt in message.content:
                    # print(message)
                    if messageInt.type == "text":
                        full_response = process_message_with_citations(messageInt)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": full_response, "typeFile": "text", "id": message.id})

                        with st.chat_message("assistant"):
                            st.markdown(full_response, unsafe_allow_html=True)

                    if messageInt.type == "image_file":
                        image = getImage(messageInt.image_file.file_id)
                        if image:
                            st.session_state.messages.append(
                                {"role": "assistant", "content": messageInt.image_file.file_id, "typeFile": "image",
                                 "id": message.id})
                            with st.chat_message("assistant"):
                                st.image(getImage(messageInt.image_file.file_id))

        st.session_state.is_running = False
