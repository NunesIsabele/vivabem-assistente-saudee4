"""Ponto de entrada do protótipo E4."""

from llm_provider import generate_response
from safety import ASSISTANT_INSTRUCTIONS


def main() -> None:
    print("Assistente de Saúde Preventiva — protótipo E4")
    print("Este protótipo não diagnostica nem prescreve. Digite 'sair' para encerrar.\n")

    while True:
        question = input("Você: ").strip()
        if question.lower() in {"sair", "s"}:
            print("Até mais.")
            break
        if not question:
            continue

        try:
            answer = generate_response(question, ASSISTANT_INSTRUCTIONS)
        except Exception as error:
            print(f"\nNão consegui consultar o Gemini: {error}\n")
            continue
        print(f"\nAssistente: {answer}\n")


if __name__ == "__main__":
    main()
