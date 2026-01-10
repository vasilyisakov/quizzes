#!/usr/bin/env python3
"""
Update index.html with all available quiz files
Automatically adds cards for all HTML quiz files in the repository
"""

import os
import re
from pathlib import Path
import json

def find_quiz_files():
    """Find all quiz HTML files in the repository root"""
    quiz_files = []
    
    # Get all HTML files in current directory
    for file in Path('.').glob('*.html'):
        # Skip index.html and uploader.html
        if file.name in ['index.html', 'uploader.html']:
            continue
        
        quiz_files.append(file.name)
    
    return sorted(quiz_files)

def extract_quiz_info(html_file):
    """Extract quiz title and question count from HTML file"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title
        title_match = re.search(r'<title>(.*?)</title>', content)
        title = title_match.group(1) if title_match else Path(html_file).stem
        
        # Extract question count from quizData
        quiz_data_match = re.search(r'const quizData = (\[.*?\]);', content, re.DOTALL)
        if quiz_data_match:
            try:
                quiz_data = json.loads(quiz_data_match.group(1))
                question_count = len(quiz_data)
            except:
                question_count = 10  # Default
        else:
            question_count = 10  # Default
        
        # Generate description based on title
        description = generate_description(title)
        
        # Estimate time (1 minute per 2 questions, rounded up)
        estimated_time = max(5, (question_count + 1) // 2)
        
        return {
            'filename': html_file,
            'title': title,
            'description': description,
            'question_count': question_count,
            'estimated_time': estimated_time,
            'icon': get_icon_for_quiz(title)
        }
    except Exception as e:
        print(f"Warning: Could not extract info from {html_file}: {e}")
        return {
            'filename': html_file,
            'title': Path(html_file).stem,
            'description': 'Test your knowledge with this interactive quiz.',
            'question_count': 10,
            'estimated_time': 5,
            'icon': '📚'
        }

def get_icon_for_quiz(title):
    """Get appropriate emoji icon based on quiz title"""
    title_lower = title.lower()
    
    if 'graph' in title_lower or 'trends' in title_lower or 'data' in title_lower:
        return '📊'
    elif 'ielts' in title_lower or 'preparation' in title_lower:
        return '📝'
    elif 'vocabulary' in title_lower or 'word' in title_lower:
        return '📖'
    elif 'grammar' in title_lower:
        return '✍️'
    elif 'sweetener' in title_lower or 'nutrition' in title_lower:
        return '🍬'
    elif 'masld' in title_lower or 'liver' in title_lower:
        return '🧬'
    elif 'science' in title_lower:
        return '🔬'
    elif 'math' in title_lower:
        return '🔢'
    else:
        return '📚'

def generate_description(title):
    """Generate a description based on the quiz title"""
    title_lower = title.lower()
    
    if 'graph' in title_lower and 'trends' in title_lower:
        return 'Master the terminology used to describe data trends, patterns, and changes in graphs and visualizations.'
    elif 'ielts' in title_lower or 'preparation' in title_lower:
        return 'Test your knowledge of IELTS Task 1 structure, vocabulary, and writing techniques for academic reports.'
    elif 'vocabulary' in title_lower:
        return 'Expand your vocabulary and test your understanding of key terms and expressions.'
    elif 'grammar' in title_lower:
        return 'Practice essential grammar rules and improve your language skills.'
    else:
        return 'Test your knowledge with this interactive quiz.'

def create_quiz_card_html(quiz_info):
    """Generate HTML for a quiz card"""
    return f'''        <a href="{quiz_info['filename']}" class="quiz-card">
            <div class="quiz-icon">{quiz_info['icon']}</div>
            <h2 class="quiz-title">{quiz_info['title']}</h2>
            <p class="quiz-description">
                {quiz_info['description']}
            </p>
            <div class="quiz-meta">
                <span>⏱️ ~{quiz_info['estimated_time']} minutes</span>
                <span>❓ {quiz_info['question_count']} questions</span>
            </div>
            <button class="btn-start">Start Quiz →</button>
        </a>
'''

def update_index_html(quiz_cards_html):
    """Update index.html with new quiz cards"""
    
    if not os.path.exists('index.html'):
        print("Error: index.html not found")
        return False
    
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the quiz-grid section
    grid_start = content.find('<div class="quiz-grid">')
    grid_end = content.find('</div>', grid_start)
    
    if grid_start == -1 or grid_end == -1:
        print("Error: Could not find quiz-grid section in index.html")
        return False
    
    # Find the closing </div> for quiz-grid (need to find the matching one)
    # Count opening and closing divs to find the right one
    div_count = 1
    search_pos = grid_start + len('<div class="quiz-grid">')
    
    while div_count > 0 and search_pos < len(content):
        if content[search_pos:search_pos+5] == '<div ':
            div_count += 1
        elif content[search_pos:search_pos+6] == '</div>':
            div_count -= 1
            if div_count == 0:
                grid_end = search_pos
                break
        search_pos += 1
    
    # Build new quiz-grid content
    new_grid_content = f'''<div class="quiz-grid">
{quiz_cards_html}
    </div>'''
    
    # Replace the quiz-grid section
    new_content = content[:grid_start] + new_grid_content + content[grid_end + 6:]
    
    # Write updated content
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    print("🔍 Scanning for quiz files...")
    quiz_files = find_quiz_files()
    
    if not quiz_files:
        print("⚠️  No quiz files found")
        return
    
    print(f"✅ Found {len(quiz_files)} quiz(zes)")
    
    # Extract info from each quiz
    quiz_infos = []
    for quiz_file in quiz_files:
        print(f"   Processing {quiz_file}...")
        info = extract_quiz_info(quiz_file)
        quiz_infos.append(info)
    
    # Generate HTML for all quiz cards
    quiz_cards_html = '\n'.join([create_quiz_card_html(info) for info in quiz_infos])
    
    # Update index.html
    print("\n📝 Updating index.html...")
    if update_index_html(quiz_cards_html):
        print("✅ index.html updated successfully!")
        print(f"\n📊 Summary:")
        for info in quiz_infos:
            print(f"   • {info['title']} ({info['question_count']} questions)")
    else:
        print("❌ Failed to update index.html")

if __name__ == '__main__':
    main()
