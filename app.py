"""Simple Streamlit interface for the existing four-tool agent."""
from pathlib import Path
import sqlite3

import streamlit as st
from dotenv import load_dotenv

from bangladesh_agent.agent import create_agent
from bangladesh_agent.validation import MAX_QUESTION_LENGTH, validate_question


st.set_page_config(page_title='BD Bangladesh AI Agent', page_icon='🇧🇩', layout='wide')
load_dotenv(Path(__file__).resolve().parent / '.env')

st.html('<style>' + (Path(__file__).resolve().parent / 'assets' / 'ui.css').read_text(encoding='utf-8') + '</style>')
# Keep the badge and image in one HTML block so Streamlit's container layout
# cannot squeeze the image wrapper or clip the artwork.
st.html(
    '<div class="bd-logo" role="img" aria-label="Bangladesh AI Agent logo">'
    '<img src="app/static/bangladesh-logo.png" alt="Bangladesh AI Agent logo" '
    'style="display:block;width:52px;height:56px;object-fit:contain;flex:none">'
    '</div>'
)
st.html('''
<header class="bd-header">
  <h1> Bangladesh AI Agent</h1>
  <p>Ask about institutions, hospitals, restaurants, or general knowledge.</p>
</header>
''')


def choose_question(text):
    st.session_state.question = text


with st.container(key='question_card'):
    with st.form('question_form', border=False):
        with st.container(key='input_row'):
            field, action = st.columns([8, 1], gap='small', vertical_alignment='center')
            with field:
                question = st.text_input(
                    'Your question', key='question', max_chars=MAX_QUESTION_LENGTH,
                    placeholder='How many hospitals are in Dhaka?',
                    label_visibility='collapsed', icon=':material/description:',
                )
            with action:
                submitted = st.form_submit_button('Ask', type='primary', icon=':material/send:', width='stretch')

    with st.container(key='quick_questions', horizontal=True, vertical_alignment='center', gap='small'):
        st.markdown('Quick questions:', width='content')
        st.button('Hospitals in Dhaka', icon=':material/local_hospital:', key='hospitals_chip',
                  on_click=choose_question, args=('How many hospitals are in Dhaka?',))
        st.button('Universities in Bangladesh', icon=':material/account_balance:', key='universities_chip',
                  on_click=choose_question, args=('How many universities are in Bangladesh?',))
        st.button('Best restaurants in Chittagong', icon=':material/restaurant:', key='restaurants_chip',
                  on_click=choose_question, args=('What are the highest-rated restaurants in Chittagong?',))

if submitted:
    question = question.strip()
    if not question:
        st.warning('Please enter a question.')
    else:
        st.session_state.pop('answer', None)
        try:
            with st.spinner('Finding your answer…'):
                question = validate_question(question)
                if 'agent' not in st.session_state:
                    st.session_state.agent = create_agent()
                result = st.session_state.agent.invoke({'input': question})
                st.session_state.answer = result['output']
        except (ValueError, OSError, sqlite3.Error):
            st.error('Check your API keys in .env and make sure the three databases are available.')
        except Exception:
            st.error('Could not answer right now. Check your API access and try again.')

if 'answer' in st.session_state:
    with st.container(key='answer_card'):
        st.subheader('Answer')
        st.markdown(st.session_state.answer)
