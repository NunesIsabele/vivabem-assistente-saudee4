"""VivaBem: assistente educativo de prevenção, com interface nativa Streamlit."""

import logging
from copy import deepcopy
from datetime import datetime
from uuid import uuid4

import streamlit as st

from llm_provider import generate_response
from safety import ASSISTANT_INSTRUCTIONS


st.set_page_config(
    page_title="VivaBem | Saúde Preventiva",
    page_icon="💙",
    layout="wide",
)

MAX_SAVED_CONVERSATIONS = 20
MAX_MESSAGES_PER_CONVERSATION = 150
MAX_MESSAGE_LENGTH = 12000

# A interface do Streamlit gerencia o tema. Este componente apenas lê e salva
# o histórico no localStorage do navegador, sem criar elementos visuais.
LOCAL_HISTORY_JS = r"""
export default function(component) {
  const { data, setStateValue } = component;
  const storageKey = "vivabem_local_conversations_v1";

  if (data.action === "load") {
    if (!window.__vivabemHistoryLoaded) {
      let conversations = [];
      try {
        const saved = window.localStorage.getItem(storageKey);
        conversations = saved ? JSON.parse(saved) : [];
        if (!Array.isArray(conversations)) conversations = [];
      } catch (error) {
        conversations = [];
      }
      window.__vivabemHistoryLoaded = true;
      setStateValue("payload", { ready: true, conversations });
    }
    return;
  }

  if (data.action === "save") {
    try {
      window.localStorage.setItem(
        storageKey,
        JSON.stringify(data.conversations || [])
      );
    } catch (error) {
      console.error("Não foi possível salvar o histórico local.", error);
    }
  }
}
"""
LOCAL_HISTORY_COMPONENT = st.components.v2.component(
    "vivabem_local_conversation_history",
    js=LOCAL_HISTORY_JS,
)

HEALTH_REFERENCES = [
    (
        "Biblioteca Virtual em Saúde — Ministério da Saúde",
        "https://bvsms.saude.gov.br/",
    ),
    (
        "Guia de Atividade Física — Ministério da Saúde",
        "https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/guias-e-manuais/2021/guia-de-atividade-fisica-para-a-populacao-brasileira.pdf/view",
    ),
    (
        "Guia Alimentar — Ministério da Saúde",
        "https://www.gov.br/saude/pt-br/assuntos/saude-brasil/publicacoes-para-promocao-a-saude/guia_alimentar_populacao_brasileira_2ed.pdf/@@download/file",
    ),
    ("Tópicos de saúde — Organização Mundial da Saúde", "https://www.who.int/pt/health-topics"),
    ("Tópicos de saúde — Organização Pan-Americana da Saúde", "https://www.paho.org/pt/topicos"),
    ("Informação em Saúde — Fiocruz/Icict", "https://www.icict.fiocruz.br/informacao-em-saude"),
    (
        "Prevenção do câncer — INCA",
        "https://ninho.inca.gov.br/jspui/handle/123456789/17929?locale=pt_BR",
    ),
]


def clean_local_history(raw_history):
    """Valida e limita o histórico recebido do armazenamento do navegador."""
    if not isinstance(raw_history, list):
        return []

    cleaned = []
    for item in raw_history[-MAX_SAVED_CONVERSATIONS:]:
        if not isinstance(item, dict):
            continue

        raw_messages = item.get("messages", [])
        if not isinstance(raw_messages, list):
            continue

        messages = []
        for message in raw_messages[-MAX_MESSAGES_PER_CONVERSATION:]:
            if not isinstance(message, dict):
                continue
            role = message.get("role")
            content = message.get("content")
            if role in {"user", "assistant"} and isinstance(content, str):
                messages.append({"role": role, "content": content[:MAX_MESSAGE_LENGTH]})

        if not messages:
            continue

        conversation_id = item.get("id")
        title = item.get("title")
        updated_at = item.get("updated_at")
        cleaned.append(
            {
                "id": conversation_id[:80] if isinstance(conversation_id, str) and conversation_id else str(uuid4()),
                "title": title[:80] if isinstance(title, str) and title else "Conversa salva",
                "updated_at": updated_at[:40] if isinstance(updated_at, str) else "",
                "messages": messages,
            }
        )
    return cleaned


