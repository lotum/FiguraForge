"""Suggestions expose the exact same context guard used when applying them."""
from figuraforge.services.workflow import advice_basis


def proposal(client):
    p=client.post('/api/projects',json={'title':'Advice context'}).json()
    store=client.app.state.store
    record={'basis_hash':advice_basis(p),'changes':[],'summary':'Existing settings retained','warnings':[]}
    store.mutate(p['id'],lambda row:row.update(suggestions={'segments':record}))
    return p['id'],store


def test_current_proposal_remains_applicable_with_same_shared_basis(client):
    ident,store=proposal(client)
    p=client.get('/api/projects/'+ident).json()
    assert p['suggestions']['segments']['stale'] is False
    assert 'stale' not in store.get(ident)['suggestions']['segments']
    result=client.post(f'/api/projects/{ident}/suggestions/segments/apply')
    assert result.status_code==200,result.text
    assert result.json()['suggestions']['segments']['applied'] is True


def test_changed_artifact_marks_old_proposal_stale_and_still_blocks_apply(client):
    ident,store=proposal(client)
    store.mutate(ident,lambda row:row['artifacts'].update(mesh={'hash':'new-source'}))
    p=client.get('/api/projects/'+ident).json()
    assert p['suggestions']['segments']['stale'] is True
    assert 'stale' not in store.get(ident)['suggestions']['segments']
    assert client.post(f'/api/projects/{ident}/suggestions/segments/apply').status_code==409


def test_applied_historical_proposal_is_not_presented_as_unapplied_stale_work(client):
    ident,store=proposal(client)
    def apply(row):
        row['suggestions']['segments']['applied']=True
        row['artifacts']['mesh']={'hash':'new-source'}
    store.mutate(ident,apply)
    p=client.get('/api/projects/'+ident).json()
    assert p['suggestions']['segments']['stale'] is False
    assert p['suggestions']['segments']['applied'] is True
