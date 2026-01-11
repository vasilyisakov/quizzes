#!/usr/bin/env python3
"""
Quiz Converter with Marked Answers
Reads correct answers marked with * or ✓ in the Word document

Format in Word:
A. wrong answer
B. *correct answer*  ← marked with asterisks
C. wrong answer
D. wrong answer

OR:

A. wrong answer
B. ✓ correct answer  ← marked with checkmark
C. wrong answer
D. wrong answer
"""

import sys
import re
import subprocess
from pathlib import Path
import json

def extract_text_from_docx(docx_path):
    """Extract text from Word document using pandoc"""
    try:
        result = subprocess.run(
            ['pandoc', docx_path, '-o', '-', '--to=plain'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error extracting text from {docx_path}: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: pandoc not found")
        sys.exit(1)

def parse_quiz_with_marked_answers(text):
    """Parse quiz questions and detect marked correct answers"""
    questions = []
    parts = re.split(r'\n\d+\s*/\s*\d+\s*\n', text)
    
    for part in parts:
        if not part.strip():
            continue
            
        question_match = re.search(r'^(.*?)\nA\.', part, re.DOTALL)
        if not question_match:
            continue
        
        question_text = question_match.group(1).strip()
        question_text = re.sub(r'_{2,}', '___________', question_text)
        
        # Extract options and detect correct answer
        options = []
        correct_answer = 0  # Default to A if not found
        
        option_lines = []
        for letter in ['A', 'B', 'C', 'D']:
            pattern = f'{letter}\\.\\s*\\n(.*?)(?=\\n[A-D]\\.|Hint|$)'
            match = re.search(pattern, part, re.DOTALL)
            if match:
                option_text = match.group(1).strip()
                
                # Check for markers
                is_correct = False
                
                # Check for asterisks: *correct answer*
                if option_text.startswith('*') and option_text.endswith('*'):
                    option_text = option_text[1:-1].strip()
                    is_correct = True
                
                # Check for checkmark: ✓ correct answer
                elif option_text.startswith('✓') or option_text.startswith('✔'):
                    option_text = option_text[1:].strip()
                    is_correct = True
                
                # Check for [CORRECT] tag
                elif '[CORRECT]' in option_text.upper():
                    option_text = re.sub(r'\[CORRECT\]', '', option_text, flags=re.IGNORECASE).strip()
                    is_correct = True
                
                # Check for (correct) tag
                elif '(correct)' in option_text.lower():
                    option_text = re.sub(r'\(correct\)', '', option_text, flags=re.IGNORECASE).strip()
                    is_correct = True
                
                options.append(option_text)
                
                if is_correct:
                    correct_answer = len(options) - 1
        
        # Extract hint
        hint_match = re.search(r'Hint.*?\n.*?\n(.*?)(?=\n\d+\s*/\s*\d+|$)', part, re.DOTALL)
        hint = hint_match.group(1).strip() if hint_match else ""
        
        question_text = question_text.replace(r"\'", "'")
        hint = hint.replace(r"\'", "'")
        options = [opt.replace(r"\'", "'") for opt in options]
        
        if question_text and len(options) >= 4:
            questions.append({
                'question': question_text,
                'options': options[:4],
                'hint': hint,
                'correct_answer': correct_answer
            })
    
    return questions

def create_html_quiz(questions, quiz_title, email="lena.lubnina@gmail.com"):
    """Generate HTML quiz file from questions"""
    
    quiz_data = []
    for q in questions:
        quiz_data.append({
            'q': q['question'],
            'options': q['options'],
            'answer': q['correct_answer'],
            'hint': q['hint']
        })
    
    # [Same HTML template as before - shortened for brevity]
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{quiz_title}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 15px; }}
        .app-container {{ background: white; width: 100%; max-width: 650px; padding: 35px; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.2); text-align: center; }}
        h1 {{ color: #2d3748; font-size: 28px; margin-bottom: 10px; font-weight: 700; }}
        .subtitle {{ color: #718096; font-size: 14px; margin-bottom: 25px; }}
        .question-text {{ font-size: 18px; margin-bottom: 25px; color: #2d3748; line-height: 1.6; font-weight: 500; }}
        .options-grid {{ display: grid; gap: 12px; margin-bottom: 15px; }}
        button {{ padding: 14px 20px; font-size: 16px; cursor: pointer; border: 2px solid #e2e8f0; background: white; border-radius: 10px; transition: all 0.2s ease; color: #2d3748; font-weight: 500; text-align: left; }}
        button:hover:not(:disabled) {{ background-color: #f7fafc; border-color: #cbd5e0; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .correct {{ background-color: #c6f6d5 !important; border-color: #68d391 !important; color: #22543d !important; }}
        .wrong {{ background-color: #fed7d7 !important; border-color: #fc8181 !important; color: #742a2a !important; }}
        .hidden {{ display: none; }}
        #next-btn {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; margin-top: 20px; font-weight: 600; width: 100%; padding: 16px; font-size: 17px; }}
        #hint-btn {{ background-color: #fef5e7; border-color: #f9e79f; color: #7d6608; font-size: 14px; padding: 10px 18px; margin-bottom: 20px; display: inline-block; text-align: center; }}
        #hint-text {{ background-color: #fffbf0; border-left: 4px solid #f9c74f; padding: 15px; margin-bottom: 20px; font-size: 14px; color: #5a5a5a; text-align: left; border-radius: 6px; line-height: 1.5; }}
        .progress-container {{ width: 100%; background-color: #e2e8f0; border-radius: 10px; margin-bottom: 20px; height: 10px; overflow: hidden; }}
        .progress-bar {{ height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); border-radius: 10px; width: 0%; transition: width 0.4s ease; }}
        #progress-text {{ font-size: 14px; color: #718096; margin-bottom: 20px; font-weight: 600; }}
        #feedback {{ min-height: 28px; font-weight: 600; margin-top: 15px; font-size: 16px; padding: 10px; border-radius: 8px; }}
        .feedback-correct {{ background-color: #c6f6d5; color: #22543d; }}
        .feedback-wrong {{ background-color: #fed7d7; color: #742a2a; }}
        .submit-btn {{ background: linear-gradient(135deg, #48bb78 0%, #38a169 100%); color: white; border: none; font-weight: 600; margin-top: 20px; padding: 16px 30px; font-size: 18px; border-radius: 10px; width: 100%; cursor: pointer; }}
        input[type=text] {{ padding: 14px; margin-bottom: 15px; width: 100%; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 16px; }}
        .score-display {{ font-size: 48px; font-weight: 700; color: #667eea; margin: 20px 0; }}
        .results-message {{ font-size: 18px; color: #4a5568; margin-bottom: 30px; line-height: 1.6; }}
        .restart-btn {{ background: #f7fafc; color: #4a5568; border: 2px solid #e2e8f0; padding: 12px 24px; font-size: 14px; margin-top: 15px; }}
        @media (max-width: 480px) {{ .app-container {{ padding: 25px 20px; }} h1 {{ font-size: 24px; }} .question-text {{ font-size: 16px; }} button {{ padding: 12px 16px; font-size: 15px; }} }}
    </style>
</head>
<body>
<div class="app-container">
    <div id="quiz-box">
        <h1>📚 {quiz_title}</h1>
        <p class="subtitle">Test your knowledge</p>
        <div class="progress-container"><div class="progress-bar" id="progress-bar"></div></div>
        <p id="progress-text">Question 1 of {len(questions)}</p>
        <p class="question-text" id="question">Loading...</p>
        <button id="hint-btn" onclick="toggleHint()">💡 Show Hint</button>
        <div id="hint-text" class="hidden"></div>
        <div class="options-grid" id="options"></div>
        <div id="feedback"></div>
        <button id="next-btn" class="hidden" onclick="nextQuestion()">Next Question →</button>
    </div>
    <div id="result-box" class="hidden">
        <h1>🎉 Quiz Complete!</h1>
        <div class="score-display" id="score-display"></div>
        <p class="results-message">Great job completing the quiz!</p>
        <p style="font-size:15px; color:#718096; margin-bottom:20px;">Enter your name to submit your results:</p>
        <form action="https://formsubmit.co/{email}" method="POST">
            <input type="hidden" name="_subject" value="New {quiz_title} Submission!">
            <input type="hidden" name="_captcha" value="false">
            <input type="hidden" name="_template" value="table">
            <input type="text" name="Student Name" placeholder="Your Name" required>
            <input type="hidden" name="Final Score" id="input-score">
            <input type="hidden" name="Questions Wrong" id="input-wrong">
            <input type="hidden" name="Hints Used On" id="input-hints">
            <input type="hidden" name="Completion Time" id="input-time">
            <button type="submit" class="submit-btn">📤 Submit Results</button>
        </form>
        <button onclick="location.reload()" class="restart-btn">🔄 Restart Quiz</button>
    </div>
</div>
<script>
    const quizData = {json.dumps(quiz_data, indent=8)};
    let currentIdx = 0, score = 0, hintsUsed = [], wrongAnswers = [], startTime = Date.now();
    const questionEl = document.getElementById("question"), optionsEl = document.getElementById("options"), progressText = document.getElementById("progress-text"), progressBar = document.getElementById("progress-bar"), feedbackEl = document.getElementById("feedback"), nextBtn = document.getElementById("next-btn"), quizBox = document.getElementById("quiz-box"), resultBox = document.getElementById("result-box"), hintBtn = document.getElementById("hint-btn"), hintText = document.getElementById("hint-text"), inputScore = document.getElementById("input-score"), inputWrong = document.getElementById("input-wrong"), inputHints = document.getElementById("input-hints"), inputTime = document.getElementById("input-time"), scoreDisplay = document.getElementById("score-display");
    function loadQuestion() {{ const currentData = quizData[currentIdx]; questionEl.textContent = currentData.q; progressText.textContent = `Question ${{currentIdx + 1}} of ${{quizData.length}}`; hintText.classList.add("hidden"); hintText.textContent = currentData.hint; hintBtn.textContent = "💡 Show Hint"; const progressPercent = (currentIdx / quizData.length) * 100; progressBar.style.width = `${{progressPercent}}%`; optionsEl.innerHTML = ""; feedbackEl.textContent = ""; feedbackEl.className = ""; nextBtn.classList.add("hidden"); currentData.options.forEach((opt, index) => {{ const btn = document.createElement("button"); btn.textContent = opt; btn.onclick = () => checkAnswer(index, btn); optionsEl.appendChild(btn); }}); }}
    function toggleHint() {{ if (hintText.classList.contains("hidden")) {{ hintText.classList.remove("hidden"); hintBtn.textContent = "🙈 Hide Hint"; const qNum = currentIdx + 1; if (!hintsUsed.includes(qNum)) hintsUsed.push(qNum); }} else {{ hintText.classList.add("hidden"); hintBtn.textContent = "💡 Show Hint"; }} }}
    function checkAnswer(selectedIndex, btnElement) {{ const currentData = quizData[currentIdx]; const buttons = optionsEl.querySelectorAll("button"); buttons.forEach(btn => btn.disabled = true); if (selectedIndex === currentData.answer) {{ btnElement.classList.add("correct"); feedbackEl.textContent = "✅ Correct! Well done!"; feedbackEl.className = "feedback-correct"; score++; }} else {{ btnElement.classList.add("wrong"); feedbackEl.textContent = "❌ Incorrect. The correct answer is highlighted."; feedbackEl.className = "feedback-wrong"; buttons[currentData.answer].classList.add("correct"); wrongAnswers.push(currentIdx + 1); }} nextBtn.classList.remove("hidden"); }}
    function nextQuestion() {{ currentIdx++; if (currentIdx < quizData.length) loadQuestion(); else showResults(); }}
    function showResults() {{ quizBox.classList.add("hidden"); resultBox.classList.remove("hidden"); const percentage = Math.round((score / quizData.length) * 100); scoreDisplay.textContent = `${{score}} / ${{quizData.length}}`; const timeElapsed = Math.round((Date.now() - startTime) / 1000); const minutes = Math.floor(timeElapsed / 60); const seconds = timeElapsed % 60; inputScore.value = `${{score}} / ${{quizData.length}} (${{percentage}}%)`; inputWrong.value = wrongAnswers.length > 0 ? wrongAnswers.join(", ") : "None"; inputHints.value = hintsUsed.length > 0 ? hintsUsed.join(", ") : "None"; inputTime.value = `${{minutes}}m ${{seconds}}s`; }}
    loadQuestion();
</script>
</body>
</html>'''
    
    return html

def main():
    if len(sys.argv) < 2:
        print("Usage: python quiz_converter_marked.py quiz.docx [quiz-title]")
        print("\nThis converter looks for marked correct answers in your Word file:")
        print("  A. wrong answer")
        print("  B. *correct answer*    ← marked with asterisks")
        print("  C. wrong answer")
        print("  D. wrong answer")
        print("\nOR use ✓ checkmark:")
        print("  A. wrong answer")
        print("  B. ✓ correct answer    ← marked with checkmark")
        sys.exit(1)
    
    docx_path = sys.argv[1]
    quiz_title = sys.argv[2] if len(sys.argv) > 2 else Path(docx_path).stem.replace('_', ' ').title()
    
    if not Path(docx_path).exists():
        print(f"Error: File not found: {docx_path}")
        sys.exit(1)
    
    print(f"📖 Reading quiz from {docx_path}...")
    text = extract_text_from_docx(docx_path)
    
    print("🔍 Parsing questions and detecting marked answers...")
    questions = parse_quiz_with_marked_answers(text)
    
    if not questions:
        print("❌ No questions found in the document!")
        sys.exit(1)
    
    print(f"✅ Found {len(questions)} questions")
    
    # Show detected correct answers
    print("\n📋 Detected correct answers:")
    for i, q in enumerate(questions, 1):
        correct_letter = chr(65 + q['correct_answer'])  # Convert 0->A, 1->B, etc.
        print(f"   Q{i}: {correct_letter}")
    
    print("\n🎨 Generating HTML quiz...")
    html = create_html_quiz(questions, quiz_title)
    
    output_filename = Path(docx_path).stem + '.html'
    output_path = Path(output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Quiz saved to: {output_path}")
    print(f"\n💡 Tip: Review the detected answers above to ensure they're correct!")

if __name__ == '__main__':
    main()
