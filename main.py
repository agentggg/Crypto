"""
Real-Time Cryptocurrency Dashboard

This script implements a real-time cryptocurrency dashboard using Streamlit. It interacts with the Twelve Data API
to fetch and visualize market data. The application features OHLC candlestick charts, line graphs, and dynamic user inputs,
providing insights into cryptocurrency trends.

Features:
- API integration for fetching real-time and historical cryptocurrency data.
- Visualization using Plotly (OHLC and line charts).
- Interactive UI with motivational messages.
- Configurable logging for debugging and monitoring.

Dependencies:
- streamlit, pandas, plotly, requests, dotenv, twelvedata

Author: Stevenson Gerard
"""

import os  # Import os module for environment variable handling
import time  # Import time module for sleep delays
import random  # Import random module for random selections
import logging  # Import logging module for logging configuration
from decimal import Decimal  # Import Decimal for precise numeric representation

import streamlit as st  # Import Streamlit for web app interface
import requests  # Import requests module for making HTTP requests
import pandas as pd  # Import pandas for data manipulation
import plotly.graph_objects as go  # Import Plotly for advanced charting
import plotly.express as px  # Import Plotly Express for simpler charting
from dotenv import load_dotenv  # Import load_dotenv to read .env files
from twelvedata import TDClient  # Import TDClient for Twelve Data API access

from api.motivational import motivational  # Import motivational texts for user interface
from api.backend_data import quote, overtime_data  # Import backend data handling

# Configure logging with a specific format and level
logging.basicConfig(
    level=logging.WARNING,  # Set logging level to show only critical errors
    format="{asctime} | {levelname} | {name} | {message}",  # Define the format for log messages
    style="{",  # Use the new style format with curly braces
    datefmt="%Y-%m-%d %H:%M:%S",  # Set the date format for log messages
    force=True,  # Override any previous logging configuration
)

# Suppress verbose DEBUG logs from external libraries
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# Load environment variables from the .env file
load_dotenv()


