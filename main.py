import os
import SessionState
import time
import re
import requests
import json
import folium
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from bs4 import BeautifulSoup
from st_aggrid import AgGrid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="YAMATO TRACKER with Map", page_icon="🚚")

state = SessionState.get(count=0)

# Email configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = os.getenv('GMAIL_USER')
EMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')
NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL')

def send_email(subject, body, to_email=None):
    if to_email is None:
        if NOTIFICATION_EMAIL is None:
            raise ValueError("通知先メールアドレスが設定されていません。.envファイルにNOTIFICATION_EMAILを設定してください")
        to_email = NOTIFICATION_EMAIL
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, to_email, text)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")

# Find the tracking number for Kuroneko Yamato.
@st.cache_data(ttl=300, show_spinner=False)
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
def get_center_status(centercode):
    def get_latlng():
        try:
            select_contents = soup.select("div #kyotenHd a")
            if not select_contents:
                return [0.0, 0.0]

            mojiretu = select_contents[0].get('href')
            if not mojiretu:
                return [0.0, 0.0]

            start = mojiretu.find('(')
            if start == -1:
                return [0.0, 0.0]

            moji = mojiretu[start:]
            moji = moji.replace('(','')
            moji = moji.replace(")",'')
            moji = moji.replace("'",'')
            moji = moji.split(',')

            if len(moji) < 2:
                return [0.0, 0.0]

            latlng = [float(s) for s in moji]
            return latlng
        except Exception:
            return [0.0, 0.0]

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
            if len(select_contents) > 6:
                kyoten_data = select_contents[6].text.split('\n')
                if len(kyoten_data) > 2:
                    center_post_code = kyoten_data[1][-8:]
                    center_address = kyoten_data[2].strip()
                    center_data = {'center_name':center_name, 'center_post_code': center_post_code, 'center_address': center_address, 'center_lat': center_lat, 'center_lng': center_lng}
                else:
                    center_data = {'center_name':center_name, 'center_post_code': '', 'center_address': '', 'center_lat': center_lat, 'center_lng': center_lng}
            else:
                center_data = {'center_name':center_name, 'center_post_code': '', 'center_address': '', 'center_lat': center_lat, 'center_lng': center_lng}
        else:
            center_data = None
        return center_data
    except Exception as e:
        st.error(f"中心基地情報の取得中にエラーが発生しました: {str(e)}")
        center_data = None
        return center_data
        return center_data

# Search for geocodes by zip code (currently not used)
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
def create_map(tolat, tolng, cities):
    lat = tolat
    lng = tolng
    name = "No name"

    red_lat = 0.0
    red_lng = 0.0
    map = folium.Map(location=[lat, lng], zoom_start=6)
    for i, r in cities.iterrows():
        if i == 0:  # 降順ソートされたデータなので先頭が最終のカレントデータとなる
            colorsign = 'red'
            #  赤色のマークを付けた緯度経度を記録する
            red_lat = r['latitude']
            red_lng = r['longtude']

        else:
            #  赤色のマークを付けた緯度経度と同じデータの場合はグリーンとせずに赤のままにしておく
            if red_lat == r['latitude'] and red_lng == r['longtude']:
                pass
            else:
                colorsign = 'green'
        folium.Marker(
            location=[r['latitude'], r['longtude']],
            popup=r['train'],
            icon=folium.Icon(color=colorsign),
        ).add_to(map)

    return map

# Create Pandas dataframe
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
        # Convert to datetime and sort by trackdate and tracktime in descending order
        current_year = pd.Timestamp.now().year
        df['datetime'] = pd.to_datetime(f'{current_year}/' + df['trackdate'] + ' ' + df['tracktime'], format='%Y/%m/%d %H:%M')
        df = df.sort_values('datetime', ascending=False)
        df = df.drop('datetime', axis=1)
        df = df.reset_index(drop=True)
        return df
    else:
        return None

