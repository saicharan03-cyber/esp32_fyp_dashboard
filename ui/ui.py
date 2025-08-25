import flet as ft
import requests
import threading
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64

# --- Utils ---
def get_blank_base64_image(width=750, height=400):
    plt.figure(figsize=(width / 100, height / 100))
    plt.axis("off")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', pad_inches=0)
    plt.close()  # ✅ prevent memory leak
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

# --- Global States ---
hr_text = ft.Text("Heart Rate: -- bpm", size=16)
spo2_text = ft.Text("SpO₂: -- %", size=16)
motion_text = ft.Text("Motion: --", size=16)
seizure_text = ft.Text("Seizure: --", size=16)
plot_data = {"x": [], "y": []}
plot_image = ft.Image(src_base64=get_blank_base64_image(), width=750, height=400)

selected_param = ft.Ref[ft.RadioGroup]()  # Y-parameter for real-time
selected_csv_column = ft.Ref[ft.RadioGroup]()  # Column for CSV plotting

param_labels = {"hr": "Heart Rate", "spo2": "SpO₂", "motion": "Motion"}
monitoring_active = False
csv_df = None
file_picker = None

# --- Button Handlers ---
def on_refresh(e):
    try:
        r = requests.get("https://esp32-fyp-dashboard-ru6l.vercel.app/latest")
        data = r.json()
        hr_text.value = f"Heart Rate: {data.get('heart_rate', '--')} bpm"
        spo2_text.value = f"SpO₂: {data.get('spo2', '--')} %"
        motion_text.value = f"Motion: {data.get('motion', '--')}"
        seizure_text.value = f"Seizure: {data.get('seizure', '--')}"
        e.page.update()
    except Exception as ex:
        print("❌ Refresh error:", ex)

def on_start(e):
    global monitoring_active
    monitoring_active = True
    print("▶ Monitoring Started")

def on_stop(e):
    global monitoring_active
    monitoring_active = False
    print("⏹ Monitoring Stopped")

def on_clear(e):
    plot_data["x"].clear()
    plot_data["y"].clear()
    plot_image.src_base64 = get_blank_base64_image()
    e.page.update()
    print("🧹 Plot cleared")

def on_save(e):
    try:
        with open("saved_plot.png", "wb") as f:
            f.write(base64.b64decode(plot_image.src_base64))
        print("💾 Plot saved")
        e.page.snack_bar = ft.SnackBar(ft.Text("Plot saved as saved_plot.png"), open=True)
        e.page.update()
    except Exception as ex:
        print("❌ Save failed:", ex)

def on_upload_csv(e: ft.FilePickerResultEvent):
    global csv_df
    if e.files:
        file_path = e.files[0].path
        try:
            csv_df = pd.read_csv(file_path)
            print(f"📂 CSV uploaded: {file_path}")
        except Exception as err:
            print("❌ Failed to load CSV:", err)

def on_plot_csv_column(e):
    global csv_df
    if csv_df is not None and selected_csv_column.current.value:
        col_key = selected_csv_column.current.value
        csv_col_map = {"hr": "hr", "spo2": "spo2", "motion": "motion"}
        col = csv_col_map.get(col_key)

        if col in csv_df.columns:
            plt.clf()
            plt.plot(csv_df[col])
            plt.title(f"{param_labels.get(col_key)} Plot")
            plt.xlabel("Index")
            plt.ylabel(param_labels.get(col_key))

            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            plt.close()  # ✅ prevent memory leak
            buf.seek(0)
            plot_image.src_base64 = base64.b64encode(buf.read()).decode("utf-8")
            e.page.update()
            print(f"📊 Plotted CSV column: {col}")
        else:
            print("⚠ Column not found in CSV:", col)
    else:
        print("⚠ CSV not uploaded or no column selected")

