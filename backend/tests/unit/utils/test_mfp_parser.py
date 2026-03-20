from datetime import datetime
from src.utils.mfp_parser import parse_mfp_text

def test_parse_single_day_text():
    text = """
19 de mar. de 2026
Alimentos       Calorias        Carboidratos    Gorduras        Proteínas       Colest  Sódio   Açúcar  Fibras
Café da manha
Arandano LOH - Arandanos, 50 gr 29      7 g     0 g     0 g     0 mg    1 mg    5 g     1 g
Almoço
Pollo - Pechuga De Pollo Al Horno, 200 g        330     0 g     7 g     62 g    170 mg  148 mg  0 g     0 g
TOTAIS  1748    153 g   47 g    182 g   500mg   920mg   32 g    15 g
    """
    results = parse_mfp_text(text)
    
    assert len(results) == 1
    day = results[0]
    assert day["date"] == datetime(2026, 3, 19).date()
    assert day["calories"] == 1748
    assert day["carbs"] == 153.0
    assert day["fat"] == 47.0
    assert day["protein"] == 182.0
    assert day["sodium"] == 920.0
    assert day["fiber"] == 15.0

def test_parse_multiple_days_text():
    text = """
18 de mar. de 2026
Alimentos       Calorias        Carboidratos    Gorduras        Proteínas
Refeição 1      500             50 g            10 g            40 g
TOTAIS          500             50 g            10 g            40 g

19 de mar. de 2026
Alimentos       Calorias        Carboidratos    Gorduras        Proteínas
Refeição 1      600             60 g            12 g            50 g
TOTAIS          600             60 g            12 g            50 g
    """
    results = parse_mfp_text(text)
    
    assert len(results) == 2
    assert results[0]["date"] == datetime(2026, 3, 18).date()
    assert results[1]["date"] == datetime(2026, 3, 19).date()
    assert results[1]["calories"] == 600

def test_parse_portuguese_months():
    text = "1 de jan. de 2026\nTOTAIS 100 10g 5g 20g"
    results = parse_mfp_text(text)
    assert results[0]["date"] == datetime(2026, 1, 1).date()
    
    text = "1 de fev. de 2026\nTOTAIS 100 10g 5g 20g"
    results = parse_mfp_text(text)
    assert results[0]["date"] == datetime(2026, 2, 1).date()
