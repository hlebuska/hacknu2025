"""Simple runner to exercise `ai_chatbot.AIChatbot` from the command line.

Usage:
    python run_ai_chatbot.py path/to/resume.json path/to/vacancy.json

Defaults to `resume_parsed.json` and `vacancy_parsed.json` in the current directory.
"""
from ai_chatbot import AIChatbot
import sys


def main(argv):
    resume = argv[1] if len(argv) > 1 else "resume_parsed.json"
    vacancy = argv[2] if len(argv) > 2 else "vacancy_parsed.json"

    bot = AIChatbot()
    data = bot.load_data(resume, vacancy)
    if not data:
        print("Failed to load files.")
        return 1

    resume_data, vacancy_data = data
    diffs = bot.analyze_differences(resume_data, vacancy_data)
    print("Differences:")
    for d in diffs:
        print(" -", d.get("description"))

    try:
        questions = bot.generate_questions(diffs)
        print("\nQuestions:\n")
        print(questions)
    except Exception as e:
        print("Could not generate questions:", e)
        print("Make sure GEMINI_API_KEY or GOOGLE_API_KEY is set and package 'google-generativeai' is installed.")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
