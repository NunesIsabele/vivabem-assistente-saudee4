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
    page_icon="🌿",
    layout="centered",
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


st.title("🌿 VivaBem")
st.caption("Informações gerais sobre prevenção e hábitos saudáveis.")
st.info(
    "Este protótipo é educativo. Não fazemos diagnósticos nem prescrevemos tratamentos "
    "ou medicamentos. Não envie dados pessoais ou informações reais de saúde. "
    "Em uma emergência, procure imediatamente um serviço de saúde local."
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

if not st.session_state.messages:
    st.subheader("Quer uma ideia para começar?")
    suggestions = [
        {
            "icon": "🥗",
            "title": "Alimentação e hidratação",
            "tip": "Pequenas escolhas e uma rotina de hidratação podem fazer parte do cuidado diário.",
            "prompt": "Quais hábitos gerais ajudam a manter uma alimentação variada e uma boa hidratação?",
        },
        {
            "icon": "🚶",
            "title": "Atividade física",
            "tip": "Movimentar o corpo de um jeito possível e agradável ajuda a construir uma rotina mais ativa.",
            "prompt": "Que hábitos gerais ajudam a incluir atividade física com segurança na rotina?",
        },
        {
            "icon": "🌙",
            "title": "Sono e descanso",
            "tip": "Horários regulares e um ambiente tranquilo podem apoiar uma rotina de descanso melhor.",
            "prompt": "Quais hábitos gerais podem ajudar a melhorar a rotina de sono e descanso?",
        },
    ]
    suggestion_columns = st.columns(len(suggestions))
    for index, (column, suggestion) in enumerate(zip(suggestion_columns, suggestions)):
        with column:
            with st.container(
                height=300,
                border=True,
                vertical_alignment="distribute",
            ):
                st.markdown(f"### {suggestion['icon']} {suggestion['title']}")
                st.write(suggestion["tip"])
                if st.button(
                    "Perguntar sobre isso",
                    key=f"suggestion_{index}",
                    use_container_width=True,
                ):
                    st.session_state.suggestion_prompt = suggestion["prompt"]
                    st.rerun()


def render_chat_message(message):
    """Usa a apresentação nativa de mensagens do Streamlit."""
    avatar = "🙂" if message["role"] == "user" else "🌿"
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

    with st.chat_message("assistant", avatar="🌿"):
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
