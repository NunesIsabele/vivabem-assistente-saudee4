"""Interface do VivaBem com acessibilidade e sem busca automática na web."""

import logging

import streamlit as st

from llm_provider import generate_response
from safety import ASSISTANT_INSTRUCTIONS


st.set_page_config(
    page_title="VivaBem | Saúde Preventiva",
    page_icon="🌿",
    layout="centered",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

PALETTE_LIGHT = {
    "Amarelo": "#806000",
    "Verde": "#1F6D49",
    "Azul": "#205A9C",
    "Roxo": "#5D3FA1",
    "Laranja": "#9C4B10",
}

PALETTE_DARK = {
    "Amarelo": "#F4D35E",
    "Verde": "#65C995",
    "Azul": "#80B5FF",
    "Roxo": "#BEA2FF",
    "Laranja": "#FFAE70",
}

HEALTH_REFERENCES = [
    (
        "Biblioteca Virtual em Saúde — Ministério da Saúde",
        "https://bvsms.saude.gov.br/",
    ),
    (
        "Guia de Atividade Física para a População Brasileira — Ministério da Saúde",
        "https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/guias-e-manuais/2021/guia-de-atividade-fisica-para-a-populacao-brasileira.pdf/view",
    ),
    (
        "Guia Alimentar para a População Brasileira — Ministério da Saúde",
        "https://www.gov.br/saude/pt-br/assuntos/saude-brasil/publicacoes-para-promocao-a-saude/guia_alimentar_populacao_brasileira_2ed.pdf/@@download/file",
    ),
    (
        "Tópicos de saúde — Organização Mundial da Saúde (OMS)",
        "https://www.who.int/pt/health-topics",
    ),
    (
        "Tópicos de saúde — Organização Pan-Americana da Saúde (OPAS)",
        "https://www.paho.org/pt/topicos",
    ),
    (
        "Informação em Saúde — Fiocruz/Icict",
        "https://www.icict.fiocruz.br/informacao-em-saude",
    ),
    (
        "Recomendações para prevenir o câncer — INCA",
        "https://ninho.inca.gov.br/jspui/handle/123456789/17929?locale=pt_BR",
    ),
]


def reset_accessibility_settings():
    """Restaura os valores iniciais dos controles de acessibilidade."""
    st.session_state.theme_mode = "Claro"
    st.session_state.accent_color = "Amarelo"
    st.session_state.high_contrast = False
    st.session_state.font_scale = 100
    st.session_state.line_spacing = 1.6
    st.session_state.reduce_motion = True


with st.sidebar:
    st.markdown("## Acessibilidade")
    st.caption("Personalize a aparência e a leitura do VivaBem.")

    st.selectbox("Tema", ["Claro", "Escuro"], key="theme_mode")
    st.selectbox("Cor de destaque", list(PALETTE_LIGHT), key="accent_color")
    st.checkbox("Ativar alto contraste", key="high_contrast")
    st.slider(
        "Tamanho do texto",
        min_value=100,
        max_value=150,
        value=100,
        step=10,
        format="%d%%",
        key="font_scale",
        help="Aumenta o texto da conversa, dos avisos e dos controles.",
    )
    st.slider(
        "Espaçamento entre linhas",
        min_value=1.4,
        max_value=2.0,
        value=1.6,
        step=0.1,
        key="line_spacing",
        help="Aumenta o espaço vertical entre as linhas do texto.",
    )
    st.checkbox("Reduzir animações", key="reduce_motion", value=True)
    st.button(
        "Restaurar padrão",
        use_container_width=True,
        on_click=reset_accessibility_settings,
    )

    st.divider()
    st.markdown("### Sobre o VivaBem")
    st.write("Um protótipo de assistente para informações gerais de prevenção e bem-estar.")
    st.markdown("**Importante**")
    st.caption(
        "Não fazemos diagnósticos nem prescrevemos tratamentos ou medicamentos. "
        "Em uma emergência, procure imediatamente um serviço de saúde local."
    )
    with st.expander("Fontes confiáveis de saúde"):
        st.caption(
            "Links para consulta. O VivaBem não pesquisa a web automaticamente; "
            "as respostas do Gemini podem não usar estes materiais."
        )
        for title, url in HEALTH_REFERENCES:
            st.markdown(f"- [{title}]({url})")

    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


theme_is_dark = st.session_state.get("theme_mode", "Claro") == "Escuro"
high_contrast = st.session_state.get("high_contrast", False)
font_scale = st.session_state.get("font_scale", 100) / 100
line_spacing = st.session_state.get("line_spacing", 1.6)
reduce_motion = st.session_state.get("reduce_motion", True)
accent_palette = PALETTE_DARK if theme_is_dark else PALETTE_LIGHT
accent = accent_palette.get(st.session_state.get("accent_color", "Amarelo"), "#806000")

if high_contrast:
    page_bg = "#000000"
    panel_bg = "#0B0B0B"
    message_bg = "#111111"
    text_color = "#FFFFFF"
    muted_color = "#FFFFFF"
    border_color = "#FFFFFF"
    accent = "#FFFF00"
    sidebar_bg = "#000000"
    sidebar_text = "#FFFFFF"
    sidebar_muted = "#FFFFFF"
    sidebar_control_bg = "#0B0B0B"
    sidebar_control_text = "#FFFFFF"
    sidebar_border = "#FFFFFF"
    notice_bg = "#000000"
    notice_text = "#FFFF00"
elif theme_is_dark:
    page_bg = "#101925"
    panel_bg = "#1B2938"
    message_bg = "#1B2938"
    text_color = "#F4F7FB"
    muted_color = "#D0DAE5"
    border_color = "#71849A"
    sidebar_bg = "#14263D"
    sidebar_text = "#FFFFFF"
    sidebar_muted = "#E8EEF5"
    sidebar_control_bg = "#0B1017"
    sidebar_control_text = "#FFFFFF"
    sidebar_border = "#AAB8C8"
    notice_bg = "#332B12"
    notice_text = "#FFF2B3"
else:
    page_bg = "#F7F9FC"
    panel_bg = "#FFFFFF"
    message_bg = "#E9EEF5"
    text_color = "#14263D"
    muted_color = "#35485E"
    border_color = "#8796A8"
    sidebar_bg = "#E8EDF3"
    sidebar_text = "#14263D"
    sidebar_muted = "#35485E"
    sidebar_control_bg = "#FFFFFF"
    sidebar_control_text = "#14263D"
    sidebar_border = "#65778C"
    notice_bg = "#FFF6CC"
    notice_text = "#322800"

motion_css = (
    "* { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; "
    "scroll-behavior: auto !important; }"
    if reduce_motion
    else ""
)

st.markdown(
    f"""
    <style>
    :root {{
        --page-bg: {page_bg};
        --panel-bg: {panel_bg};
        --message-bg: {message_bg};
        --text-color: {text_color};
        --muted-color: {muted_color};
        --border-color: {border_color};
        --accent-color: {accent};
        --sidebar-bg: {sidebar_bg};
        --sidebar-text: {sidebar_text};
        --sidebar-muted: {sidebar_muted};
        --sidebar-control-bg: {sidebar_control_bg};
        --sidebar-control-text: {sidebar_control_text};
        --sidebar-border: {sidebar_border};
        --font-scale: {font_scale};
        --line-spacing: {line_spacing};
    }}
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
        background: var(--page-bg);
        color: var(--text-color);
        font-size: calc(16px * var(--font-scale));
    }}
    [data-testid="stHeader"] {{ background: var(--page-bg); }}
    [data-testid="stSidebar"] > div {{ background: var(--sidebar-bg); }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
    [data-testid="stSidebar"] [data-testid="stCheckbox"] label,
    [data-testid="stSidebar"] [data-testid="stCheckbox"] label *,
    [data-testid="stSidebar"] [data-testid="stSlider"] label,
    [data-testid="stSidebar"] [data-testid="stSlider"] label * {{
        color: var(--sidebar-text) !important;
        opacity: 1 !important;
    }}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        color: var(--sidebar-muted) !important;
        opacity: 1 !important;
        line-height: var(--line-spacing) !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background: var(--sidebar-control-bg) !important;
        border: 1px solid var(--sidebar-border) !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-baseweb="select"] input {{
        color: var(--sidebar-control-text) !important;
        opacity: 1 !important;
    }}
    [data-testid="stSidebar"] button {{
        color: var(--sidebar-control-text) !important;
        background: var(--sidebar-control-bg) !important;
        border: 1px solid var(--sidebar-border) !important;
        border-radius: 9px !important;
        opacity: 1 !important;
    }}
    [data-testid="stSidebar"] button:hover {{ border-color: var(--accent-color) !important; }}
    [data-testid="stSidebar"] [data-baseweb="slider"] {{ color: var(--accent-color) !important; }}
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] strong,
    [data-testid="stChatMessageContent"], [data-testid="stChatMessageContent"] *,
    [data-testid="stAlert"] *, [data-testid="stCaptionContainer"] {{
        color: var(--text-color) !important;
        line-height: var(--line-spacing) !important;
        font-size: calc(1rem * var(--font-scale)) !important;
    }}
    [data-testid="stMarkdownContainer"] a {{
        color: var(--accent-color) !important;
        text-decoration: underline !important;
    }}
    [data-testid="stAlert"] {{
        background: var(--message-bg) !important;
        border: 1px solid var(--border-color) !important;
    }}
    [data-testid="stChatMessage"] {{
        background: var(--message-bg);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: .7rem .9rem;
    }}
    [data-testid="stChatInput"] textarea {{
        color: var(--text-color) !important;
        background: var(--panel-bg) !important;
        border-color: var(--border-color) !important;
        font-size: calc(1rem * var(--font-scale)) !important;
    }}
    [data-testid="stChatInput"] textarea::placeholder {{ color: var(--muted-color) !important; }}
    [data-testid="stChatInput"] > div, [data-testid="stChatInput"] {{
        background: var(--panel-bg) !important;
        border-color: var(--border-color) !important;
    }}
    [data-baseweb="popover"] [role="listbox"],
    [data-baseweb="popover"] [role="option"] {{
        color: var(--text-color) !important;
        background: var(--panel-bg) !important;
    }}
    [data-testid="stSidebar"] button:focus,
    [data-testid="stSidebar"] input:focus,
    [data-testid="stSidebar"] [role="combobox"]:focus,
    [data-testid="stChatInput"] textarea:focus {{
        outline: 3px solid var(--accent-color) !important;
        outline-offset: 2px !important;
    }}
    .block-container {{ max-width: 900px; padding-top: 1.5rem; }}
    .hero {{
        padding: 1.5rem 1.8rem;
        border-radius: 18px;
        color: var(--text-color);
        background: var(--panel-bg);
        border: 2px solid var(--accent-color);
        margin-bottom: 1rem;
    }}
    .hero h1 {{ margin: 0; font-size: calc(2rem * var(--font-scale)); color: var(--text-color); }}
    .hero p {{ margin: .5rem 0 0; color: var(--muted-color); font-size: calc(1rem * var(--font-scale)); }}
    .notice {{
        padding: .9rem 1rem;
        border-radius: 12px;
        background: {notice_bg};
        border: 2px solid var(--accent-color);
        color: {notice_text};
        font-size: calc(.95rem * var(--font-scale));
        line-height: var(--line-spacing);
        margin-bottom: 1rem;
    }}
    .notice * {{ color: {notice_text} !important; }}
    {motion_css}
    </style>
    <div class="hero">
      <h1>🌿 VivaBem</h1>
      <p>Seu espaço para conversar sobre prevenção e hábitos saudáveis.</p>
    </div>
    <div class="notice">
      <strong>Aviso:</strong> este protótipo tem finalidade educativa e não substitui atendimento
      profissional. Não envie dados pessoais ou informações reais de saúde. Em uma emergência,
      procure um serviço de saúde local.
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.info("Olá! Você pode perguntar sobre hábitos gerais de prevenção e bem-estar.")

for message in st.session_state.messages:
    avatar = "🙂" if message["role"] == "user" else "🌿"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            st.caption("Resposta gerada pelo Gemini, sem pesquisa automática na web.")

prompt = st.chat_input("Escreva uma pergunta geral...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🙂"):
        st.markdown(prompt)

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
                st.caption("Resposta gerada pelo Gemini, sem pesquisa automática na web.")
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )