from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests
import re

app = Flask(__name__)
# Enable CORS
CORS(app)

# ---------------------------------------------------------
# 📚 MASTER ANSWER KEY (GATE 2026 EE)
# ---------------------------------------------------------
ANSWER_KEY = {
    "2284829475": {"type": "MCQ", "ans": "B", "marks": 1, "neg": 0.33}, 
    "2284829476": {"type": "MCQ", "ans": "C", "marks": 1, "neg": 0.33}, 
    "2284829477": {"type": "MCQ", "ans": "D", "marks": 1, "neg": 0.33}, 
    "2284829478": {"type": "MCQ", "ans": "A", "marks": 1, "neg": 0.33}, 
    "2284829479": {"type": "MCQ", "ans": "C", "marks": 1, "neg": 0.33}, 
    "2284829480": {"type": "MCQ", "ans": "C", "marks": 2, "neg": 0.66}, 
    "2284829481": {"type": "MCQ", "ans": "D", "marks": 2, "neg": 0.66}, 
    "2284829482": {"type": "MCQ", "ans": "D", "marks": 2, "neg": 0.66}, 
    "2284829483": {"type": "MCQ", "ans": "B", "marks": 2, "neg": 0.66}, 
    "2284829484": {"type": "MCQ", "ans": "B", "marks": 2, "neg": 0.66}, 
    "2284829488": {"type": "MCQ", "ans": "B", "marks": 1, "neg": 0.33},
    "2284829505": {"type": "MSQ", "ans": ["A", "C", "D"], "marks": 1, "neg": 0}, 
    "2284829507": {"type": "NAT", "range": [750, 750], "marks": 2, "neg": 0}, 
    "2284829508": {"type": "NAT", "range": [32.3, 32.5], "marks": 1, "neg": 0},
    "2284829532": {"type": "NAT", "range": [118.4, 118.4], "marks": 2, "neg": 0}, 
    "2284829533": {"type": "NAT", "range": [0.29, 0.29], "marks": 2, "neg": 0}, 
}

@app.route('/api/analyze', methods=['POST'])
def analyze_marks():
    data = request.json
    url = data.get('url')

    if not url or "digialm.com" not in url:
        return jsonify({"error": "Please provide a valid GOAPS response sheet URL."}), 400

    try:
        # 1. Fetch the HTML from the provided URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html_content = response.text

        # 2. Check if the server blocked access (session expired)
        if "Access Denied" in html_content or "<table" not in html_content.lower():
            return jsonify({"error": "Access Denied. The URL session may have expired, or it requires login."}), 403

        # 3. Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        total_score = 0.0
        correct_count = 0
        incorrect_count = 0

        question_panels = soup.find_all('table', class_='menu-tbl')

        if not question_panels:
            return jsonify({"error": "Could not find question data on this page."}), 400

        for panel in question_panels:
            q_data = {}
            for row in panel.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) == 2:
                    key = cols[0].text.strip().replace(" :", "").strip()
                    val = cols[1].text.strip()
                    q_data[key] = val

            q_id = q_data.get('Question ID')
            status = q_data.get('Status')

            if status in ['Answered', 'Answered & Marked For Review']:
                
                if not q_id or q_id not in ANSWER_KEY:
                    continue 
                
                official = ANSWER_KEY[q_id]
                q_type = official['type']
                
                if q_type == "NAT":
                    user_ans_str = q_data.get('Given Answer', '')
                    try:
                        user_ans = float(user_ans_str)
                        min_val, max_val = official['range'][0], official['range'][1]
                        if min_val <= user_ans <= max_val:
                            total_score += official['marks']
                            correct_count += 1
                        else:
                            incorrect_count += 1 
                    except ValueError:
                        incorrect_count += 1

                elif q_type == "MSQ":
                    user_ans_raw = q_data.get('Chosen Option', '')
                    user_ans_list = [x.strip() for x in re.split(r',|;', user_ans_raw) if x.strip()]
                    if sorted(user_ans_list) == sorted(official['ans']):
                        total_score += official['marks']
                        correct_count += 1
                    else:
                        incorrect_count += 1

                elif q_type == "MCQ":
                    user_ans = q_data.get('Chosen Option', '')
                    if user_ans == official['ans']:
                        total_score += official['marks']
                        correct_count += 1
                    else:
                        total_score -= official['neg']
                        incorrect_count += 1

        return jsonify({
            "score": round(total_score, 2),
            "correct": correct_count,
            "incorrect": incorrect_count
        }), 200

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return jsonify({"error": "Failed to fetch the URL. The link might be broken or inaccessible."}), 500
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "An error occurred while parsing the data."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)