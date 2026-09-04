from frontend.layout import configure_page
from frontend.seasonal_occupancy import render_seasonal_occupancy


configure_page("Seasonal occupancy", ":chart_with_upwards_trend:")
render_seasonal_occupancy()
