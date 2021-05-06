import SessionState

import time
import re

import requests
import json
import folium
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as componentsv1
from bs4 import BeautifulSoup
from st_aggrid import AgGrid

st.set_page_config(page_title="YAMATO TRACKER with Map", page_icon="🚚")

state = SessionState.get(count=0)

# Find the tracking number for Kuroneko Yamato.
# クロネコヤマトの追跡番号を検索
def get_kuroneko_tracking(tracking_number, view_track_code=False):
    try:
        tracking_data = []
        URL_JSON = f'http://nanoappli.com/tracking/api/{tracking_number}.json'
        res = requests.get(URL_JSON)
        json_contents = res.json()
        status = json_contents['status']
        itemType = json_contents['itemType']
        slipNo = json_contents['slipNo']
        trackingLists = json_contents['statusList']
        tracking_data = [[{'itemType': itemType, 'tracking_number': tracking_number}]]

        if not view_track_code:
            my_bar_len = len(trackingLists)
            if my_bar_len > 0:
                my_bar_add = int(100 / my_bar_len)
                my_bar_count = my_bar_add
                my_bar = st.progress(my_bar_add)
            else:
                my_bar_add = 0
                my_bar_count = 0
                my_bar = st.progress(0)

        for trackingList in trackingLists[1:]:
            status = trackingList['status']
            trackdate = trackingList['date']
            tracktime = trackingList['time']
            placeName = trackingList['placeName']
            placeCode = trackingList['placeCode']
            if placeCode == '':
                if placeName != '':
                    pass
                else:
                    placeName = ''
                placePostcode = ''
                placeAddress = ''
                placeLat = None
                placeLng = None
            else:
                center_data = get_center_status(placeCode)
                if center_data is None:
                    if placeName != '':
                        pass
                    else:
                        placeName = ''
                    placePostcode = ''
                    placeAddress = ''
                    placeLat = None
                    placeLng = None
                else:
                    if center_data['center_name'] == '':
                        pass
                    else:
                        placeName = center_data['center_name']
                    placePostcode = center_data['center_post_code']
                    placeAddress = center_data['center_address']
                    placeLat = center_data['center_lat']
                    placeLng = center_data['center_lng']

                    # get placePostcode to geo code
    #                 if placePostcode != '':
    #                     geo_data = get_geo_api(placePostcode)
    #                     placeLat = geo_data['lat']
    #                     placeLng = geo_data['lng']
                time.sleep(1)
            tracking_data.append([{'status': status,
                        'placeCode': placeCode,
                        'placeName': placeName,
                        'trackdate': trackdate,
                        'tracktime': tracktime,
                        'placePostcode': placePostcode,
                        'placeAddress': placeAddress,
                        'placeLat': placeLat,
                        'placeLng': placeLng,
                        }])

            if not view_track_code:
                my_bar_count += my_bar_add
                my_bar.progress(my_bar_count)
        if not view_track_code:
            my_bar.empty()
        return tracking_data
    except Exception as e:
        print('get_kuroneko_tracking error:', e)
        tracking_data = None
        return tracking_data

# Search for information on Kuroneko Yamato's relay bases.
# クロネコヤマトの中継拠点の情報を検索
def get_center_status(centercode):
    def get_latlng():
        select_contents = soup.select("div #kyotenHd a")
        mojiretu = select_contents[0].get('href')
        start = mojiretu.find('(')
        moji = mojiretu[start:]
        moji = moji.replace('(','')
        moji = moji.replace(")",'')
        moji = moji.replace("'",'')
        moji = moji.split(',')
        latlng = [float(s) for s in moji]
        return latlng

    center_data = []
    try:
        URL_CENTER = f'https://www.e-map.ne.jp/p/yamato01/dtl/{centercode}/'
        contents = requests.get(URL_CENTER)
        soup = BeautifulSoup(contents.content,'html.parser')
        status = contents.status_code
        center_name = ''
        center_post_code = ''
        center_address = ''
        center_lat = 0.0
        center_lng = 0.0
        if status == 200:
            # lat lng set
            fromlatlng = get_latlng()
            center_lat = fromlatlng[0]
            center_lng = fromlatlng[1]

            # page set
            select_contents = soup.select("div #kyotenHd a")
            center_name = select_contents[0].text.strip()
            center_name = center_name.replace('ヤマト運輸　','')

            select_contents = soup.select("div .kyotenDtlData")
            center_post_code = select_contents[6].text.split('\n')[1][-8:]
            center_address = select_contents[6].text.split('\n')[2].strip()
            center_data = {'center_name':center_name, 'center_post_code': center_post_code, 'center_address': center_address, 'center_lat': center_lat, 'center_lng': center_lng}
        else:
            center_data = None
        return center_data
    except Exception as e:
