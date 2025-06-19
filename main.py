from flask import Flask, render_template, request, jsonify
import yfinance as yf
from datetime import datetime

app = Flask(__name__)

# Store the current options list in memory
options_data = []

def get_option_price(ticker, expiry_str, strike, option_type):
    try:
        stock = yf.Ticker(ticker)
        all_dates = stock.options
        if not all_dates:
            return {'ticker': ticker, 'error': 'No option data'}

        # Find the closest available expiry date
        target_date = datetime.strptime(expiry_str, "%Y-%m-%d")
        actual_expiry = min(all_dates, key=lambda d: abs(datetime.strptime(d, "%Y-%m-%d") - target_date))

        opt_chain = stock.option_chain(actual_expiry)
        chain = opt_chain.calls if option_type == 'call' else opt_chain.puts

        # Find the strike price closest to the target
        chain['strike_diff'] = abs(chain['strike'] - strike)
        best_row = chain.loc[chain['strike_diff'].idxmin()]

        return {
            'ticker': ticker.upper(),
            'type': option_type,
            'actual_expiry': actual_expiry,
            'actual_strike': float(best_row['strike']),
            'last': float(best_row['lastPrice']),
            'bid': float(best_row['bid']),
            'ask': float(best_row['ask'])
        }
    except Exception as e:
        return {'ticker': ticker.upper(), 'error': str(e)}

@app.route('/', methods=['GET', 'POST'])
def index():
    global options_data
    if request.method == 'POST':
        # Read multiple tickers
        tickers = request.form.getlist('ticker')
        types = request.form.getlist('type')
        expiries = request.form.getlist('expiry')
        strikes = request.form.getlist('strike')

        new_data = []
        for t, ty, ex, st in zip(tickers, types, expiries, strikes):
            if t and ty and ex and st:
                try:
                    new_data.append({
                        'ticker': t.strip(),
                        'type': ty.strip().lower(),
                        'expiry': ex.strip(),
                        'strike': float(st)
                    })
                except ValueError:
                    pass  # skip malformed rows

        options_data = new_data

    return render_template('index.html')

@app.route('/api/options')
def api_options():
    results = []
    for opt in options_data:
        res = get_option_price(opt['ticker'], opt['expiry'], opt['strike'], opt['type'])
        results.append(res)
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
