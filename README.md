# E4 — Assistente de Saúde Preventiva

Protótipo em Python 3.13.14 com uma interface de conversa feita em Streamlit e respostas geradas pela API Gemini.

## Arquivos

- `main.py`: inicia a conversa no terminal.
- `app.py`: inicia a interface visual no navegador.
- `llm_provider.py`: conecta o programa à API Gemini.
- `safety.py`: define o escopo seguro das respostas.
- `.env`: exemplo da configuração local, sem chave real.
- `.gitignore`: exclui configurações locais e chaves do controle de versão.
- `requirements.txt`: dependência da API Gemini.

## Acessibilidade da interface

Na barra lateral do aplicativo, o usuário pode selecionar tema claro ou escuro, escolher uma cor de destaque, ativar alto contraste, aumentar o tamanho do texto, ajustar o espaçamento entre linhas e reduzir animações. As preferências ficam salvas durante a sessão atual do aplicativo.

## Fontes e transparência

O usuário pode deixar a busca atual na web desligada ou ativá-la para uma resposta. Quando ativada, o aplicativo mostra os links de fontes que o Gemini devolveu; se nenhum link vier, a interface avisa que a resposta não tem referências verificáveis. A busca pode consumir cotas e gerar cobrança conforme os limites da API. A barra lateral também apresenta dois guias oficiais do Ministério da Saúde. A busca não garante que todas as fontes sejam oficiais ou que a resposta esteja correta; confira os links e procure orientação profissional para decisões individuais.

## Publicação no Streamlit Community Cloud

O `app.py` pode ser publicado a partir de um repositório GitHub. Configure `GEMINI_API_KEY` na área **Secrets** das configurações avançadas de publicação. Nunca envie o arquivo `.env` ao GitHub. Um aplicativo publicado pode ser acessado pelo público e as mensagens enviadas são processadas pelo Gemini; não informe dados pessoais ou informações reais de saúde. O uso do aplicativo também pode consumir a cota da chave configurada.

## Configuração

1. Instale as dependências com `python -m pip install -r requirements.txt`.
2. Crie um arquivo `.env` nesta pasta e coloque nele `GEMINI_API_KEY=sua_chave`.
3. Inicie a interface com `python -m streamlit run app.py`.

O programa usa `gemini-3.5-flash-lite` por padrão. O acesso gratuito tem limites e depende da elegibilidade da conta. Não use dados reais ou identificáveis de saúde; use apenas exemplos fictícios.

O assistente oferece informações gerais. Ele não deve diagnosticar doenças, recomendar tratamentos individualizados nem prescrever medicamentos. Em situações urgentes, deve orientar a pessoa a procurar um serviço de emergência local ou profissional de saúde.

Nunca coloque a chave no código, em capturas de tela ou em mensagens. O arquivo `.env` deve permanecer local e não deve ser enviado junto com o projeto.
