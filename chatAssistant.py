import openai
import streamlit as st
from faker.decode import unidecode
import os
from dotenv import load_dotenv

from packages.chatOpenAi import chat_openai

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

perguntas = [
    "Qual faixa etária apresentou o maior volume de pedidos e qual foi o valor médio destes pedidos?",
    "Há diferenças significativas nos padrões de compra entre os diferentes gêneros listados no documento?",
    "Qual foi o ticket médio dos pedidos aprovados comparado com os pedidos não aprovados? Isso pode indicar alguma tendência ou comportamento específico dos consumidores?",
    "Qual é a taxa de aprovação dos pedidos recebidos e como ela se distribui entre as diferentes cidades ou estados?",
    "A localização impacta o valor médio dos pedidos ou a preferência por formas de pagamento?",
    "Comparando os dados de agosto de 2023 com meses anteriores, existe alguma tendência de crescimento ou decréscimo nas transações?",
]

pergunta_ = ""

#local
#api_key = os.getenv("OPENAI_API_KEY")
#git
api_key = st.secrets.OpenAIAPI.openai_api_key
#Faça a apresentação do valor aprovado e valor recebido por mes dos ultimos 12 meses e utilize gráficos em visualizações para facilitar a interpretação dos resultados. Forneça insights sobre o que pode ter impactados os 3 meses com menor volume de vendas e o que pode tem impactado os 3 meses com maior volume de vendas. Forneça recomendações para aumentar as vendas aprovadas.


if api_key:
    openai.api_key = api_key

st.sidebar.write('<style>p, ol, ul, dl {font-size:0.9rem}</style>', unsafe_allow_html=True)

if not st.session_state.start_chat:
    if True:
        #if uploaded_file:
        ds = client.beta.assistants.files.list(assistant_id=assistant_id)
        if ds:
            for file in ds:
                st.session_state.file_id_list.append(file.id)
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
            #st.write("id da thread: ", thread.id)
        else:
            st.sidebar.warning("Por favor, clique em \"Iniciar análise\" iniciar o chat")

if st.session_state.start_chat:
    on = st.sidebar.toggle('Ver sugestões de perguntas', value=True)
    search = st.sidebar.text_input("Pesquisar perguntas sugeridas")

    if on:
        for indice, pergunta in enumerate(perguntas):
            # st.sidebar.write(f"<a style=\"color:white;display:flex;align-items:center;gap:26px;text-decoration:none\" target=\"_self\" id=\"pergunta{indice}\" href=\"javascript:(function(){{var conteudo = document.getElementById('pergunta{indice}').innerText; navigator.clipboard.writeText(conteudo).then(function() {{ console.log('Conteúdo copiado para a área de transferência: ' + conteudo); }}, function(err) {{ console.error('Erro ao copiar conteúdo: ', err); }});}})()\">{pergunta}<span>{icon_copy}</span></a>", unsafe_allow_html=True)
            if unidecode(search.lower()) in unidecode(pergunta.lower()):
                if st.sidebar.button(f"{pergunta}"):
                    pergunta_ = pergunta


    st.sidebar.write('<style>label[data-baseweb="checkbox"] > div > div {background: #282828}</style>', unsafe_allow_html=True)

# Interface do chat
st.subheader("ANÁLISE DE PEDIDOS")

#st.write("Este chat usa a API da OpenAI para gerar respostas.")
st.session_state.is_running = False

# Só vai mostrar o chat se for iniciado
if st.session_state.start_chat:
    chat_openai(pergunta_, client, assistant_id, "Obs. Toda vez que você se referir ao arquivo, fale que é a base de dados (o cliente não precisa saber que o arquivo foi enviado), não fale que irá 'analisar o arquivo' e sim a base")

else:
    # Prompt pra iniciar o chat
    st.write("Por favor, selecione o(s) arquivo(s) e clique em *iniciar chat* para gerar respostas")
