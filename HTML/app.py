import os
import json
import heapq
from flask import Flask, request, render_template, jsonify, send_from_directory

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'result'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class Node:
    def __init__(self, char=None, freq=None):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_frequency_table(text):
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    return freq
def build_huffman_tree(freq):
    heap = [Node(char, freq) for char, freq in freq.items()]
    heapq.heapify(heap)
    if not heap:
        return None
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = Node(freq=left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)
    return heap[0]
def build_codes(node, prefix='', codes=None):
    if codes is None:
        codes = {}
    if node is None:
        return codes
    if node.char is not None:
        codes[node.char] = prefix
    else:
        build_codes(node.left, prefix + '0', codes)
        build_codes(node.right, prefix + '1', codes)
    return codes
def compress_text(text):
    if not text:
        return '', {}
    freq = build_frequency_table(text)
    tree = build_huffman_tree(freq)
    codes = build_codes(tree)
    compressed = ''.join(codes[char] for char in text)
    return compressed, codes
def decompress_text(compressed, codes):
    reverse_codes = {v: k for k, v in codes.items()}
    result = ''
    buffer = ''
    for bit in compressed:
        buffer += bit
        if buffer in reverse_codes:
            result += reverse_codes[buffer]
            buffer = ''
    return result
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'error': 'No file provided'}), 400
        text = file.read().decode('utf-8')
        compressed, codes = compress_text(text)
        base = os.path.splitext(file.filename)[0]
        huff_path = os.path.join(app.config['UPLOAD_FOLDER'], base + '.huff')
        json_path = os.path.join(app.config['UPLOAD_FOLDER'], base + '.json')
        with open(huff_path, 'w') as f:
            f.write(compressed)
        with open(json_path, 'w') as f:
            json.dump(codes, f)
        return jsonify({
            'compressedUrl': f'/result/{base}.huff',
            'jsonUrl': f'/result/{base}.json'
        })
    except Exception as e:
        return jsonify({'error': f'Error during compression: {str(e)}'}), 500
@app.route('/decompress', methods=['POST'])
def decompress_file():
    try:
        compressed_file = request.files['compressedFile']
        map_file = request.files['mapFile']
        if not compressed_file or not map_file:
            return jsonify({'error': 'Missing files'}), 400
        compressed = compressed_file.read().decode('utf-8')
        codes = json.load(map_file)
        text = decompress_text(compressed, codes)
        base = os.path.splitext(compressed_file.filename)[0]
        result_path = os.path.join(app.config['UPLOAD_FOLDER'], base + '_decompressed.txt')
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return jsonify({'decompressedUrl': f'/result/{base}_decompressed.txt'})
    except Exception as e:
        return jsonify({'error': f'Error during decompression: {str(e)}'}), 500
@app.route('/result/<filename>')
def result_files(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
if __name__ == '__main__':
    app.run(debug=True)   