class CryptoView:
    """
    CryptoView Class

    This class contains methods for fetching, processing, and visualizing cryptocurrency data
    within a Streamlit application.
    """

    def dataset_arrays(self):
        """
        Generates a random color and motivational text for UI elements.

        Returns:
        - tuple: (str, str) A random color and a motivational text.
        """
        # Select a random color for UI elements
        gui_color = self.randomColorSelection(["green", "orange", "red", "violet", "gray", "rainbow"])
        # Select a random motivational text
        motivational_text = self.randomColorSelection(motivational())
        return gui_color, motivational_text  # Return both selections as a tuple

    def randomColorSelection(self, dataset):
        """
        Randomly selects an item from a given list.

        Parameters:
        - dataset (list): List of items to choose from.

        Returns:
        - str: A randomly selected item from the list.
        """
        # Calculate the maximum index for random selection
        array_length = len(dataset) - 1
        # Generate a random index
        random_number = random.randint(0, array_length)
        # Return the item at the randomly selected index
        return dataset[random_number]

    def allMarketData(self):
        """
        Fetches and displays an OHLC candlestick chart for market data.

        Returns:
        - None
        """
        # Load market data into a pandas DataFrame
        df = pd.DataFrame(quote())

        # Convert string columns to numeric types for plotting
        df['open'] = pd.to_numeric(df['open'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['close'] = pd.to_numeric(df['close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Sort data by timestamp for correct chronological plotting
        df.sort_values(by='timestamp', inplace=True)

        # Create a candlestick chart using Plotly
        fig = go.Figure(data=go.Candlestick(
            x=df['timestamp'],  # X-axis with timestamps
            open=df['open'],  # Open prices
            high=df['high'],  # High prices
            low=df['low'],  # Low prices
            close=df['close'],  # Close prices
            increasing_line_color='green',  # Color for increasing candles
            decreasing_line_color='red'  # Color for decreasing candles
        ))

        # Update chart layout for better appearance
        fig.update_layout(
            title='Stock OHLC Chart',
            xaxis_title='Date',
            yaxis_title='Price (USD)',
            xaxis_rangeslider_visible=False  # Hide the range slider for clarity
        )

        # Display the chart in the Streamlit app
        st.plotly_chart(fig)

    def selectedCryptoChart(self, crypto):
        """
        Displays real-time and historical charts for a selected cryptocurrency.

        Parameters:
        - crypto (dict): Dictionary containing cryptocurrency data.

        Returns:
        - None
        """
        # Construct API parameters for fetching real-time price
        real_time_price_parameter = f"?symbol={crypto['symbol']}&apikey={os.getenv('TOKEN')}"
        # Fetch real-time price data
        real_time_price_response = self.apiCall('price', real_time_price_parameter, False)

        # Construct API parameters for monthly time series
        time_series_parameter = f"?symbol={crypto['symbol']}&interval=1month&outputsize=12&apikey={os.getenv('TOKEN')}"
        # Fetch monthly time series data
        time_series_response = self.apiCall('time_series', time_series_parameter, False)

        # Construct API parameters for daily time series of the last 32 days
        last_month_daily_parameter = f"?symbol={crypto['symbol']}&interval=1day&outputsize=32&apikey={os.getenv('TOKEN')}"
        last_month_daily = self.apiCall('time_series', last_month_daily_parameter, False)

        # Display the real-time price
        st.markdown(f"""
### 💰 Real-Time Price for **{crypto['currency_base']}**
#### Current Price: **${real_time_price_response['price']}**
""", unsafe_allow_html=True)

        # Plot the monthly and daily charts
        self.cryptoLineGraphCreation(pd.DataFrame(time_series_response['values']))
        self.cryptoLineGraphCreation(pd.DataFrame(last_month_daily['values']))

    def cryptoLineGraphCreation(self, df):
        """
        Creates a line graph with markers for closing prices.

        Parameters:
        - df (DataFrame): DataFrame containing time series data.

        Returns:
        - None
        """
        # Convert 'datetime' column to pandas datetime type
        df["datetime"] = pd.to_datetime(df["datetime"])
        # Convert 'close' column to Decimal type for precision
        df["close"] = df["close"].apply(lambda x: Decimal(x))

        # Sort DataFrame by datetime
        df.sort_values(by="datetime", inplace=True)

        # Calculate the difference in close prices and assign marker colors
        df["change"] = df["close"].diff()
        df["marker_color"] = df["change"].apply(lambda x: "green" if x > 0 else "red")

        # Create a line graph of close prices
        fig = px.line(df, x="datetime", y="close")

        # Add markers for monthly close points
        fig.add_trace(go.Scatter(
            x=df["datetime"],
            y=df["close"],
            mode="markers",
            marker=dict(size=10, color=df["marker_color"]),
            name="Close Markers"
        ))

        # Update layout and display the graph
        fig.update_layout(
            xaxis_title="Date", 
            yaxis_title="Price (USD)",
            margin=dict(l=10, r=10, t=30, b=10),  # Reduce margins for a larger display area
            height=600  # Increase the height of the chart
            )
        st.plotly_chart(fig, use_container_width=True)
  
    def selectedCryptoChart(self, crypto):
        """
        Fetches and displays real-time price, monthly trend, and daily trend charts for a selected cryptocurrency.

        Parameters:
        - crypto (dict): Dictionary containing information about the selected cryptocurrency.

        Returns:
        - None
        """
        # Construct API query parameter for real-time price
        real_time_price_parameter = f'?symbol={crypto["symbol"]}&apikey={os.getenv("TOKEN")}'
        # Make an API call to fetch real-time price data
        real_time_price_response = self.apiCall('price', real_time_price_parameter, False)

        # Construct API query parameter for monthly time series data
        time_series_parameter = f'?symbol={crypto["symbol"]}&interval=1month&apikey={os.getenv("TOKEN")}'
        # Make an API call to fetch monthly time series data
        time_series_response = self.apiCall('time_series', time_series_parameter, False)

        # Construct API query parameter for daily time series data (last 32 days)
        last_month_daily_parameter = f'?symbol={crypto["symbol"]}&interval=1day&outputsize=32&apikey={os.getenv("TOKEN")}'
        # Make an API call to fetch daily time series data
        last_month_daily = self.apiCall('time_series', last_month_daily_parameter, False)

        # Log the fetched monthly time series data for debugging purposes
        logging.info(f"==>> time_series_response: {time_series_response}")

        # Display real-time price using Markdown
        st.markdown(f"""
### 💰 Real-Time Price for **{crypto['currency_base']}**
#### Current Price: **${real_time_price_response['price']}**
""", unsafe_allow_html=True)

        # Convert monthly time series data to a DataFrame
        monthly_chart = pd.DataFrame(time_series_response['values'])
        st.subheader('Monthly Chart Trend')  # Add a subheader for the monthly trend chart
        self.cryptoLineGraphCreation(monthly_chart)  # Create and display the line graph for the monthly trend

        # Convert daily time series data to a DataFrame
        thirty_two_days = pd.DataFrame(last_month_daily['values'])
        st.subheader('Daily Chart Trend for Last 32 Days')  # Add a subheader for the daily trend chart
        self.cryptoLineGraphCreation(thirty_two_days)  # Create and display the line graph for the daily trend

    def cryptoLineGraphCreation(self, df):
        """
        Creates a line graph with markers indicating the closing prices of the cryptocurrency.

        Parameters:
        - df (DataFrame): DataFrame containing the time series data.

        Returns:
        - None
        """
        # Convert the 'datetime' column to pandas datetime format
        df["datetime"] = pd.to_datetime(df["datetime"])

        # Convert 'open' and 'close' columns to Decimal type for better precision
        df["open"] = df["open"].apply(lambda x: Decimal(x))
        df["close"] = df["close"].apply(lambda x: Decimal(x))

        # Sort the DataFrame by the 'datetime' column
        df = df.sort_values(by="datetime")

        # Calculate the change in 'close' prices and determine marker colors (green for increase, red for decrease)
        df["change"] = df["close"].diff()
        df["marker_color"] = df["change"].apply(lambda x: "green" if x > 0 else "red")

        # Create a line chart for the 'close' prices using Plotly Express
        fig = px.line(df, x="datetime", y="close",
                      labels={"close": "Close Price (USD)", "datetime": "Date"})

        # Add markers at the end of each month with colors indicating price increase or decrease
        fig.add_trace(go.Scatter(
            x=df["datetime"],  # X-axis values (dates)
            y=df["close"],  # Y-axis values (close prices)
            mode="markers",  # Display as markers
            marker=dict(
                size=10,  # Marker size
                color=df["marker_color"],  # Marker color based on price change
                line=dict(width=1, color="black")  # Outline color of the markers
            ),
            name="Monthly Close Marker"  # Name for the legend
        ))

        # Update chart layout for better readability
        fig.update_layout(xaxis_title="Date", yaxis_title="Price (USD)")

        # Display the line chart in Streamlit
        st.plotly_chart(fig)

    def apiCall(self, endpoint: str, parameters: str = '', header: bool = True):
        """
        Sends an HTTP GET request to the Twelve Data API to fetch cryptocurrency data.

        Parameters:
        - endpoint (str): The API endpoint to call (e.g., 'price', 'time_series').
        - parameters (str): The query parameters for the API request.
        - header (bool): If True, include authorization headers; otherwise, make a simple GET request.

        Returns:
        - dict: The JSON response from the API.
        """
        # Log the API call for debugging
        logging.error(f"==>> api call to {endpoint} endpoint")

        # Construct the URL without headers
        if header == False:
            url = f"https://api.twelvedata.com/{endpoint}{parameters}"
            logging.warning(f"==>> url: {url}")
            response = requests.get(url)  # Send GET request without headers

        # Construct the URL with headers
        else:
            url = f"https://api.twelvedata.com/{endpoint}{parameters}"
            headers = {
                "accept": "application/json",  # Accept JSON response
                "Authorization": os.getenv('TOKEN')  # Include API token from environment variables
            }
            response = requests.get(url, headers)  # Send GET request with headers

        # Return the JSON response from the API
        return response.json()

    def loadingComponent(self):
        """
        Displays a loading spinner with motivational messages during data fetch.

        Returns:
        - None
        """
        motivation_placeholder = st.empty()  # Create an empty placeholder for motivational messages
        time.sleep(2)  # Delay for 2 seconds

        # Display a loading spinner with motivational messages
        with st.spinner('Wait for it...'):
            counter = 0
            while counter < 2:  # Show two messages before clearing
                motivation_placeholder.caption(self.dataset_arrays()[1])  # Display a random motivational message
                time.sleep(2)  # Delay for 2 seconds
                counter += 1

        motivation_placeholder.empty()  # Clear the placeholder after loading
    
    def sourceCode():
        """
        Displays the source code of the current script using Streamlit's `st.code()` component.

        Returns:
        - None
        """
        st.markdown(
            """
            <style>
            .streamlit-container pre {
                white-space: pre-wrap;       /* Enable line wrapping */
                word-wrap: break-word;       /* Break words if necessary */
                overflow-x: auto;            /* Allow horizontal scrolling if needed */
            }
            </style>
            """,
            unsafe_allow_html=True
        ) #allows wrapping and styling to fit your screen

        # Open the script file and display it with wrapping enabled
        with open('main.py', 'r') as f:
            content = f.read()  # Read the entire content of the file
            st.code(content, language='python')  # Display the source code with wrapping


    def main(self):
        """
        Main method to manage view switching and handle user interaction.

        Returns:
        - None
        """
        # Initialize session state for view management if it doesn't exist
        if "current_view" not in st.session_state:
            st.session_state["current_view"] = "dashboard"  # Set the default view to 'dashboard'

        # Button to switch to the source code view
        if st.button("Checkout Python Source Code 👏🏾🎬🐍💻📚📈", type='primary'):
            st.session_state["current_view"] = "source_code"  # Update session state to display the source code view

        # Conditional rendering based on the current view
        if st.session_state["current_view"] == "source_code":
            self.source_code_view()  # Display the source code view
        else:
            self.dashboard_view()  # Display the main dashboard view


    def dashboard_view(self):
        """
        Displays the main dashboard view with cryptocurrency data using Streamlit components.

        Returns:
        - None
        """
        # Title and header for the dashboard
        st.title("Real-Time Crypto Dashboard")
        st.header("This is a simple app to display cryptocurrency data")
        st.divider()  # Add a horizontal divider for visual separation

        # Display a styled markdown message with color and text
        st.markdown(
            f"<span style='color: {self.dataset_arrays()[0]};'>Full Stack</span> Development by Stevenson Gerard",
            unsafe_allow_html=True
        )
        # Display another styled markdown message with emoji and dynamic text color
        st.markdown(f"The :{self.dataset_arrays()[0]}[power] and :{self.dataset_arrays()[0]}[agility] of Python")

        # Create an empty placeholder for the 'Get Stock Data' button
        market_placeholder = st.empty()

        # Initialize session state for the 'button_clicked' flag if it doesn't exist
        if 'button_clicked' not in st.session_state:
            st.session_state['button_clicked'] = False  # Set the default flag to False

        # Display a button to fetch stock data, update session state on click
        if market_placeholder.button('Get Stock Data', type='primary'):
            st.session_state['button_clicked'] = True  # Set the flag to True when the button is clicked

        # Check if the 'Get Stock Data' button was clicked
        if st.session_state['button_clicked']:
            market_placeholder.empty()  # Clear the placeholder after the button is clicked

            # Fetch the list of cryptocurrencies from the API
            crypto_response = self.apiCall('cryptocurrencies')
            # Create a list of unique cryptocurrency names
            unique_names = list({each_object['currency_base']: "" for each_object in crypto_response['data']})
            unique_names.insert(0, 'Select an option')  # Insert a default option at the beginning

            # Initialize session state for the selected cryptocurrency if it doesn't exist
            if 'selected_crypto' not in st.session_state:
                st.session_state['selected_crypto'] = 'Select an option'  # Set default selection

            # Display a select box for choosing a cryptocurrency
            selection_options = st.selectbox(
                "Select a cryptocurrency:",  # Label for the select box
                unique_names,  # List of options to display
                index=unique_names.index(st.session_state['selected_crypto']),  # Set the default index
                key='crypto_select'  # Use session state key to track the selected option
            )

            # Update session state with the selected option
            st.session_state['selected_crypto'] = selection_options
            logging.info(f"==>> selection_options: {selection_options}")  # Log the selected option for debugging

            # Check if a valid cryptocurrency is selected
            if selection_options != 'Select an option':
                self.loadingComponent()  # Display a loading spinner

                # Filter the API response to find the selected cryptocurrency object
                find_selected_object = filter(
                    lambda tmp: tmp['currency_base'] == selection_options,
                    crypto_response['data']
                )
                crypto_selected = list(find_selected_object)[0]  # Extract the selected cryptocurrency object

                # Display the selected cryptocurrency's chart
                self.selectedCryptoChart(crypto_selected)


    def source_code_view(self):
        # Button to return to the main dashboard view
        if st.button("Tap Twice to Go Back to Dashboard"):
            st.session_state["current_view"] = "dashboard"  # Update session state to display the dashboard view
            st.session_state.clear()  # Clear session state to force a re-render of the dashboard view

        with open('main.py', 'r') as f:
            content = f.read()  # Read the entire content of the file
            # Provide a download button with the specified filename and extension
            st.download_button(
                label="Tap to Download Python Code For Better Viewing",
                data=content,
                file_name="Stevenson_Stock_App.py",  # Set the desired filename with .py extension
                mime="text/plain"  # Set the MIME type to plain text
            )
            
        #Displays the source code of the current script using Streamlit's `st.code()` component.
        #Returns: - None
        # Display the title of the source code view
        st.title("Source Code View")
        # Display a markdown message
        st.header('Instructions 😄')
        st.markdown(
            """
            1. Press the 3 dots on the top right side and select **Wide mode** for a better view. 🙏🏾
            2. If you are on a mobile device, rotate your device to landscape mode for an even better view. 🙏🏾📲
            3. Or you can just view it on a laptop for the best experience. 🙏🏾😄💻
            """
        )



        # Inject custom CSS to enable line wrapping for `st.code()`
        st.markdown(
            """
            <style>
            .streamlit-container pre {
                white-space: pre-wrap;       /* Enable line wrapping */
                word-wrap: break-word;       /* Break words if necessary */
                overflow-x: auto;            /* Allow horizontal scrolling if needed */
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Open the script file and display it with wrapping enabled
        with open('main.py', 'r') as f:
            content = f.read()  # Read the entire content of the file
            st.code(content, language='python')  # Display the source code with wrapping

        if st.button("Tap Twice to Go Back to Dashboard."):
            st.session_state["current_view"] = "dashboard"  # Update session state to display the dashboard view
            st.session_state.clear()  # Clear session state to force a re-render of the dashboard view

        

# Entry point of the application
if __name__ == "__main__":
    instantiate = CryptoView()  # Instantiate the CryptoView class
    main_page_header = instantiate.main()  # Call the main method to start the app
