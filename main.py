from dotenv import load_dotenv
from pathlib import Path
import sqlite3
from agent import create_agent


def main():
    load_dotenv(Path(__file__).resolve().parent / '.env')
    try:
        agent = create_agent()
    except (ValueError, OSError, sqlite3.Error) as error:
        print(f'Setup error: {error}. Run python convert_data.py before starting.')
        return 1
    print('Multi-Tool AI Agent for Bangladesh (type exit to quit)')
    while True:
        try:
            question = input('\nQuestion: ').strip()
            if question.lower() in ('exit', 'quit'):
                break
            if question:
                print(agent.invoke({'input': question})['output'])
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as error:
            print(f'Request failed ({type(error).__name__}). Check API access and try again.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
