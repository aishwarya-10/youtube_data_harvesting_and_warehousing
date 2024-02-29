# ==================================================       /     IMPORT LIBRARY    /      =================================================== #
#[API]
import googleapiclient.discovery

#[MongoDB]
import pymongo

#[MySQL]
import pymysql

#[Pandas]
import pandas as pd

#[Format dtype]
import re

#[UI]
import streamlit as st
import plotly.express as px


# ==================================================       /     CUSTOMIZATION    /      =================================================== #
# Streamlit Page Configuration
st.set_page_config(
    page_title = "YouTube Data",
    layout = "wide")
st.title(":red[YouTube Data Harvesting and Warehouse using SQL, MongoDB and Streamlit]")


# ==================================================       /     DATA COLLECTION SECTION    /      =================================================== #
st.header(":violet[Data Collection] :envelope_with_arrow:")

channel_id = st.text_input("Enter a YouTube Channel-id:")

# Initial value for session state
if "button_clicked" not in st.session_state:
    st.session_state["button_clicked"] = False

# Button to trigger state change
if st.button("Collect and Store Data"):
    st.session_state["button_clicked"] = True

    with st.spinner("Fetching Data..."):
        def Api_key_client():
            """
            Creates a client object for interacting with an API using an API key.

            Returns:
                object: An object representing the API client
            """
            api_key = "YOUR-API-KEY"
            api_service_name = "youtube"
            api_version = "v3"
            youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)
            return youtube

        # Create API client
        youtube = Api_key_client()

        def get_channel_info(channel_id: str):
            """
            Collects channel infromation from YouTube API.

            Args:
                Channel_id (str): Unique Youtube chnanel id.
            
            Returns:
                dict: A dict containing channel information or None if entered invalid channel-id.
            """
            try:
                channel_response = youtube.channels().list(
                    part= "snippet,contentDetails,statistics",
                    id= channel_id
                ).execute()

                # Input validation
                if "items" not in channel_response:
                    st.error("Please enter an valid channel-id.")
                    return None
                return channel_response
            
            except Exception as e:
                st.error("Error fetching channel data for ", e)
                return None


        # Extract neccessary info from channel response
        channel_data = get_channel_info(channel_id)
        channel_name = channel_data["items"][0]["snippet"]["localized"]["title"]
        channel_video_count = channel_data['items'][0]['statistics']['videoCount']
        channel_subscriber_count = channel_data['items'][0]['statistics']['subscriberCount']
        channel_view_count = channel_data['items'][0]['statistics']['viewCount']
        channel_description = channel_data['items'][0]['snippet']['description']
        channel_playlist_id = channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # Channel data into dict
        channel_stats = {
            "Channel_Details": {
                "Channel_name": channel_name,
                "Channel_id": channel_id,
                "Channel_description": channel_description,
                "Subscription_count": channel_subscriber_count,
                "Video_count": channel_video_count,
                "View_count": channel_view_count,
                "Playlist_id": channel_playlist_id
            }
        }


        def get_video_ids(channel_playlist_id: str):
            """
            Collects video ids of videos available in playlist.

            Args:
                channel_playlist_id (str): Unique playlist id from channel.

            Returns:
                list: A list of video ids.
            """
            video_ids = []
            next_page_token = None

            while True:
                # Generate playlist details
                playlist_response = youtube.playlistItems().list(
                    playlistId = channel_playlist_id,
                    part = "snippet, contentDetails",
                    pageToken = next_page_token
                ).execute()

                # Store video id of each video in playlist
                for item in playlist_response['items']:
                    video_ids.append(item["contentDetails"]["videoId"])

                # Check if there's next page in playlist
                next_page_token = playlist_response.get("nextPageToken")

                if next_page_token is None:
                    break
            return video_ids


        def duration_to_seconds(duration_str: str):
            """
            Converts a duration string in the format "PT[Xh]M[Xm]S" to seconds.

            Args:
                duration_str (str): The duration string to convert.

            Returns:
                int: The duration in seconds, or None if the format is invalid.
            """
            match = re.match(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$", duration_str)

            if not match:
                return 0
            hours = int(match.group(1) or 0) * 3600
            minutes = int(match.group(2) or 0) * 60
            seconds = int(match.group(3) or 0)
            return hours + minutes + seconds


        # Collect video ids
        video_ids = get_video_ids(channel_playlist_id)

        def get_video_comments(video_id: str, max_comments_per_video=100):
            """
            Collects all the comment details of a video

            Args:
                video_id (str): a unique identifier of YouTube video.
                max_comments_per_video (int): Comment count.

            Returns:
                dict: A dict containing comment details. 
            """
            comment_response = youtube.commentThreads().list(
                part= "snippet",
                videoId= video_id,
                maxResults= max_comments_per_video,
                ).execute()     
            return comment_response


        def get_video_info(video_ids: list):
            """
            Collects video information along with comments information.

            Args:
                video_ids (list): A list of video ids

            Returns:
                dict: A dict with video details.
            """
            video_info = []
            for video_id in video_ids:
                video_response = youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=video_id
                ).execute()
                video = video_response["items"][0]

                # Get comments 
                try:
                    video['comment_threads'] = get_video_comments(video_id, max_comments_per_video=10)
                except:
                    video['comment_threads'] = None

                # Format duration
                duration = video.get('contentDetails', {}).get('duration', 'Not Available')
                if duration != 'Not Available':
                    duration = duration_to_seconds(duration)
                video['contentDetails']['duration'] = duration

                video_info.append(video)
            return video_info


        # Fetch Video and Comment Data
        video_data = get_video_info(video_ids)

        # Format video data with comments
        video_stats = {}
        for i, video in enumerate(video_data):
            # store required details
            video_id = video["id"]
            video_name = video["snippet"]["title"]
            description = video['snippet']['description']
            thumbnail = video["snippet"]["thumbnails"]['default']['url']
            published_date = video['snippet']['publishedAt']
            duration = video['contentDetails']['duration']
            views = video['statistics']['viewCount']
            likes = video['statistics'].get('likeCount')
            comment_count = video['statistics'].get('commentCount')
            favorite_count = video['statistics']['favoriteCount']
            caption_status = video['contentDetails']['caption']
            comments = {}

            # To add comments info of each video
            if video[f"comment_threads"] is not None:
                comments = {}
                for index, comment_thread in enumerate(video['comment_threads']['items']):
                    comment = comment_thread['snippet']['topLevelComment']['snippet']
                    comment_id = comment_thread['id']
                    comment_text = comment['textDisplay']
                    comment_author = comment['authorDisplayName']
                    comment_published_at = comment['publishedAt']

                    comments[f"Comment_ID_{index + 1}"] = {
                        'Comment_ID': comment_id,
                        'Comment_Text': comment_text,
                        'Comment_Author': comment_author,
                        'Comment_PublishedAt': comment_published_at
                    }

            # Process comment data into video data as dictionary
            video_stats[f"Video_ID_{i+1}"] = {
                "Video_id": video_id,
                "Video_name": video_name,
                "Description": description,
                "Thumbnail": thumbnail,
                "Published_date": published_date,
                "Duration": duration,
                "View_count": views,
                "Like_count": likes,
                "Comment_count": comment_count,
                "Favorite_count": favorite_count,
                "Caption_status": caption_status,
                "comments": comments
            }

        # Combine channel details and video details to a dictionary
        fetched_data = {**channel_stats, **video_stats}


        # Connect to MongoDB & upload the data
        client = pymongo.MongoClient('MONGO-CLIENT-URL')
        mydb = client["youtube_DB"]
        collection = mydb["youtube_data"]

        # define the data to insert
        final_output_data = {
            'Channel_Name': channel_name,
            "Channel_data": fetched_data
            }

        # insert data or create new document
        upload = collection.replace_one({"_id": channel_id}, final_output_data, upsert = True)

        # Display a success message of upload
        st.success('The channel details are uploaded successfully!', icon="✅")

        # close connection
        client.close()


