from watermark_remover.models import Area, ProcessingOptions, corner_areas

def test_area_normalize_and_clamp():
    assert Area(20,20,-10,-5).normalized() == Area(10,15,10,5)
    assert Area(-5,-5,20,20).clamp(10,10) == Area(0,0,10,10)
    assert Area(20,20,5,5).clamp(10,10) is None

def test_corner_areas():
    assert corner_areas(1000,500,["top_left","bottom_right"],0.2) == [Area(0,0,200,100),Area(800,400,200,100)]

def test_options_validation():
    o=ProcessingOptions(method="mixed",radius=99,margin=-1,feather=4); o.validate(); assert o.radius==25 and o.margin==0 and o.feather==5
