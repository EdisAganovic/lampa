import asyncio
import threading
import customtkinter as ctk
from CTkColorPicker import AskColor
from control_lamp import LampController, load_config, save_config

class LampGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MELK-OA10 Controller")
        self.geometry("500x750")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Load Configuration
        config = load_config()
        self.address = config.get("default_address")
        self.controller = LampController(self.address)
        
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_async_loop, daemon=True)
        self.thread.start()

        self.setup_ui()

    def start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_async(self, coro):
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def setup_ui(self):
        # 1. Scanner & Connection Header
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.pack(pady=10, padx=20, fill="x")

        self.scan_label = ctk.CTkLabel(self.top_frame, text="Bluetooth Device Setup", font=("Roboto", 14, "bold"))
        self.scan_label.pack(pady=5)

        self.addr_var = ctk.StringVar(value=self.address if self.address else "No device selected")
        self.addr_entry = ctk.CTkEntry(self.top_frame, textvariable=self.addr_var, width=250)
        self.addr_entry.pack(pady=5, padx=10, side="left", expand=True)

        self.scan_btn = ctk.CTkButton(self.top_frame, text="🔍 Scan", width=80, command=self.start_scan)
        self.scan_btn.pack(pady=5, padx=5, side="left")

        self.connect_btn = ctk.CTkButton(self, text="⚡ Connect to Lamp", font=("Roboto", 16, "bold"), height=45,
                                         fg_color="#27AE60", hover_color="#2ECC71", command=self.connect_lamp)
        self.connect_btn.pack(pady=10, padx=20, fill="x")

        self.status_label = ctk.CTkLabel(self, text="Status: Ready", text_color="#BDC3C7")
        self.status_label.pack(pady=5)

        # 2. Main Controls
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Power
        self.pwr_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.pwr_frame.pack(pady=10)
        self.on_btn = ctk.CTkButton(self.pwr_frame, text="POWER ON", fg_color="#2E7D32", command=lambda: self.run_async(self.controller.power_on()))
        self.on_btn.pack(side="left", padx=10)
        self.off_btn = ctk.CTkButton(self.pwr_frame, text="POWER OFF", fg_color="#C62828", command=lambda: self.run_async(self.controller.power_off()))
        self.off_btn.pack(side="left", padx=10)

        # AutoPlay
        self.autoplay_btn = ctk.CTkButton(self.control_frame, text="✨ Start AutoPlay Mode", font=("Roboto", 16, "bold"), 
                                         height=50, fg_color="#6A1B9A", hover_color="#8E24AA", command=self.start_autoplay)
        self.autoplay_btn.pack(pady=15, padx=20, fill="x")

        # Sliders
        ctk.CTkLabel(self.control_frame, text="Effect Speed").pack()
        self.speed_slider = ctk.CTkSlider(self.control_frame, from_=0, to=100, command=self.update_speed)
        self.speed_slider.set(50)
        self.speed_slider.pack(fill="x", pady=5, padx=30)

        ctk.CTkLabel(self.control_frame, text="Brightness").pack()
        self.bright_slider = ctk.CTkSlider(self.control_frame, from_=0, to=100, command=self.update_brightness)
        self.bright_slider.set(100)
        self.bright_slider.pack(fill="x", pady=5, padx=30)

        # Palette
        ctk.CTkLabel(self.control_frame, text="Quick Palette").pack(pady=(15, 0))
        self.palette_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.palette_frame.pack(pady=5)
        
        colors = ["#FF0000", "#FF8C00", "#FFD700", "#FFFF00", "#FFF4E0", "#FFFFFF", "#00FF00", "#0000FF"]
        for color in colors:
            btn = ctk.CTkButton(self.palette_frame, text="", width=35, height=35, fg_color=color, hover_color=color, corner_radius=18,
                               command=lambda c=color: self.set_hex_color(c))
            btn.pack(side="left", padx=3)

        self.picker_btn = ctk.CTkButton(self.control_frame, text="🎨 Custom Color Picker", command=self.pick_color)
        self.picker_btn.pack(pady=15, padx=30, fill="x")

    def start_scan(self):
        self.scan_btn.configure(text="Scanning...", state="disabled")
        self.status_label.configure(text="Searching for lamps...", text_color="#3498DB")
        
        async def do_scan():
            print("GUI: Starting background scan...")
            found = await self.controller.scan_for_lamps()
            print(f"GUI: Scan finished. Found {len(found)} devices.")
            
            if found:
                first = found[0]
                addr = first['address']
                name = first['name']
                print(f"GUI: Auto-selecting {name} ({addr})")
                
                # Update UI in main thread
                self.after(0, lambda: self.addr_var.set(addr))
                self.after(0, lambda: self.status_label.configure(text=f"Found: {name}", text_color="#F1C40F"))
                
                # Persist
                save_config(addr)
                self.controller.address = addr
            else:
                self.after(0, lambda: self.status_label.configure(text="No lamps found nearby", text_color="#E74C3C"))
            
            # Reset button state
            self.after(0, lambda: self.scan_btn.configure(text="🔍 Scan Again", state="normal"))
            
        self.run_async(do_scan())

    def connect_lamp(self):
        target = self.addr_var.get()
        if not target or ":" not in target:
            self.status_label.configure(text="Please enter a valid MAC address", text_color="#E74C3C")
            return

        self.controller.address = target
        save_config(target)
        
        self.connect_btn.configure(text="Connecting...", state="disabled")
        async def do_connect():
            success = await self.controller.connect()
            if success:
                self.after(0, lambda: self.connect_btn.configure(text="Connected (Click to sync)", state="normal", fg_color="#34495E"))
                self.after(0, lambda: self.status_label.configure(text="Connected Successfully", text_color="#2ECC71"))
                self.after(200, self.start_autoplay)
            else:
                self.after(0, lambda: self.connect_btn.configure(text="Retry Connection", state="normal", fg_color="#C0392B"))
                self.after(0, lambda: self.status_label.configure(text="Connection Failed", text_color="#E74C3C"))
        self.run_async(do_connect())

    def start_autoplay(self):
        if not self.controller.client or not self.controller.client.is_connected: return
        speed = int(self.speed_slider.get())
        self.run_async(self.controller.set_mode(0x00, speed=speed))

    def set_hex_color(self, hex_color):
        if not self.controller.client or not self.controller.client.is_connected: return
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        self.run_async(self.controller.set_color(r, g, b))

    def pick_color(self):
        color = AskColor()
        color_hex = color.get()
        if color_hex:
            self.set_hex_color(color_hex)

    def update_brightness(self, val):
        if not self.controller.client or not self.controller.client.is_connected: return
        if hasattr(self, "_bright_debounce_id"):
            self.after_cancel(self._bright_debounce_id)
        self._bright_debounce_id = self.after(80, lambda: self.run_async(self.controller.set_brightness(int(val), response=False)))

    def update_speed(self, val):
        if not self.controller.client or not self.controller.client.is_connected: return
        if hasattr(self, "_speed_debounce_id"):
            self.after_cancel(self._speed_debounce_id)
        self._speed_debounce_id = self.after(100, lambda: self.run_async(self.controller.set_speed(int(val), response=True)))

if __name__ == "__main__":
    app = LampGUI()
    app.mainloop()