# Data generation for map markers
def create_cities_dataframe(dataframe):
    train = []
    latitude = []
    longtude = []
    for index,item in dataframe[0:].iterrows():
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
    cities_dataframe = cities_dataframe.sort_index(ascending=True)
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

    # Default light theme colors
    LIGHT_COLOR = "black"
    LIGHT_BACKGROUND_COLOR = "#fff"
    LIGHT_STCK_COLOR = 'black'
    LIGHT_STCK_BACKGROUND_COLOR = "rgb(240, 246, 246)"

    # Dark theme colors
    DARK_COLOR = "white"
    DARK_BACKGROUND_COLOR = "rgb(17,17,17)"
    DARK_STCK_COLOR = 'white'
    DARK_STCK_BACKGROUND_COLOR = "rgb(17,17,17)"

    # Set initial values
    COLOR = LIGHT_COLOR
    BACKGROUND_COLOR = LIGHT_BACKGROUND_COLOR
    STCK_COLOR = LIGHT_STCK_COLOR
    STCK_BACKGROUND_COLOR = LIGHT_STCK_BACKGROUND_COLOR
    max_width = 1000
    padding_top = 5
    padding_right = 1
    padding_left = 1
    padding_bottom = 10

    # Get current date in Japanese and English formats
    from datetime import datetime
    current_date_jp = datetime.now().strftime('%Y/%m/%d')
    current_date_en = datetime.now().strftime('%m/%d/%Y')

    hedder_text_jp = f"""クロネコヤマト（ヤマト運輸）の荷物お問い合わせが少しだけ便利になるアプリです。[update:{current_date_jp}]<br><br>
・追跡番号を複数コピペして一括調査できます<br>
・最新の配送状況が経路毎に一覧表示できます<br>
・経路情報を地図表示できます<br>
・ヤマトへの直リンクが追跡番号に含まれています<br><br>
下記テキストエリアに追跡番号を入力してください。（★入力完了はCtrl+Enter★）"""

    hedder_text_en = f"""This is an application that makes Kuroneko Yamato (Yamato Transport) package inquiries a little more convenient.<br>
[update:{current_date_en}]<br><br>
- multiple tracking numbers can be copied and pasted for batch investigation<br>
- latest delivery status can be listed by route.<br>
- route information can be displayed on a map<br>
- direct link to Yamato is included in the tracking number<br><br>
Please enter the tracking number in the text area below. (★To complete, press Ctrl+Enter★)"""

    # Theme settings
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True

    # Add dark mode toggle
    dark_mode = st.checkbox('ダークモード', value=True, key='dark_mode_toggle')

    if dark_mode:
        COLOR = "white"
        BACKGROUND_COLOR = "rgb(17,17,17)"
        STCK_COLOR = 'white'
        STCK_BACKGROUND_COLOR = "rgb(17,17,17)"
    else:
        COLOR = "black"
        BACKGROUND_COLOR = "white"
        STCK_COLOR = 'black'
        STCK_BACKGROUND_COLOR = "rgb(240, 246, 246)"

    # Force mobile responsive design
    st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """, unsafe_allow_html=True)

    st.markdown(
    f"""
    <style>
        .reportview-container .main .block-container{{
            max-width: {max_width}px;
            padding-top: {padding_top}rem;
            padding-right: {padding_right}rem;
            padding-left: {padding_left}rem;
            padding-bottom: {padding_bottom}rem;
        }}
        .reportview-container {{
            color: {COLOR} !important;
            background-color: {BACKGROUND_COLOR} !important;
        }}
        body {{
            color: {COLOR} !important;
            background-color: {BACKGROUND_COLOR} !important;
        }}
        h1 {{
            color: {COLOR} !important;
            background-color: {BACKGROUND_COLOR} !important;
        }}
        h5 {{
            color: {COLOR} !important;
            background-color: {BACKGROUND_COLOR} !important;
        }}
        #MainMenu {{
            color: {STCK_COLOR} !important;
            background-color: {STCK_BACKGROUND_COLOR} !important;
        }}
        .st-cl {{
            color: {COLOR} !important;
        }}
        .css-145kmo2 {{
            color: {COLOR} !important;
        }}
        .css-xq1lnh-EmotionIconBase {{
            color: {COLOR} !important;
            background-color: {BACKGROUND_COLOR} !important;
        }}
        .stTextInput > div > div > input {{
            color: {COLOR} !important;
            background-color: {BACKGROUND_COLOR} !important;
        }}
        .stTextArea > div > div > textarea {{
            color: {COLOR} !important;
            background-color: {BACKGROUND_COLOR} !important;
        }}
        .stRadio > div {{
            color: {COLOR} !important;
            background-color: {BACKGROUND_COLOR} !important;
        }}
        .stCheckbox > div {{
            color: {COLOR} !important;
            background-color: {BACKGROUND_COLOR} !important;
        }}
        .stButton > button {{
            color: {COLOR} !important;
            background-color: {BACKGROUND_COLOR} !important;
        }}
        .ag-theme-streamlit {{
            --ag-background-color: {BACKGROUND_COLOR} !important;
            --ag-foreground-color: {COLOR} !important;
            --ag-border-color: {COLOR} !important;
        }}
        .stProgress > div > div > div > div {{
            background-color: {COLOR} !important;
        }}
        .folium-map {{
            background-color: {BACKGROUND_COLOR} !important;
        }}
        .stApp {{
            background-color: {BACKGROUND_COLOR} !important;
        }}
        .stSidebar {{
            background-color: {BACKGROUND_COLOR} !important;
        }}
        .stTextArea > div > div > textarea {{
            background-color: {BACKGROUND_COLOR} !important;
        }}
        .stText {{
            color: {COLOR} !important;
        }}
        .stTextArea > div > div > textarea {{
            color: {COLOR} !important;
        }}
        .stTextArea > div > div > label {{
            color: {COLOR} !important;
        }}
    </style>
    """,
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("YAMATO TRACKER with Map")
    with col2:
        language = st.radio('言語(Language)',('Japanese', 'English'))

    # Header text with proper styling
    header_style = f"""
    <style>
        .custom-header {{
            color: {COLOR} !important;
            background-color: {BACKGROUND_COLOR} !important;
            padding: 1rem;
            font-size: 16px;
        }}
    </style>
    """
    st.markdown(header_style, unsafe_allow_html=True)

    if language == 'Japanese':
        st.markdown(f'<div class="custom-header">{hedder_text_jp}</div>', unsafe_allow_html=True)
        tnumber_text = st.text_area(
            '数字以外の文字は自動削除',
            "",
            help='★入力完了はCtrl+Enter★',
            key='text_area_jp'
        )
    else:
        st.markdown(f'<div class="custom-header">{hedder_text_en}</div>', unsafe_allow_html=True)
        tnumber_text = st.text_area(
            'Automatic deletion of non-numeric characters.',
            "",
            help='★Ctrl+Enter for completion★',
            key='text_area_en'
        )
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
        select_radio = st.radio(
            '表示したい件数を選択してください。',
            ('１件表示・地図付き', '全件表示'),
            key='display_option_radio',
            help='表示する追跡情報の件数を選択'
        )
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
            col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
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
                    st.info('*** データがありません! ***')
                else:
                    st.info('*** No data! ***')
            else:
                d1 = get_kuroneko_tracking(select,view_track_code=False)
                if d1 is None:
                    if language == 'Japanese':
                        st.error('*** 一致するデータがありません! ***')
                    else:
                        st.error('*** No matching data! ***')
                else:
                    df = create_pandas_dataframe(d1)
                    if df is None:
                        if language == 'Japanese':
                            st.error('*** 表示可能な記録はありません! ***')
                        else:
                            st.error('*** No records available for display! ***')
                    else:
                        # df.index = np.arange(1, len(df)+1)
                        AgGrid(df,height=140,fit_columns_on_grid_load=True)
                        if language == 'Japanese':
                            hideMapSW = st.checkbox('マップ非表示')
                        else:
                            hideMapSW = st.checkbox('Hide Map')
                        if not hideMapSW:
                            cities = create_cities_dataframe(df)
                            lat = float(df.iloc[0]['placeLat'])
                            lng = float(df.iloc[0]['placeLng'])
                            mapdata = create_map(lat, lng, cities)
                            if language == 'Japanese':
                                st.markdown('##### 中継地:GREEN / 現在地:RED')
                            else:
                                st.markdown('##### Relay point:GREEN / Current point:RED')
                            st.components.v1.html(folium.Figure().add_child(mapdata).render(), height=500)
                            st.write('done')
    else:
        if tnumber_count == 0:
            if language == 'Japanese':
                st.info('*** データがありません! ***')
            else:
                st.info('*** No data! ***')
        elif tnumber_count >= 1:
            update_button = st.button('Update',help='Update Tracking...')
            keycount = 0
            for i,select in enumerate(tnumbers):
                st.markdown(f'##### [{i+1}/{tnumber_count}] Tracking-code 追跡番号: [{select}](http://jizen.kuronekoyamato.co.jp/jizen/servlet/crjz.b.NQ0010?id={select})')
                if select == '':
                    if language == 'Japanese':
                        st.info('*** データがありません! ***')
                    else:
                        st.info('*** No data! ***')
                else:
                    d1 = get_kuroneko_tracking(select,view_track_code=False)
                    if d1 is None:
                        if language == 'Japanese':
                            st.error('*** 一致するデータがありません! ***')
                        else:
                            st.error('*** No matching data! ***')
                    else:
                        df = create_pandas_dataframe(d1)
                        if df is None:
                            if language == 'Japanese':
                                st.error('*** 表示可能な記録はありません! ***')
                            else:
                                st.error('*** No records available for display! ***')
                        else:
                            # df.index = np.arange(1, len(df)+1)
                            df = df.sort_index(ascending=False)
                            AgGrid(df,height=140,autosize=True, key=keycount)
                            keycount += 1
            st.write('done')

if __name__ == "__main__":
    main()
