from pathlib import Path
from watermark_remover.models import Area
from watermark_remover.settings import SettingsStore

def test_settings_roundtrip(tmp_path: Path):
    store=SettingsStore(tmp_path/"settings.json"); payload={"language":"pl","areas":[Area(1,2,3,4).to_dict()]}; store.save(payload); loaded=store.load(); assert loaded["language"]=="pl"; assert SettingsStore.areas_from(loaded["areas"])==[Area(1,2,3,4)]
