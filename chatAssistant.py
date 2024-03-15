import openai
import streamlit as st
from bs4 import BeautifulSoup
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
import urllib
import pandas as pd

load_dotenv()
#id do assistente
assistant_id = "asst_RyDmETRf7S9E7gPmXje6HKwD"

# inicializa cliente openai
client = openai

# inicializa a sessão para ler os ids
if "file_id_list" not in st.session_state:
    st.session_state.file_id_list = []

if "start_chat" not in st.session_state:
    st.session_state.start_chat = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# titulo e icone da página
# Função para converter XLSX pra PDF

def convert_xlsx_to_markdown(input_path, output_path) :
    # Read and store content
    # of an excel file
    read_file = pd.read_csv(input_path)

    # Write the dataframe object
    # into csv file
    read_file.to_markdown(output_path)

def convert_xlsx_to_pdf(input_path, output_path):
    workbook = load_workbook(input_path)
    sheets = workbook.sheetnames

    pdf = canvas.Canvas(output_path, pagesize=letter)

    for sheet_name in sheets:
        sheet = workbook[sheet_name]

        for row in sheet.iter_rows():
            for cell in row:
                pdf.drawString(cell.column * 50, letter[1] - cell.row * 10, str(cell.value))

    pdf.save()

perguntas = [
    "Qual faixa etária apresentou o maior volume de pedidos e qual foi o valor médio destes pedidos?",
    "Há diferenças significativas nos padrões de compra entre os diferentes gêneros listados no documento?",
    "Qual foi o ticket médio dos pedidos aprovados comparado com os pedidos não aprovados? Isso pode indicar alguma tendência ou comportamento específico dos consumidores?",
    "Qual é a taxa de aprovação dos pedidos recebidos e como ela se distribui entre as diferentes cidades ou estados?",
    "A localização impacta o valor médio dos pedidos ou a preferência por formas de pagamento?",
    "Comparando os dados de agosto de 2023 com meses anteriores, existe alguma tendência de crescimento ou decréscimo nas transações?",
]

pergunta_ = ""

def download_file(file) :
    file = urllib.request.urlopen(file)
    return file

# Função pra enviar arquivo convertido pra OpenAI
def upload_to_openai(filepath):
    with open(filepath, "rb") as file:
        response = openai.files.create(file=file.read(), purpose="assistants")
        return response.id

#local
#api_key = os.getenv("OPENAI_API_KEY")
#git
api_key = st.secrets.OpenAIAPI.openai_api_key
if api_key:
    openai.api_key = api_key

#st.sidebar.write("<a style='color:white'  href='https://tecnologia2.chleba.net/_ftp/chatgpt/BotasVentoPedidos.xlsx' id='baixarArquivo'>[Baixe o arquivo para fazer a análise]</a>", unsafe_allow_html=True)

#uploaded_file = st.sidebar.file_uploader("Envie um arquivo", key="file_uploader")
# Botão para iniciar o chat
if st.sidebar.button("Iniciar"):

    if not st.session_state.file_id_list:
        ds = client.beta.assistants.files.list(assistant_id=assistant_id)
        for file in ds:
            client.beta.assistants.files.delete(assistant_id=assistant_id, file_id=file.id)

    uploaded_file = download_file("https://tecnologia2.chleba.net/_ftp/chatgpt/BotasVentoPedidos.csv")
    if uploaded_file:
        # Converter XLSX para PDF
        pdf_output_path = "converted_file.xls"
        convert_xlsx_to_markdown(uploaded_file, pdf_output_path)
        # Enviar o arquivo convertido
        additional_file_id = upload_to_openai(pdf_output_path)

        st.session_state.file_id_list.append(additional_file_id)
        #st.sidebar.write(f"ID do arquivo: {additional_file_id}")

    # Mostra os ids
    if st.session_state.file_id_list:
        #st.sidebar.write("IDs dos arquivos enviados:")
        for file_id in st.session_state.file_id_list:
            #st.sidebar.write(file_id)


            # Associa os arquivos ao assistente
            assistant_file = client.beta.assistants.files.create(
                assistant_id=assistant_id,
                file_id=file_id
            )


    # Verifica se o arquivo foi upado antes de iniciar
    if st.session_state.file_id_list:
        st.session_state.start_chat = True
        # Cria a thread e guarda o id na sessão
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        st.write("id da thread: ", thread.id)
    else:
        st.sidebar.warning("Por favor, selecione pelo menos um arquivo para iniciar o chat")


if st.session_state.start_chat:
    on = st.sidebar.toggle('Ver sugestões de perguntas', value=True)

    if on:
        for indice, pergunta in enumerate(perguntas):
            # st.sidebar.write(f"<a style=\"color:white;display:flex;align-items:center;gap:26px;text-decoration:none\" target=\"_self\" id=\"pergunta{indice}\" href=\"javascript:(function(){{var conteudo = document.getElementById('pergunta{indice}').innerText; navigator.clipboard.writeText(conteudo).then(function() {{ console.log('Conteúdo copiado para a área de transferência: ' + conteudo); }}, function(err) {{ console.error('Erro ao copiar conteúdo: ', err); }});}})()\">{pergunta}<span>{icon_copy}</span></a>", unsafe_allow_html=True)
            if st.sidebar.button(f"{pergunta}"):
                pergunta_ = pergunta

    st.sidebar.write('<style>label[data-baseweb="checkbox"] > div > div {background: #282828}</style>', unsafe_allow_html=True)
# Define a função para iniciar
def process_message_with_citations(message):
    """Extract content and annotations from the message and format citations as footnotes."""
    message_content = message.content[0].text
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

# Interface do chat
st.subheader("ANÁLISE DE PEDIDOS")
#st.write("Este chat usa a API da OpenAI para gerar respostas.")

# Só vai mostrar o chat se for iniciado
if st.session_state.start_chat:
    # Inicializa o modelo usado
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4-turbo-preview"
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostra mensagens anteriores
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt_ =  st.chat_input("Faça uma pergunta!" )

    if pergunta_ :
        prompt = pergunta_

    if not pergunta_ :
        prompt = prompt_

    # Campo pro usuário escrever
    if prompt:
        # Adiciona as mensagens do usuário e mostra no chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Adiciona as mensagens criadas na thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )

        # Cria a requisição com mais instruções
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
            instructions="Por favor, responda as perguntas usando o conteúdo do arquivo. Quando adicionar informações externas, seja claro e mostre essas informações em outra cor."
        )

        # Pedido para finalizar a requisição e retornar as mensagens do assistente
        while run.status != 'completed':
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )

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
            full_response = process_message_with_citations(message)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            with st.chat_message("assistant"):
                st.markdown(full_response, unsafe_allow_html=True)
else:
    # Prompt pra iniciar o chat
    st.write("Por favor, selecione o(s) arquivo(s) e clique em *iniciar chat* para gerar respostas")
