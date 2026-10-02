"""
A class for plotting guesses on a map relative to a "correct" guess
"""

import html
import os
import re
import time
import webbrowser
from pathlib import Path

import folium
from folium.map import FitBounds
from sty import fg

from .. import botfiles
from ..Utils.color import colormsg

# tile.openstreetmap.org blocks requests without a Referer, which a map opened from a
# local file never sends, and CARTO now needs an API key, so use Esri which needs neither.
# The first layer is shown by default
TILES = [
    (
        "Satellite",
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "Tiles &copy; Esri, Maxar, Earthstar Geographics",
    ),
    (
        "Streets",
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        "Tiles &copy; Esri, HERE, Garmin, OpenStreetMap contributors",
    ),
]
LABELS = (
    "Labels",
    "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
    "Labels &copy; Esri",
)


class Map:
    def __init__(self, latitude, longitude, tolerance=None, name="round", zoomLevel=10):
        self.answer = [latitude, longitude]
        self.bounds = [self.answer]
        self.fitBounds = None
        self.map = folium.Map(location=self.answer, zoom_start=zoomLevel, tiles=None)
        for i, (tileName, url, attribution) in enumerate(TILES):
            folium.TileLayer(
                tiles=url, attr=attribution, name=tileName, show=i == 0, max_zoom=19
            ).add_to(self.map)
        folium.TileLayer(
            tiles=LABELS[1], attr=LABELS[2], name=LABELS[0], overlay=True
        ).add_to(self.map)
        folium.LayerControl().add_to(self.map)

        folium.Marker(
            location=self.answer,
            tooltip="Answer",
            popup=f"<b>Answer</b><br>{latitude}, {longitude}",
            icon=folium.Icon(color="blue", icon="star"),
        ).add_to(self.map)
        if tolerance:
            folium.Circle(
                location=self.answer,
                radius=float(tolerance),
                color="#2a81cb",
                fill=True,
                fill_opacity=0.15,
                tooltip=f"Tolerance: {tolerance}m",
            ).add_to(self.map)

        safeName = re.sub(r"[^\w-]+", "_", str(name)).strip("_") or "round"
        Path(botfiles.mapsdir).mkdir(parents=True, exist_ok=True)
        self.filePath = os.path.join(
            botfiles.mapsdir, f"{time.strftime('%Y-%m-%d_%H%M%S')}_{safeName}.html"
        )
        self.saveMap()

    def addPoint(self, latitude, longitude, user, distance, link, correct):
        if distance < 1000:
            off = f"{round(distance, 2)}m"
        else:
            off = f"{round(distance / 1000, 2)}km"
        user = html.escape(user)
        link = html.escape(link, quote=True)
        folium.Marker(
            location=[latitude, longitude],
            tooltip=f"{user}: {off}",
            popup=folium.Popup(
                f'<b>{user}</b><br>{off} away<br><a href="{link}" target="_blank">view guess</a>',
                max_width=250,
            ),
            icon=folium.Icon(
                color="green" if correct else "red", icon="ok" if correct else "remove"
            ),
        ).add_to(self.map)
        folium.PolyLine(
            [[latitude, longitude], self.answer],
            color="green" if correct else "red",
            weight=1.5,
            opacity=0.6,
        ).add_to(self.map)
        self.bounds.append([latitude, longitude])
        self.saveMap()

    def saveMap(self):
        """the map is saved after every guess, so it can be refreshed in the browser during the round"""
        if len(self.bounds) > 1:
            if self.fitBounds is not None:
                self.map._children.pop(self.fitBounds.get_name(), None)
            self.fitBounds = FitBounds(self.bounds, padding=(30, 30))
            self.map.add_child(self.fitBounds)
        try:
            self.map.save(self.filePath)
        except Exception as e:  # pylint: disable=broad-except
            colormsg(f"Could not save map: {e}", fg.red)

    def getFilePath(self):
        return self.filePath if os.path.exists(self.filePath) else ""

    def openMapInBrowser(self):
        if not self.getFilePath():
            return
        webbrowser.open(Path(self.filePath).resolve().as_uri())
