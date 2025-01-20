import os
import re
import time
import requests
import json
import pandas as pd
import folium
from bs4 import BeautifulSoup
# [update:2025/01/20, ver 1.0.5]
import streamlit as st
import streamlit.components.v1 as components

# Initialize session state
if 'count' not in st.session_state:
    st.session_state.count = 0
from st_aggrid import AgGrid
from src.database import database
from src.map import map
from src.utils import utils


def get_kuroneko_tracking(conn, tracking_number, view_track_code=False):
    """Get tracking information from Kuroneko Yamato API"""
    try:
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

        # Save data to database after all data is collected
        database.save_tracking_data(conn, tracking_data)
        return tracking_data
    except Exception as e:
        print('get_kuroneko_tracking error:', e)
        tracking_data = None
        return tracking_data

def get_center_status(centercode):
    """Get center status information"""
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

def main():
    # Initialize database
    conn = database.init_db()

    # Page configuration
    st.set_page_config(page_title="YAMATO TRACKER with Map", page_icon="🚚")
    st.markdown(""" <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    h1 {font-size: 28px !important;}
    .stDeployButton {display:none;}
    </style> """, unsafe_allow_html=True)
    hide_streamlit_logo = True

    # Display image at the top with rounded corners
    st.markdown(
        f'<div style="display: flex; justify-content: center; width: 100%;">'
        f'<img src="https://github.com/user-attachments/assets/93aaadfc-8b31-467c-bc18-77711a2b6991" '
        f'style="border-radius: 15px; width: 100%; max-width: 800px; filter: blur(4px); opacity: 0.9; transform: scale(1); transform-origin: center; margin-bottom: 20px;">'
        f'</div>',
        unsafe_allow_html=True
    )

    # Get current date and version
    current_date_jp, current_date_en = utils.get_current_date()
    with open('VERSION', 'r') as f:
        version = f.read().strip()

    # Header text
    hedder_text_jp = f"""<u>クロネコヤマト（ヤマト運輸）の荷物お問い合わせが少しだけ便利になるアプリです。</u> [update:{current_date_jp}, ver {version}]<br><br>
・追跡番号を複数コピペして一括調査できます<br>
・最新の配送状況が経路毎に一覧表示できます<br>
・経路情報を地図表示できます<br>
・ヤマトへの直リンクが追跡番号に含まれています<br>
・過去の追跡データを表示・管理できます<br>
・データベースに最大20件まで記録を保持"""

    hedder_text_en = f"""<u>This is an application that makes Kuroneko Yamato (Yamato Transport) package inquiries a little more convenient.</u> [update:{current_date_en}, ver {version}]<br><br>
- multiple tracking numbers can be copied and pasted for batch investigation<br>
- latest delivery status can be listed by route.<br>
- route information can be displayed on a map<br>
- direct link to Yamato is included in the tracking number<br>
- past tracking data can be displayed and managed<br>
- database keeps up to 20 records"""


    # Language selection
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("YAMATO TRACKER with Map")
    with col2:
        language = st.radio('言語(Language)',('Japanese', 'English'))

    # Display tracking data
    if st.checkbox('Show past tracking data' if language == 'English' else '過去の追跡データを表示'):
        rows = database.get_tracking_data()

        if rows:
            df_history = pd.DataFrame(rows, columns=[
                'id', 'tracking_number', 'status', 'place_name', 'place_code',
                'track_date', 'track_time', 'place_postcode', 'place_address',
                'place_lat', 'place_lng', 'created_at'
            ])
            # Group by tracking_number and display with expander, sorted by latest first
            grouped = df_history.sort_values('id', ascending=False).groupby('tracking_number')
            for tracking_number, group in grouped:
                with st.expander(f"追跡番号: {tracking_number}"):
                    st.dataframe(group[['status', 'place_name', 'place_code',
                                     'track_date', 'track_time', 'place_postcode', 'place_address',
                                     'place_lat', 'place_lng', 'created_at']])
        else:
            st.info("過去の追跡データはありません")

    # Tracking number input
    if language == 'Japanese':
        st.markdown(f'<div class="custom-header">{hedder_text_jp}</div>', unsafe_allow_html=True)
        st.write("")
        tnumber_text = st.text_area(
            '数字以外の文字は自動削除',
            "",
            placeholder="ここに追跡番号を入力してください。（入力完了はCtrl+Enter）",
            help='ここに追跡番号を入力してください。（入力完了はCtrl+Enter）',
            key='text_area_jp'
        )
    else:
        st.markdown(f'<div class="custom-header">{hedder_text_en}</div>', unsafe_allow_html=True)
        st.write("")
        tnumber_text = st.text_area(
            'Automatic deletion of non-numeric characters.',
            "",
            placeholder="Please enter the tracking number here. (Press Ctrl+Enter to complete)",
            help='Please enter the tracking number here. (Press Ctrl+Enter to complete)',
            key='text_area_en'
        )

    # Process tracking numbers
    temp_tnumbers = tnumber_text.split("\n")
    tnumbers = [re.sub('[^0-9]','', row) for row in temp_tnumbers if row != '']
    tnumber_df = pd.DataFrame({'number': tnumbers}).dropna()
    tnumber_count = len(tnumber_df)

    # Display options
    if language == 'Japanese':
        select_radio = st.radio(
            '表示したい件数を選択してください。',
            ('１件表示・地図付き', '全件表示'),
            key='display_option_radio',
            help='表示する追跡情報の件数を選択'
        )
    else:
        select_radio = st.radio('Select the number of items you wish to display.',('Show 1 item with Map','Show all item'))

    # Display tracking information
    if select_radio == 'Show 1 item with Map' or select_radio == '１件表示・地図付き':
        if tnumber_count == 0:
            st.info('*** データがありません ***' if language == 'Japanese' else '*** No data ***')
        elif tnumber_count >= 1:
            # Display tracking information for single item
            if tnumber_count == 1:
                select = tnumbers[0]
                update_button = st.button('Update',help='Update Tracking...')
                st.markdown(f'##### [1/{tnumber_count}] Tracking-code 追跡番号: [{select}](http://jizen.kuronekoyamato.co.jp/jizen/servlet/crjz.b.NQ0010?id={select})')
            else:
                select = tnumbers[st.session_state.count-1]
                st.markdown(f'##### [{st.session_state.count}/{tnumber_count}] Tracking-code 追跡番号: [{select}](http://jizen.kuronekoyamato.co.jp/jizen/servlet/crjz.b.NQ0010?id={select})')

            if select != '':
                d1 = get_kuroneko_tracking(conn, select, view_track_code=False)
                if d1 is None:
                    st.error('*** 一致するデータがありません! ***' if language == 'Japanese' else '*** No matching data! ***')
                else:
                    df = utils.create_pandas_dataframe(d1)
                    if df is None:
                        st.error('*** 表示可能な記録はありません! ***' if language == 'Japanese' else '*** No records available for display! ***')
                    else:
                        AgGrid(
                            df,
                            height=140,
                            fit_columns_on_grid_load=True,
                            defaultColDef={
                                "autoSize": True,
                                "minWidth": 100,
                                "maxWidth": 500,
                                "resizable": True
                            },
                            suppressSizeToFit=False
                        )
                        hideMapSW = st.checkbox('マップ非表示' if language == 'Japanese' else 'Hide Map')
                        if not hideMapSW:
                            cities = map.create_cities_dataframe(df)
                            lat = float(df.iloc[0]['placeLat'])
                            lng = float(df.iloc[0]['placeLng'])
                            mapdata = map.create_map(lat, lng, cities)
                            st.markdown('##### 中継地:GREEN / 現在地:RED' if language == 'Japanese' else '##### Relay point:GREEN / Current point:RED')
                            st.components.v1.html(folium.Figure().add_child(mapdata).render(), height=500)
                            st.write('done')
    else:
        if tnumber_count == 0:
            st.info('*** データがありません! ***' if language == 'Japanese' else '*** No data! ***')
        elif tnumber_count >= 1:
            update_button = st.button('Update',help='Update Tracking...')
            keycount = 0
            for i,select in enumerate(tnumbers):
                st.markdown(f'##### [{i+1}/{tnumber_count}] Tracking-code 追跡番号: [{select}](http://jizen.kuronekoyamato.co.jp/jizen/servlet/crjz.b.NQ0010?id={select})')
                if select == '':
                    st.info('*** データがありません! ***' if language == 'Japanese' else '*** No data! ***')
                else:
                    d1 = get_kuroneko_tracking(conn, select,view_track_code=False)
                    if d1 is None:
                        st.error('*** 一致するデータがありません! ***' if language == 'Japanese' else '*** No matching data! ***')
                    else:
                        df = utils.create_pandas_dataframe(d1)
                        if df is None:
                            st.error('*** 表示可能な記録はありません! ***' if language == 'Japanese' else '*** No records available for display! ***')
                        else:
                            df = df.sort_index(ascending=False)
                            AgGrid(df, height=140, fit_columns_on_grid_load=True, key=str(keycount))
                            keycount += 1
            st.write('done')

if __name__ == "__main__":
    try:
        main()
    finally:
        if 'conn' in locals():
            conn.close()
