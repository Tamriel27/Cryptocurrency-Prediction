# Importing Packages
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import time
import base64
import tweepy
import config
from streamlit_option_menu import option_menu
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
from plotly import graph_objs as go
# from prophet.plot import add_changepoints_to_plot


# Initializing the Binance Client
from binance.client import Client
api_key = 'NbcrOTXY6LQcQXyNMCQEFFcAXln5P2XsJv4myAZqeD4zKH2tpvQThR1NzqQBWaeU'
api_secret = '5Va1PebJWDHEj48wt5ETFxgwARxzcwEJiWkxEb3VumaoJxKTaAWzvknUYArk7cJO'
client = Client(api_key, api_secret)

# Initializing the Twitter Client
klient = tweepy.Client(bearer_token=config.BEARER_TOKEN)

# Accessing Data from Binance
df = pd.read_json('https://api.binance.com/api/v3/ticker/24hr')
df = df[df['symbol'].str.endswith('USDT')]
df = df.sort_values(by=['lastPrice'], ascending=False)[:100]
df = df.reset_index(drop=True)

# Navigation Bar
with st.sidebar:
    choose = option_menu('Navigation', ['Price Change', 'Prediction', 'Twitter'], menu_icon='app-indicator', default_index=0,)

# Price Change
if choose == 'Price Change':
    # Title
    st.title('Cryptocurrency Price Prediction App')
    st.markdown("""
    This app predicts the top 4 cryptocurrencies that have risen the most in the last 24 hours
    """)

    # About
    expander_bar = st.expander('About')
    expander_bar.markdown("""
    * **Python libraries: ** base64, pandas, streamlit, matplotlib, json, time, fbprophet, plotly, tweepy
    * **Data source: ** [Binance](http://binance.com).
    """)

    # Page layout
    ## Divide page to 3 columns (col1 = sidebar, col2 and col3 = page contents)
    col1 = st.sidebar
    col2, col3 = st.columns((2,1))

    # Input Option
    col1.header('Input Options')

    sorted_coin = sorted(df['symbol'])
    selected_coin = col1.multiselect('Cryptocurrencies', sorted_coin, sorted_coin)

    # Filtering Data
    df_selected_coin = df[(df['symbol'].isin(selected_coin))]

    ## Sidebar - Number of Coins to Display
    num_coin = col1.slider('Display Top Number of Coins', 1, 100, 100)
    df_coins = df_selected_coin[:num_coin]

    ## Sidebar - Sorting Values
    sort_values = col1.selectbox('Sort values?', ['Yes', 'No'])

    col2.subheader('Price Data of Selected Cryptocurrency')
    col2.markdown("""
    This chart shows the 100 most expensive cryptocurrencies in the last 24 hours
    """)
    col2.write('Data Dimension: ' + str(df_selected_coin.shape[0]) + ' rows and ' + str(df_selected_coin.shape[1]) + ' columns.')

    # Color Function
    def color_df(val):
        if val > 0:
            color = 'green'
        else:
            color = 'red'
        return f'background-color: {color}'

    # Dataframe
    col2.dataframe(df_coins.style.applymap(color_df, subset=['priceChange', 'priceChangePercent']))

    # Download CSV Data
    def filedownload(df):
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="crypto.csv">Download CSV File</a>'
        return href

    col2.markdown(filedownload(df_selected_coin), unsafe_allow_html=True)

    # Dataframe
    col2.subheader('Table of % Price Change')
    col2.markdown("""
    This chart shows the 100 cryptocurrencies that have grown the most in the last 24 hours
    """)
    df_change = pd.concat([df_coins.symbol, df_coins.priceChangePercent], axis=1)
    df_change = df_change.set_index('symbol')
    df_change['positive_percent_change'] = df_change['priceChangePercent'] > 0
    df_change = df_change.sort_values(by=['priceChangePercent'], ascending=False)
    col2.dataframe(df_change)

    col3.subheader('Bar plot of % Price Change')


    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['priceChangePercent'])
        col3.write('*24 hours period*')
        plt.figure(figsize=(5,25))
        plt.subplots_adjust(top = 1, bottom = 0)
        df_change['priceChangePercent'].plot(kind='barh', color=df_change.positive_percent_change.map({True: 'g', False: 'r'}))
        col3.pyplot(plt)
    else:
        col3.write('*24 hours period*')
        plt.figure(figsize=(5,25))
        plt.subplots_adjust(top = 1, bottom = 0)
        df_change['priceChangePercent'].plot(kind='barh', color=df_change.positive_percent_change.map({True: 'g', False: 'r'}))
        col3.pyplot(plt)

