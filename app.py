import dash
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Load data
DATA_URL = os.getenv("DATA_URL")
df = pd.read_csv(DATA_URL, header=None)
df.columns = ['state', 'year', 'population']

# Initialize Gemini AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Create Dash app
app = dash.Dash(__name__)

# Define layout
app.layout = html.Div([
    html.H1("US State Historic Population Dashboard"),
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': year, 'value': year} for year in sorted(df['year'].unique(), reverse=True)],
        value=df['year'].max(),
        style={'width': '100px'}
    ),
    html.Br(),
    dcc.Input(id='ai-query-input', type='text', placeholder='Q: What was the population of [ST] in [YYYY]?', style={'width': '280px'}),
    html.Div(id='ai-query-output'),
    dcc.Graph(id='us-map'),
    dcc.Graph(id='state-line-chart')
], style={'marginLeft': '50px'})

# Define callbacks
@app.callback(
    dash.Output('us-map', 'figure'),
    [dash.Input('year-dropdown', 'value')]
)
def update_map(selected_year):
    # Filter data by year
    filtered_df = df[df['year'] == selected_year]

    # Create choropleth map
    fig = px.choropleth(
        filtered_df,
        locations='state',
        locationmode="USA-states",
        color='population',
        scope="usa",
        color_continuous_scale="Rainbow",
        title=f"US Population by State in {selected_year}",
        hover_data={'state': False, 'population': True}
    )
    fig.update_traces(hovertemplate="%{location}: %{z:,}")
    fig.update_layout(
        title_x=0.5,
        coloraxis_colorbar=dict(
            orientation="v",
            x=-0.2,
            y=0.5,
            len=0.8
        ),
        coloraxis_colorscale="Rainbow"
    )
    #fig.update_coloraxes(autocolorscale=True)
    return fig

@app.callback(
    dash.Output('state-line-chart', 'figure'),
    [dash.Input('us-map', 'clickData')]
)
def update_line_chart(clickData):
    if clickData is None:
        return px.line(title="Click on a state to see its population history")

    state_name = clickData['points'][0]['location']
    state_df = df[df['state'] == state_name]

    fig = px.line(
        state_df,
        x='year',
        y='population',
        title=f"Population History of {state_name}",
    )
    fig.update_layout(
        title_x=0.5,
        yaxis = dict(tickformat=","),
    )
    return fig

@app.callback(
    dash.Output('ai-query-output', 'children'),
    [dash.Input('ai-query-input', 'value')]
)
def update_ai_query_output(query):
    if query is None:
        return ""

    try:
        import re
        # Extract state and year from the query
        match = re.search(r"What was the population of\s*([A-Z]{2})\s*in\s*(\d{4})\?", query)
        if match:
            state = match.group(1)
            year = int(match.group(2))

            # Get the population for the specified state and year
            population = df[(df['state'] == state) & (df['year'] == year)]['population'].values
            if len(population) > 0:
                return html.H3(f"A: The population of {state} in {year} was {population[0]:,}", style={'textAlign': 'center'})
            else:
                return html.H3(f"No data found for {state} in {year}.", style={'textAlign': 'center'})
        else:
            return "Invalid query format. Please use the format 'What was the population of [ST] in [YYYY]?'"
    except Exception as e:
        return f"Error: {e}"

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)