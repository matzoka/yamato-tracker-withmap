import pandas as pd
from datetime import datetime

def create_pandas_dataframe(d1):
    """Create pandas dataframe from tracking data"""
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

    d1_dict = {
        'status': data_status,
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
        current_year = pd.Timestamp.now().year
        df['datetime'] = pd.to_datetime(f'{current_year}/' + df['trackdate'] + ' ' + df['tracktime'], format='%Y/%m/%d %H:%M')
        df = df.sort_values('datetime', ascending=False)
        df = df.drop('datetime', axis=1)
        return df.reset_index(drop=True)
    else:
        return None

def get_current_date():
    """Get current date in Japanese and English formats"""
    current_date_jp = datetime.now().strftime('%Y/%m/%d')
    current_date_en = datetime.now().strftime('%m/%d/%Y')
    return current_date_jp, current_date_en
