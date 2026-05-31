import json
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path

try:
    import serial
except ImportError:  # Allows UI demo without hardware libraries installed.
    serial = None


STATE_FILE = Path("inventory_state.json")


@dataclass
class Product:
    code: str
    name: str
    price: int
    slot: int
    turns: int


PRODUCTS = [
    Product("1", "Sanitary Pads", 30, 1, 2),
    Product("2", "Band-Aids", 20, 2, 1),
    Product("3", "Antiseptic", 45, 3, 3),
    Product("4", "Gloves", 25, 4, 2),
    Product("5", "Sanitizer", 35, 5, 2),
    Product("6", "Antacid", 15, 6, 1),
    Product("7", "Digestive Tablet", 15, 7, 1),
    Product("8", "Mask", 10, 8, 1),
    Product("9", "Cotton Roll", 25, 9, 2),
]


class VendingApp:
    def __init__(self, root, serial_port=None):
        self.root = root
        self.root.title("Medi Smart Vending")
        self.selected = tk.StringVar(value="")
        self.status = tk.StringVar(value="Select a product code")
        self.inventory = self.load_inventory()
        self.serial_port = serial_port

        tk.Label(root, text="Medi Smart", font=("Arial", 24, "bold")).pack(pady=12)
        tk.Label(root, textvariable=self.status, font=("Arial", 14)).pack(pady=8)

        grid = tk.Frame(root)
        grid.pack()
        for idx, product in enumerate(PRODUCTS):
            text = f"{product.code}. {product.name}\nRs.{product.price} | Stock {self.inventory[product.code]}"
            tk.Button(grid, text=text, width=22, height=3, command=lambda p=product: self.choose(p)).grid(
                row=idx // 3, column=idx % 3, padx=8, pady=8
            )

        tk.Button(root, text="Verify Payment and Dispense", command=self.dispense, height=2).pack(pady=10)
        tk.Button(root, text="Reset Inventory", command=self.reset_inventory).pack()

    def load_inventory(self):
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {product.code: 10 for product in PRODUCTS}

    def save_inventory(self):
        STATE_FILE.write_text(json.dumps(self.inventory, indent=2))

    def choose(self, product):
        self.selected.set(product.code)
        self.status.set(f"Selected {product.name}. Collect Rs.{product.price} payment.")

    def send_motor_command(self, product):
        command = f"DISPENSE:{product.slot}:{product.turns}\n"
        if self.serial_port:
            self.serial_port.write(command.encode("ascii"))
        print(command.strip())

    def dispense(self):
        code = self.selected.get()
        product = next((item for item in PRODUCTS if item.code == code), None)
        if not product:
            self.status.set("Select a product before dispensing")
            return
        if self.inventory[code] <= 0:
            self.status.set(f"{product.name} is out of stock")
            return

        payment_verified = True
        if payment_verified:
            self.send_motor_command(product)
            self.inventory[code] -= 1
            self.save_inventory()
            self.status.set(f"Dispensed {product.name}. Remaining: {self.inventory[code]}")

    def reset_inventory(self):
        self.inventory = {product.code: 10 for product in PRODUCTS}
        self.save_inventory()
        self.status.set("Inventory reset complete")


def main():
    serial_port = None
    if serial:
        # Update COM port or Linux device path for real hardware.
        # serial_port = serial.Serial("COM3", 9600, timeout=2)
        pass
    root = tk.Tk()
    VendingApp(root, serial_port)
    root.mainloop()


if __name__ == "__main__":
    main()
