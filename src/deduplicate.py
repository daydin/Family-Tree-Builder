import re

start_lines = []
end_lines = []
pattern = r'(\tsubgraph\s+cluster_(\d+)[^{]*{([^C]*))(\t\tCFIB\d+[^}]*)(\t})'

with open('./family_trees/CFIB00687_family_tree') as f:
    s = f.read()

matches = re.findall(pattern, s)

clusters = {}

s_to_write = ''

for match in matches:
    if match[1] not in clusters.keys():
        clusters[match[1]] = []  # If key doesn't exist, create an empty list for it
    clusters[match[1]].append(match[3])

seen = set()
for match in matches:
    if match[1] not in seen:
        s_to_write += match[0]
        for key, values in clusters.items():
            if match[1] == key:
                for value in values:
                    s_to_write += value
        s_to_write += match[4] + '\n'
    seen.add(match[1])

s = re.sub(pattern, s_to_write, s)

with open('./family_trees/CFIB00687_family_tree_processed', 'w') as f:
    f.write(s)


pass
