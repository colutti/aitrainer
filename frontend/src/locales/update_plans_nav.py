import json
import os

files = ['en-US.json', 'es-ES.json', 'pt-BR.json']
for f in files:
    with open('/home/colutti/projects/personal/frontend/src/locales/' + f, 'r') as fp:
        data = json.load(fp)
    data['landing']['nav']['plans'] = 'Plans' if 'en' in f else 'Planes' if 'es' in f else 'Planos'
    with open('/home/colutti/projects/personal/frontend/src/locales/' + f, 'w') as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)
