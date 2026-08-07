# ui/main_window.py

from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget

from ui.canvas.grid_canvas import GridCanvas


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GridForge")
        self.setGeometry(100, 100, 900, 700)

        self.canvas = GridCanvas()

        self.run_button = QPushButton("Run Load Flow")
        self.run_button.clicked.connect(self.run_simulation)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.run_button)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

    def run_simulation(self):
        results = self.canvas.controller.run_simulation()

        print("\n--- RESULTS ---")
        for r in results:
            print(r)