# --- Background Thread ---
def fetch_data(layout):
    counter = 0
    while True:
        try:
            if not monitoring_active:
                continue

            r = requests.get("http://127.0.0.1:8000/latest")
            data = r.json()

            hr = data.get("heart_rate", "--")
            spo2 = data.get("spo2", "--")
            motion = data.get("motion", "--")
            seizure = data.get("seizure", "--")

            hr_text.value = f"Heart Rate: {hr} bpm"
            spo2_text.value = f"SpO₂: {spo2} %"
            motion_text.value = f"Motion: {motion}"
            seizure_text.value = f"Seizure: {seizure}"

            y_param = selected_param.current.value
            y_val = 0
            if y_param == "hr" and isinstance(hr, int):
                y_val = hr
            elif y_param == "spo2" and isinstance(spo2, int):
                y_val = spo2
            elif y_param == "motion":
                y_val = 1 if motion == "jerking" else 0

            plot_data["x"].append(counter)
            plot_data["y"].append(y_val)
            counter += 1

            if len(plot_data["x"]) > 50:
                plot_data["x"].pop(0)
                plot_data["y"].pop(0)

            plt.clf()
            plt.plot(plot_data["x"], plot_data["y"])
            plt.title(f"Real-Time {param_labels.get(y_param)} Plot")
            plt.xlabel("Time")
            plt.ylabel(param_labels.get(y_param))

            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            plt.close()  # ✅ prevent memory leak
            buf.seek(0)
            plot_image.src_base64 = base64.b64encode(buf.read()).decode("utf-8")

            layout.update()

        except Exception as e:
            print("❌ Fetch error:", e)

# --- Main UI ---
def main(page: ft.Page):
    global file_picker
    page.title = "ESP32 Seizure Monitoring Dashboard"
    page.scroll = True
    page.padding = 20

    title = ft.Text("ESP32 Seizure Monitoring Dashboard", size=28, weight="bold")
    title_row = ft.Row([title], alignment=ft.MainAxisAlignment.CENTER)

    # File Picker
    file_picker = ft.FilePicker(on_result=on_upload_csv)
    page.overlay.append(file_picker)

    # Y-Parameter Selection
    y_param_section = ft.Container(
        content=ft.Column([
            ft.Text("📈 Y-Parameter Selection", weight="bold"),
            ft.RadioGroup(
                ref=selected_param,
                value="hr",
                content=ft.Column([
                    ft.Radio(value="hr", label="Heart Rate"),
                    ft.Radio(value="spo2", label="SpO₂"),
                    ft.Radio(value="motion", label="Motion"),
                ])
            ),
            ft.ElevatedButton("Refresh", on_click=on_refresh),
        ]),
        padding=10,
        border=ft.border.all(1),
        width=230,
        height=250
    )

    # Real-Time Monitoring
    monitoring_section = ft.Container(
        content=ft.Column([
            ft.Text("🩺 Real-Time Monitoring", weight="bold"),
            hr_text,
            spo2_text,
            motion_text,
            seizure_text,
            ft.Row([
                ft.ElevatedButton("▶ Start", on_click=on_start),
                ft.ElevatedButton("⏹ Stop", on_click=on_stop),
            ], alignment=ft.MainAxisAlignment.CENTER)
        ]),
        padding=10,
        border=ft.border.all(1),
        width=230,
        height=250
    )

    # Data Analysis Section
    data_analysis_section = ft.Container(
        content=ft.Column([
            ft.Text("📊 Data Analysis", weight="bold"),
            ft.ElevatedButton("Upload CSV", on_click=lambda e: file_picker.pick_files(allow_multiple=False, allowed_extensions=["csv"])),
            ft.RadioGroup(
                ref=selected_csv_column,
                value="hr",
                content=ft.Column([
                    ft.Radio(value="hr", label="Heart Rate"),
                    ft.Radio(value="spo2", label="SpO₂"),
                    ft.Radio(value="motion", label="Motion")
                ])
            ),
            ft.Row([
                ft.ElevatedButton("Plot", on_click=on_plot_csv_column),
                ft.ElevatedButton("Clear", on_click=on_clear),
                ft.ElevatedButton("Save", on_click=on_save),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
        ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START),
        padding=10,
        border=ft.border.all(1),
        width=230,
        height=250
    )

    # Layout
    cards_row = ft.Row(
        controls=[y_param_section, monitoring_section, data_analysis_section],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        spacing=30,
        width=750
    )

    plot_container = ft.Container(
        content=plot_image,
        padding=10,
        border=ft.border.all(1),
        width=750,
        alignment=ft.alignment.center
    )

    layout = ft.Column(
        [title_row, cards_row, plot_container],
        spacing=30,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    page.add(layout)

    # Background Thread
    threading.Thread(target=fetch_data, args=(layout,), daemon=True).start()

# Run the app
ft.app(target=main)
