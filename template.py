import streamlit as st
from random import random
import webbrowser
import requests
import json
import pandas as pd
import numpy as np
from time import sleep

# You would have to set the value of 'X-MAL-CLIENT-ID' to a MyAnimeList API client ID for the script to work
headers = {'X-MAL-CLIENT-ID': ''}


def get_clubs(mal_username):

    user_clubs = requests.get(
        f'https://api.jikan.moe/v4/users/{mal_username}/clubs')
    if user_clubs.status_code != 200:
        sleep(0.5)
        user_clubs = requests.get(
            f'https://api.jikan.moe/v4/users/{mal_username}/clubs')
        if user_clubs.status_code != 200:
            return None
    sleep(0.5)

# test

    club_df = pd.DataFrame([(club['mal_id'], club['name'])
                            for club in user_clubs.json()['data']], columns=['id', 'name'])

    club_images = []
    club_nmembers = []
    for club_id in club_df['id']:
        response = requests.get(f'https://api.jikan.moe/v4/clubs/{club_id}')
        if response.status_code != 200:
            sleep(0.5)
            response = requests.get(
                f'https://api.jikan.moe/v4/clubs/{club_id}')
            if response.status_code != 200:
                club_images.append(None)
                club_nmembers.append(None)
                continue
        try:
            club = response.json()['data']
            club_images.append(club['images']['jpg']['image_url'])
            club_nmembers.append(club['members'])
        except:
            club_images.append(None)
            club_nmembers.append(None)
        sleep(0.34)
    club_df['image_url'] = club_images
    club_df['members'] = club_nmembers
    return club_df


def get_community_lists(target_community, mal_username):

    if target_community in st.session_state['communities']:
        return None

    st.session_state['communities'][target_community] = dict()

    master_df = pd.DataFrame(
        columns=['title', 'image_url']).set_index(['title'])

    # get friend list
    if target_community == 'friend_list':
        jikan_response = requests.get(
            f'https://api.jikan.moe/v4/users/{mal_username}/friends')
        if jikan_response.status_code != 200:
            # for some reason the initial request returns a 500 response code when trying a new username. This is why I try to rerun the request before returning an error
            sleep(0.34)
            jikan_response = requests.get(
                f'https://api.jikan.moe/v4/users/{mal_username}/friends')
            if jikan_response.status_code != 200:
                st.write(
                    'An error has occured: the API has returned a bad response')
                return st.write('An error has occured')

        # get friend list with all metadata; this also contains the friend's avatars in case I need them.

        st.session_state['communities'][target_community]['members_list_raw'] = jikan_response.json()[
            'data']
        members_usernames = [member['user']['username']
                             for member in st.session_state['communities'][target_community]['members_list_raw']]

    else:
        # fetch (sample) club members and add to variable
        club = st.session_state['user']['club_df'][st.session_state['user']
                                                   ['club_df']['id'] == target_community]  # CORRECT

        if type(club['members'][0]) == np.int64:
            # the API endpoint for getting club members returns only 36 members per call/page, which is why I am taking the club members from a random page
            n_pages = np.ceil(club['members']/36)
            page = np.random.randint(1, n_pages, 1)[0]
        else:
            page = 1

        members_response = requests.get(
            f'https://api.jikan.moe/v4/clubs/{target_community}/members/?q=&page={page}')
        if members_response.status_code != 200:
            sleep(0.34)
            members_response = requests.get(
                f'https://api.jikan.moe/v4/clubs/{target_community}/members/?q=&page={page}')
            if members_response.status_code != 200:
                return st.write('An error has occured')

        members_usernames = [user['username']
                             for user in members_response.json()['data']]
        members_usernames

        # for each member get their anime list and append to st.session_state['communities'][target_community]['master_df']
    if len(members_usernames) > 50:
        members_usernames = np.random.choice(
            np.array(members_usernames), 50)  # make it a list if I have issues
    st.session_state['communities'][target_community]['members_usernames'] = members_usernames

    for user in members_usernames:

        # getting user animelist as a dataframe
        try:
            user_animelist = requests.get(
                f'https://api.myanimelist.net/v2/users/{user}/animelist?fields=list_status&limit=1000', headers=headers)
            clean_animelist = pd.DataFrame([(anime['node']['title'], anime['node']['main_picture']['medium'], anime['list_status']['score'])
                                            for anime in user_animelist.json()['data']], columns=['title', 'image_url', user])
            clean_animelist = clean_animelist[clean_animelist[user] != 0]
            clean_animelist = clean_animelist.set_index('title')

            # appending to master_df
            master_df = master_df.merge(
                clean_animelist, how='outer', on=['title', 'image_url'])
            sleep(0.25)
        except:
            sleep(0.25)
            continue

    st.session_state['communities'][target_community]['master_df'] = master_df

    # creating unseen df
    st.session_state['communities'][target_community]['unseen_df'] = master_df[~master_df.index.isin(
        st.session_state['user']['target_list'].index)]
    st.session_state['communities'][target_community]['unseen_df'].drop(
        'image_url', axis=1, inplace=True)


