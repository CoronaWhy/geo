import itertools

import pandas as pd
import requests

from task_geo.dataset_builders.nasa.references import PARAMETERS


def nasa_data_loc(lat, lon, str_start_date, str_end_date, params_str):
    """Extract data for a single location.

    Parameters:
        lat(string)
        lon(string)
        str_start_date(string)
        str_end_date(string)
        params_str(string)

    Returns:
        pandas.DataFrame

    """
    base_url = "https://power.larc.nasa.gov/cgi-bin/v1/DataAccess.py"

    identifier = "identifier=SinglePoint"
    user_community = "userCommunity=SSE"
    temporal_average = "tempAverage=DAILY"
    output_format = "outputList=JSON,ASCII"
    user = "user=anonymous"

    url = (
        f"{base_url}?request=execute&{identifier}&{params_str}&"
        f"startDate={str_start_date}&endDate={str_end_date}&"
        f"lat={lat}&lon={lon}&{temporal_average}&{output_format}&"
        f"{user_community}&{user}"
    )
    response = requests.get(url)
    data_json = response.json()
    df = pd.DataFrame(data_json['features'][0]['properties']['parameter'])
    df['lon'] = lon
    df['lat'] = lat
    return df


def nasa_connector(df_locations, start_date, end_date=None, parms=None):
    """Retrieve meteorologic data from NASA.

    Given a dataset with columns country, region, sub_region, lon, and lat, for
    each geographic coordinate (lon, lat) corresponding to a place (specified
    if country, region, or sub_region) extract the time series of the desired
    data at the location.

    Arguments:
        df_locations(pandas.DataFrame): Dataset with columns lon, and lat
        start_date(datetime): Start date for the time series
        end_date(datetime): End date for the time series (optional)
        parms(list of strings): Desired data, accepted are 'temperature',
                                'humidity', and 'pressure' (optional)

    Returns:
        pandas.DataFrame:   Columns are country, region, sub_region (non-null),
                            lon, lat, date, and the desired data.

    """
    if parms is None:
        parms = list(PARAMETERS.keys())

    df_locations = df_locations[
        ~pd.isna(df_locations[['lon', 'lat']]).all(axis=1)
    ]
    location_data = ['country', 'region', 'sub_region', 'lon', 'lat']
    locations = df_locations[location_data].drop_duplicates()

    str_start_date = str(start_date.date()).replace('-', '')

    if end_date is None:
        str_end_date = str(pd.Timestamp.today().date()).replace('-', '')
    else:
        str_end_date = str(end_date.date()).replace('-', '')

    all_parms = list(itertools.chain.from_iterable([PARAMETERS[p] for p in parms]))
    parms_str = f"parameters={','.join(all_parms)}"

    return pd.concat([
        nasa_data_loc(row.lat, row.lon, str_start_date, str_end_date, parms_str)
        for row in locations.itertuples()
    ])
