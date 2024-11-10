import os
import time
import random
from dotenv import load_dotenv
import logging
from decimal import Decimal

import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from twelvedata import TDClient

from api.motivational import motivational
from api.backend_data import quote, overtime_data

 
logging.basicConfig(
    level=logging.CRITICAL,  # Set the logging level to INFO
    format="{asctime} | {levelname} | {name} | {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,  # Ensures that previous configurations are overridden
)

# Suppress DEBUG logs from `urllib3` and `requests`
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

load_dotenv()


class CryptoView():
    def dataset_arrays(self):
        gui_color = self.randomColorSelection(["green", "orange", "red", "violet", "gray", "rainbow"])
        motivational_text = self.randomColorSelection(motivational())
        return gui_color, motivational_text

    def randomColorSelection(self, dataset):
        array_length = len(dataset) - 1
        random_number = random.randint(0, array_length)
        random_color_selection = dataset[random_number]
        return random_color_selection
    
    def allMarketData(self):
        df = pd.DataFrame(quote())

        df['open'] = pd.to_numeric(df['open'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['close'] = pd.to_numeric(df['close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Sort by timestamp
        df.sort_values(by='timestamp', inplace=True)

        # Create a Plotly OHLC Chart
        fig = go.Figure(data=go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            increasing_line_color='green',  # Color for increasing candles
            decreasing_line_color='red'     # Color for decreasing candles
        ))

        # Update layout for better display
        fig.update_layout(
            title='Apple Inc. (AAPL) Stock OHLC Chart',
            xaxis_title='Date',
            yaxis_title='Price (USD)',
            xaxis_rangeslider_visible=False
        )

        # Display the Plotly chart in Streamlit
        st.plotly_chart(fig)
    
    def selectedCryptoChart(self, crypto):
        real_time_price_parameter = f'?symbol={crypto['symbol']}&apikey={os.getenv('TOKEN')}'
        real_time_price_response = self.apiCall('price', real_time_price_parameter, False)
        time_series_parameter = f'?symbol={crypto['symbol']}&interval=1month&apikey={os.getenv('TOKEN')}'
        time_series_response = self.apiCall('time_series', time_series_parameter, False)
        last_month_daily_parameter = f'?symbol={crypto['symbol']}&interval=1day&outputsize=32&apikey={os.getenv('TOKEN')}'
        last_month_daily = self.apiCall('time_series', last_month_daily_parameter, False)
        # https://api.twelvedata.com/time_series?symbol=AAPL&interval=1day&outputsize=31&apikey=your_api_key

        logging.info(f"==>> time_series_response: {time_series_response}")        
        st.markdown(f"""
### 💰 Real-Time Price for **{crypto['currency_base']}**
#### Current Price: **${real_time_price_response['price']}**
""", unsafe_allow_html=True)
        monthly_chart = pd.DataFrame(time_series_response['values'])
        st.subheader('Monthly Chart Trend')
        self.cryptoLineGraphCreation(monthly_chart)
        thirty_two_days = pd.DataFrame(last_month_daily['values'])
        st.subheader('Daily Chart Trend for Last 32 Days')
        self.cryptoLineGraphCreation(thirty_two_days)
        # st.write(df)


    def cryptoLineGraphCreation(self, df):
        # Convert datetime column to pandas datetime type
        df["datetime"] = pd.to_datetime(df["datetime"])
        # Convert to float and then format as strings with 4 decimal places
        df["open"] = df["open"].apply(lambda x: Decimal(x))
        df["close"] = df["close"].apply(lambda x: Decimal(x))


        # Sort the DataFrame by date
        df = df.sort_values(by="datetime")

        # Calculate whether the close went up or down compared to the previous month
        df["change"] = df["close"].diff()
        df["marker_color"] = df["change"].apply(lambda x: "green" if x > 0 else "red")

        # Create a line chart for the closing prices
        fig = px.line(df, x="datetime", y="close",
                    labels={"close": "Close Price (USD)", "datetime": "Date"})

        # Add markers at the end of each month
        fig.add_trace(go.Scatter(
            x=df["datetime"],
            y=df["close"],
            mode="markers",
            marker=dict(
                size=10,
                color=df["marker_color"],
                line=dict(width=1, color="black")
            ),
            name="Monthly Close Marker"
        ))

        # Update layout for better readability
        fig.update_layout(xaxis_title="Date", yaxis_title="Price (USD)")

        # Display the chart in Streamlit
        st.plotly_chart(fig)
        
    def apiCall(self, endpoint: str, parameters: str = '', header: bool = True):
        logging.error(f"==>> api call to {endpoint} endpoint")
        if header == False:
            url = f"https://api.twelvedata.com/{endpoint}{parameters}" 
            logging.warning(f"==>> url: {url}")
            response = requests.get(url)
        else:
            url = f"https://api.twelvedata.com/{endpoint}{parameters}"
            headers = {
                "accept": "application/json",
                "Authorization":os.getenv('TOKEN')
            }
            response = requests.get(url, headers)
        # st.write(response.json())
        return response.json()
    
    def loadingComponent(self):
        motivation_placeholder = st.empty()
        time.sleep(2)
        with st.spinner('Wait for it...'):
            counter = 0
            while counter < 2:
                motivation_placeholder.caption(self.dataset_arrays()[1])
                time.sleep(2)
                counter += 1
        motivation_placeholder.empty()
        return

    def main(self):
        st.title("Real-Time Crypto Dashboard")
        st.header("This is a simple app to display cryptocurrency data")
        st.divider()
        st.markdown(f"<span style='color: {self.dataset_arrays()[0]};'>Full Stack</span> Development by Stevenson Gerard", unsafe_allow_html=True)
        st.markdown(f"The :{self.dataset_arrays()[0]}[power] and :{self.dataset_arrays()[0]}[agility] of Python")

        market_placeholder = st.empty()

        # Button to get stock data
        if 'button_clicked' not in st.session_state:
            st.session_state['button_clicked'] = False

        if market_placeholder.button('Get Stock Data', type='primary'):
            st.session_state['button_clicked'] = True

        # Check if the button was clicked
        if st.session_state['button_clicked']:
            market_placeholder.empty()

            # Fetch cryptocurrency data
            crypto_response = self.apiCall('cryptocurrencies')
            unique_names = list({each_object['currency_base']: "" for each_object in crypto_response['data']})
            unique_names.insert(0, 'Select an option')

            # Initialize session state for the selected option
            if 'selected_crypto' not in st.session_state:
                st.session_state['selected_crypto'] = 'Select an option'

            # Create the selectbox and update session state
            selection_options = st.selectbox(
                "Select a cryptocurrency:",
                unique_names,
                index=unique_names.index(st.session_state['selected_crypto']),
                key='crypto_select'
            )

            # Update session state with the selected option
            st.session_state['selected_crypto'] = selection_options
            logging.info(f"==>> selection_options: {selection_options}")
            logging.info(f"==>> unique_names: {unique_names}")

            # Check if a valid cryptocurrency is selected
            if selection_options != 'Select an option':
                logging.info(f"==>> selection_options: {selection_options}")
                self.loadingComponent()

                # Filter the selected cryptocurrency
                find_selected_object = filter(
                    lambda tmp: tmp['currency_base'] == selection_options,
                    crypto_response['data']
                )
                crypto_selected = list(find_selected_object)[0]

                # Display the selected cryptocurrency chart
                self.selectedCryptoChart(crypto_selected)


 


if __name__ == "__main__":
    instantiate = CryptoView()
    main_page_header = instantiate.main()