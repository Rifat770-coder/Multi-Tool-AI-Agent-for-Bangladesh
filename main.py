from dotenv import load_dotenv
from pathlib import Path
import sqlite3
from bangladesh_agent.agent import create_agent
from bangladesh_agent.validation import validate_question


def main():
    load_dotenv(Path(__file__).resolve().parent / '.env')
    try:
        agent = create_agent()
    except (ValueError, OSError, sqlite3.Error) as error:
        print('Setup error: check API keys in .env and the three databases. See README.md.')
        return 1
    print('Multi-Tool AI Agent for Bangladesh (type exit to quit)')
    while True:
        try:
            question = input('\nQuestion: ').strip()
            if question.lower() in ('exit', 'quit'):
                break
            if question:
                print(agent.invoke({'input': validate_question(question)})['output'])
        except (EOFError, KeyboardInterrupt):
            break
        except ValueError as error:
            print('Invalid question or response. Use a question of at most 2,000 characters and try again.')
        except Exception as error:
            print(f'Request failed ({type(error).__name__}). Check API access and try again.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
