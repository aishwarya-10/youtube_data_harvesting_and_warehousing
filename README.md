# YouTube Data Harvesting and Warehousing
The project extracts YouTube channel data using the YouTube API key.

## Overview
  The project uses the YouTube Data API to harvest data from YouTube channels, followed by meticulous processing and subsequent warehousing. At first, the acquired data is stored in MongoDB as documents and then converted into SQL records to facilitate comprehensive data analysis. Finally, the retrieved data is displayed on the Streamlit app.

**Demo Video:** Click here to watch

## Problem Statement
- To create a Streamlit application that allows users to enter a YouTube channel ID and retrieve channel details using YouTube Data API.
- The harvested data is to be stored in MongoDB and later transformed to migrate it into a SQL data warehouse.
- The application should be able to retrieve data from SQL DB by multiple search options.

## Take Away Skills
The following skills were acquired from the project:
  1. Python scripting,
  2. API integration,
  3. Data Management using MongoDB and MySQL,
  4. Pandas,
  5. Streamlit app development,
  6. Plotly data visualization.

## Work Flow
- **API connect:** Establish a connection to the YouTube API to collect channel, video, and comment details. The Google API client library for Python is used to send requests and retrieve necessary data.
- **Data Harvest:** Streamlit app creates a simple UI for users to enter the channel ID to extract information.
- **Data Management:** Initially the harvested data is stored in MongoDB, as it can handle unstructured and semi-structured data easily. '''pymongo''' library is used to connect Python with MongoDB.
- **Data Migration:** Upon collecting data from multiple channels, the next phase involves the transformation and migration of the documented data into a structured MySQL database. This meticulous process ensures that the collected data is organized and optimized for efficient querying and analysis in the '''pymysql''' environment.
- **Data Analysis:** Leveraging join functions in SQL queries, valuable insights about channels are retrieved according to user input.
- **Display Data:** Finally Streamlit displays the channel insights using tables and charts to help users to analyze the data.

![image](https://github.com/aishwarya-10/youtube_data_harvesting_and_warehousing/assets/48954230/cf82d0b5-37d2-4090-a57a-5a7aaf7887d1)

## App Usage
Upon successful setup and activation of the project, users can engage with the Streamlit application via a web browser. The application presents a user-friendly interface, enabling users to perform the following actions:
- Input a YouTube channel ID to fetch data for the specified channel.
- Collect and store data for numerous YouTube channels in MongoDB.
- Choose a channel and transfer its data from MongoDB to the SQL data warehouse.
- View the details of uploaded channels.
- Search and fetch data from SQL database using diverse search options.
- Conduct channel data analysis and visualization using these integrated features.

## Conclusion
  This project endeavors to craft a user-friendly Streamlit application, leveraging the Google API to extract detailed information from YouTube channels. The retrieved data is then stored in a MongoDB database and seamlessly migrated to a SQL data warehouse. The Streamlit app offers users the functionality to effortlessly search for channel details and perform table joins, enhancing the overall data exploration experience.

## References
- YouTube Data API [https://developers.google.com/youtube/v3/getting-started]
- MongoDB [https://www.mongodb.com/docs/drivers/pymongo/]
- MySQL [https://pypi.org/project/pymysql/]
- Pandas [https://pandas.pydata.org/docs/]
- Streamlit App [https://docs.streamlit.io/library/api-reference]
- Plotly [https://plotly.com/python-api-reference/]