def conversation_label(conversation):
    """Cria o rótulo da conversa, tolerando datas antigas inválidas."""
    title = conversation.get("title", "Conversa salva")
    updated_at = conversation.get("updated_at", "")
    if updated_at:
        try:
            date_label = datetime.fromisoformat(updated_at).strftime("%d/%m/%Y %H:%M")
            return f"{title} · {date_label}"
        except ValueError:
            pass
    return title


if "local_history_ready" not in st.session_state:
    load_result = LOCAL_HISTORY_COMPONENT(
        data={"action": "load"},
        key="vivabem_load_history",
    )
    loaded_payload = getattr(load_result, "payload", None)
    if not isinstance(loaded_payload, dict) or not loaded_payload.get("ready"):
        st.info("Carregando conversas salvas neste navegador…")
        st.stop()

    st.session_state.local_conversations = clean_local_history(
        loaded_payload.get("conversations", [])
    )
    latest = (
        st.session_state.local_conversations[-1]
        if st.session_state.local_conversations
        else None
    )
    st.session_state.active_conversation_id = latest["id"] if latest else None
    st.session_state.messages = deepcopy(latest["messages"]) if latest else []
    st.session_state.local_history_ready = True

if "messages" not in st.session_state:
    st.session_state.messages = []


def save_current_conversation():
    """Atualiza a conversa ativa; a gravação local é feita pelo componente."""
    messages = st.session_state.messages
    if not messages:
        return

    conversation_id = st.session_state.active_conversation_id or str(uuid4())
    st.session_state.active_conversation_id = conversation_id
    conversation = next(
        (item for item in st.session_state.local_conversations if item["id"] == conversation_id),
        None,
    )
    if conversation is None:
        conversation = {"id": conversation_id}
        st.session_state.local_conversations.append(conversation)

    first_question = next(
        (message["content"] for message in messages if message["role"] == "user"),
        "Nova conversa",
    )
    conversation["title"] = first_question.strip().replace("\n", " ")[:48]
    conversation["updated_at"] = datetime.now().astimezone().isoformat(timespec="minutes")
    conversation["messages"] = deepcopy(messages[-MAX_MESSAGES_PER_CONVERSATION:])
    st.session_state.local_conversations.sort(key=lambda item: item.get("updated_at", ""))
    st.session_state.local_conversations = st.session_state.local_conversations[
        -MAX_SAVED_CONVERSATIONS:
    ]


def start_new_conversation():
    st.session_state.active_conversation_id = None
    st.session_state.messages = []


def reset_text_accessibility():
    st.session_state.font_scale = 100
    st.session_state.line_spacing = 1.6


