import xarray as xr


class CalculateAnomaly:
    def __init__(self, index: str, ref_period: str, ds: xr.Dataset) -> None:
        self.index = index
        start = ref_period[:4]
        end = ref_period[5:]

        da = ds[index].convert_calendar('all_leap', missing=-999)

        for i, val in enumerate(da.values):
            if val == -999:
                da.values[i] = (da.values[i - 1] + da.values[i + 1]) / 2

        self.mean = (
            da.sel(time=slice(start, end)).groupby('time.dayofyear').mean()
        )

    def get_clim_anom(self, ds: xr.Dataset) -> xr.Dataset:
        ds[f'{self.index}_10pctile'].values = (
            ds[f'{self.index}_10pctile'].values - self.mean.values
        )
        ds[f'{self.index}_90pctile'].values = (
            ds[f'{self.index}_90pctile'].values - self.mean.values
        )
        ds[f'{self.index}_25pctile'].values = (
            ds[f'{self.index}_25pctile'].values - self.mean.values
        )
        ds[f'{self.index}_75pctile'].values = (
            ds[f'{self.index}_75pctile'].values - self.mean.values
        )
        ds[f'{self.index}_median'].values = (
            ds[f'{self.index}_median'].values - self.mean.values
        )

        return ds

    def get_decade_anom(
        self, ds_dict: dict[str, xr.Dataset]
    ) -> dict[str, xr.Dataset]:
        for decade in ds_dict.keys():
            ds_dict[decade][f'{self.index}_min'].values = (
                ds_dict[decade][f'{self.index}_min'].values - self.mean.values
            )
            ds_dict[decade][f'{self.index}_max'].values = (
                ds_dict[decade][f'{self.index}_max'].values - self.mean.values
            )
            ds_dict[decade][f'{self.index}_median'].values = (
                ds_dict[decade][f'{self.index}_median'].values
                - self.mean.values
            )

        return ds_dict

    def get_daily_anom(self, ds: xr.Dataset) -> xr.Dataset:
        ds['min_per_doy'].values = ds.min_per_doy.values - self.mean.values
        ds['max_per_doy'].values = ds.max_per_doy.values - self.mean.values
        da = ds[self.index].convert_calendar('all_leap')
        ds[self.index].values = (
            da.groupby('time.dayofyear') - self.mean
        ).values

        year_min = ds['yearly_min_value'].values
        year_max = ds['yearly_max_value'].values

        for i, year in enumerate(ds['year'].values):
            doy_min = ds.sel(year=year).yearly_min_date.dt.dayofyear.values
            doy_max = ds.sel(year=year).yearly_max_date.dt.dayofyear.values

            year_min[i] = year_min[i] - self.mean.sel(dayofyear=doy_min).values
            year_max[i] = year_max[i] - self.mean.sel(dayofyear=doy_max).values

        ds['yearly_min_value'].values = year_min
        ds['yearly_max_value'].values = year_max

        return ds

    def get_forecast_anom(self, ds: xr.Dataset):
        doy = ds.time.dt.dayofyear.values
        ds[self.index].values = (
            ds[self.index].values - self.mean.sel(dayofyear=doy).values
        )

        return ds
