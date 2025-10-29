from flask import Flask, render_template, jsonify
import pandas as pd

app = Flask(__name__)

# 🔗 Use your correct published Google Sheets CSV link (must end with ?output=csv)
EXCEL_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTPIR5j2TyzJAorJsGX9reIhOXQKrTfyDbbv2GreXPDf2nWcBCddhoedW93yEaK1S93imugCke-dRD_/pub?output=csv"

def load_data():
    df = pd.read_csv(EXCEL_URL)
    # Normalize headers
    df.columns = df.columns.str.strip().str.upper()
    df.fillna("NO DATA", inplace=True)
    return df

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/month/<month>')
def get_month_data(month):
    try:
        df = load_data()

        if 'MONTH' not in df.columns:
            return jsonify({"error": "Google Sheet missing required column: MONTH"})

        # Find matching row (case-insensitive)
        mask = df['MONTH'].astype(str).str.strip().str.upper() == month.strip().upper()
        month_rows = df[mask]

        if month_rows.empty:
            return jsonify({"error": f"No data found for {month}"})

        row = month_rows.iloc[0].to_dict()

        # Get numeric fields safely
        days_in_month = int(row.get("NO. OF DAYS IN MONTH", 0))
        days_coming = int(row.get("NO. OF DAYS COMING", 0))

        # ✅ Use "DAYS ABSENT" from sheet (no auto calculation)
        days_absent = row.get("DAYS ABSENT", "NO DATA")

        # Auto-calculate only the total bill
        total_bill = days_coming * 50  # ₹50/day

        result = {
            "Month": row.get("MONTH", month),
            "Paid": row.get("PAID", "NO DATA"),
            "Days in Month": days_in_month,
            "Days Coming": days_coming,
            "Days Absent": days_absent,
            "Amount": f"{total_bill:.2f}",
            "Payment Mode": row.get("PAYMENT MODE", "NO DATA")
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Error loading data: {e}"})


# 💰 Auto Annual Spend (SUM of all months)
@app.route('/annual')
def get_annual_spend():
    try:
        df = load_data()

        # Ensure required column exists
        if 'NO. OF DAYS COMING' not in df.columns:
            return jsonify({"error": "Missing column: NO. OF DAYS COMING"})

        # Convert to numbers and fill invalid with 0
        df["NO. OF DAYS COMING"] = pd.to_numeric(df["NO. OF DAYS COMING"], errors='coerce').fillna(0)

        # 💡 Total of all months = sum of (days coming × ₹50)
        total_annual_spend = (df["NO. OF DAYS COMING"] * 50).sum()

        return jsonify({
            "Total Annual Spend": f"{total_annual_spend:.2f}"
        })

    except Exception as e:
        return jsonify({"error": f"Error calculating annual spend: {e}"})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