# ==================================================       /     DATA MIGRATION SECTION    /      =================================================== #
# Fetch Data from MongoDB to Migrate Data to MySQL
st.header(":violet[Data Migration] :arrow_right:")

# Create a connection with MongoClient
client = pymongo.MongoClient('MONGO-CLIENT-URL')
mydb = client["youtube_DB"]
collection = mydb["youtube_data"]

# Collect the channel names 
channel_names = []
for channel in collection.find():
    channel_names.append(channel["Channel_Name"])

channel_name = st.selectbox("Choose channel for MySQL Migration", options= channel_names)

# Initial value for session state
if "migration_button_clicked" not in st.session_state:
    st.session_state["migration_button_clicked"] = False

# Button to trigger state change
if st.button("Migarte to MySQL"):
    st.session_state["migration_button_clicked"] = True

    with st.spinner("Warehousing Data..."):
        # Fetch document with the specified channel name
        document = collection.find_one({"Channel_Name":channel_name})
        client.close()

        # Dictionary to DataFrame conversion
        dict_channel = {
            "Channel_name": document['Channel_Name'],
            "Channel_id": document['_id'],
            "Channel_description": document['Channel_data']['Channel_Details']['Channel_description'],
            "Subscription_count": document['Channel_data']['Channel_Details']['Subscription_count'],
            "Video_count": document['Channel_data']['Channel_Details']['Video_count'],
            "View_count": document['Channel_data']['Channel_Details']['View_count'],
            }
        df_channel = pd.DataFrame.from_dict(dict_channel, orient='index').T


        dict_playlist = {"Playlist_id": document['Channel_data']['Channel_Details']["Playlist_id"],
                        "Channel_id": document['_id'],
                        }
        df_playlist = pd.DataFrame.from_dict(dict_playlist, orient= "index").T


        list_video = []
        for i in range(1,len(document['Channel_data'])):
            video_details_dict = {
                'Video_Id': document['Channel_data'][f"Video_ID_{i}"]['Video_id'],
                'Playlist_Id':document['Channel_data']['Channel_Details']['Playlist_id'],
                'Video_Name': document['Channel_data'][f"Video_ID_{i}"]['Video_name'],
                'Video_Description': document['Channel_data'][f"Video_ID_{i}"]['Description'],
                'Published_date': document['Channel_data'][f"Video_ID_{i}"]['Published_date'],
                'View_Count': document['Channel_data'][f"Video_ID_{i}"]['View_count'],
                'Like_Count': document['Channel_data'][f"Video_ID_{i}"]['Like_count'],
                'Favorite_Count': document['Channel_data'][f"Video_ID_{i}"]['Favorite_count'],
                'Comment_Count': document['Channel_data'][f"Video_ID_{i}"]['Comment_count'],
                'Duration': document['Channel_data'][f"Video_ID_{i}"]['Duration'],
                'Thumbnail': document['Channel_data'][f"Video_ID_{i}"]['Thumbnail'],
                'Caption_Status': document['Channel_data'][f"Video_ID_{i}"]['Caption_status']
                }
            list_video.append(video_details_dict)
        df_video = pd.DataFrame(list_video)

        list_comment = []
        for i in range(1,len(document['Channel_data'])):
            comments_section = document['Channel_data'][f"Video_ID_{i}"]['comments']
            if len(comments_section) != 0:
                for j in range(1, len(comments_section)+1):
                    comment_details_dict = {
                        "Comment_id": document['Channel_data'][f"Video_ID_{i}"]["comments"][f"Comment_ID_{j}"]['Comment_ID'],
                        "Video_id": document['Channel_data'][f"Video_ID_{i}"]['Video_id'],
                        "Comment_text": document['Channel_data'][f"Video_ID_{i}"]["comments"][f"Comment_ID_{j}"]['Comment_Text'],
                        "Comment_author": document['Channel_data'][f"Video_ID_{i}"]["comments"][f"Comment_ID_{j}"]['Comment_Author'],
                        "Comment_published_date": document['Channel_data'][f"Video_ID_{i}"]["comments"][f"Comment_ID_{j}"]['Comment_PublishedAt']
                    }
                list_comment.append(comment_details_dict)

        df_comment = pd.DataFrame(list_comment)


        # Create DB on MySQL
        myconnection = pymysql.connect(
            host = 'HOST',
            user='USER-NAME',
            passwd='YOUR-PASSWORD'
            )
        cur = myconnection.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS youtube_sql_db")
        cur.close()
        myconnection.close()

        # Connect to SQL database
        myconnection = pymysql.connect(
            host = 'HOST',
            user='USER-NAME',
            passwd='YOUR-PASSWORD',
            database = "youtube_sql_db"
            )
        cur = myconnection.cursor()

        # Create SQL table
        cur.execute("""CREATE TABLE IF NOT EXISTS Channel(
                    Channel_name VARCHAR(255),
                    Channel_id VARCHAR(255) PRIMARY KEY,
                    Channel_description TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    Subscription_count BIGINT,
                    Video_count INT,
                    View_count BIGINT
                    )""")

        cur.execute("""CREATE TABLE IF NOT EXISTS Playlist(
                    Playlist_id VARCHAR(255) PRIMARY KEY,
                    Channel_id VARCHAR(255), 
                    FOREIGN KEY (Channel_id) REFERENCES Channel(Channel_id)
                    )""")

        cur.execute("""CREATE TABLE IF NOT EXISTS Video(
                    Video_Id VARCHAR(255) PRIMARY KEY,
                    Playlist_Id VARCHAR(255),
                    Video_Name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    Video_Description TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    Published_date VARCHAR(255),
                    View_Count BIGINT,
                    Like_Count BIGINT,
                    Favorite_Count INT,
                    Comment_Count BIGINT,
                    Duration INT,
                    Thumbnail VARCHAR(255),
                    Caption_Status VARCHAR(255),
                    FOREIGN KEY (Playlist_Id) REFERENCES Playlist(Playlist_id)
                    )""")

        cur.execute("""CREATE TABLE IF NOT EXISTS Comment(
                    Comment_id VARCHAR(255) PRIMARY KEY,
                    Video_id VARCHAR(255),
                    Comment_text TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    Comment_author VARCHAR(255),
                    Comment_published_date VARCHAR(255),
                    FOREIGN KEY (Video_id) REFERENCES Video(Video_Id)
                    )""")

        # Insert channel, playlist, video and comment dataframe into SQL table
        channel_insert_sql = "INSERT INTO Channel (Channel_name, Channel_id, Channel_description, Subscription_count, Video_count, View_count) VALUES (%s,%s,%s,%s,%s,%s)"
        for i in range(0,len(df_channel)):
            cur.execute(channel_insert_sql,tuple(df_channel.iloc[i]))
            myconnection.commit()

        playlist_insert_sql = "INSERT INTO Playlist (Playlist_id, Channel_id) VALUES (%s,%s)"
        for i in range(0,len(df_playlist)):
            cur.execute(playlist_insert_sql,tuple(df_playlist.iloc[i]))
            myconnection.commit()

        video_insert_sql = "INSERT INTO Video (Video_Id, Playlist_Id, Video_Name, Video_Description, Published_date, View_Count, Like_Count, Favorite_Count, Comment_Count, Duration, Thumbnail, Caption_Status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        for i in range(0,len(df_video)):
            cur.execute(video_insert_sql,tuple(df_video.iloc[i]))
            myconnection.commit()

        comment_insert_sql = "INSERT INTO Comment (Comment_id, Video_id, Comment_text, Comment_author, Comment_published_date) VALUES (%s,%s,%s,%s,%s)"
        for i in range(0,len(df_comment)):
            cur.execute(comment_insert_sql,tuple(df_comment.iloc[i]))
            myconnection.commit()


