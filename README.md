# Community-Centered Recommendation System for Anime Fans

Note: Please note that I have removed my private API key from line 11 of the template.py file. To use this application you would have to set the value of the 'X-MAL-CLIENT-ID' key of the headers dictionary to a MyAnimeList API key which can be generated at myanimelist.net/apiconfig.

This is an application that generates community-based anime recommendations based on a user's friend list or club membership on MyAnimeList. A MyAnimeList account is required to use the application.

The application generates three types of recommendations based on a selected target community (i.e., a user's friend list or a particular club):
- Most popular in X community
- Highest rated in X community
- Personalized recommendations based on similar users in X community

The application is fully written in Python and Streamlit. Real-time data (user ratings, clubs, friend list, etc.) is fetched from MyAnimeList using both the official MyAnimeList API as well as the Jikan unnoficial MAL API. As all data is collected in real-time, nothing is pre-trained and all recommendations 
are calculated in real time as well. 

The fetched data is stored as variables in streamlit's session state. The structure of the session state is as follows:

![session_state diagram](https://user-images.githubusercontent.com/78442887/183166979-e4aabc16-17c4-4f81-81ea-44fb36e42d98.jpg)

User-based collaborative filtering is used for the third type of recommendations where recommendations are made based on the ratings of a neighbourhood of similar users in the target community.

A report elaborating on the context, data, methods and user interface of the application is included in this repo. The report along with the streamlit app were initially submitted as an assignment for the "Personalization for (Public) Media" course of the Applied Data Science program.

Credits:

- MyAnimeList API: https://myanimelist.net/apiconfig/references/api/v2
- Jikan API: https://jikan.moe/
