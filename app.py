import streamlit as st
import template as t
import pandas as pd
import numpy as np
from random import random


st.set_page_config(layout="wide")

# probably obselete because it's in the get_mal_account function
if 'communities' not in st.session_state:
    st.session_state['communities'] = dict()

# probably obselete because it's in the get_mal_account function
if 'user' not in st.session_state:
    st.session_state['user'] = dict()

with st.form(key='username_form'):
    mal_username = st.text_input(label='MAL username', max_chars=150,
                                 type="default", help='Please enter your MyAnimeList username', key='username_field')
    submit_button = st.form_submit_button(
        label='Submit', on_click=t.get_mal_account2, args=(mal_username, ))

# it does not run the rest of the script if no username has been entered
if 'mal_username' in st.session_state['user']:

    # create an avatar and groups column

    n_clubs = len(st.session_state['user']['club_df'])

    profile, info = st.columns([2, 4])

    with profile:
        st.image(st.session_state['user']
                 ['image_url'], use_column_width='always')
        # st.header(st.session_state['user']['mal_username'])

    if n_clubs <= 6:

        st.subheader('My communities')

        with info:
            st.subheader('How to use the app')
            st.markdown(r""" This app serves community-centered anime recommendations based on your MyAnimeList friends and clubs.           

Below this text you can find the communities you are a part of on MyAnimeList and generate recommendations based on a specific community.

Each club you are a member of is regarded as a seperate "community". Your group of friends on MyAnimeList are also regarded as a distinct community. The first community is always your friends group, followed by any clubs you are a member of.

You can select a community by clicking on the "Generate Recommendations" button (above said community) and the app will generate the following recommendations:
- Most popular among X community members
- Highest rated among X community members
- Personalized recommendations based on similar users in X community

Note that the recommendations that appear in each category are only anime that are unseen to you 
(i.e., they do not appear in your anime list on MAL)
            """)

        community_tiles = st.columns(7)

        with community_tiles[0]:
            # add path to local image
            st.button('Get Recommendations', key=random(),
                      on_click=t.select_community, args=('friend_list', ))
            st.image(r'images/friends_black400.png',
                     use_column_width='always', caption='Friend List')

        for x in zip(community_tiles[1: n_clubs + 1], st.session_state['user']['club_df'].iloc):
            t.club_tile(x[0], x[1])

    if n_clubs > 6:

        with info:
            st.subheader('How to use the app')
            st.markdown(""" This app serves community-centered anime recommendations based on your MyAnimeList friends and clubs.

Below this text you can find a dropdown menu of the communities you are a part of on MyAnimeList and generate recommendations by selecting a specific community.

Each club you are a member of is regarded as a seperate "community". Your group of friends on MyAnimeList are also regarded as a distinct community. The first community is always your friends group, followed by any clubs you are a member of.

Selecting a community will generate the following recommendations:
- Most popular among members in X community
- Highest rated among members in X community
- Personalized recommendations based on similar users in X community

Note that the recommendations that appear in each category are only anime that are unseen to you (i.e., they do not appear in your anime list on MAL)
            """)

            communities_list = list(
                st.session_state['user']['club_df']['name'].values)
            communities_list.insert(0, 'Friends')

            communities_dropdown = st.selectbox(
                'Select community', options=communities_list, index=0)

            # setting the target community to the id of the community selected in communities_dropdown
            t.dropdown_select_community(communities_dropdown)

            # communities_dropdown = st.selectbox('Select community', options=(list(st.session_state['user']['club_df']['name'].values).insert(0, 'Friends')), index=0,
            #                                     on_change=t.dropdown_select_community,
            #                                     args=(communities_dropdown, ))

    # select a target community to kickstart the interface - I CAN REMOVE THIS ACTUALLY AND JUST LOAD RECS IF THE USER SELECTS A COMMUNITY
    if 'target_community' not in st.session_state['communities']:
        st.session_state['communities']['target_community'] = 'friend_list'

    # Get recommendations
    t.get_recs(st.session_state['communities']['target_community'])

    # target group is the currently selected club or friend list
    st.subheader(
        f"Most popular among {st.session_state['communities']['target_community_name']}")
    t.display_recommendations(
        st.session_state['communities'][st.session_state['communities']['target_community']]['df_mostpopular'])

    # Highest rated
    st.subheader('Highest rated among ' +
                 st.session_state['communities']['target_community_name'])
    t.display_recommendations(
        st.session_state['communities'][st.session_state['communities']['target_community']]['df_highestrated'])

    # Personalized recommendations
    st.markdown(
        f"""### Personalized recommendations based on similar users in {st.session_state['communities']['target_community_name']}""")
    t.display_recommendations(
        st.session_state['communities'][st.session_state['communities']['target_community']]['df_personalized'])
