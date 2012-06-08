# coding: utf-8
#
# Transformation script to turn denormalized CSV version of the transparency
# index into JSON that can be consumed easily by a web client. 

import csv
import json

FILE_NAME = 'transparency-index-all_regions_series.csv'

Q1_RELEASES = (('Answer', 'non_produit'), ('Points earned', 'non_public'),
               ('Possible points', 'sur_demande'), ('Weight', 'public'))


Q2_COLUMNS = (('Answer', u'Budget adopté'), 
              ('Points earned', u'Résumé du Budget'), 
              ('Possible points', u'Rapport en Milieu dannée'),
              ('Weight', u'Rapport de fin dannée'), 
              ('Max possible', u'Rapport daudit'))


Q2_FRAGMENTS = (('connue au moins un mois', 'month_ahead'),
                ('aux utilisateurs', 'press_announcement'),
                ('Est-ce que le', 'same_day'),
                ('Internet', 'internet'),
                ('sont disponibles gratuitement', 'printed_copies'),
                ('tenue pour discuter', 'press_conference'),
                ('conseillers municipaux', 'local_councilors'))


def csvdata():
    data = []
    fh = open(FILE_NAME, 'rb')
    for row in csv.DictReader(fh):
        data.append(row)
    fh.close()
    return data


def scoredata():
    data = {}
    fh = open('scores.json', 'rb')
    for row in json.load(fh):
        data[row['commune']] = row
    fh.close()
    return data


def scale_num(c):
    if 'Moins de 25' in c:
        return '0-25%', 25
    elif 'Entre 25' in c:
        return '25-50%', 50
    elif 'Entre 50' in c:
        return '50-75%', 75
    elif 'Entre 75' in c:
        return '75-100%', 100
    elif 'Plus de 100' in c:
        return '100%+', 125
    else:
        return '-', 0


def transform():
    data = {}
    scores = scoredata()
    for row in csvdata():
        p = row['Place_Normalized'].decode('utf-8')
        if not p in data:
            data[p] = {'score': scores[p]['bti_score'],
                       'rank': scores[p]['bti_rank'],
                       'questions': {},
                       'documents': {},
                       'sheet_name': row['Place']}
        q = int(row['Question'])
        if q == 1:
            doc = row['Comments'].split(' ', 1)[-1].strip().decode('utf-8')
            data[p]['documents'][doc] = {}
            for col, flag in Q1_RELEASES:
                if row[col] == '1':
                    data[p]['documents'][doc][flag] = True
                else:
                    data[p]['documents'][doc][flag] = False
            continue
        elif q == 2:
            flag = row['Comments'].split(' ', 1)[-1].strip()
            for frag, name in Q2_FRAGMENTS:
                if frag in flag:
                    flag = name
            for col, doc in Q2_COLUMNS:
                #print [col, doc]
                if not doc in data[p]['documents']:
                    data[p]['documents'][doc] = {}
                if row[col] == '1':
                    data[p]['documents'][doc][flag] = True
                else:
                    data[p]['documents'][doc][flag] = False
            continue
        elif q == 3:
            if row['Answer'].strip() == '1':
                data[p]['revenue_realized'], data[p]['revenue_realized_num'] = \
                    scale_num(row['Comments'])
            continue
        elif q == 4:
            if row['Answer'].strip() == '1':
                data[p]['spending_realized'], data[p]['spending_realized_num'] = \
                    scale_num(row['Comments'])
            continue
        else:
            if not q in data[p]['questions']:
                data[p]['questions'][q] = {'text': row['Question_Text']}
            if 'svp produire un commentaire' in row['Comments']:
                data[p]['questions'][q]['comment'] = row['Answer']
            elif row['Answer'].strip() == '1':
                data[p]['questions'][q]['answer'] = row['Comments']
    return data

if __name__ == '__main__':
    data = transform()
    fh = open('bti.json', 'wb')
    json.dump(data, fh, indent=2)
    fh.close()

