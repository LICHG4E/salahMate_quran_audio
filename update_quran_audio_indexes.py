import os
import json

def format_unit(size):
	if size >= 1024 * 1024:
		return f"{size / (1024 * 1024):.2f} MB"
	else:
		return f"{size / 1024:.2f} KB"

def process_high_quality(surah_dir):
	index_path = os.path.join(surah_dir, 'index.json')
	if not os.path.isfile(index_path):
		return None
	with open(index_path, 'r', encoding='utf-8') as f:
		data = json.load(f)
	verse_dict = data.get('verse', {})
	total = 0
	for v in verse_dict.values():
		v['unit'] = format_unit(v.get('size', 0))
		total += v.get('size', 0)
	data['total'] = total
	data['total_unit'] = format_unit(total)
	with open(index_path, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=2)
	return {'index': data.get('index', os.path.basename(surah_dir)), 'total': total, 'total_unit': format_unit(total)}

def process_low_quality(surah_dir):
	index_path = os.path.join(surah_dir, 'index.json')
	mp3_files = [f for f in os.listdir(surah_dir) if f.lower().endswith('.mp3')]
	if not os.path.isfile(index_path):
		# Create index.json from mp3 files
		verse = {}
		for i, mp3 in enumerate(sorted(mp3_files), 1):
			size = os.path.getsize(os.path.join(surah_dir, mp3))
			verse[f'verse_{i}'] = {
				'file': mp3,
				'size': size,
				'unit': format_unit(size)
			}
		data = {
			'index': os.path.basename(surah_dir),
			'verse': verse,
			'count': len(verse)
		}
	else:
		with open(index_path, 'r', encoding='utf-8') as f:
			data = json.load(f)
		verse = data.get('verse', {})
		for k, v in verse.items():
			mp3_file = os.path.join(surah_dir, v.get('file', ''))
			if os.path.isfile(mp3_file):
				size = os.path.getsize(mp3_file)
				v['size'] = size
				v['unit'] = format_unit(size)
			else:
				v['size'] = 0
				v['unit'] = "0 KB"
		data['verse'] = verse
		data['count'] = len(verse)
	total = sum(v['size'] for v in data['verse'].values())
	data['total'] = total
	data['total_unit'] = format_unit(total)
	with open(index_path, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=2)
	return {'index': data.get('index', os.path.basename(surah_dir)), 'total': total, 'total_unit': format_unit(total)}

def aggregate_folder(parent_dir, process_func):
	surah_dirs = [os.path.join(parent_dir, d) for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
	surahs = []
	for surah_dir in surah_dirs:
		result = process_func(surah_dir)
		if result:
			surahs.append(result)
	total = sum(s['total'] for s in surahs)
	agg = {
		'total': total,
		'total_unit': format_unit(total),
		'surahs': surahs
	}
	with open(os.path.join(parent_dir, 'index.json'), 'w', encoding='utf-8') as f:
		json.dump(agg, f, ensure_ascii=False, indent=2)

def main():
	root = os.path.dirname(os.path.abspath(__file__))
	folders = {
		'high_quality_audio': process_high_quality,
		'low_quality_audio': process_low_quality
	}
	root_agg = []
	for folder, func in folders.items():
		path = os.path.join(root, folder)
		if os.path.isdir(path):
			print(f'Processing {folder}...')
			aggregate_folder(path, func)
			# Read the just-written aggregate index
			agg_path = os.path.join(path, 'index.json')
			if os.path.isfile(agg_path):
				with open(agg_path, 'r', encoding='utf-8') as f:
					agg = json.load(f)
				root_agg.append({'folder': folder, 'total': agg.get('total', 0), 'total_unit': agg.get('total_unit', '')})
	# Write root index.json
	if root_agg:
		root_total = sum(f['total'] for f in root_agg)
		with open(os.path.join(root, 'index.json'), 'w', encoding='utf-8') as f:
			json.dump({'folders': root_agg, 'total': root_total, 'total_unit': format_unit(root_total)}, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
	main()