#         print('except error:', e)
        center_data = {'center_name':center_name, 'center_post_code': center_post_code, 'center_address': center_address, 'center_lat': center_lat, 'center_lng': center_lng}
        return center_data

# Search for geocodes by zip code (currently not used)
# 郵便番号からジオコードを検索する（現在不使用）
def get_geo_api(post_code):
    url = 'http://geoapi.heartrails.com/api/json?method=searchByPostal&postal='
    res_dict = requests.get(url+post_code).json()['response']['location'][0]

    #地理情報
    prefecture = res_dict['prefecture'] #東京都
    city = res_dict['city'] #千代田区
    town = res_dict['town'] #千代田
    lat = res_dict['y'] #軽度
    lng = res_dict['x'] # 緯度
    return {'prefecture': prefecture, 'city': city, 'town': town, 'lat': lat, 'lng': lng }

# Create Map
# マップの生成
def create_map(tolat, tolng, cities):
    lat = tolat
    lng = tolng
    name = "No name"

    map = folium.Map(location=[lat, lng], zoom_start=6)
#     folium.Marker(location=[lat, lng], popup=name).add_to(map)
    cities_count = len(cities)
    if cities_count > 0:
        cities_count -= 1
    for i, r in cities.iterrows():
        if i == cities_count:
            colorsign = 'red'
        else:
            colorsign = 'green'
        folium.Marker(
            location=[r['latitude'], r['longtude']],
            popup=r['train'],
            icon=folium.Icon(color=colorsign),
        ).add_to(map)

    return map

# Create Pandas dataframe
# パンダスのデータフレーム生成
def create_pandas_dataframe(d1):
    data_status = []
    data_placeName = []
    data_placeCode = []
    data_trackdate = []
    data_tracktime = []
    data_placePostcode = []
    data_placeAddress = []
    data_placeLat = []
    data_placeLng = []
    for track_data in d1[1:]:
        data_status.append(track_data[0]['status'])
        data_placeName.append(track_data[0]['placeName'])
        data_placeCode.append(track_data[0]['placeCode'])
        data_trackdate.append(track_data[0]['trackdate'])
        data_tracktime.append(track_data[0]['tracktime'])
        data_placePostcode.append(track_data[0]['placePostcode'])
        data_placeAddress.append(track_data[0]['placeAddress'])
        data_placeLat.append(track_data[0]['placeLat'])
        data_placeLng.append(track_data[0]['placeLng'])

    d1_dict = {'status': data_status,
               'placeName': data_placeName,
               'placeCode': data_placeCode,
               'trackdate': data_trackdate,
               'tracktime': data_tracktime,
               'placePostcode': data_placePostcode,
               'placeAddress': data_placeAddress,
               'placeLat': data_placeLat,
               'placeLng': data_placeLng,
              }
    
    if d1_dict['status'] != []:
        d1_change_dict = {}
        for k,v in d1_dict.items():
            d1_change_dict[k] = pd.Series(v)

        df = pd.DataFrame(d1_change_dict)
        return df
    else:
        return None

# Data generation for map markers
# 地図マーカーのデータ生成
def create_cities_dataframe(dataframe):
    train = []
    latitude = []
    longtude = []
    for index,item in dataframe[1:].iterrows():
        tempLat = item['placeLat']
        if tempLat != 0:
            train.append(item['placeName'])
            latitude.append(item['placeLat'])
            longtude.append(item['placeLng'])

    cities_dataframe = pd.DataFrame({
        'train': train,
        'latitude': latitude,
        'longtude': longtude,
    })

    cities_dataframe = cities_dataframe.dropna()
    return cities_dataframe


