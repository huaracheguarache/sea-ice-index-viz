import xarray as xr
import numpy as np


class DataDownloader:
    def __init__(self, index: str, area: str, ref_period: str):
        self.obs_path = (
            'https://thredds.met.no/thredds/dodsC/metusers/'
            'signeaa/test-data-sii-v3p0'
        )
        self.fcst_path = (
            'https://thredds.met.no/thredds/dodsC/metusers/'
            'thomasl/SII_forecast/final_topaz5'
        )
        self.decades = ['1980-1989', '1990-1999', '2000-2009', '2010-2019']
        self.nsidc_nh_areas = [
            'baffin',
            'baltic',
            'barents',
            'beaufort',
            'bering',
            'bohai',
            'canarch',
            'centralarc',
            'chukchi',
            'ess',
            'greenland',
            'hudson',
            'japan',
            'kara',
            'laptev',
            'lawrence',
            'nh',
            'okhotsk',
        ]

        index_translation = {'sie': 'ice_extent', 'sia': 'ice_area'}
        self.index = index
        self.index_translated = index_translation[index]
        self.area = area
        self.ref_period = ref_period

    def download_daily_data(self):
        path = (
            f'{self.obs_path}/sii_v3p0/{self.area}/{self.index_translated}'
            f'_{self.area}_sii-v3p0_daily.nc'
        )
        ds = xr.open_dataset(path, cache=False).load()

        return ds

    def download_clim_data(self):
        path = (
            f'{self.obs_path}/clim/{self.area}/{self.index_translated}'
            f'_{self.area}_sii-v3p0_daily-climatology'
            f'-{self.ref_period}.nc'
        )
        ds = xr.open_dataset(path, cache=False).load()

        return ds

    def download_decades_data(self):
        ds_dict = {}
        for decade in self.decades:
            path = (
                f'{self.obs_path}/clim/{self.area}/{self.index_translated}'
                f'_{self.area}_sii-v3p0_daily-climatology-{decade}.nc'
            )
            ds_dict[decade] = xr.open_dataset(path, cache=False).load()

        return ds_dict

    def download_forecast_data(self):
        if self.area in self.nsidc_nh_areas:
            path = f'{self.fcst_path}/{self.index}_{self.area}.nc'
            ds = xr.open_dataset(path, cache=False).load()
        else:
            # Create a fake Dataset if requested area is not in the NSIDC
            # list of areas for the northern hemisphere.
            values = np.full((10, 1), np.nan)
            data_vars = {self.index: (['member', 'time'], values)}
            coords = {
                'member': [i for i in range(1, 11)],
                'time': [np.datetime64('1970-01-01')],
            }
            ds = xr.Dataset(data_vars=data_vars, coords=coords)

        return ds
