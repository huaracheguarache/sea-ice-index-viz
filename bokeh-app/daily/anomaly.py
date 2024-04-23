import panel as pn
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, Legend
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import toolkit as tk

# Add dropdown menu for index selection, and sync to url parameter.
index_selector = pn.widgets.Select(name="Index:",
                                   options={"Sea Ice Extent": "sie", "Sea Ice Area": "sia"},
                                   value="sie",
                                   sizing_mode="stretch_width")

# Add dropdown menu for area selection, and sync to url parameter.
area_groups = {
    "Global": {
        "Global": "glb",
        "Northern Hemisphere": "nh",
        "Southern Hemisphere": "sh",
    },
    "Northern Hemisphere Regions": {
        "Barents Sea": "bar",
        "Beaufort Sea": "beau",
        "Chukchi Sea": "chuk",
        "East Siberian Sea": "ess",
        "Fram Strait": "fram",
        "Kara Sea": "kara",
        "Laptev Sea": "lap",
        "Svalbard": "sval",
    },
    "Southern Hemisphere Regions": {
        "Amundsen-Bellingshausen Sea": "bell",
        "Dronning Maud Land": "drml",
        "Indian Ocean": "indi",
        "Ross Sea": "ross",
        "Troll Station": "trol",
        "Weddell Sea": "wedd",
        "Western Pacific Ocean": "wpac",
    }
}

area_selector = pn.widgets.Select(name="Area:",
                                  groups=area_groups,
                                  value="nh",
                                  sizing_mode="stretch_width")

# Add a dropdown menu for selecting the reference period of the percentile and median plots, and sync to url parameter.
reference_period_selector = pn.widgets.Select(name='Reference period of percentiles and median:',
                                              options={'1981-2010': ('1981', '2010'), '1991-2020': ('1991', '2020')},
                                              value='1981-2010',
                                              sizing_mode='stretch_width')


# Add a dropdown menu for selecting the colorscale that will be used for plotting the individual years,
# and sync parameter to url.
color_groups = {
    "Sequential colour maps": {
        "Viridis": "viridis",
        "Viridis (reversed)": "viridis_r",
        "Plasma": "plasma",
        "Plasma (reversed)": "plasma_r",
        "Batlow": "batlow",
        "Batlow (reversed)": "batlow_r",
        "Custom decadal": "decadal",
    },
    "Non-sequential colour maps": {
        "BatlowS": "batlowS",
        "8 repeating colours": "cyclic_8",
        "17 repeating colours": "cyclic_17",
    }
}

color_scale_selector = pn.widgets.Select(name="Color scale of yearly data:",
                                         groups=color_groups,
                                         value="viridis",
                                         sizing_mode="stretch_width")


extracted_data = tk.download_and_extract_data(index_selector.value,
                                              area_selector.value,
                                              "daily",
                                              'v2p2')
da = extracted_data["da"]
da_converted = tk.convert_and_interpolate_calendar(da)
years = np.unique(da_converted.time.dt.year.values).astype(str)

mean = da_converted.sel(time=slice('1981', '2010')).groupby('time.dayofyear').mean()
anomaly = da_converted.groupby('time.dayofyear') - mean
standard_deviation = anomaly.sel(time=slice('1981', '2010')).groupby('dayofyear').std()
sd_cds = ColumnDataSource({'dayofyear': standard_deviation.dayofyear.values,
                           '1sd_u': standard_deviation.values,
                           '1sd_l': -standard_deviation.values,
                           '2sd_u': 2 * standard_deviation.values,
                           '2sd_l': -2 * standard_deviation.values,
                           '3sd_u': 3 * standard_deviation.values,
                           '3sd_l': -3 * standard_deviation.values})

min = anomaly.sel(time=slice(years[0], years[-2])).groupby('dayofyear').min()
max = anomaly.sel(time=slice(years[0], years[-2])).groupby('dayofyear').max()
min_max_cds = ColumnDataSource({'dayofyear': min.dayofyear.values,
                                'min': min.values,
                                'max': max.values})

cds_dict = {}

for year in years:
    anomaly_values = anomaly.sel(time=year)
    cds_dict[year] = ColumnDataSource({'dayofyear': anomaly_values.dayofyear.values,
                                       'anomaly': anomaly_values.values})

colors_dict = tk.find_line_colors(years, color_scale_selector.value)

plot = figure(tools="pan, wheel_zoom, box_zoom, save")
plot.sizing_mode = "stretch_both"

sd_visible = False

plot.varea(x='dayofyear',
           y1='3sd_u',
           y2='3sd_l',
           source=sd_cds,
           color='darkgray',
           alpha=0.6,
           visible=sd_visible)

plot.varea(x='dayofyear',
           y1='2sd_u',
           y2='2sd_l',
           source=sd_cds,
           color='gray',
           alpha=0.6,
           visible=sd_visible)

plot.varea(x='dayofyear',
           y1='1sd_u',
           y2='1sd_l',
           source=sd_cds,
           color='dimgray',
           alpha=0.6,
           visible=sd_visible)

glyphs = []

min_glyph = plot.line(x='dayofyear',
                      y='min',
                      source=min_max_cds,
                      color='black',
                      line_dash='dashed',
                      line_width=2)

max_glyph = plot.line(x='dayofyear',
                      y='max',
                      source=min_max_cds,
                      color='black',
                      line_dash='dashed',
                      line_width=2)

glyphs.append(('Min/max', [min_glyph, max_glyph]))

for year, cds in cds_dict.items():
    glyph = plot.line(x='dayofyear',
                      y='anomaly',
                      source=cds,
                      line_color=colors_dict[year],
                      line_width=2)
    glyphs.append((year, [glyph]))

n = 23
legend_split = [glyphs[i:i+n] for i in range(0, len(glyphs), n)]

for sublist in legend_split:
    legend = Legend(items=sublist, location="top_center")
    legend.spacing = 1
    plot.add_layout(legend, "right")

plot.legend.click_policy = "hide"

gspec = pn.GridSpec(sizing_mode="stretch_both")

inputs = pn.Column(index_selector,
                   area_selector,
                   reference_period_selector,
                   color_scale_selector,
                   sizing_mode='stretch_both')

gspec[0:5, 0:4] = pn.pane.Bokeh(plot)
gspec[0:5, 4] = inputs


def update_data(event):
    extracted_data = tk.download_and_extract_data(index_selector.value,
                                                  area_selector.value,
                                                  "daily",
                                                  'v2p2')
    da = extracted_data["da"]

    da_converted = tk.convert_and_interpolate_calendar(da)

    ref_period_start = reference_period_selector.value[0]
    ref_period_stop = reference_period_selector.value[1]
    mean = da_converted.sel(time=slice(ref_period_start, ref_period_stop)).groupby('time.dayofyear').mean()
    anomaly = da_converted.groupby('time.dayofyear') - mean

    min = anomaly.sel(time=slice(years[0], years[-2])).groupby('dayofyear').min()
    max = anomaly.sel(time=slice(years[0], years[-2])).groupby('dayofyear').max()

    min_max_cds.data.update({'dayofyear': min.dayofyear.values, 'min': min.values, 'max': max.values})

    for year in years:
        anomaly_values = anomaly.sel(time=year)
        cds_dict[year].data.update({'dayofyear': anomaly_values.dayofyear.values, 'anomaly': anomaly_values.values})


index_selector.param.watch(update_data, "value")
area_selector.param.watch(update_data, 'value')
reference_period_selector.param.watch(update_data, 'value')

gspec.servable()
