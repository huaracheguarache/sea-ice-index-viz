from download import DataDownloader
from anomaly import CalculateAnomaly


index = 'sie'
area = 'nh'
ref_period = '1981-2010'

data = DataDownloader(index, area, ref_period)
daily = data.download_daily_data()
clim = data.download_clim_data()
decades = data.download_decades_data()
forecast = data.download_forecast_data()

anomaly = CalculateAnomaly(index, ref_period, daily)
anomaly.get_daily_anom(daily)
anomaly.get_clim_anom(clim)
anomaly.get_decade_anom(decades)
anomaly.get_forecast_anom(forecast)