# ==================================================       /     CHANNEL DATA ANALYSIS    /      =================================================== #
# View Channel Details Uploaded
st.header(":violet[Channel Data Analysis] :gear:")

# check stored channel data
check_channel = st.checkbox("View Uploaded Channel Details")

if check_channel:
    # Connect to SQL database
    connection = pymysql.connect(
        host = 'HOST',
        user='USER-NAME',
        passwd='YOUR-PASSWORD',
        db="youtube_sql_db"
        )
    cur = connection.cursor()
    cur.execute("SELECT Channel_id, Channel_name FROM Channel")
    result = cur.fetchall()
    df_viewChannel = pd.DataFrame(result, columns=["Channel ID", "Channel Name"]).reset_index(drop=True)
    df_viewChannel.index += 1
    st.dataframe(df_viewChannel)
    connection.close()


# ==================================================       /     DATA EXTRACTION SECTION    /      =================================================== #
# Query the SQL data
st.subheader(":blue[Extract Channel Data]")

# Connect to SQL database
try:
    Query_connection = pymysql.connect(
        host = 'HOST',
        user='USER-NAME',
        passwd='YOUR-PASSWORD',
        db="youtube_sql_db"
        )
    cur = Query_connection.cursor()
except:
    print('Database connection could not be established.')

