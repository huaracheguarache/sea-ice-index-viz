import xarray as xr
import numpy as np
from bokeh.models import ColumnDataSource
from numpy.typing import NDArray


class Climatology:
    def __init__(self, index: str, ds: xr.Dataset) -> None:
        self.p10_90 = ColumnDataSource(self._p10_90(ds, index))
        self.p25_75 = ColumnDataSource(self._p25_75(ds, index))
        self.median = ColumnDataSource(self._median(ds, index))

    def _p10_90(self, ds: xr.Dataset, index: str) -> dict[str, NDArray[float]]:
        return {
            'doy': ds.time.dt.dayofyear.values,
            'p10': ds[f'{index}_10pctile'].values,
            'p90': ds[f'{index}_90pctile'].values,
        }

    def _p25_75(self, ds: xr.Dataset, index: str) -> dict[str, NDArray[float]]:
        return {
            'doy': ds.time.dt.dayofyear.values,
            'p25': ds[f'{index}_25pctile'].values,
            'p75': ds[f'{index}_75pctile'].values,
        }

    def _median(self, ds: xr.Dataset, index: str) -> dict[str, NDArray[float]]:
        return {
            'doy': ds.time.dt.dayofyear.values,
            'value': ds[f'{index}_median'].values,
        }

    def update(self, index: str, ds: xr.Dataset) -> None:
        self.p10_90.data.update(self._p10_90(ds, index))
        self.p25_75.data.update(self._p25_75(ds, index))
        self.median.data.update(self._median(ds, index))


class MinMaxPerDOY:
    def __init__(self, ds: xr.Dataset):
        self.min = ColumnDataSource(self._min(ds))
        self.max = ColumnDataSource(self._max(ds))

    def _min(self, ds: xr.Dataset) -> dict[str, NDArray[float]]:
        return {'doy': ds.dayofyear.values, 'value': ds.min_per_doy.values}

    def _max(self, ds: xr.Dataset) -> dict[str, NDArray[float]]:
        return {'doy': ds.dayofyear.values, 'value': ds.max_per_doy.values}

    def update(self, ds: xr.Dataset) -> None:
        self.min.data.update(self._min(ds))
        self.max.data.update(self._max(ds))


class Decades:
    def __init__(self, index: str, ds_dict: dict[str, xr.Dataset]):
        self.cds_decades = {}
        for decade, ds in ds_dict.items():
            span = ColumnDataSource(self._span(ds, index))
            median = ColumnDataSource(self._median(ds, index))

            self.cds_decades[decade] = [span, median]

    def _span(self, ds: xr.Dataset, index: str) -> dict[str, NDArray[float]]:
        return {
            'doy': ds.time.dt.dayofyear.values,
            'min': ds[f'{index}_min'].values,
            'max': ds[f'{index}_max'].values,
        }

    def _median(self, ds: xr.Dataset, index: str) -> dict[str, NDArray[float]]:
        return {
            'doy': ds.time.dt.dayofyear.values,
            'value': ds[f'{index}_median'].values,
        }

    def update(self, index: str, ds_dict: dict[str, xr.Dataset]) -> None:
        for decade, ds in ds_dict.items():
            self.cds_decades[decade][0].data.update(self._span(ds, index))
            self.cds_decades[decade][1].data.update(self._median(ds, index))


class Daily:
    def __init__(self, index: str, ds: xr.Dataset) -> None:
        self.years = np.unique(ds.time.dt.year.values).astype(str)
        da = ds[index]
        da_all_leap = da.convert_calendar('all_leap')

        self.yearly = {}
        for year in self.years:
            subset = da_all_leap.sel(time=year)
            rank = ds.rank_per_doy.sel(time=year)
            self.yearly[year] = ColumnDataSource(self._yearly(subset, rank))

    def _yearly(
        self, da: xr.DataArray, rank: xr.DataArray
    ) -> dict[str, NDArray]:
        return {
            'doy': da.time.dt.dayofyear.values,
            'value': da.values,
            'date': da.time.dt.strftime('%Y-%m-%d').values,
            'rank': rank.values,
        }

    def update(self, index, ds):
        da = ds[index]
        da_all_leap = da.convert_calendar('all_leap')

        for year in self.years:
            subset = da_all_leap.sel(time=year)
            rank = ds.rank_per_doy.sel(time=year)
            self.yearly[year].data.update(self._yearly(subset, rank))


class MinMaxPerYear:
    def __init__(self, ds: xr.Dataset, colours) -> None:
        self.min = ColumnDataSource(self._min(ds, colours))
        self.max = ColumnDataSource(self._max(ds, colours))

    def _min(self, ds: xr.Dataset, colours: NDArray[str] | list[str]):
        return {
            'doy': ds.yearly_min_date.dt.dayofyear.values,
            'value': ds.yearly_min_value.values,
            'date': ds.yearly_min_date.dt.strftime('%Y-%m-%d').values,
            'rank': ds.yearly_min_rank.values,
            'colour': colours,
        }

    def _max(self, ds: xr.Dataset, colours: NDArray[str] | list[str]):
        return {
            'doy': ds.yearly_max_date.dt.dayofyear.values,
            'value': ds.yearly_max_value.values,
            'date': ds.yearly_max_date.dt.strftime('%Y-%m-%d').values,
            'rank': ds.yearly_max_rank.values,
            'colour': colours,
        }

    def update(self, ds: xr.Dataset, colours) -> None:
        self.min.data.update(self._min(ds, colours))
        self.max.data.update(self._max(ds, colours))


class Forecast:
    def __init__(self, index: str, ds: xr.Dataset) -> None:
        self.forecast = {}

        for i in range(1, 11):
            da = ds[index].sel(member=i)
            self.forecast[i] = ColumnDataSource(self._forecast(da))

    def _forecast(self, da: xr.DataArray):
        doy = da.time.dt.dayofyear.values
        values = da.values
        member = np.full(len(da.values), da.member.values)
        dates = da.time.dt.strftime('%Y-%m-%d').values

        # Check whether dayofyear array contains both 1 and 366 which
        # indicates that it runs into the next year. If yes, we need to
        # insert a nan-value in the values array to prevent the forecast
        # glyph made with this cds from wrapping around the plot.
        if sum(np.isin(doy, [366, 1])) == 2:
            year_start_index = np.where(doy == 1)[0]
            doy = np.insert(doy, year_start_index, 367)
            values = np.insert(values, year_start_index, np.nan)
            member = np.insert(member, year_start_index, 999)
            dates = np.insert(dates, year_start_index, 'foo')

        return {
            'doy': doy,
            'value': values,
            'member': member,
            'date': dates,
        }

    def update(self, index: str, ds: xr.Dataset) -> None:
        for i in range(1, 11):
            da = ds[index].sel(member=i)
            self.forecast[i].data.update(self._forecast(da))
