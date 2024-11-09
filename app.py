import os
import time
import random


import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from api.motivational import motivational
from api.backend_data import quote, overtime_data



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
        filtered_object = [each_crypto for each_crypto in quote() if each_crypto["name"] == crypto][0]
        st.subheader(filtered_object['name'])
        df = pd.DataFrame.from_dict(filtered_object, orient='index')
        st.scatter_chart(df)

    def loadingComponent(self):
        motivation_placeholder = st.empty()
        time.sleep(2)
        with st.spinner('Wait for it...'):
            counter = 0
            while counter < 1:
                motivation_placeholder.caption(self.dataset_arrays()[1])
                time.sleep(1)
                counter += 1
        motivation_placeholder.empty()
        return

    def main(self):
        st.title("Real-Time Crypto Dashboard")
        st.header("This is a simple app to display cryptocurrency data")
        st.divider()
        st.markdown(f"<span style='color: {self.dataset_arrays()[0]};'>Full Stack</span> Development by Stevenson Gerard", unsafe_allow_html=True)
        st.markdown(f"The :{self.dataset_arrays()[0]}[power] and :{self.dataset_arrays()[0]}[agility] of Python")
        crypto_id = [each_object['name'] for each_object in quote()]
        crypto_id.insert(0, 'Select an option')
        # select_placeholder = st.empty()
        selected_crypto = st.selectbox(
            "Select a cryptocurrency:",
            crypto_id
        )
        market_placeholder = st.empty()  # Define the placeholder here
        market = market_placeholder.button('View Market', type='primary')
        if selected_crypto != 'Select an option':
            market_placeholder.empty()
            self.loadingComponent()
            self.selectedCryptoChart(selected_crypto)
        if market:
            market_placeholder.empty()
            self.allMarketData()
            # st.bar_chart(data=None, *, x=None, y=None, x_label=None, y_label=None, color=None, horizontal=False, stack=None, width=None, height=None, use_container_width=True)


 

    # print(x)


if __name__ == "__main__":
    instantiate = CryptoView()
    main_page_header = instantiate.main()