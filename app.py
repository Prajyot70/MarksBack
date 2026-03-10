from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
# Enable CORS so your frontend can communicate with this backend from any domain
CORS(app)

# ---------------------------------------------------------
# 📚 MASTER ANSWER KEY (GATE 2026 EE)
# You must map all the unique 10-digit Question IDs to their correct answers.
# I have populated a few examples based on the official documents you provided.
# ---------------------------------------------------------
ANSWER_KEY = {
    # --- General Aptitude (GA) ---
    # 1 Mark each, -1/3 Negative
    "2284829475": {"type": "MCQ", "ans": "B", "marks": 1, "neg": 0.33}, 
    "2284829476": {"type": "MCQ", "ans": "C", "marks": 1, "neg": 0.33}, 
    "2284829477": {"type": "MCQ", "ans": "D", "marks": 1, "neg": 0.33}, 
    "2284829478": {"type": "MCQ", "ans": "A", "marks": 1, "neg": 0.33}, 
    "2284829479": {"type": "MCQ", "ans": "C", "marks": 1, "neg": 0.33}, 
    
    # 2 Marks each, -2/3 Negative
    "2284829480": {"type": "MCQ", "ans": "C", "marks": 2, "neg": 0.66}, 
    "2284829481": {"type": "MCQ", "ans": "D", "marks": 2, "neg": 0.66}, 
    "2284829482": {"type": "MCQ", "ans": "D", "marks": 2, "neg": 0.66}, 
    "2284829483": {"type": "MCQ", "ans": "B", "marks": 2, "neg": 0.66}, 
    "2284829484": {"type": "MCQ", "ans": "B", "marks": 2, "neg": 0.66}, 

    # --- Electrical Engineering (EE) Examples ---
    # MCQ Example
    "2284829488": {"type": "MCQ", "ans": "B", "marks": 1, "neg": 0.33},
    
    # MSQ Example (Multiple Select Question)
    "2284829505": {"type": "MSQ", "ans": ["A", "C", "D"], "marks": 1, "neg": 0}, 
    
    # NAT Example (Numerical Answer Type)
    "2284829507": {"type": "NAT", "range": [750, 750], "marks": 2, "neg": 0}, 
    "2284829508": {"type": "NAT", "range": [32.3, 32.5], "marks": 1, "neg": 0},
    "2284829532": {"type": "NAT", "range": [118.4, 118.4], "marks": 2, "neg": 0}, 
    "2284829533": {"type": "NAT", "range": [0.29, 0.29], "marks": 2, "neg": 0}, 
}

@app.route('/api/analyze', methods=['POST'])
def analyze_marks():
    data = request.json
    html_content = data.get('html')

    # Basic validation to ensure the user pasted HTML
    if not html_content or "<table" not in html_content.lower():
        return jsonify({"error": "Invalid HTML provided. Please paste the full source code (Ctrl+U) of the response sheet."}), 400

    try:
        # Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        total_score = 0.0
        correct_count = 0
        incorrect_count = 0

        # Extract Data from TCS iON 'menu-tbl' structure
        question_panels = soup.find_all('table', class_='menu-tbl')

        if not question_panels:
            return jsonify({"error": "Could not find question data. Ensure this is a valid GATE response sheet."}), 400

        for panel in question_panels:
            q_data = {}
            # Loop through table rows to extract key-value pairs
            for row in panel.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) == 2:
                    # Clean up keys (remove trailing colons and extra spaces)
                    key = cols[0].text.strip().replace(" :", "").strip()
                    val = cols[1].text.strip()
                    q_data[key] = val

            q_id = q_data.get('Question ID')
            status = q_data.get('Status')

            # Process only Attempted Questions
            if status in ['Answered', 'Answered & Marked For Review']:
                
                # Skip if we haven't mapped this ID in our master key yet
                if not q_id or q_id not in ANSWER_KEY:
                    print(f"Warning: Question ID {q_id} is missing from the ANSWER_KEY database.")
                    continue 
                
                official = ANSWER_KEY[q_id]
                q_type = official['type']
                
                # --- EVALUATION LOGIC ---
                
                # 1. Numerical Answer Type (NAT)
                if q_type == "NAT":
                    user_ans_str = q_data.get('Given Answer', '')
                    try:
                        user_ans = float(user_ans_str)
                        min_val, max_val = official['range'][0], official['range'][1]
                        
                        # Check if user answer falls within the official range
                        if min_val <= user_ans <= max_val:
                            total_score += official['marks']
                            correct_count += 1
                        else:
                            incorrect_count += 1 # NAT questions have no negative marking
                    except ValueError:
                        incorrect_count += 1

                # 2. Multiple Select Question (MSQ)
                elif q_type == "MSQ":
                    user_ans_raw = q_data.get('Chosen Option', '')
                    # Clean and split the comma-separated options (e.g., "A, C" -> ["A", "C"])
                    user_ans_list = [x.strip() for x in re.split(r',|;', user_ans_raw) if x.strip()]
                    
                    # MSQ requires an EXACT match of all options. No partial marking, no negative marking.
                    if sorted(user_ans_list) == sorted(official['ans']):
                        total_score += official['marks']
                        correct_count += 1
                    else:
                        incorrect_count += 1

                # 3. Multiple Choice Question (MCQ)
                elif q_type == "MCQ":
                    user_ans = q_data.get('Chosen Option', '')
                    
                    if user_ans == official['ans']:
                        total_score += official['marks']
                        correct_count += 1
                    else:
                        # Deduct negative marks for incorrect MCQs
                        total_score -= official['neg']
                        incorrect_count += 1

        return jsonify({
            "score": round(total_score, 2),
            "correct": correct_count,
            "incorrect": incorrect_count
        }), 200

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "An error occurred while parsing the HTML. Please ensure the code is copied completely."}), 500

if __name__ == '__main__':
    # Run the server locally on port 5000
    app.run(debug=True, port=5000)