def select_community(target_community):
    st.session_state['communities']['target_community'] = target_community


def dropdown_select_community(community_name):
    if community_name == 'Friends':
        st.session_state['communities']['target_community'] = 'friend_list'
    else:
        st.session_state['communities']['target_community'] = st.session_state['user'][
            'club_df'][st.session_state['user']['club_df']['name'] == community_name]['id'].values[0]


def club_tile(column, club):
    with column:
        st.button('Get Recommendations', key=random(),
                  on_click=select_community, args=(club['id'], ))
        try:
            st.image(club['image_url'], use_column_width='auto',
                     caption=club['name'])
        except:
            pass

        # st.caption(club['name'])


def get_most_popular(unseen_df, master_df):
    recs = unseen_df.transpose().count().sort_values(ascending=False).head(10)
    recs.name = 'members'
    recs = master_df[['image_url']].merge(recs, how='right', on='title')
    return recs


def get_highest_rated(unseen_df, master_df, n_members):
    # the anime that appear in more than n_members**0.5 number of user anime lists
    unseen_min_n = unseen_df[unseen_df.transpose().count() >= n_members**0.5]
    recs = unseen_min_n.transpose().mean().sort_values(ascending=False).head(10)
    recs = recs.round(2)  # rounding the average rating
    recs.name = 'rating'
    recs = master_df[['image_url']].merge(recs, how='right', on='title')
    return recs


def get_personalized_recs(target_list, master_df, mal_username, n_members):

    # removing the image_url column from master_df
    master_clean = master_df.iloc[:, 1:]

    # Calculating similarity between friends/club members and target user
    user_similarities = master_clean.apply(
        target_list[mal_username].corr, axis=0)
    neighbourhood_similarities = user_similarities[user_similarities > 0.10]

    # Filtering master_clean for similar users only
    similar_users = master_clean.loc[:, user_similarities > 0.10]

    # Creating neighbourhood_unseen df
    # the anime unseen by the target user that appear in the neightbourhood of similar users
    neighbourhood_unseen = similar_users[~similar_users.index.isin(
        target_list.index)]

    # Applying weights (based on similarity) to ratings
    def apply_weights(x): return x * neighbourhood_similarities[x.name]
    weighted_scores = neighbourhood_unseen.apply(apply_weights)

    # Filtering out anime that appear in less than n_friends**0.5 number of user lists
    unseen_min_neighbourhood = weighted_scores[weighted_scores.transpose(
    ).count() >= n_members**0.5]

    # Calculating similarity-weighted recommendations
    def weighted_rating(anime): return anime.sum() / \
        neighbourhood_similarities[anime.notna()].sum()
    personalized_recommendations = unseen_min_neighbourhood.apply(
        weighted_rating, axis=1).sort_values(ascending=False).head(10)

    personalized_recommendations = personalized_recommendations.round(
        2)  # rounding the predicted rating
    personalized_recommendations.name = 'predicted_rating'
    personalized_recommendations = master_df[['image_url']].merge(
        personalized_recommendations, how='right', on='title')
    return personalized_recommendations


