from pathlib import Path
import json, os, re
import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent.parent
CORPUS = BASE / 'corpus' / 'sources.json'
FRONTEND = BASE / 'frontend' / 'index.html'

app = FastAPI(title='AlgoJury Live', version='0.1.0')

class Incident(BaseModel):
    description: str = Field(min_length=5, max_length=12000)
    relationship: str = 'unknown'
    immediate_danger: bool = False
    consent_to_processing: bool = True

KEYWORDS = {
    'non_consensual_intimate_image': ['nude', 'nudes', 'intimate image', 'intimate photo', 'sex video', 'private video', 'revenge porn'],
    'deepfake_or_impersonation': ['deepfake', 'fake video', 'fake audio', 'voice clone', 'impersonat', 'synthetic media'],
    'harassment_or_stalking': ['stalk', 'followed', 'harass', 'repeated messages', 'spam', 'watching me', 'threatening messages'],
    'doxxing_or_privacy': ['doxx', 'address leaked', 'phone number leaked', 'personal information', 'private information', 'home address'],
    'threats': ['kill me', 'kill you', 'threat', 'hurt me', 'harm me'],
    'sextortion': ['sextortion', 'pay or', 'send money', 'blackmail', 'extort'],
    'cyberbullying': ['cyberbully', 'bullying', 'group chat', 'school group'],
    'coercive_or_domestic_abuse': ['partner', 'ex-partner', 'husband', 'wife', 'boyfriend', 'girlfriend', 'controlling', 'coercive', 'domestic abuse'],
}

SOURCE_IDS = {
    'non_consensual_intimate_image': ['ZA-CYBERCRIMES-2020', 'ZA-DVA-1998', 'ZA-PHA-2011'],
    'deepfake_or_impersonation': ['ZA-CYBERCRIMES-2020', 'ZA-POPIA-2013'],
    'harassment_or_stalking': ['ZA-PHA-2011', 'ZA-DVA-1998'],
    'doxxing_or_privacy': ['ZA-POPIA-2013', 'ZA-PHA-2011'],
    'threats': ['ZA-CYBERCRIMES-2020', 'ZA-PHA-2011'],
    'sextortion': ['ZA-CYBERCRIMES-2020', 'ZA-DVA-1998'],
    'cyberbullying': ['ZA-CYBERCRIMES-2020', 'ZA-PHA-2011'],
    'coercive_or_domestic_abuse': ['ZA-DVA-1998', 'ZA-DVA-2021'],
}

SAFETY_ACTIONS = [
    'Preserve the original messages/files and record dates, usernames, URLs and platform names.',
    'Do not delete evidence before making a secure copy.',
    'Use the platform reporting tools and save the report/reference number if one is provided.',
    'Review account security: change passwords, enable MFA and check active sessions.',
]

def classify(text: str, relationship: str):
    t = text.lower()
    hits = []
    for label, words in KEYWORDS.items():
        matched = [w for w in words if w in t]
        if matched:
            hits.append((label, matched))
    if relationship in {'partner','ex-partner','family'} and 'coercive_or_domestic_abuse' not in [h[0] for h in hits]:
        hits.append(('coercive_or_domestic_abuse', ['relationship context']))
    return hits

def load_sources():
    return json.loads(CORPUS.read_text())

def build_assessment(i: Incident):
    hits = classify(i.description, i.relationship)
    categories = [h[0] for h in hits]
    ids = []
    for c in categories:
        ids.extend(SOURCE_IDS.get(c, []))
    ids = list(dict.fromkeys(ids))
    if 'UNESCO-AI-2021' not in ids:
        ids.append('UNESCO-AI-2021')
    if 'UNESCO-DP-2023' not in ids:
        ids.append('UNESCO-DP-2023')
    urgency = 'high' if i.immediate_danger or any(c in categories for c in ['threats','sextortion']) else ('medium' if categories else 'low')
    confidence = 'high' if len(categories) >= 2 else ('medium' if categories else 'low')
    return {
        'mode': 'deterministic-offline',
        'incident_categories': categories,
        'matched_indicators': {c: m for c,m in hits},
        'potential_frameworks': ids,
        'urgency': urgency,
        'confidence': confidence,
        'recommended_actions': SAFETY_ACTIONS,
        'legal_position': 'Potentially relevant legal frameworks are identified for further review; this is not a finding of illegality or legal advice.',
        'llm': {'available': False, 'used': False}
    }

async def llm_assessment(i: Incident, base):
    url = os.getenv('ALGOJURY_LLM_URL')
    if not url:
        return base
    prompt = f'''You are AlgoJury, an offline digital-harm assessment assistant for South Africa.\n\nRules: never claim guilt; never invent laws; distinguish facts from allegations; cite only source IDs supplied below; recommend safety and redress steps; state uncertainty.\n\nIncident:\n{i.description}\nRelationship: {i.relationship}\n\nSource IDs available:\n{', '.join(base['potential_frameworks'])}\n\nReturn concise JSON with keys: summary, harm, legal_considerations, redress_steps, uncertainty.'''
    payload = {'model': os.getenv('ALGOJURY_LLM_MODEL','local-model'), 'messages':[{'role':'user','content':prompt}], 'temperature':0.1}
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            content = data['choices'][0]['message']['content']
            base['llm'] = {'available': True, 'used': True, 'raw': content}
    except Exception as e:
        base['llm'] = {'available': False, 'used': False, 'fallback': True}
    return base

@app.get('/')
async def home():
    return FileResponse(FRONTEND)

@app.get('/api/health')
async def health():
    return {'status':'ok','offline_mode':True,'llm_configured':bool(os.getenv('ALGOJURY_LLM_URL'))}

@app.get('/api/sources')
async def sources():
    return load_sources()

@app.post('/api/assess')
async def assess(incident: Incident):
    if not incident.consent_to_processing:
        return {'error':'Consent is required to process this incident.'}
    result = build_assessment(incident)
    result = await llm_assessment(incident, result)
    return result
