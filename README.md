# WHO Growth Reference 2007 — Z-score Calculator (Python)

Cálculo de z-scores de **BMI-por-idade** e **Estatura-por-idade** usando o método LMS com a **WHO Reference 2007** para crianças e adolescentes de 5-19 anos.

## Referência

> de Onis M, Onyango AW, Borghi E, Siyam A, Nishida C, Siekmann J. **Development of a WHO growth reference for school-aged children and adolescents.** *Bulletin of the World Health Organization.* 2007;85:660-667.

## Fonte das tabelas LMS

Extraídas do pacote R oficial da OMS:  
[WorldHealthOrganization/anthroplus](https://github.com/WorldHealthOrganization/anthroplus)

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `who_zscore.py` | Módulo Python com funções de cálculo |
| `who_bmi_for_age_lms.csv` | Tabela LMS — BMI-for-age (60-229 meses, M/F) |
| `who_height_for_age_lms.csv` | Tabela LMS — Height-for-age (60-229 meses, M/F) |

## Uso

```python
from who_zscore import calc_who_zscore

# BMI-for-age z-score
z_bmi = calc_who_zscore(measurement=18.5, age_months=100, sex=1, indicator='bfa')
# → -0.22

# Height-for-age z-score
z_hfa = calc_who_zscore(measurement=130, age_months=100, sex=2, indicator='hfa')
# → 0.06
```

### Uso vetorizado (DataFrame)

```python
from who_zscore import calc_who_zscore_series

df = calc_who_zscore_series(
    df, 
    bmi_col='bmi', 
    height_col='height', 
    age_col='age_months', 
    sex_col='sex'
)
# Adiciona colunas 'zbmi' e 'zhfa'
```

## Parâmetros

| Parâmetro | Valores |
|-----------|---------|
| `sex` | 1 = masculino, 2 = feminino |
| `age_months` | 61-228 meses (arredondado para inteiro) |
| `indicator` | `'bfa'` = BMI-for-age, `'hfa'` = height-for-age |

## Fórmula LMS

```
z = ((X/M)^L - 1) / (L × S)    quando L ≠ 0
z = ln(X/M) / S                 quando L = 0
```

Para BMI-for-age com |z| > 3, aplica-se a correção restrita da OMS:
- z > 3: `z_adj = 3 + (X - SD3pos) / (SD3pos - SD2pos)`
- z < -3: `z_adj = -3 + (X - SD3neg) / (SD2neg - SD3neg)`

## Classificação OMS (BMI-for-age)

| Classificação | Critério |
|---------------|----------|
| Obesidade | z > +2 DP |
| Sobrepeso | z > +1 DP |
| Eutrófico | -2 DP ≤ z ≤ +1 DP |
| Magreza | z < -2 DP |
| Magreza severa | z < -3 DP |

## Validação

Testado contra o pacote R `anthroplus` (WHO oficial):

| Teste | Python | R | ✓ |
|-------|--------|---|---|
| Menino 100mo BMI=30 (bfa) | 5.03 | 5.03 | ✅ |
| Menino 100mo ht=100 (hfa) | -5.04 | -5.04 | ✅ |
| Menina 110mo ht=90 (hfa) | -7.06 | -7.06 | ✅ |

## Dependências

- Python 3.8+
- pandas
- numpy

## Contexto

Desenvolvido para o projeto de doutorado (USP) sobre **predição de obesidade infantil com aprendizado contínuo**, usando dados longitudinais do ECLS-K:2011.

## Licença

Tabelas LMS: WHO Growth Reference 2007 (domínio público).  
Código: MIT License.