def get_mal_account2(mal_username):
    if mal_username == '':
        return None
    elif 'mal_username' in st.session_state['user']:
        if mal_username == st.session_state['user']['mal_username']:
            return None

    # reset the user data if new user is entered
    st.session_state['user'] = dict()
    st.session_state['user']['mal_username'] = mal_username

    # reset the communities data if new user is entered
    st.session_state['communities'] = dict()

    # get the user's animelist
    mal_response = requests.get(
        f'https://api.myanimelist.net/v2/users/{mal_username}/animelist?fields=list_status&limit=1000', headers=headers)
    if mal_response.status_code == 404:
        return st.write('Please enter a valid username')
    else:
        user_animelist_raw = mal_response.json()['data']
        target_list = pd.DataFrame([(anime['node']['title'], anime['list_status']['score'])
                                    for anime in user_animelist_raw], columns=['title', mal_username])
        target_list.set_index('title', inplace=True)
        target_list[mal_username].replace(0, np.nan, inplace=True)

        st.session_state['user']['target_list'] = target_list

        # aslo have to get the user's profile image
        try:
            user_request = requests.get(
                f'https://api.jikan.moe/v4/users/{mal_username}')
            if user_request.status_code != 200:
                sleep(0.34)
                user_request = requests.get(
                    f'https://api.jikan.moe/v4/users/{mal_username}')
            user_info = user_request.json()
            st.session_state['user']['image_url'] = user_info['data']['images']['jpg']['image_url']
        except:
            st.session_state['user']['image_url'] = 'images/n_profile_picture.jpg'

        # get the user's club list
        st.session_state['user']['club_df'] = get_clubs(mal_username)


def get_recs(target_community):

    if target_community not in st.session_state['communities']:
        get_community_lists(
            target_community, st.session_state['user']['mal_username'])
        # fetch (sample) club members and add to variable

        # for each member get their anime list and append to master_df

    # continue code
    mal_username = st.session_state['user']['mal_username']
    target_list = st.session_state['user']['target_list']
    master_df = st.session_state['communities'][target_community]['master_df']
    unseen_df = st.session_state['communities'][target_community]['unseen_df']
    n_members = len(unseen_df.transpose())

    st.session_state['communities'][target_community]['df_mostpopular'] = get_most_popular(
        unseen_df=unseen_df, master_df=master_df)
    st.session_state['communities'][target_community]['df_highestrated'] = get_highest_rated(
        unseen_df=unseen_df, master_df=master_df, n_members=n_members)
    st.session_state['communities'][target_community]['df_personalized'] = get_personalized_recs(
        target_list, master_df, mal_username, n_members)

    # maybe move this
    st.session_state['communities']['target_community_name'] = 'friends' if target_community == 'friend_list' else st.session_state[
        'user']['club_df'][st.session_state['user']['club_df']['id'] == st.session_state['communities']['target_community']]['name'].values[0] + ' members'


def go_to_anime_page(mal_url):
    webbrowser.open_new_tab(mal_url)


def tile_item2(column, anime):
    with column:
        # st.button('MAL link', key=random(), on_click=go_to_anime_page(anime['mal_url']))

        if 'members' in anime:
            st.caption(f"Watched by {anime['members']} members")
        elif 'rating' in anime:
            st.caption(f"Average score: {anime['rating']}")
        elif 'predicted_rating' in anime:
            st.caption(f"Predicted score: {anime['predicted_rating']}")
        st.image(anime['image_url'], use_column_width='always')
        st.caption(anime.name)


def display_recommendations(df_recommendations):

    # check the number of items
    nbr_items = df_recommendations.shape[0]

    if nbr_items != 0:

        # create columns with the corresponding number of items
        columns = st.columns(nbr_items)

        # apply tile_item to each column-item tuple (created with python 'zip')
        for x in zip(columns, df_recommendations.iloc):
            tile_item2(x[0], x[1])
