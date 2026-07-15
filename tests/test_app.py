from app import app


def test_health():
    client = app.test_client()
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'ok'


def test_workbook_crud(tmp_path, monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(app_module, 'DATABASE_PATH', tmp_path / 'test.db')
    app_module.init_database()

    client = app.test_client()
    created = client.post('/api/workbooks', json={
        'name': 'Teste',
        'data': {'version': 1, 'cells': [[1, '=SOMA(A1:A1)']]},
    })
    assert created.status_code == 200
    workbook_id = created.get_json()['id']

    loaded = client.get(f'/api/workbooks/{workbook_id}')
    assert loaded.status_code == 200
    assert loaded.get_json()['data']['cells'][0][0] == 1

    deleted = client.delete(f'/api/workbooks/{workbook_id}')
    assert deleted.status_code == 200
