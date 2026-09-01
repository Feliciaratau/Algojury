from app.main import classify, build_assessment, Incident

def test_deepfake_maps_to_frameworks():
    i=Incident(description='Someone made a deepfake video of me and shared it in a WhatsApp group.')
    r=build_assessment(i)
    assert 'deepfake_or_impersonation' in r['incident_categories']
    assert 'ZA-CYBERCRIMES-2020' in r['potential_frameworks']

def test_domestic_context():
    i=Incident(description='My ex-partner keeps threatening me with private photos.', relationship='ex-partner')
    r=build_assessment(i)
    assert 'coercive_or_domestic_abuse' in r['incident_categories']
    assert r['urgency']=='high'

def test_offline_is_safe_without_llm():
    i=Incident(description='Someone keeps sending me repeated messages and stalking me.')
    r=build_assessment(i)
    assert r['llm']['used'] is False
    assert r['mode']=='deterministic-offline'
