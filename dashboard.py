import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QLabel, QMessageBox

# self.fuel_usage_entry.setText(str)  # Sets text in text box, could be useful for info imports
# textbox.text() fetches current text in box, textbox.setText(str) changes text in text box
# No need for QLineEdit.returnPressed.connect(func) for now


class Window(QMainWindow):
    def closeEvent(self, event):
        # This is where to write the code for saving presets if autosave is desired
        event.accept()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard")
        self.setGeometry(100, 100, 400, 370)

        # Todo: margin of error module
        
        # Fuel used per lap
        self.label_fuel_usage_entry = QLabel("Fuel Used Per Lap:", self)
        self.label_fuel_usage_entry.setGeometry(20, 10, 200, 30)
        self.fuel_usage_entry = QLineEdit(self)
        self.fuel_usage_entry.setGeometry(20, 40, 200, 30)

        # Refueling Rate
        self.label_refueling_rate_entry = QLabel("Seconds Per Liter Refueled:", self)
        self.label_refueling_rate_entry.setGeometry(20, 80, 200, 30)
        self.refueling_rate_entry = QLineEdit(self)
        self.refueling_rate_entry.setGeometry(20, 110, 200, 30)

        # Tire Swap Length
        self.label_tire_swap_length_entry = QLabel("Tire Swap Length (s):", self)
        self.label_tire_swap_length_entry.setGeometry(20, 150, 200, 30)
        self.tire_swap_length_entry = QLineEdit(self)
        self.tire_swap_length_entry.setGeometry(20, 180, 200, 30)

        # Base Time Lost on Pit Stop
        self.label_pit_stop_entry = QLabel("Base Time Lost on Pit Stop (s):", self)
        self.label_pit_stop_entry.setGeometry(20, 220, 200, 30)
        self.pit_stop_entry = QLineEdit(self)
        self.pit_stop_entry.setGeometry(20, 250, 200, 30)

        # Assumed Time Lost Per Overtake, unused for now
        self.label_overtake_entry = QLabel("Assumed Time Lost Per Overtake (s):", self)
        self.label_overtake_entry.setGeometry(20, 290, 210, 30)
        self.overtake_entry = QLineEdit(self)
        self.overtake_entry.setGeometry(20, 320, 200, 30)

        # Gap to next car
        self.label_car_gap = QLabel("Gap to Next Car (s):", self)
        self.label_car_gap.setGeometry(260, 290, 200, 30)
        self.car_gap_entry = QLineEdit(self)
        self.car_gap_entry.setGeometry(275, 320, 100, 30)

        
        # Safety Car
        self.safety_car_button = QPushButton("Safety Car", self)
        self.safety_car_button.setGeometry(275, 40, 100, 30)
        self.safety_car_button.clicked.connect(self.calculate_safety_car_strat)
        
        # FYC
        self.fyc_button = QPushButton("FYC", self)
        self.fyc_button.setGeometry(275, 110, 100, 30)
        self.fyc_button.clicked.connect(self.calculate_fyc_strat)

    def calculate_safety_car_strat(self):  # Refactor to support margin of error, FCY
        # Maximize liters refueled/tire change without time loss exceeding gap to next car
        try:
            gap = float(self.car_gap_entry.text())
            base_timeloss = float(self.pit_stop_entry.text())
            loss_per_liter = float(self.refueling_rate_entry.text())
            tire_change_loss = float(self.tire_swap_length_entry.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Inputs must be numeric.", QMessageBox.Ok)
            return
        
        if base_timeloss + loss_per_liter > gap:
            strategy = "Do not pit"
        else:
            current_refuel = 1
            while base_timeloss + (current_refuel + 1) * loss_per_liter < gap:
                current_refuel += 1

            strategy = f"Pit and refuel {current_refuel} liters"
            if base_timeloss + tire_change_loss < gap:
                strategy += f" and change tires"
        
        QMessageBox.information(self, "Safety Car Strategy", strategy, QMessageBox.Ok)


    def calculate_fyc_strat(self):
        # Maximize liters refueled/tire change without time loss exceeding gap to next car
        pass



App = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(App.exec_())