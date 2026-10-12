"""Simple Streamlit interface for the existing four-tool agent."""
import base64
from pathlib import Path
import sqlite3

import streamlit as st
from dotenv import load_dotenv

from agent import create_agent


st.set_page_config(page_title='BD Bangladesh AI Agent', page_icon='🇧🇩', layout='wide')
load_dotenv(Path(__file__).resolve().parent / '.env')

st.html('<style>' + (Path(__file__).resolve().parent / 'ui.css').read_text(encoding='utf-8') + '</style>')
logo_data = base64.b64encode((Path(__file__).resolve().parent / 'assets' / 'bangladesh-logo.png').read_bytes()).decode('ascii')
st.html(f'''
<header class="bd-header">
  <div class="bd-logo" role="img" aria-label="Bangladesh map">
    <img src="data:image/png;base64,{logo_data}" alt="Bangladesh flag map" />
  </div>
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
                    'Your question', key='question',
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
