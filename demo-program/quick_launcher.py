# =============================================================================
# QuickLauncher for SquareLine-generated LVGL interfaces (MicroPython)
# Target : Elecrow CrowPanel 5.0" ESP32-S3 HMI (800x480 RGB, capacitive touch)
# LVGL   : 8.3.7
# Author : Pieter Oosthuizen
# Date   : 2025-10-16
#
# Notes:
# - Ctrl+C rapidly on the serial REPL to interrupt a boot-looped main.py
# - This script avoids double display registration and prints useful diagnostics.
# =============================================================================

import sys
import lvgl as lv
import lv_utils
import tft_config
import gt911
from machine import Pin, I2C

# 1) Initialise LVGL first
lv.init()

# 2) Configure the display (CrowPanel helper)
try:
	tft = tft_config.config()
except Exception as e:
	print("Display configuration error:")
	sys.print_exception(e)
	raise

# 3) Ensure a default display is registered (some builds of tft_config already do this)
disp = lv.disp_get_default()
if disp is None:
	WIDTH, HEIGHT = 800, 480
	# ~80 lines worth of draw buffer is fine; increase if you want a bit more perf
	buf = bytearray(WIDTH * 80 * lv.color_t.__SIZE__)
	db = lv.disp_draw_buf_t(); db.init(buf, None, len(buf)//lv.color_t.__SIZE__)

	drv = lv.disp_drv_t(); drv.init()
	drv.draw_buf = db
	drv.flush_cb = tft.flush
	drv.hor_res = WIDTH
	drv.ver_res = HEIGHT
	disp = drv.register()  # becomes default

# Optional theme (some SquareLine exports expect a theme to be set)
try:
	theme = lv.theme_default_init(
		disp,
		lv.palette_main(lv.PALETTE.BLUE),
		lv.palette_main(lv.PALETTE.RED),
		False,
		lv.font_montserrat_14
	)
	disp.set_theme(theme)
except Exception as e:
	print("Theme init warning:")
	sys.print_exception(e)

# 4) Register touch (GT911 on I2C, SDA=19, SCL=20)
try:
	# NOTE: CrowPanel routing commonly uses I2C0 or I2C1; keep pins 19/20 as wired on the board
	i2c = I2C(1, scl=Pin(20), sda=Pin(19), freq=400000)
	tp = gt911.GT911(i2c, width=800, height=480)
	# Optional orientation:
	if hasattr(tp, "set_rotation"):
		tp.set_rotation(getattr(tp, "ROTATION_NORMAL", 0))

	indev_drv = lv.indev_drv_t(); indev_drv.init()
	indev_drv.disp = disp
	indev_drv.type = lv.INDEV_TYPE.POINTER
	indev_drv.read_cb = tp.lvgl_read  # requires gt911.py to provide this callable
	indev = indev_drv.register()
	print("Touch: GT911 registered")
except Exception as e:
	print("Touch Driver Failure:")
	sys.print_exception(e)

# 5) Start LVGL timers (animations, input, screen transitions)
if not lv_utils.event_loop.is_running():
	loop = lv_utils.event_loop()

# Diagnostics
try:
	print("LVGL:", lv.version_major(), lv.version_minor(), lv.version_patch())
except Exception as e:
	print("Diagnostic check warning:")
	sys.print_exception(e)

# 6) Import the SquareLine UI (ui.py must be on the device)
import ui
