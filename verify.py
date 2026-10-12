"""Offline integration checks. No API requests or real LLM routing are tested."""
import io
import json
import sqlite3
import unittest
from contextlib import closing
from types import SimpleNamespace
from unittest.mock import patch

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from agent import build_executor
from db_tools import DATA, QueryPlan, create_db_tools, execute_sql, make_db_tool, schema
from web_tool import create_web_tool


class ScriptedSQLModel:
    def __init__(self, sql='', reason=''):
        self.plan = QueryPlan(sql=sql, unavailable_reason=reason)

    def with_structured_output(self, model):
        return SimpleNamespace(invoke=lambda messages: self.plan)

    def invoke(self, messages):
        payload = json.loads(messages[-1][1])
        count = payload['results']['rows'][0][0]
        return SimpleNamespace(content=f'The query matched {count} records in this dataset.')


class ScriptedAgentModel(BaseChatModel):
    selected_tool: str

    @property
    def _llm_type(self):
        return 'offline-scripted-integration-model'

    def bind_tools(self, tools, **kwargs):
        assert len(tools) == 4
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        observations = [m for m in messages if isinstance(m, ToolMessage)]
        if observations:
            answer = AIMessage(content=observations[-1].content)
        else:
            question = next(m.content for m in messages if m.type == 'human')
            answer = AIMessage(content='', tool_calls=[{
                'name': self.selected_tool, 'args': {'question': question}, 'id': 'offline-test-call',
            }])
        return ChatResult(generations=[ChatGeneration(message=answer)])


class Verification(unittest.TestCase):
    def test_database_imports_and_types(self):
        report = json.loads((DATA / 'schema.json').read_text(encoding='utf-8'))
        for table, info in report.items():
            with self.subTest(table=table), closing(sqlite3.connect(DATA / f'{table}.db')) as con:
                self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                self.assertEqual(con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0], info['rows'])
                self.assertEqual(schema(table), [(c['name'], c['type']) for c in info['columns']])
                for col in info['columns']:
                    kinds = {r[0] for r in con.execute(f'SELECT DISTINCT typeof("{col["name"]}") FROM "{table}"')}
                    self.assertLessEqual(kinds, {col['type'].lower(), 'null'})

    def test_restricted_sql_and_output_limits(self):
        for sql in ['DELETE FROM hospitals', 'DROP TABLE hospitals',
                    'SELECT * FROM sqlite_master', 'PRAGMA table_info(hospitals)',
                    "ATTACH DATABASE ':memory:' AS extra", 'SELECT load_extension(\'bad\')']:
            with self.subTest(sql=sql), self.assertRaises(sqlite3.Error):
                execute_sql('hospitals', sql)
        results = execute_sql('restaurants', 'SELECT name FROM restaurants')
        self.assertEqual(len(results['rows']), 200)
        self.assertTrue(results['truncated'])
        self.assertGreater(execute_sql('restaurants', 'SELECT COUNT(*) FROM restaurants')['rows'][0][0], 200)

    def test_database_tools_and_missing_fields(self):
        for table, name in [('institutions', 'InstitutionsDBTool'), ('hospitals', 'HospitalsDBTool'), ('restaurants', 'RestaurantsDBTool')]:
            model = ScriptedSQLModel(f'SELECT COUNT(*) FROM {table}')
            tool = make_db_tool(table, name, 'Offline test', model)
            expected = execute_sql(table, f'SELECT COUNT(*) FROM {table}')['rows'][0][0]
            self.assertEqual(tool.invoke({'question': 'Count dataset records'}), f'The query matched {expected} records in this dataset.')
        tool = make_db_tool('hospitals', 'HospitalsDBTool', 'Offline test', ScriptedSQLModel(reason='No beds column is available.'))
        self.assertIn('No beds column', tool.invoke({'question': 'How many beds?'}))

    def test_tavily_request_and_failures(self):
        tool = create_web_tool('offline-test-key')
        payload = {'results': [{'title': 'Test result', 'url': 'https://example.com', 'content': 'Mocked search excerpt.'}]}
        with patch('web_tool.urllib.request.urlopen', return_value=io.BytesIO(json.dumps(payload).encode())) as mocked:
            self.assertEqual(json.loads(tool.invoke({'question': 'DGHS role'})), payload['results'])
            request = mocked.call_args.args[0]
            self.assertEqual(request.full_url, 'https://api.tavily.com/search')
            self.assertEqual(request.get_method(), 'POST')
            self.assertEqual(json.loads(request.data)['query'], 'DGHS role')
            self.assertEqual(request.get_header('Authorization'), 'Bearer offline-test-key')
        with patch('web_tool.urllib.request.urlopen', side_effect=OSError('offline')):
            self.assertIn('Web search failed', tool.invoke({'question': 'DGHS role'}))

    def test_four_executor_paths_with_scripted_routing(self):
        cases = [
            ('How many universities are in Dhaka?', 'InstitutionsDBTool', 'institutions', '', 'University category is unavailable in this dataset.'),
            ('How many hospitals are in Dhaka?', 'HospitalsDBTool', 'hospitals', "SELECT COUNT(*) FROM hospitals WHERE district = 'Dhaka' AND type LIKE '%Hospital%'", ''),
            ('How many restaurants are in Chittagong?', 'RestaurantsDBTool', 'restaurants', "SELECT COUNT(*) FROM restaurants WHERE address LIKE '%Chittagong%' OR address LIKE '%Chattogram%'", ''),
            ('What is the role of DGHS in Bangladesh?', 'WebSearchTool', '', '', ''),
        ]
        for question, name, table, sql, reason in cases:
            with self.subTest(tool=name):
                tools = create_db_tools(ScriptedSQLModel())
                if table:
                    tools = [make_db_tool(table, name, 'Offline test', ScriptedSQLModel(sql, reason)) if t.name == name else t for t in tools]
                tools.append(create_web_tool('offline-test-key'))
                executor = build_executor(ScriptedAgentModel(selected_tool=name), tools)
                executor.return_intermediate_steps = True
                response = {'results': [{'title': 'Offline fixture', 'url': 'https://example.com', 'content': 'Mocked search excerpt, not verified general knowledge.'}]}
                with patch('web_tool.urllib.request.urlopen', return_value=io.BytesIO(json.dumps(response).encode())):
                    result = executor.invoke({'input': question})
                steps = result['intermediate_steps']
                self.assertEqual(len(steps), 1)
                self.assertEqual(steps[0][0].tool, name)
                self.assertEqual(result['output'], steps[0][1])
                self.assertTrue(result['output'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