#==============================================================
# Main start
#==============================================================
def main():
    st.markdown(""" <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style> """, unsafe_allow_html=True)

    padding = 0
    st.markdown(f""" <style>
        .reportview-container .main .block-container{{
            padding-top: {padding}rem;
            padding-right: {padding}rem;
            padding-left: {padding}rem;
            padding-bottom: {padding}rem;
        }} </style> """, unsafe_allow_html=True)

    COLOR = "black"
    STCK_COLOR = 'black'
    BACKGROUND_COLOR = "#fff"
    STCK_BACKGROUND_COLOR = "rgb(240, 246, 246)"
    max_width = 1000
    padding_top = 5
    padding_right = 1
    padding_left = 1
    padding_bottom = 10
    
    hedder_text_jp = """少しだけ便利になるクロネコヤマト（ヤマト運輸）の荷物お問い合わせアプリです。
    
1. 追跡番号を複数コピペして一括調査できます
2. 最新の配送状況が経路毎に一覧表示できます
3. 経路情報を地図表示できます
4. ヤマトへの直リンクが追跡番号に含まれています

下記テキストエリアに追跡番号を入力してください。（入力完了はCtrl+Enter）"""

    hedder_text_en = """This is a package inquiry application for Kuroneko Yamato (Yamato Transport) that makes things a little more convenient.
    
1. multiple tracking numbers can be copied and pasted for batch investigation
2. latest delivery status can be listed by route.
3. route information can be displayed on a map
4. direct link to Yamato is included in the tracking number

Please enter the tracking number in the text area below. (To complete, press Ctrl+Enter)"""

    # dark_theme = st.sidebar.checkbox("Dark Theme", False)
    # if dark_theme:
    #     COLOR = "white"
    #     BACKGROUND_COLOR = "rgb(17,17,17)"
    #     STCK_COLOR = 'white'
    #     STCK_BACKGROUND_COLOR = "rgb(17,17,17)"
    # else:
    #     COLOR = "black"
    #     BACKGROUND_COLOR = "white"
    #     STCK_COLOR = 'black'
    #     STCK_BACKGROUND_COLOR = "rgb(240, 246, 246)"

    # st.markdown(
    # f"""
    # <style>
    #     .reportview-container .main .block-container{{
    #         max-width: {max_width}px;
    #         padding-top: {padding_top}rem;
    #         padding-right: {padding_right}rem;
    #         padding-left: {padding_left}rem;
    #         padding-bottom: {padding_bottom}rem;
    #     }}
    #     .reportview-container {{
    #         color: {COLOR};
    #         background-color: {BACKGROUND_COLOR};
    #     }}
    #     h1 {{
    #         color: {COLOR};
    #         background-color: {BACKGROUND_COLOR};
    #     }}
    #     h5 {{
    #         color: {COLOR};
    #         background-color: {BACKGROUND_COLOR};
    #     }}
    #     #MainMenu {{
    #         color: {STCK_COLOR};
    #         background-color: {STCK_BACKGROUND_COLOR};
    #     }}
    #     .st-cl {{
    #         color: {'gray'};
    #     }}
    #     .css-145kmo2 {{
    #         color: {STCK_COLOR};
    #     }}
    #     .css-xq1lnh-EmotionIconBase {{
    #         color: {STCK_COLOR};
    #         background-color: {STCK_BACKGROUND_COLOR};
    #     }}
    #     #bui-4__anchor {{
    #         color: {'black'};
    #         background-color: {STCK_BACKGROUND_COLOR};
    #     }}
    #     #bui-5__anchor {{
    #         color: {'black'};
    #         background-color: {STCK_BACKGROUND_COLOR};
    #     }}
    #     #bui-6__anchor {{
    #         color: {'black'};
    #         background-color: {STCK_BACKGROUND_COLOR};
    #     }}
    #     #bui-7__anchor {{
    #         color: {'black'};
    #         background-color: {STCK_BACKGROUND_COLOR};
    #     }}
    #     #bui-8__anchor {{
    #         color: {'black'};
    #         background-color: {STCK_BACKGROUND_COLOR};
    #     }}
    # </style>
    # """,
    #         unsafe_allow_html=True,
    #     )
    
    col1, col2 = st.beta_columns([3, 1])
    with col1:
        st.title("YAMATO TRACKER with Map")
    with col2:
        language = st.radio('言語選択(Select Language)',('Japanese', 'English'))
        
    if language == 'Japanese':
        st.text(hedder_text_jp)
    else:
        st.text(hedder_text_en)

    if language == 'Japanese':
        tnumber_text = st.text_area('数字以外の文字は自動削除',"",help='入力完了はCtrl+Enter')
    else:
        tnumber_text = st.text_area('Automatic deletion of non-numeric characters.',"",help='Ctrl+Enter for completion.')
    temp_tnumbers = tnumber_text.split("\n")

    # Non-numbers will be automatically deleted
    # 数字以外は削除する
    tnumbers = []
    for row in temp_tnumbers:
        if row != '':
            temp_text = re.sub('[^0-9]','', row)
            tnumbers.append(temp_text)

    tnumber_dict = {}
    tnumber_dict = {'number': tnumbers}

    tnumber_df = pd.DataFrame(tnumber_dict)
    tnumber_df = tnumber_df.dropna()

    # st.dataframe(tnumber_df)
    tnumber_count = len(tnumber_df)
    if tnumber_count >= 2:
        slider_min = 1
        slider_max = tnumber_count
        slider_value = 1

    if language == 'Japanese':
        select_radio = st.radio('表示したい件数を選択してください。',('１件表示・地図付き','全件表示'))
    else:
        select_radio = st.radio('Select the number of items you wish to display.',('Show 1 item with Map','Show all item'))
        
    if select_radio == 'Show 1 item with Map' or select_radio == '１件表示・地図付き':
        if tnumber_count == 0:
            if language == 'Japanese':
                st.info('*** データがありません ***')
            else:
                st.info('*** No data ***')
        elif tnumber_count == 1:
            pass
        elif tnumber_count >=2:
            placeholder = st.empty()
            col1, col2, col3, col4, col5, col6, col7 = st.beta_columns(7)
            with col1:
                prev_button = st.button('Prev',help='Preview Tracking-code')
            with col2:
                next_button = st.button('Next',help='Next Tracking-code')
            with col3:
                update_button = st.button('Update',help='Update Tracking...')
            if prev_button:
                state.count -= 1
                if state.count < 1:
                    state.count = tnumber_count
                slider_value = state.count
                select_slider = placeholder.slider('', min_value=slider_min, max_value=slider_max, step=1, value=slider_value, help='Change Tracking-code')
            elif next_button:
                state.count += 1
                if state.count > tnumber_count:
                    state.count = 1
                slider_value = state.count
                select_slider = placeholder.slider('', min_value=slider_min, max_value=slider_max, step=1, value=slider_value, help='Change Tracking-code')
            elif update_button:
                slider_value = state.count
                select_slider = placeholder.slider('', min_value=slider_min, max_value=slider_max, step=1, value=slider_value, help='Change Tracking-code')
            else:
                select_slider = placeholder.slider('', min_value=slider_min, max_value=slider_max, step=1, value=slider_value, help='Change Tracking-code')
                state.count = select_slider

        if tnumber_count >= 1:
            if tnumber_count == 1:
                select = tnumbers[0]
                update_button = st.button('Update',help='Update Tracking...')
                st.markdown(f'##### [1/{tnumber_count}] Tracking-code 追跡番号: [{select}](http://jizen.kuronekoyamato.co.jp/jizen/servlet/crjz.b.NQ0010?id={select})')
            else:
                select = tnumbers[select_slider-1]
                st.markdown(f'##### [{select_slider}/{tnumber_count}] Tracking-code 追跡番号: [{select}](http://jizen.kuronekoyamato.co.jp/jizen/servlet/crjz.b.NQ0010?id={select})')
            if select == '':
                if language == 'Japanese':
                    st.info('*** データがありません ***')
                else:
                    st.info('*** No data ***')
            else:
                d1 = get_kuroneko_tracking(select,view_track_code=False)
                if d1 is None:
                    if language == 'Japanese':
                        st.error('*** 一致するデータがありません ***')
                    else:
                        st.error('*** No matching data ***')
                else:
                    df = create_pandas_dataframe(d1)
                    if df is None:
                        if language == 'Japanese':
                            st.error('*** 表示可能な記録はありません ***')
                        else:
                            st.error('*** No records available for display ***')
                    else:
                        # df.index = np.arange(1, len(df)+1)
                        df = df.sort_index(ascending=False)
                        AgGrid(df,height=140,autosize=True, )
                        if language == 'Japanese':
                            hideMapSW = st.checkbox('マップ非表示')
                        else:
                            hideMapSW = st.checkbox('Hide Map')
                        if hideMapSW:
                            pass
                        else:
                            cities = create_cities_dataframe(df)
                            lat = df[-1:]['placeLat']
                            lng = df[-1:]['placeLng']
                            mapdata = create_map(lat, lng, cities)
                            if language == 'Japanese':
                                st.markdown('###### 中継地:GREEN / 現在地:RED')
                            else:
                                st.markdown('###### Relay point:GREEN / Current point:RED')
                            st.components.v1.html(folium.Figure().add_child(mapdata).render(), height=500)
                            st.write('done')
    else:
        if tnumber_count == 0:
            if language == 'Japanese':
                st.info('*** データがありません ***')
            else:
                st.info('*** No data ***')
        elif tnumber_count >= 1:
            update_button = st.button('Update',help='Update Tracking...')

            for i,select in enumerate(tnumbers):
                st.markdown(f'##### [{i+1}/{tnumber_count}] Tracking-code 追跡番号: [{select}](http://jizen.kuronekoyamato.co.jp/jizen/servlet/crjz.b.NQ0010?id={select})')
                if select == '':
                    if language == 'Japanese':
                        st.info('*** データがありません ***')
                    else:
                        st.info('*** No data ***')
                else:
                    d1 = get_kuroneko_tracking(select,view_track_code=False)
                    if d1 is None:
                        if language == 'Japanese':
                            st.error('*** 一致するデータがありません ***')
                        else:
                            st.error('*** No matching data ***')
                    else:
                        df = create_pandas_dataframe(d1)
                        if df is None:
                            if language == 'Japanese':
                                st.error('*** 表示可能な記録はありません ***')
                            else:
                                st.error('*** No records available for display ***')
                        else:
                            # df.index = np.arange(1, len(df)+1)
                            df = df.sort_index(ascending=False)
                            AgGrid(df,height=140,autosize=True, )
            st.write('done')

if __name__ == "__main__":
    main()