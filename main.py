import os
import re
import time
import requests
import json
import pandas as pd
import folium
from bs4 import BeautifulSoup
# [update:2025/01/20, ver 1.0.6]
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
    st.set_page_config(
        page_title="YAMATO TRACKER with Map",
        page_icon="🚚",
        menu_items={
            'Get help': None,
            'Report a bug': None,
            'About': None
        }
    )

    # Hide deploy button and developer options
    st.markdown(
        """
        <style>
        :root {
            --yamato-red: #FF0000;
            --yamato-blue: #003366;
            --yamato-black: #000000;
            --background-color: rgba(255, 255, 255, 0.05);
            --border-color: rgba(170, 170, 170, 0.3);
            --hover-color: rgba(0, 0, 0, 0.05);
        }
        /* 基本スタイル */
        .block-container {
            padding: 2rem 1rem !important;
        }

        /* 入力エリアのスタイル */
        .stTextArea > div > div {
            border-radius: 8px !important;
            border: 2px solid rgba(255, 0, 0, 0.1) !important;
            background: rgba(255, 255, 255, 0.02) !important;
            transition: all 0.3s ease !important;
        }
        .stTextArea > div > div:focus-within {
            border-color: rgba(255, 0, 0, 0.3) !important;
            box-shadow: 0 0 0 2px rgba(255, 0, 0, 0.1) !important;
        }

        /* 地図コンテナのスタイル */
        iframe {
            border-radius: 12px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
        }

        /* ステータス表示のスタイル */
        .status-container {
            background: linear-gradient(135deg, var(--yamato-red), #ff4d4d);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            color: white;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(255, 0, 0, 0.2);
        }

        /* AgGridのスタイル改善 */
        .ag-theme-alpine {
            --ag-header-background-color: rgba(255, 0, 0, 0.05);
            --ag-header-foreground-color: var(--yamato-black);
            --ag-row-hover-color: rgba(255, 0, 0, 0.05);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        /* 通常ボタンのスタイル（Update用） */
        .stButton > button:first-child ){
            background: linear-gradient(135deg, var(--yamato-blue), #0066cc) !important;
            color: white !important;
            border: none !important;
            padding: 0.5rem 1.5rem !important;
            border-radius: 20px !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px rgba(0, 51, 102, 0.2) !important;
        }
        /* 警告ボタンのスタイル（データ消去用） */
        .stButton.clear-data > button:first-child {
            background: linear-gradient(135deg, var(--yamato-red), #ff4d4d) !important;
            color: white !important;
            border: none !important;
            padding: 0.5rem 1.5rem !important;
            border-radius: 20px !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px rgba(255, 0, 0, 0.2) !important;
        }
        .stButton > button:first-child:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 8px rgba(0, 51, 102, 0.3) !important;
        }
        .stButton.clear-data > button:first-child:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 8px rgba(255, 0, 0, 0.3) !important;
        }

        /* モバイル対応のスタイル */
        @media (max-width: 768px) {
            div[data-testid="column"]:nth-of-type(1) {
                flex: 0 1 auto !important;
                width: auto !important;
                min-width: 0px !important;
            }
            div[data-testid="column"]:nth-of-type(2) {
                flex: 0 0 auto !important;
                width: auto !important;
                min-width: fit-content !important;
            }
        }
        [data-theme="dark"] {
            --background-color: rgba(255, 255, 255, 0.05);
            --border-color: rgba(170, 170, 170, 0.2);
            --hover-color: rgba(255, 255, 255, 0.05);
        }
        details {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.5em 0.5em 0;
            margin-bottom: 1em;
            background: var(--background-color);
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        }
        summary {
            font-weight: bold;
            margin: -0.5em -0.5em 0;
            padding: 0.5em;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        summary:hover {
            background-color: var(--hover-color);
        }
        details[open] {
            padding: 0.5em;
        }
        details[open] summary {
            margin-bottom: 0.5em;
            border-bottom: 1px solid var(--border-color);
        }
        /* Streamlitのexpander用スタイル */
        .streamlit-expanderHeader {
            background-color: var(--background-color) !important;
        }
        .streamlit-expanderContent {
            background-color: var(--background-color) !important;
        }
        .stDeployButton {
            display: none;
        }
        [data-testid="stStatusWidget"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown(""" <style>

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    h1 {font-size: 28px !important;}
    .stDeployButton {display:none;}
    </style> """, unsafe_allow_html=True)

    # Get current date and version
    current_date_jp, current_date_en = utils.get_current_date()
    with open('VERSION', 'r') as f:
        version = f.read().strip()

    # Display image at the top with rounded corners
    st.markdown(
        f'<div style="display: flex; justify-content: center; width: 100%;">'
        f'<div style="position: relative; width: 100%; max-width: 800px;">'
        f'  <img src="https://github.com/user-attachments/assets/93aaadfc-8b31-467c-bc18-77711a2b6991" '
        f'  style="border-radius: 15px; width: 100%; filter: blur(4px); opacity: 0.9; transform: scale(1); transform-origin: center; margin-bottom: 20px;">'
        f'  <div style="position: absolute; bottom: 25px; right: 15px; color: white; font-size: 12px; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">'
        f'    [update:{current_date_jp}, ver {version}]'
        f'  </div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
        <style>
        header.stAppHeader {
            background-color: transparent;
        }
        section.stMain .block-container {
            padding-top: 0rem;
            z-index: 1;
        }
        </style>""", unsafe_allow_html=True)

    # Header text
    hedder_text_jp = f"""<div style="
        font-size: 1.2em;
        color: #333;
        background: linear-gradient(to right, #f8f9fa, #ffffff);
        padding: 1.2rem;
        border-left: 4px solid var(--yamato-red);
        border-radius: 4px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
    クロネコヤマト（ヤマト運輸）の荷物お問い合わせが少しだけ便利になるアプリです。
    </div><br>
    <details><summary>🚚 便利機能 ✨</summary>
 ・追跡番号を複数コピペして一括調査できます<br>
 ・最新の配送状況が経路毎に一覧表示できます<br>
 ・経路情報を地図表示できます<br>
 ・ヤマトへの直リンクが追跡番号に含まれています<br>
 ・過去の追跡データを表示・管理できます<br>
 ・データベースに最大20件まで記録を保持
    </details>"""

    hedder_text_en = f"""<div style="
        font-size: 1.2em;
        color: #333;
        background: linear-gradient(to right, #f8f9fa, #ffffff);
        padding: 1.2rem;
        border-left: 4px solid var(--yamato-red);
        border-radius: 4px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
    This is an application that makes Kuroneko Yamato (Yamato Transport) package inquiries a little more convenient.
    </div><br>
    <details><summary>🚚 Convenient Features ✨</summary>
 - multiple tracking numbers can be copied and pasted for batch investigation<br>
 - latest delivery status can be listed by route.<br>
 - route information can be displayed on a map<br>
 - direct link to Yamato is included in the tracking number<br>
 - past tracking data can be displayed and managed<br>
 - database keeps up to 20 records
    </details>"""


    # Language selection
    col1, col2 = st.columns([4, 1])
    with col1:
        st.header("YAMATO TRACKER with Map")
    with col2:
        language = st.radio('言語(Language)',('Japanese', 'English'))

    # Display tracking data
    if st.checkbox('Show past tracking data' if language == 'English' else '過去の追跡データを表示'):
        rows = database.get_tracking_data()

        # スマートフォン対応のスタイル

        st.markdown("""
            <style>
            div.stButton {
                display: flex;
                width: 100%;
                justify-content: center;
                margin: 1rem 0;
            }
            div.stButton > button {
                background: linear-gradient(135deg, var(--yamato-red), #ff4d4d) !important;
                color: white !important;
                border: none !important;
                padding: 0.5rem 2rem !important;
                border-radius: 20px !important;
                font-weight: 500 !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 2px 4px rgba(255, 0, 0, 0.2) !important;
            }
            div.stButton > button:hover {
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 8px rgba(255, 0, 0, 0.3) !important;
            }
            @media screen and (max-width: 640px) {
                div.stButton {
                    margin: 0.5rem 0;
                }
                div.stButton > button {
                    margin-left: auto !important;
                    width: auto !important;
                }
            }
            </style>
        """, unsafe_allow_html=True)

        # Clear Data button with custom container style
        st.markdown('<style>.clear-data-container .stButton{display: inline-block;}</style>', unsafe_allow_html=True)
        st.markdown('<div class="clear-data-container">', unsafe_allow_html=True)
        clear_data_clicked = st.button('データ消去' if language == 'Japanese' else 'Clear Data', key='clear_data_button')
        st.markdown('</div>', unsafe_allow_html=True)
        if rows and clear_data_clicked:
            database.clear_all_data()
            st.success('全てのデータが消去されました。' if language == 'Japanese' else 'All data has been cleared.')
            st.rerun()  # Force page reload

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
                    st.markdown(f"##### 追跡番号: [{tracking_number}](http://jizen.kuronekoyamato.co.jp/jizen/servlet/crjz.b.NQ0010?id={tracking_number})")
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
            placeholder="ここに追跡番号を入力または貼り付けてください（複数可）",
            help='ここに追跡番号を入力または貼り付けてください（複数可）',
            key='text_area_jp'
        )
    else:
        st.markdown(f'<div class="custom-header">{hedder_text_en}</div>', unsafe_allow_html=True)
        st.write("")
        tnumber_text = st.text_area(
            'Automatic deletion of non-numeric characters.',
            "",
            placeholder="Please enter or paste the tracking number here (multiple allowed)",
            help='Please enter or paste the tracking number here (multiple allowed)',
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
                update_button = st.button('Update', help='Update Tracking...')
                st.markdown(f'##### [1/{tnumber_count}] Tracking-code 追跡番号: [{select}](http://jizen.kuronekoyamato.co.jp/jizen/servlet/crjz.b.NQ0010?id={select})')
            else:
                select = tnumbers[0]  # Always use the first tracking number
                st.markdown(f'##### [1/{tnumber_count}] Tracking-code 追跡番号: [{select}](http://jizen.kuronekoyamato.co.jp/jizen/servlet/crjz.b.NQ0010?id={select})')
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
                            fit_columns_on_grid_load=False,
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
                            # デフォルトの緯度経度（日本の中心付近）
                            default_lat = 36.2048
                            default_lng = 138.2529
                            try:
                                lat = float(df.iloc[0]['placeLat'])
                                lng = float(df.iloc[0]['placeLng'])
                                # NaNチェック
                                if pd.isna(lat) or pd.isna(lng):
                                    lat, lng = default_lat, default_lng
                            except (ValueError, TypeError):
                                lat, lng = default_lat, default_lng

                            try:
                                mapdata = map.create_map(lat, lng, cities)
                                st.markdown('##### 中継地:GREEN / 現在地:RED' if language == 'Japanese' else '##### Relay point:GREEN / Current point:RED')
                                st.components.v1.html(folium.Figure().add_child(mapdata).render(), height=500)
                            except Exception as e:
                                st.error('地図の表示中にエラーが発生しました' if language == 'Japanese' else 'Error occurred while displaying the map')
                            st.write('done')
    else:
        if tnumber_count == 0:
            st.info('*** データがありません! ***' if language == 'Japanese' else '*** No data! ***')
        elif tnumber_count >= 1:
            update_button = st.button('Update', help='Update Tracking...')
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
                            AgGrid(df, height=140, fit_columns_on_grid_load=False, key=str(keycount))
                            keycount += 1

if __name__ == "__main__":
    try:
        main()
    finally:
        if 'conn' in locals():
            conn.close()