# Prediction
elif choose == 'Prediction':
    # About
    expander_bar = st.expander('About')
    expander_bar.markdown("""
    * **Python libraries: ** base64, pandas, streamlit, matplotlib, json, time, fbprophet, plotly, tweepy
    * **Data source: ** [Binance](http://binance.com).
    """)

    st.title('Cryptocurrency Prediction')

    df_change = pd.concat([df.symbol, df.priceChangePercent], axis=1)
    df_change['positive_percent_change'] = df['priceChangePercent'] > 0
    df_change = df_change.sort_values(by=['priceChangePercent'], ascending=False)
    df_change = df_change.reset_index(drop=True)
    crypto = (df_change.loc[0, 'symbol'], df_change.loc[1, 'symbol'], df_change.loc[2, 'symbol'], df_change.loc[3, 'symbol'])

    selected_crypto = st.selectbox('Select cryptocurrency for prediction', crypto)


    @st.cache
    def load_data(ticker):
        data = client.get_historical_klines(ticker, Client.KLINE_INTERVAL_1MINUTE, '1 day ago UTC')
        data = pd.DataFrame(data)
        data.columns = ['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time', 'Quote Asset Volume', 'Number of Trades', 'TB Base Volume', 'TB Quote Volume', 'Ignore']
        data = data.reset_index(drop=True)
        data['Open Time'] = pd.to_datetime(data['Open Time']/1000, unit='s')
        data['Close Time'] = pd.to_datetime(data['Close Time']/1000, unit='s')
        return data
    
    data_load_state = st.text('Loading data...')
    data = load_data(selected_crypto)
    data_load_state.text('Loading data... done!')

    st.subheader('Raw data')
    st.write(data.head())

    # Plot Raw Data
    def plot_raw_data():
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['Close Time'], y=data['Close'], name='Close'))
        fig.layout.update(title_text='Time Series Data', yaxis_title='Cryptocurrency Price (US Dollars)', xaxis_rangeslider_visible=True)
        fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=15, label='15m', step='minute', stepmode='backward'),
                dict(count=45, label='45m', step='minute', stepmode='backward'),
                dict(count=1, label='HTD', step='hour', stepmode='todate'),
                dict(count=6, label='6h', step='hour', stepmode='backward'),
                dict(step='all')])))
        st.plotly_chart(fig)
    plot_raw_data()

    # Predicting Forecast with Prophet.
    st.subheader('FbProphet')
    df_train = data[['Close Time','Close']]
    df_train = df_train.rename(columns={'Close Time': 'ds', 'Close': 'y'})

    m = Prophet()
    m.fit(df_train)
    future = m.make_future_dataframe(periods=1, freq='H')
    forecast = m.predict(future)

    # Show and plot forecast
    st.subheader('Forecast data')
    st.write(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(20))
        
    st.write(f'Forecast plot')
    fig1 = plot_plotly(m, forecast)
    st.plotly_chart(fig1)

    st.write('Forecast components')
    fig2 = m.plot_components(forecast)
    st.write(fig2)
    
    st.write('Automatic changepoint detection')
    fig = m.plot(forecast)
#     a = add_changepoints_to_plot(fig.gca(), m, forecast)
#     st.write(fig)

# Twitter
elif choose == 'Twitter':
    # About
    expander_bar = st.expander('About')
    expander_bar.markdown("""
    * **Python libraries: ** base64, pandas, streamlit, matplotlib, json, time, fbprophet, plotly, tweepy
    * **Data source: ** [Binance](http://binance.com).
    """)

    st.title('Tweet Generator')

    df_change = pd.concat([df.symbol, df.priceChangePercent], axis=1)
    df_change['positive_percent_change'] = df['priceChangePercent'] > 0
    df_change = df_change.sort_values(by=['priceChangePercent'], ascending=False)
    df_change = df_change.reset_index(drop=True)
    crypto = (df_change.loc[0, 'symbol'][:-4], df_change.loc[1, 'symbol'][:-4], df_change.loc[2, 'symbol'][:-4], df_change.loc[3, 'symbol'][:-4])

    # Select Box
    selected_crypto = st.selectbox('Select cryptocurrency', crypto)
    st.subheader('Tweets')

    def twitter_tweets(query):
        tweets = klient.search_recent_tweets(query=query, tweet_fields=['context_annotations', 'created_at'], user_fields=['profile_image_url'], expansions='author_id', max_results=100)
        for tweet in tweets.data:
            st.write('Created at:', tweet.created_at)
            st.write('User ID:', tweet.author_id)
            st.write(tweet.text)
            st.markdown("***")
           
    data_load_state = st.text('Loading Tweets...')
    data = twitter_tweets(selected_crypto)
    data_load_state.text('Loading Tweets... done!')

    
