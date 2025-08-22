import json
import os
import re

# 📁 File paths
VOCAB_PATH = "D:/tokenid/onlyjson/new_mainvocab.json"
FINAL_TOKENS_PATH = "D:/tokenid/onlyjson/unique_ids.json"
INDIVIDUAL_WORDS_PATH = "D:/tokenid/onlyjson/individual_words.json"

# 🔄 Load or create vocab
if os.path.exists(VOCAB_PATH):
    try:
        with open(VOCAB_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                vocab = json.loads(content)
            else:
                vocab = {}
    except (json.JSONDecodeError, ValueError):
        print(f"⚠️ Warning: {VOCAB_PATH} is corrupted, creating new file")
        vocab = {}
else:
    vocab = {}

# 🔄 Load or create final tokens
if os.path.exists(FINAL_TOKENS_PATH):
    try:
        with open(FINAL_TOKENS_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                final_tokens = json.loads(content)
            else:
                final_tokens = {}
    except (json.JSONDecodeError, ValueError):
        print(f"⚠️ Warning: {FINAL_TOKENS_PATH} is corrupted, creating new file")
        final_tokens = {}
else:
    final_tokens = {}

# 🔄 Load or create individual words (simple word:token_id format)
if os.path.exists(INDIVIDUAL_WORDS_PATH):
    try:
        with open(INDIVIDUAL_WORDS_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                # Handle both old and new formats
                old_data = json.loads(content)
                if isinstance(old_data, dict) and any(isinstance(v, dict) for v in old_data.values()):
                    # Convert old format to new format
                    individual_words = {word: data['final_token_id'] for word, data in old_data.items()}
                else:
                    individual_words = old_data
            else:
                individual_words = {}
    except (json.JSONDecodeError, ValueError):
        print(f"⚠️ Warning: {INDIVIDUAL_WORDS_PATH} is corrupted, creating new file")
        individual_words = {}
else:
    individual_words = {}

# 🔢 Start from the current max token ID
max_token_id = max(vocab.values(), default=150000)

# ✅ Token ID threshold
MAX_ALLOWED_ID = 9999

# 🆕 Function to separate letters and special characters
def separate_special_chars(word):
    return re.findall(r'([a-z]+|[^a-z]+)', word)

# ✅ Smart chunk splitter
def split_word_into_chunks(word):
    parts = separate_special_chars(word)
    all_chunks = []
    
    for part in parts:
        if not part.isalpha():
            all_chunks.append(part)
            continue
            
        n = len(part)
        if n == 0:
            continue

        dp = [None] * (n + 1)
        dp[0] = (0, [])

        for i in range(1, n + 1):
            best_score = float('inf')
            best_path = []

            for length in range(1, min(4, i + 1)):
                start = i - length
                chunk = part[start:i]

                if dp[start] is not None:
                    chunk_id = vocab.get(chunk)
                    if chunk_id is not None and chunk_id <= MAX_ALLOWED_ID:
                        score = 1.0 / length
                    else:
                        score = 10.0 / length

                    total_score = dp[start][0] + score
                    if total_score < best_score:
                        best_score = total_score
                        best_path = dp[start][1] + [chunk]

            if best_score != float('inf'):
                dp[i] = (best_score, best_path)

        if dp[n]:
            all_chunks.extend(dp[n][1])
    
    return all_chunks

# 🧮 Function to calculate token ID for a single word
def calculate_word_token_id(word):
    global max_token_id
    
    initial_parts = split_word_into_chunks(word)
    part_ids = []
    final_parts = []

    for part in initial_parts:
        if part.isalpha():
            if part in vocab and vocab[part] <= MAX_ALLOWED_ID:
                part_ids.append(vocab[part])
                final_parts.append(part)
            elif len(part) > 1:
                sub_parts = split_word_into_chunks(part)
                for sub in sub_parts:
                    if sub in vocab and vocab[sub] <= MAX_ALLOWED_ID:
                        part_ids.append(vocab[sub])
                    else:
                        max_token_id += 1
                        vocab[sub] = max_token_id
                        part_ids.append(max_token_id)
                    final_parts.append(sub)
            else:
                max_token_id += 1
                vocab[part] = max_token_id
                part_ids.append(max_token_id)
                final_parts.append(part)
    
    # Calculate final token ID with conditional logic
    total_sum = sum(part_ids)
    
    if total_sum <= 9999:  # 4 digits or less
        final_token_id = total_sum
        division_note = "no division"
    elif 10000 <= total_sum <= 99999:  # 5 digits
        final_token_id = total_sum // 128  # 2^7
        division_note = f"÷ 128 (2^7)"
    else:  # 6+ digits
        final_token_id = total_sum // 32   # 2^5
        division_note = f"÷ 32 (2^5)"
    
    return {
        'word': word,
        'parts': final_parts,
        'part_ids': part_ids,
        'sum': total_sum,
        'final_token_id': final_token_id,
        'division_note': division_note
    }

# 🔤 Get input
input_text = input("Enter text (words or phrases): ").strip().lower()

# 📝 Extract individual words (alphabetic only)
words = re.findall(r'[a-z]+', input_text)

print(f"\n🔍 Found {len(words)} words: {words}")
print("\n" + "="*60)

# 📊 Process each word individually
for word in words:
    if word not in individual_words:  # Only process if not already calculated
        result = calculate_word_token_id(word)
        # Store only the final_token_id (simple key-value pair)
        individual_words[word] = result['final_token_id']
        
        print(f"\n🔠 Word: '{word}'")
        print(f"🧩 Parts: {result['parts']}")
        print(f"🆔 Token IDs: {result['part_ids']}")
        print(f"➕ Sum: {result['sum']}")
        print(f"🎯 Final Token ID: {result['final_token_id']} ({result['sum']} {result['division_note']})")
    else:
        print(f"\n🔠 Word: '{word}' (already processed)")
        print(f"🎯 Final Token ID: {individual_words[word]}")

# 💾 Save all data
with open(VOCAB_PATH, "w", encoding="utf-8") as f:
    json.dump(vocab, f, indent=2, ensure_ascii=False)

# Save individual_words as simple word:token_id pairs
with open(INDIVIDUAL_WORDS_PATH, "w", encoding="utf-8") as f:
    json.dump(individual_words, f, indent=2, ensure_ascii=False)

# Process the full phrase
if words:
    phrase_token = sum(individual_words[word] for word in words) // len(words)
else:
    phrase_token = 0

final_tokens[input_text] = phrase_token

with open(FINAL_TOKENS_PATH, "w", encoding="utf-8") as f:
    json.dump(final_tokens, f, indent=2, ensure_ascii=False)

print(f"\n💾 Saved {len(words)} individual words to individual_words.json")
print("💾 Updated vocab_ids.json and unique_ids.json")

# ================================
# 🧾 Show tokenization summary
# ================================
if words:
    token_sequence = [individual_words[word] for word in words]
    token_count = len(token_sequence)

    print("\n" + "="*60)
    print(f"📝 Sentence: {input_text}")
    print(f"🔢 Tokens: {token_count}")
    print(f"🆔 Token sequence: {token_sequence}")
   
     # 🆕 Character counts
    total_chars = len(input_text)
    print(f"🔠 Total characters (including spaces & punctuation): {total_chars}")
    
    # print("\n📊 Character count per word:")
    # for w in words:
    #     print(f"   '{w}': {len(w)} characters")
    
    print("="*60)