# Initial value for session state
if "selectbox_enabled" not in st.session_state:
    st.session_state["selectbox_enabled"] = False

# Function to execute the chosen query
def execute_query(selected_option: str):
    """
    Extracts data from SQL table.

    Args:
        selected_option (str): A question selected to query SQL table.

    Returns:
        DataFrame: The extracted info is displayed in table.
    """
    if selected_option == "1. What are the names of all the videos and their corresponding channels?":
        cur.execute("""SELECT T3.Channel_name, T1.video_Name FROM Video AS T1
                        INNER JOIN Playlist AS T2 ON T1.Playlist_Id = T2.Playlist_id
                        INNER JOIN Channel AS T3 ON T2.Channel_id = T3.Channel_id
                        ORDER BY T3.Channel_name ASC
                    """)
        result1 = cur.fetchall()
        df1 = pd.DataFrame(result1, columns=["Channel Name", "Video Name"]).reset_index(drop=True)
        df1.index += 1
        st.dataframe(df1)

    elif selected_option == "2. Which channels have the most number of videos, and how many videos do they have?":
        cur.execute("SELECT Channel_name, Video_count FROM Channel WHERE Video_count IN (SELECT MAX(Video_count) FROM Channel)")
        result2 = cur.fetchall()
        df2 = pd.DataFrame(result2, columns=["Channel Name", "Total number of Videos"]).reset_index(drop=True)
        df2.index += 1
        st.dataframe(df2)

    elif selected_option == "3. What are the top 10 most viewed videos and their respective channels?":
        col1, col2 = st.columns(2)
        with col1:
            cur.execute("""SELECT T3.Channel_name, T1.video_Name, T1.View_count FROM Video AS T1
                            INNER JOIN Playlist AS T2 ON T1.Playlist_Id = T2.Playlist_id
                            INNER JOIN Channel AS T3 ON T2.Channel_id = T3.Channel_id
                            ORDER BY T1.View_count DESC LIMIT 10
                        """)
            result3 = cur.fetchall()
            df3 = pd.DataFrame(result3, columns=["Channel Name", "Video Name", "Views"]).reset_index(drop=True)
            df3.index += 1
            st.dataframe(df3)

        with col2:
            fig_topvc = px.bar(df3, x= "Views", y= "Video Name", orientation= 'h', color= "Channel Name", text_auto='.2s', title="Top 10 Most Viewed Videos")
            fig_topvc.update_traces(textfont_size= 16)
            fig_topvc.update_xaxes(title_font=dict(size= 20))
            fig_topvc.update_yaxes(title_font=dict(size= 20))
            fig_topvc.update_layout(title_font_color= '#1308C2 ', title_font=dict(size= 25))
            st.plotly_chart(fig_topvc, use_container_width=True)

    elif selected_option == "4. How many comments were made on each video, and what are their corresponding channel names?":
        cur.execute("""SELECT T3.Channel_name, T1.Video_Name, T1.Comment_Count FROM Video AS T1
                        INNER JOIN Playlist AS T2 ON T1.Playlist_Id = T2.Playlist_id
                        INNER JOIN Channel AS T3 ON T2.Channel_id = T3.Channel_id 
                        ORDER BY T3.Channel_name
                    """)
        result4 = cur.fetchall()
        df4 = pd.DataFrame(result4, columns=["Channel Name", "Video Name", "Comment Count"]).reset_index(drop=True)
        df4.index += 1
        st.dataframe(df4)

    elif selected_option == "5. Which videos have the highest number of likes, and what are their corresponding channel names?":
        col1, col2 = st.columns(2)
        with col1:
            cur.execute("""SELECT T3.Channel_name, T1.video_Name, T1.Like_Count FROM Video AS T1
                            INNER JOIN Playlist AS T2 ON T1.Playlist_Id = T2.Playlist_id
                            INNER JOIN Channel AS T3 ON T2.Channel_id = T3.Channel_id
                            WHERE T1.Like_Count = (SELECT MAX(Like_Count) FROM Video AS V2 
                                                    INNER JOIN Playlist AS T2 ON V2.Playlist_Id = T2.Playlist_id 
                                                    WHERE T2.Channel_id = T3.Channel_id)
                            ORDER BY T1.Like_Count DESC
                        """)
            result5 = cur.fetchall()
            df5 = pd.DataFrame(result5, columns=["Channel Name", "Video Name", "Like Count"]).reset_index(drop=True)
            df5.index += 1
            st.dataframe(df5)

        with col2:
            fig_vc = px.bar(df5, x= "Like Count", y= "Video Name", orientation= 'h', color= "Channel Name", text_auto='.2s', title="Videos with Most Likes")
            fig_vc.update_traces(textfont_size= 16)
            fig_vc.update_xaxes(title_font=dict(size= 20))
            fig_vc.update_yaxes(title_font=dict(size= 20))
            fig_vc.update_layout(title_font_color= '#1308C2 ', title_font=dict(size= 25))
            st.plotly_chart(fig_vc, use_container_width=True) 

    elif selected_option == "6. What is the total number of likes for each video, and what are their corresponding video names?":
        cur.execute("SELECT Video_Name, Like_Count FROM Video ORDER BY Video_Name")
        result6 = cur.fetchall()
        df6 = pd.DataFrame(result6, columns=["Video Name", "Like Count"]).reset_index(drop=True)
        df6.index += 1
        st.dataframe(df6)

    elif selected_option == "7. What is the total number of views for each channel, and what are their corresponding channel names?":
        col1, col2 = st.columns(2)
        with col1:
            cur.execute("SELECT Channel_name, View_count FROM Channel")
            result7 = cur.fetchall()
            df7 = pd.DataFrame(result7, columns=["Channel Name", "Total number of views"]).reset_index(drop=True)
            df7.index += 1
            st.dataframe(df7)

        with col2:
            fig_vc = px.bar(df7, x= "Channel Name", y= "Total number of views", orientation= 'v', color= "Channel Name", text_auto='.2s', title="Total Views of each Channel")
            fig_vc.update_traces(textfont_size= 16)
            fig_vc.update_xaxes(title_font=dict(size= 20))
            fig_vc.update_yaxes(title_font=dict(size= 20))
            fig_vc.update_layout(title_font_color= '#1308C2 ', title_font=dict(size= 25))
            st.plotly_chart(fig_vc, use_container_width=True) 

    elif selected_option == "8. What are the names of all the channels that have published videos in the year 2022?":
        cur.execute("""SELECT T3.Channel_name as Channel_names, T1.video_Name, T1.Published_date FROM Video AS T1
                        INNER JOIN Playlist AS T2 ON T1.Playlist_Id = T2.Playlist_id
                        INNER JOIN Channel AS T3 ON T2.Channel_id = T3.Channel_id
                        WHERE YEAR(T1.Published_date) = "2022"
                    """)
        result8 = cur.fetchall()
        df8 = pd.DataFrame(result8, columns=["Channel Name", "Video Name", "Published Date"]).reset_index(drop=True)
        df8.index += 1
        st.dataframe(df8)

    elif selected_option == "9. What is the average duration of all videos in each channel, and what are their corresponding channel names?":
        col1, col2 = st.columns(2)
        with col1:
            cur.execute("""SELECT T3.Channel_name, TIME_FORMAT(SEC_TO_TIME(AVG(T1.Duration)), "%T") AS Duration FROM Video AS T1
                            INNER JOIN Playlist AS T2 ON T1.Playlist_Id = T2.Playlist_id
                            INNER JOIN Channel AS T3 ON T2.Channel_id = T3.Channel_id
                            GROUP BY T3.Channel_id
                            ORDER BY Duration
                        """)
            result9 = cur.fetchall()
            df9 = pd.DataFrame(result9, columns=["Channel Name", "Average Duration of Videos"]).reset_index(drop=True)
            df9.index += 1
            st.dataframe(df9)

        with col2:
            fig_vc = px.bar(df9, x= "Channel Name", y= "Average Duration of Videos", orientation= 'v', color= "Channel Name", title="Average Duration of Videos in each Channel")
            fig_vc.update_traces(textfont_size= 16)
            fig_vc.update_xaxes(title_font=dict(size= 20))
            fig_vc.update_yaxes(title_font=dict(size= 20))
            fig_vc.update_layout(title_font_color= '#1308C2 ', title_font=dict(size= 25))
            st.plotly_chart(fig_vc, use_container_width=True) 

    elif selected_option == "10. Which videos have the highest number of comments, and what are their corresponding channel names?":
        col1, col2 = st.columns(2)
        with col1:
            cur.execute("""SELECT T3.Channel_name, T1.video_Name, T1.Comment_Count FROM Video AS T1
                            INNER JOIN Playlist AS T2 ON T1.Playlist_Id = T2.Playlist_id
                            INNER JOIN Channel AS T3 ON T2.Channel_id = T3.Channel_id
                            WHERE T1.Comment_Count = (SELECT MAX(Comment_Count) FROM Video AS V2 
                                                        INNER JOIN Playlist AS T2 ON V2.Playlist_Id = T2.Playlist_id 
                                                        WHERE T2.Channel_id = T3.Channel_id)
                            ORDER BY T1.Comment_Count DESC 
                        """)
            result10 = cur.fetchall()
            df10 = pd.DataFrame(result10, columns=["Channel Name", "Video Name", "Comment Count"]).reset_index(drop=True)
            df10.index += 1
            st.dataframe(df10)

        with col2:
            fig_vc = px.bar(df10, x= "Comment Count", y= "Video Name", orientation= 'h', color= "Channel Name", text_auto='.2s', title="Videos with Most Comments")
            fig_vc.update_traces(textfont_size= 16)
            fig_vc.update_xaxes(title_font=dict(size= 20))
            fig_vc.update_yaxes(title_font=dict(size= 20))
            fig_vc.update_layout(title_font_color= '#1308C2 ', title_font=dict(size= 25))
            st.plotly_chart(fig_vc, use_container_width=True) 

selected_option = st.selectbox(
    "Choose the question you want to answer using an SQL query",
    ["1. What are the names of all the videos and their corresponding channels?", 
    "2. Which channels have the most number of videos, and how many videos do they have?",
    "3. What are the top 10 most viewed videos and their respective channels?",
    "4. How many comments were made on each video, and what are their corresponding channel names?",
    "5. Which videos have the highest number of likes, and what are their corresponding channel names?",
    "6. What is the total number of likes for each video, and what are their corresponding video names?",
    "7. What is the total number of views for each channel, and what are their corresponding channel names?",
    "8. What are the names of all the channels that have published videos in the year 2022?",
    "9. What is the average duration of all videos in each channel, and what are their corresponding channel names?",
    "10. Which videos have the highest number of comments, and what are their corresponding channel names?"],
    index=None,
    placeholder="Select your Question...")

st.write("Question: ", selected_option)

if selected_option:
    st.session_state["selectbox_enabled"] = True
    execute_query(selected_option)

# Close MySQL connection
Query_connection.close()
