import folium
import webbrowser
import tempfile
import os
from sty import fg
'''
A class for plotting guesses on a map relative to a "correct" guess
'''


class Map():

    def __init__(self, latitude, longitude, zoomLevel=10):
        # TODO: we might want to center the map about the center of all points instead of the correct answer
        self.map = folium.Map(location=[latitude, longitude],
                              zoom_start=zoomLevel)
        self.filePath = ''

    def addPoint(self, latitude, longitude, user, distance, link, color):
        description = '''
        {username}

        {distance}m away

        {link}
        '''
        folium.Marker(location=[latitude, longitude],
                      popup=description.format(username=user,
                                               distance=distance,
                                               link=link),
                      icon=folium.Icon(color=color)).add_to(self.map)

    def saveMap(self):
        tempFile = tempfile.NamedTemporaryFile(suffix='.html', delete=False)
        try:
            self.map.save(tempFile)
        except Exception as e:
            print(f'{fg.red}Could not save map: {e} {fg.rs}')
            return
        self.filePath = tempFile.name

    def getFilePath(self):
        return self.filePath

    def openMapInBrowser(self):
        if not self.filePath:
            return
        webbrowser.open(f'file://{os.path.realpath(self.filePath)}')
