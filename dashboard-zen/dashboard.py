# !/usr/bin/python
# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

db_config = {'user': 'my_user',
			 'pwd': 'my_user_password',
			 'host': 'localhost',
			 'port': 5432,
			 'db': 'zen'}   
connection_string = 'postgresql://{}:{}@{}:{}/{}'.format(db_config['user'], 
                                                         db_config['pwd'], 
                                                         db_config['host'], 
                                                         db_config['port'], 
                                                         db_config['db'])

engine = create_engine(connection_string)


query = '''
            SELECT *
            FROM dash_visits
        '''
dash_visits = pd.io.sql.read_sql(query, con = engine)
dash_visits['dt'] = pd.to_datetime(dash_visits['dt'])

query = '''
            SELECT *
            FROM dash_engagement
        '''
dash_engagement = pd.io.sql.read_sql(query, con = engine)

note1 = '''
          Этот дашборд показывает историю событий по темам карточек, разбивку событий по темам источников,
          глубину взаимодействия пользователей с карточками.
        '''
note2 = '''
          Используйте выбор интервала даты, возрастных категорий и тем карточек для управления дашбордом.
        '''

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(children=[

    html.H1(children = 'Взаимодействие пользователей с карточками Яндекс.Дзен.', style={'textAlign': 'center'}),
    html.Div([
        html.P(note1),
        html.P(note2),
    ], style={'textAlign': 'center'}),

    html.Br(),

    html.Div([
        html.Div([
            # выбор временного периода
            html.Label('Период:'),
            dcc.DatePickerRange(
                start_date = dash_visits['dt'].min().date(),
                end_date = dash_visits['dt'].max().date(),
                display_format = 'YYYY-MM-DD',
                id = 'dt_selector',
            ),

            html.Div([
                dcc.Input(
                    placeholder='HH:MM',
                    type='text',
                    value=dash_visits['dt'].min().time(),
                    id = 'start_time', style = {'width': '9.3vw'}
                ),
                dcc.Input(
                    placeholder='HH:MM',
                    type='text',
                    value=dash_visits['dt'].max().time(),
                    id = 'end_time', style = {'width': '9.3vw'}
                ),
            ]),

            # возрастные категории
            html.Label('Возрастные категории:'),
            dcc.Dropdown(
                options = [{'label': x, 'value': x} for x in dash_visits['age_segment'].unique()],
                value = dash_visits['age_segment'].unique().tolist(),
                multi = True,
                id = 'age_selector'
            ),
        ], className = 'six columns'),            

        html.Div([
            # выбор тем
            html.Label('Темы:'),
            dcc.Dropdown(
                options = [{'label': x, 'value': x} for x in dash_visits['item_topic'].unique()],
                value = dash_visits['item_topic'].unique().tolist(),
                multi = True,
                id = 'topic_selector'
            ),  
        ], className = 'six columns'),

    ], className = 'row'),

    html.Br(),

    html.Div([
        html.Div([
            html.Label('История событий по темам карточек:'),
            dcc.Graph(
            	style = {'height': '50vw'},
                id = 'history-absolute-visits'
            ), 
        ], className = 'six columns'),            

        html.Div([
            html.Label('Количество событий по темам источников:'),
            dcc.Graph(
            	style = {'height': '30vw'},
                id = 'pie-visits'
            ), 

            html.Label('Глубина взаимодействия:'),
            dcc.Graph(
            	style = {'height': '20vw'},
                id = 'engagement-graph'
            ), 
        ], className = 'six columns'),

    ], className = 'row'),
])


@app.callback(
    [Output('history-absolute-visits', 'figure'),
     Output('pie-visits', 'figure'),
     Output('engagement-graph', 'figure'),
    ],
    [Input('topic_selector', 'value'),
     Input('age_selector', 'value'),
     Input('dt_selector', 'start_date'),
     Input('dt_selector', 'end_date'),
     Input('start_time', 'value'),
     Input('end_time', 'value')
    ])

def update_figures(selected_item_topics, selected_ages, start_date, end_date, start_time, end_time):

    start_date += 'T' + str(start_time)
    end_date += 'T' + str(end_time)
    start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S')
    end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')

    #применяем фильтрацию
    filtered_visits = dash_visits.query('item_topic.isin(@selected_item_topics) and \
    									 dt >= @start_date and dt <= @end_date and \
    									 age_segment.isin(@selected_ages)', engine = 'python')

    filtered_engagement = dash_engagement.query('item_topic.isin(@selected_item_topics) and \
                                         age_segment.isin(@selected_ages)', engine = 'python')

    # группируем по темам и по возрастным категориям
    visits_by_item = (filtered_visits.groupby(['item_topic', 'dt'])
                      .agg({'visits': 'sum'})
                      .reset_index()
                     )

    visits_by_source = (filtered_visits.groupby(['source_topic'])
                      .agg({'visits': 'sum'})
                      .reset_index()
                     )
    visits_by_source['percent'] = visits_by_source['visits'] / visits_by_source['visits'].sum()
    visits_by_source.loc[visits_by_source['percent'] < 0.035, 'source_topic'] = 'Другие'
    pop_source_topic = visits_by_source.query('source_topic != "Другие"')['source_topic'].unique()
    other_source_topic = filtered_visits.query('source_topic not in @pop_source_topic', engine = 'python')['source_topic'].unique()
    f = open('other_source_topic.txt', 'w')
    for val in other_source_topic:
        f.write (val + '\n')
    f.close()
    # и ещё раз группируем
    visits_by_source = (visits_by_source.groupby(['source_topic'])
                        .agg({'visits': 'sum'})
                        .reset_index()
                       )

    engagement_by_event = (dash_engagement.groupby(['event'])
                         .agg({'unique_users': 'sum'})
                         .reset_index()
                        )
    
    total = engagement_by_event.loc[engagement_by_event['event'] == "show", 'unique_users']
    engagement_by_event['avg_unique_users'] = engagement_by_event['unique_users'].apply(lambda x: x / total * 100)
    engagement_by_event.loc[engagement_by_event['event'] == "show", 'num_event'] = 1
    engagement_by_event.loc[engagement_by_event['event'] == "click", 'num_event'] = 2
    engagement_by_event.loc[engagement_by_event['event'] == "view", 'num_event'] = 3
    engagement_by_event = engagement_by_event.sort_values('num_event', ascending = False)

    # график истории событий
    data_by_item = []
    for topic in visits_by_item['item_topic'].unique():
        data_by_item += [go.Scatter(x = visits_by_item.query('item_topic == @topic')['dt'],
                                    y = visits_by_item.query('item_topic == @topic')['visits'],
                                    mode = 'lines',
                                    stackgroup = 'one',
                                    name = topic)]

    # график количества карточек по темам источников   
    data_by_source = [go.Pie(labels = visits_by_source['source_topic'],
    						 values = visits_by_source['visits'])]

    # график глубины взаимодействия
    data_by_event = [go.Bar(x = engagement_by_event['avg_unique_users'],
                            y = engagement_by_event['event'] + ' ',
        					orientation = 'h')]

    # формируем результат для отображения
    return (
        {
            'data': data_by_item,
            'layout': go.Layout(xaxis = {'title': 'Дата'},
                                yaxis = {'title': 'Количество'})
        },            
        {
            'data': data_by_source,
            'layout': go.Layout()
        },
        {
            'data': data_by_event,
            'layout': go.Layout(xaxis = {'title': 'Среднее количество пользователей, %'},
                                yaxis = {'title': 'Событие'})
        },             
	)  
if __name__ == '__main__':
    app.run_server(debug=True)