from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import pyqtgraph as pg


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create a pyqtgraph plot item
        self.plot = pg.PlotWidget()

        # Create an infinite line and add it to the plot
        self.vLine = pg.InfiniteLine(angle=90, movable=True)
        self.plot.addItem(self.vLine, ignoreBounds=True)

        # Connect the signal for the line's position change to a slot
        self.vLine.sigPositionChanged.connect(self.onVLineMoved)

        # Set up the layout
        centralWidget = QWidget()
        layout = QVBoxLayout(centralWidget)
        layout.addWidget(self.plot)
        self.setCentralWidget(centralWidget)

    def onVLineMoved(self):
        # Get the x position of the vertical line
        xPos = self.vLine.value()
        print(f"Selected x position: {xPos}")
    def update_regions(self):
        # Update the position of all region items when one is moved
        for region_item in self.region_items:
            region_item.setRegion(self.region_items[0].getRegion())

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
