import folium
from folium.plugins import MousePosition


def create_base_map(center_lat: float = 20.5937,
                    center_lon: float = 78.9629,
                    zoom: int = 5) -> folium.Map:
    """
    Create a base Folium map centered on India by default.
    User can click anywhere to get AQI for that location.
    """
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB positron",
        control_scale=True
    )

    # Add mouse position display
    MousePosition(
        position="bottomleft",
        separator=" | ",
        prefix="Lat/Lon:",
    ).add_to(m)

    # Add click instructions
    title_html = """
    <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
         background: white; padding: 8px 16px; border-radius: 8px;
         box-shadow: 0 2px 6px rgba(0,0,0,0.2); z-index: 1000;
         font-family: sans-serif; font-size: 13px; color: #333;">
        🗺️ Click anywhere on the map to get AQI data for that location
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    return m


def add_aqi_marker(m: folium.Map,
                   lat: float,
                   lon: float,
                   aqi_data: dict,
                   location_name: str) -> folium.Map:
    """
    Add a colour-coded AQI marker to the map.
    """
    aqi = aqi_data.get("aqi", 0)
    label = aqi_data.get("aqi_label", "Unknown")
    color = aqi_data.get("aqi_color", "#888888")
    advice = aqi_data.get("advice", "")

    popup_html = f"""
    <div style="font-family: sans-serif; min-width: 200px;">
        <h4 style="margin: 0 0 8px; color: #333;">{location_name}</h4>
        <div style="background: {color}; color: {'#000' if aqi <= 2 else '#fff'};
             padding: 6px 12px; border-radius: 4px; text-align: center;
             font-weight: bold; margin-bottom: 8px;">
            AQI {aqi} — {label}
        </div>
        <p style="margin: 4px 0; font-size: 12px; color: #555;">{advice}</p>
        <hr style="margin: 8px 0;">
        <table style="font-size: 12px; width: 100%;">
            <tr><td>PM2.5</td><td><b>{aqi_data['components']['PM2.5']} µg/m³</b></td></tr>
            <tr><td>PM10</td><td><b>{aqi_data['components']['PM10']} µg/m³</b></td></tr>
            <tr><td>O3</td><td><b>{aqi_data['components']['O3']} µg/m³</b></td></tr>
            <tr><td>NO2</td><td><b>{aqi_data['components']['NO2']} µg/m³</b></td></tr>
        </table>
        <p style="margin: 6px 0 0; font-size: 11px; color: #999;">
            📍 {lat:.4f}, {lon:.4f}
        </p>
    </div>
    """

    folium.CircleMarker(
        location=[lat, lon],
        radius=18,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=f"AQI {aqi} — {label}"
    ).add_to(m)

    return m


def get_aqi_color(aqi: int) -> str:
    colors = {1: "#00E400", 2: "#FFFF00", 3: "#FF7E00", 4: "#FF0000", 5: "#8F3F97"}
    return colors.get(aqi, "#888888")


if __name__ == "__main__":
    m = create_base_map()
    m.save("test_map.html")
    print("Map saved to test_map.html — open it in your browser to check.")