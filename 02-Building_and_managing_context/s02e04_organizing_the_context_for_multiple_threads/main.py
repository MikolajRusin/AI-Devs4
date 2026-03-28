import asyncio

from src.config import Settings
from src.hub_client import AiDevsHubClient
from workspace.prompts.zmail_agent import SYSTEM_INSTRUCTIONS
from src.agent import run_agent
from src.logger import logger

async def main():
    logger.start('Start application')

    settings = Settings()
    hub_client = AiDevsHubClient(
        api_key=settings.ai_devs_hub.api_key,
        base_url=settings.ai_devs_hub.base_url
    )

    task = """
Przeszukaj skrzynkę mailową i rozwiąż zadanie mailbox.

Znajdź trzy wartości:
- date: kiedy dział bezpieczeństwa planuje atak na naszą elektrownię; zwróć datę w formacie YYYY-MM-DD
- password: hasło do systemu pracowniczego znalezione w skrzynce
- confirmation_code: kod potwierdzenia z ticketa wysłanego przez dział bezpieczeństwa; kod musi zaczynać się od 'SEC-' i mieć dokładnie 36 znaków

Ważne wskazówki:
- skrzynka jest aktywna, więc nowe wiadomości mogą pojawić się w trakcie pracy
- wiemy, że Wiktor wysłał co najmniej jedną wiadomość z domeny proton.me
- korzystaj z wyszukiwania, odczytu pełnych wiadomości i feedbacku z huba
- nie zgaduj wartości; opieraj się wyłącznie na treści wiadomości
- wysyłaj dane do huba dopiero wtedy, gdy masz komplet trzech konkretnych kandydatów

Twoim celem jest zdobycie poprawnej odpowiedzi dla huba.
"""
    results = await run_agent(
        settings=settings,
        hub_client=hub_client,
        task=task,
        instructions=SYSTEM_INSTRUCTIONS
    )


if __name__ == '__main__':
    asyncio.run(main())



# google/gemini-3-flash-preview -> 9 iteracji       input/output  $0.50 $3
# kwaipilot/kat-coder-pro-v2 -> 14 iteracji         input/output  $0.30 $1.20
# minimax/minimax-m2.7 -> raz 11, raz 15 iteracji   input/output  $0.30 $1.20
# openai/gpt-5.4-nano  -> 15 iteracji (zla odp)     input/output  $0.20 $1.25
# nvidia/nemotron-3-super-120b-a12b:free -> po 8 iteracji strasznie zwolnil     input/output  $0.20 $1.25
# inception/mercury-2 -> 17 iteracji (bardzo szybki) input/output  $0.25 $0.75
# google/gemini-3.1-flash-lite-preview -> 8/10/12 iteracji input/output  $0.25 $1.50


