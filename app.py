"""Interface do VivaBem com controles básicos de acessibilidade."""

import streamlit as st

from llm_provider import generate_response, generate_response_with_sources
from safety import ASSISTANT_INSTRUCTIONS


st.set_page_config(
    page_title="VivaBem | Saúde Preventiva",
    page_icon="🌿",
    layout="centered",
)


PALETTE = {
    "Amarelo": "#F4D35E",
    "Verde": "#1F6D49",
    "Azul": "#205A9C",
    "Roxo": "#5D3FA1",
    "Laranja": "#9C4B10",
}

OFFICIAL_REFERENCES = [
    (
        "Guia de Atividade Física para a População Brasileira — Ministério da Saúde",
        "https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/guias-e-manuais/2021/guia-de-atividade-fisica-para-a-populacao-brasileira.pdf/view",
    ),
    (
        "Guia Alimentar para a População Brasileira — Ministério da Saúde",
        "https://www.gov.br/saude/pt-br/assuntos/saude-brasil/publicacoes-para-promocao-a-saude/guia_alimentar_populacao_brasileira_2ed.pdf/@@download/file",
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
    st.selectbox("Cor de destaque", list(PALETTE), key="accent_color")
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
    st.checkbox(
        "Pesquisar fontes atuais na web",
        key="web_grounding",
        help=(
            "Quando ativada, permite que o Gemini pesquise a web e retorne links "
            "das fontes encontradas. A busca pode consumir cotas e gerar cobrança "
            "conforme os limites e as condições da API do Google."
        ),
    )
    if st.session_state.get("web_grounding", False):
        st.warning(
            "Busca na web ativada: cada pergunta pode usar recursos adicionais da API. "
            "Confira as cotas e os custos da sua conta Google AI Studio."
        )
    with st.expander("Materiais oficiais de referência"):
        st.caption(
            "Guias públicos do Ministério da Saúde. Eles são referências gerais; "
            "nem toda resposta do Gemini é baseada nesses materiais."
        )
        for title, url in OFFICIAL_REFERENCES:
            st.markdown(f"- [{title}]({url})")
    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


if "messages" not in st.session_state:
    st.session_state.messages = []

theme_is_dark = st.session_state.get("theme_mode", "Claro") == "Escuro"
high_contrast = st.session_state.get("high_contrast", False)
font_scale = st.session_state.get("font_scale", 100) / 100
line_spacing = st.session_state.get("line_spacing", 1.6)
reduce_motion = st.session_state.get("reduce_motion", True)
accent = PALETTE.get(st.session_state.get("accent_color", "Amarelo"), "#F4D35E")

if high_contrast:
    page_bg = "#080B10"
    panel_bg = "#111820"
    message_bg = "#17212B"
    user_bg = "#202B36"
    text_color = "#FFFFFF"
    muted_color = "#E2E8F0"
    border_color = "#F4D35E"
    accent = "#F4D35E"
    sidebar_bg = "#080B10"
    sidebar_text = "#FFFFFF"
    sidebar_muted = "#F1F5F9"
    sidebar_control_bg = "#111820"
    sidebar_control_text = "#FFFFFF"
    sidebar_border = "#F4D35E"
elif theme_is_dark:
    page_bg = "#101925"
    panel_bg = "#1B2938"
    message_bg = "#1B2938"
    user_bg = "#26384D"
    text_color = "#F4F7FB"
    muted_color = "#D0DAE5"
    border_color = "#52677C"
    sidebar_bg = "#14263D"
    sidebar_text = "#F8FAFC"
    sidebar_muted = "#E2E8F0"
    sidebar_control_bg = "#0B1017"
    sidebar_control_text = "#F8FAFC"
    sidebar_border = "#9BAABD"
else:
    page_bg = "#F7F9FC"
    panel_bg = "#FFFFFF"
    message_bg = "#E9EEF5"
    user_bg = "#DCE9F8"
    text_color = "#14263D"
    muted_color = "#43556B"
    border_color = "#C6D1DF"
    sidebar_bg = "#E8EDF3"
    sidebar_text = "#14263D"
    sidebar_muted = "#43556B"
    sidebar_control_bg = "#FFFFFF"
    sidebar_control_text = "#14263D"
    sidebar_border = "#738399"

notice_bg = "#332B12" if theme_is_dark or high_contrast else "#FFF6CC"
notice_text = "#FFF2B3" if theme_is_dark or high_contrast else "#322800"
motion_css = "* { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; scroll-behavior: auto !important; }" if reduce_motion else ""

st.markdown(
    f"""
    <style>
    :root {{
        --page-bg: {page_bg};
        --panel-bg: {panel_bg};
        --message-bg: {message_bg};
        --user-bg: {user_bg};
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
        background: var(--page-bg); color: var(--text-color);
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
    [data-testid="stSidebar"] [data-testid="stSlider"] label *,
    [data-testid="stSidebar"] button {{
        color: var(--sidebar-text) !important; opacity: 1 !important;
    }}
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] * {{
        display: block !important; visibility: visible !important;
    }}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        color: var(--sidebar-muted) !important; opacity: 1 !important;
        line-height: var(--line-spacing) !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background: var(--sidebar-control-bg) !important;
        border-color: var(--sidebar-border) !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-baseweb="select"] input {{
        color: var(--sidebar-control-text) !important; opacity: 1 !important;
    }}
    [data-testid="stSidebar"] button {{
        border: 1px solid var(--sidebar-border) !important;
        border-radius: 9px !important;
        background: var(--sidebar-control-bg) !important;
    }}
    [data-testid="stSidebar"] button:hover {{ border-color: var(--accent-color) !important; }}
    ::selection {{ color: #FFFFFF; background: #205A9C; }}
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] [data-baseweb="slider"] {{ border-color: #9BAABD !important; }}
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] strong,
    [data-testid="stChatMessageContent"], [data-testid="stChatMessageContent"] *,
    [data-testid="stAlert"] *, [data-testid="stCaptionContainer"] {{
        color: var(--text-color) !important;
        line-height: var(--line-spacing) !important;
        font-size: calc(1rem * var(--font-scale)) !important;
    }}
    [data-testid="stChatMessage"] {{
        background: var(--message-bg); border: 1px solid var(--border-color);
        border-radius: 14px; padding: .7rem .9rem;
    }}
    [data-testid="stChatInput"] textarea, [data-testid="stTextInput"] input {{
        color: var(--text-color) !important; background: var(--panel-bg) !important;
        border-color: var(--border-color) !important;
        font-size: calc(1rem * var(--font-scale)) !important;
    }}
    [data-testid="stChatInput"] textarea::placeholder {{ color: var(--muted-color) !important; }}
    [data-testid="stChatInput"] > div, [data-testid="stChatInput"] {{
        background: var(--panel-bg) !important; border-color: var(--border-color) !important;
    }}
    [data-testid="stSidebar"] button {{
        border: 1px solid #DCE5EF !important; border-radius: 9px !important;
        color: #FFFFFF !important; background: #14263D !important;
    }}
    [data-testid="stSidebar"] button:hover {{ border-color: var(--accent-color) !important; }}
    [data-testid="stSidebar"] input:focus, [data-testid="stSidebar"] button:focus,
    [data-testid="stSidebar"] [role="combobox"]:focus,
    [data-testid="stChatInput"] textarea:focus {{
        outline: 3px solid var(--accent-color) !important; outline-offset: 2px !important;
    }}
    .block-container {{ max-width: 900px; padding-top: 1.5rem; }}
    .hero {{
        padding: 1.5rem 1.8rem; border-radius: 18px; color: var(--text-color);
        background: var(--panel-bg); border: 2px solid var(--accent-color); margin-bottom: 1rem;
    }}
    .hero h1 {{ margin: 0; font-size: calc(2rem * var(--font-scale)); color: var(--text-color); }}
    .hero p {{ margin: .5rem 0 0; color: var(--muted-color); font-size: calc(1rem * var(--font-scale)); }}
    .notice {{
        padding: .9rem 1rem; border-radius: 12px; background: {notice_bg};
        border: 2px solid var(--accent-color); color: {notice_text};
        font-size: calc(.95rem * var(--font-scale)); line-height: var(--line-spacing); margin-bottom: 1rem;
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
        if message.get("search_requested"):
            if message.get("sources"):
                with st.expander("Fontes consultadas nesta resposta"):
                    for source in message["sources"]:
                        st.link_button(
                            source["title"], source["url"],
                            use_container_width=False,
                        )
            else:
                st.info(
                    "A busca não retornou links de fontes para esta resposta. "
                    "Considere-a sem referências verificáveis."
                )
        elif message["role"] == "assistant":
            st.caption("Esta resposta foi gerada sem busca atual na web.")

prompt = st.chat_input("Escreva uma pergunta geral...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🙂"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🌿"):
        with st.spinner("Preparando uma resposta..."):
            try:
                search_requested = st.session_state.get("web_grounding", False)
                if search_requested:
                    source_instructions = (
                        ASSISTANT_INSTRUCTIONS
                        + "\nAo pesquisar, dê preferência a fontes oficiais de saúde "
                        "e não apresente uma página encontrada como prova de um diagnóstico. "
                        "Deixe claro quando a busca não trouxer evidência suficiente."
                    )
                    answer, sources = generate_response_with_sources(
                        prompt, source_instructions
                    )
                else:
                    answer = generate_response(prompt, ASSISTANT_INSTRUCTIONS)
                    sources = []
            except Exception:
                st.error(
                    "Não consegui consultar o Gemini. Confira se a chave está "
                    "configurada e tente novamente."
                )
            else:
                st.markdown(answer)
                if search_requested and sources:
                    with st.expander("Fontes consultadas nesta resposta"):
                        for source in sources:
                            st.link_button(
                                source["title"], source["url"],
                                use_container_width=False,
                            )
                elif search_requested:
                    st.info(
                        "A busca não retornou links de fontes para esta resposta. "
                        "Considere-a sem referências verificáveis."
                    )
                else:
                    st.caption("Esta resposta foi gerada sem busca atual na web.")
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "search_requested": search_requested,
                    }
                )