# Cabeçalho principal inspirado na referência visual.
st.markdown(
    """
    <section class="hero-vivabem">
        <div class="hero-copy">
            <div class="hero-eyebrow">SEU ASSISTENTE DE SAÚDE E BEM-ESTAR</div>
            <h1>Olá!<br>Eu sou o <span>VivaBem</span></h1>
            <p>Pergunte, aprenda e cuide da sua saúde!</p>
            <div class="hero-notice">
                <span class="notice-icon">i</span>
                <span>Este protótipo é educativo. Não fazemos diagnósticos
                nem prescrevemos tratamentos ou medicamentos.</span>
            </div>
        </div>
        <div class="hero-art" aria-hidden="true">
            <div class="hero-heart">💙</div>
            <div class="hero-medical">🩺</div>
            <div class="hero-plus">+</div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Acessibilidade")
    st.slider(
        "Tamanho da letra",
        min_value=100,
        max_value=150,
        value=100,
        step=10,
        format="%d%%",
        key="font_scale",
        help="Ajusta o tamanho do texto do aplicativo.",
    )
    st.slider(
        "Espaçamento entre linhas",
        min_value=1.2,
        max_value=2.0,
        value=1.6,
        step=0.1,
        key="line_spacing",
        help="Ajusta a distância entre as linhas do texto.",
    )
    st.button("Restaurar texto padrão", on_click=reset_text_accessibility)
    st.divider()

    st.header("Sobre o VivaBem")
    st.write("Um protótipo de assistente para informações gerais de prevenção e bem-estar.")
    st.write(
        "As conversas ficam salvas neste navegador. Em computadores compartilhados, "
        "outras pessoas que usam o mesmo perfil podem ver o histórico. As mensagens "
        "enviadas continuam sendo processadas pelo Streamlit e pelo Gemini."
    )

    with st.expander("Fontes confiáveis de saúde"):
        st.write(
            "Links para consulta. O VivaBem não pesquisa a web automaticamente; "
            "as respostas do Gemini podem não usar estes materiais."
        )
        for title, url in HEALTH_REFERENCES:
            st.markdown(f"- [{title}]({url})")

    st.divider()
    st.subheader("Conversas neste navegador")
    conversations = st.session_state.local_conversations
    choices = [None] + [item["id"] for item in conversations]
    active_id = st.session_state.active_conversation_id
    selected_index = choices.index(active_id) if active_id in choices else 0

    selected_id = st.selectbox(
        "Abrir conversa salva",
        options=choices,
        index=selected_index,
        format_func=lambda value: (
            "Conversa nova"
            if value is None
            else next(
                (conversation_label(item) for item in conversations if item["id"] == value),
                "Conversa salva",
            )
        ),
    )
    if selected_id != st.session_state.active_conversation_id:
        st.session_state.active_conversation_id = selected_id
        selected_conversation = next(
            (item for item in conversations if item["id"] == selected_id),
            None,
        )
        st.session_state.messages = (
            deepcopy(selected_conversation["messages"]) if selected_conversation else []
        )
        st.rerun()

    st.button("Nova conversa", on_click=start_new_conversation, use_container_width=True)

    active_exists = st.session_state.active_conversation_id in [item["id"] for item in conversations]
    if st.button("Excluir conversa aberta", disabled=not active_exists, use_container_width=True):
        st.session_state.local_conversations = [
            item for item in conversations if item["id"] != st.session_state.active_conversation_id
        ]
        start_new_conversation()
        st.rerun()

    with st.expander("Apagar todo o histórico deste navegador"):
        st.caption("Isso remove as conversas salvas neste navegador e não pode ser desfeito.")
        if st.button("Apagar histórico salvo", use_container_width=True):
            st.session_state.local_conversations = []
            start_new_conversation()
            st.rerun()


font_scale = st.session_state.get("font_scale", 100) / 100
line_spacing = st.session_state.get("line_spacing", 1.6)
st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"],
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] *,
    [data-testid="stAppViewContainer"] [data-testid="stChatMessageContent"],
    [data-testid="stAppViewContainer"] [data-testid="stChatMessageContent"] *,
    [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"],
    [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"],
    [data-testid="stAppViewContainer"] [data-testid="stChatInput"] textarea,
    [data-testid="stAppViewContainer"] button,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] * {{
        font-size: calc(1rem * {font_scale}) !important;
        line-height: {line_spacing} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Estilo visual: azul, branco, cartões leves e bastante espaço em branco.
st.markdown(
    """
    <style>
    :root {
        --vb-blue: #1677e8;
        --vb-navy: #102b5c;
        --vb-pale: #eef5ff;
        --vb-border: #d7e6fb;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 78% 8%, rgba(202, 228, 255, .48), transparent 28%),
            linear-gradient(145deg, #fbfdff 0%, #f3f8ff 100%);
    }

    [data-testid="stHeader"] {
        background: rgba(255,255,255,.65);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #edf5ff 0%, #e5f0ff 100%);
        border-right: 1px solid #d5e5fa;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: var(--vb-navy);
    }

    [data-testid="stSidebar"] [data-testid="stButton"] button {
        border: 1px solid #c5daf8;
        border-radius: 18px;
        color: var(--vb-navy);
        background: rgba(255,255,255,.78);
    }

    [data-testid="stAppViewContainer"] .main .block-container {
        max-width: 1420px;
        padding-top: 2.2rem;
        padding-bottom: 2.5rem;
    }

    .hero-vivabem {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 2rem;
        min-height: 285px;
        padding: 2rem 2.4rem;
        margin: .2rem 0 2rem;
        overflow: hidden;
        border: 1px solid rgba(199, 222, 252, .8);
        border-radius: 28px;
        background: linear-gradient(112deg, #ffffff 0%, #f0f7ff 58%, #dceeff 100%);
        box-shadow: 0 12px 34px rgba(40, 102, 180, .08);
    }

    .hero-vivabem:after {
        content: "";
        position: absolute;
        width: 360px;
        height: 360px;
        right: 4%;
        top: -190px;
        border-radius: 50%;
        background: rgba(123, 190, 255, .16);
    }

    .hero-copy {
        position: relative;
        z-index: 1;
        max-width: 680px;
    }

    .hero-eyebrow {
        color: #4387d8;
        font-size: .76rem;
        font-weight: 800;
        letter-spacing: .12em;
        margin-bottom: .8rem;
    }

    .hero-vivabem h1 {
        color: var(--vb-navy);
        font-size: clamp(2.4rem, 5vw, 4.3rem);
        line-height: 1.02;
        letter-spacing: -.045em;
        margin: 0;
        font-weight: 800;
    }

    .hero-vivabem h1 span {
        color: var(--vb-blue);
    }

    .hero-vivabem p {
        color: #244675;
        font-size: 1.25rem;
        margin: .9rem 0 1.25rem;
    }

    .hero-notice {
        display: flex;
        align-items: center;
        gap: .8rem;
        max-width: 660px;
        padding: .85rem 1rem;
        border: 1px solid #c9e0ff;
        border-radius: 18px;
        color: #174b91;
        background: rgba(218, 235, 255, .78);
        font-size: .92rem;
        line-height: 1.45;
    }

    .notice-icon {
        display: inline-flex;
        flex: 0 0 32px;
        width: 32px;
        height: 32px;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        color: white;
        background: var(--vb-blue);
        font-weight: 800;
        font-size: 1.15rem;
        font-family: Georgia, serif;
    }

    .hero-art {
        position: relative;
        z-index: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        flex: 0 0 260px;
        height: 220px;
        border-radius: 48% 52% 44% 56%;
        background: radial-gradient(circle, #ffffff 0%, #d9edff 68%, rgba(217,237,255,0) 70%);
    }

    .hero-heart {
        font-size: 8rem;
        filter: drop-shadow(0 12px 12px rgba(28, 100, 190, .18));
    }

    .hero-medical {
        position: absolute;
        right: 2px;
        bottom: 8px;
        font-size: 4rem;
        transform: rotate(-12deg);
        filter: drop-shadow(0 5px 5px rgba(28, 100, 190, .15));
    }

    .hero-plus {
        position: absolute;
        left: 25px;
        top: 24px;
        color: #398ce8;
        font-size: 2.4rem;
        font-weight: 800;
    }

    .section-heading {
        color: var(--vb-navy);
        text-align: center;
        font-size: 1.65rem;
        font-weight: 800;
        margin: 1.3rem 0 1.15rem;
    }

    .topic-card {
        min-height: 220px;
        padding: 1.25rem 1.35rem;
        border: 1px solid var(--vb-border);
        border-radius: 23px;
        background: rgba(255,255,255,.92);
        box-shadow: 0 7px 18px rgba(38, 100, 180, .08);
    }

    .topic-icon {
        font-size: 3.8rem;
        line-height: 1.2;
        margin-bottom: .5rem;
    }

    .topic-card h3 {
        color: var(--vb-navy);
        font-size: 1.25rem;
        line-height: 1.2;
        margin: .25rem 0 .55rem;
    }

    .topic-card p {
        color: #365477;
        font-size: .96rem;
        line-height: 1.45;
        margin: 0;
    }

    [data-testid="stButton"] button {
        border-radius: 16px;
        border: 1px solid #c8ddfa;
        color: #145bb2;
        background: #e7f1ff;
        font-weight: 650;
        transition: all .15s ease;
    }

    [data-testid="stButton"] button:hover {
        border-color: #78b2f5;
        color: #0c4f9f;
        background: #d8eaff;
    }

    [data-testid="stChatInput"] {
        border: 1px solid #cbdff8;
        border-radius: 22px;
        background: white;
        box-shadow: 0 6px 18px rgba(38, 100, 180, .08);
    }

    [data-testid="stChatMessage"] {
        border: 1px solid #e0ebf8;
        border-radius: 18px;
        background: rgba(255,255,255,.82);
        padding: .8rem 1rem;
    }

    [data-testid="stAlert"] {
        border-radius: 16px;
    }

    @media (max-width: 850px) {
        .hero-vivabem {
            padding: 1.5rem;
            min-height: auto;
        }
        .hero-art {
            flex-basis: 150px;
            height: 150px;
        }
        .hero-heart { font-size: 5rem; }
        .hero-medical { font-size: 2.5rem; }
    }

    @media (max-width: 600px) {
        .hero-art { display: none; }
        .hero-vivabem { padding: 1.25rem; }
        .hero-vivabem p { font-size: 1.05rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown(
        '<div class="section-heading">Escolha um assunto para começar</div>',
        unsafe_allow_html=True,
    )
    suggestions = [
        {
            "icon": "🍎",
            "title": "Alimentação e hidratação",
            "tip": "Dicas e orientações para uma vida mais saudável.",
            "prompt": "Quais hábitos gerais ajudam a manter uma alimentação variada e uma boa hidratação?",
        },
        {
            "icon": "👟",
            "title": "Atividade física",
            "tip": "Movimente-se e cuide do seu corpo.",
            "prompt": "Que hábitos gerais ajudam a incluir atividade física com segurança na rotina?",
        },
        {
            "icon": "🛏️",
            "title": "Sono e descanso",
            "tip": "Melhore sua rotina de sono e descanso.",
            "prompt": "Quais hábitos gerais podem ajudar a melhorar a rotina de sono e descanso?",
        },
    ]

    suggestion_columns = st.columns(3, gap="large")
    for index, (column, suggestion) in enumerate(zip(suggestion_columns, suggestions)):
        with column:
            st.markdown(
                f"""
                <div class="topic-card">
                    <div class="topic-icon">{suggestion['icon']}</div>
                    <h3>{suggestion['title']}</h3>
                    <p>{suggestion['tip']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "Explorar assunto  →",
                key=f"suggestion_{index}",
                use_container_width=True,
            ):
                st.session_state.suggestion_prompt = suggestion["prompt"]
                st.rerun()


def render_chat_message(message):
    """Usa a apresentação nativa de mensagens do Streamlit."""
    avatar = "🙂" if message["role"] == "user" else "💙"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])


for saved_message in st.session_state.messages:
    render_chat_message(saved_message)

typed_prompt = st.chat_input("Escreva uma pergunta geral...")
prompt = st.session_state.pop("suggestion_prompt", None) or typed_prompt

if prompt:
    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)
    save_current_conversation()
    render_chat_message(user_message)

    with st.chat_message("assistant", avatar="💙"):
        with st.spinner("Preparando uma resposta..."):
            try:
                answer = generate_response(prompt, ASSISTANT_INSTRUCTIONS)
            except Exception:
                logging.exception("Falha ao consultar o Gemini")
                st.error(
                    "Não consegui consultar o Gemini. Confira se a chave está "
                    "configurada e tente novamente."
                )
            else:
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                save_current_conversation()


LOCAL_HISTORY_COMPONENT(
    data={
        "action": "save",
        "conversations": st.session_state.local_conversations,
    },
    key="vivabem_save_history",
)
