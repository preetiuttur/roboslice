import os
from datetime import date
from flask import Flask, request, jsonify, send_from_directory
import qrcode

# ---------- Config ----------
COUNTER_FILE = "order_counter.txt"
QR_FOLDER = os.path.join("static", "qrs")

app = Flask(__name__, static_folder="static")

# Ensure QR folder exists
os.makedirs(QR_FOLDER, exist_ok=True)


# ---------- Daily counter logic ----------
def save_order_number(number, date_str):
    with open(COUNTER_FILE, "w") as f:
        f.write(f"{number},{date_str}")


def get_next_order_number():
    today = date.today().isoformat()

    if not os.path.exists(COUNTER_FILE):
        save_order_number(1, today)
        return 1

    with open(COUNTER_FILE, "r") as f:
        data = f.read().strip()

    if not data:
        save_order_number(1, today)
        return 1

    try:
        last_no, last_date = data.split(",")
    except:
        save_order_number(1, today)
        return 1

    if last_date != today:
        save_order_number(1, today)
        return 1

    next_no = int(last_no) + 1
    save_order_number(next_no, today)
    return next_no


# ---------- QR generation ----------
def generate_qr(order_number):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(str(order_number))  # only order number in QR
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    filename = f"order_{order_number}.png"
    path = os.path.join(QR_FOLDER, filename)
    img.save(path)

    print(f"[QR CREATED] {path}")
    # URL that frontend can access
    qr_url = f"/static/qrs/{filename}"
    return qr_url


# ---------- Routes ----------

# Serve the frontend page
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# API endpoint: create order and generate QR
@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json(force=True)

    customer_name = data.get("customerName", "").strip()
    pizza_type = data.get("pizzaType", "").strip()
    order_mode = data.get("orderMode", "Dine-In").strip()
    table_no = data.get("tableNo", "").strip()

    order_no = get_next_order_number()
    qr_url = generate_qr(order_no)

    # Simple log (you could write to DB or CSV here)
    print(f"[NEW ORDER] #{order_no} | {order_mode} | {pizza_type} | {customer_name} | Table: {table_no}")

    return jsonify({
        "orderNo": order_no,
        "qrUrl": qr_url,
        "customerName": customer_name,
        "pizzaType": pizza_type,
        "orderMode": order_mode,
        "tableNo": table_no
    }), 201


if __name__ == "__main__":
    # Install Flask if needed: pip install flask qrcode pillow
    app.run(host="0.0.0.0", port=5000, debug=True)
