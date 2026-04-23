# ============================================================
# Data Processing Pipeline — Q3 Dual Choropleth Visualization
# 7CCSMSDV Coursework | Ashmitha Shree Chandrasekar K25114648
# Sources:
#   [1] World Bank EdStats — world-education-data.csv
#       https://data.worldbank.org/indicator/SE.PRM.ENRR
#   [2] Global Data Lab IWI — GDL-Mean-International-Wealth-Index-(IWI).csv
#       https://globaldatalab.org/iwi/
# ============================================================
import json
import math

# ── STEP 1: LOAD SOURCE DATASETS ─────────────────────────────
# Both CSV files loaded directly from original coursework files
# without modification — ensures data integrity
edu    = pd.read_csv('world-education-data.csv')
wealth = pd.read_csv('GDL-Mean-International-Wealth-Index-(IWI).csv')


# ── STEP 2: BUILD CONTINENT LOOKUP FROM WEALTH CSV ───────────
# Extract one continent label per country from the GDL dataset.
# This is done before merge so countries present in the education data but absent from GDL 
# do not lose their continent label during the join.
continent_lookup = (
    wealth.drop_duplicates(subset=['ISO_Code'])
          .set_index('ISO_Code')['Continent']
          .to_dict()
)

# ── STEP 3: REMOVE WORLD BANK REGIONAL AGGREGATES ────────────
# The World Bank education CSV includes regional groupings
# (e.g. SSA = Sub-Saharan Africa, WLD = World, HIC = High Income Countries). 
# These are weighted averages of multiple countries and cannot be mapped to geographic boundaries in TopoJSON.
exclude = {
    'AFE','AFW','ARB','CEB','CSS','EAP','EAR','EAS','ECA','ECS',
    'EMU','EUU','FCS','HIC','IBD','IBT','IDA','IDB','IDX','LAC',
    'LCN','LDC','LIC','LMC','LMY','LTE','MEA','MIC','MNA','NAC',
    'OED','OSS','PRE','PSS','PST','SAS','SSA','SSF','SST','TEA',
    'TEC','TLA','TMN','TSA','TSS','UMC','WLD', 'HPC'
}

# ── STEP 4: ASSIGN CONTINENT TO EDUCATION ROWS ───────────────
# Primary mapping: use continent from GDL lookup (Step 2)
edu = edu[~edu['country_code'].isin(exclude)].copy()
edu['continent'] = edu['country_code'].map(continent_lookup)

# Fallback mapping: 74 countries in World Bank EdStats are not covered by GDL.
# For these, continent is assigned using ISO 3166 standard regional
# classification. No data values are fabricated — only the
# regional grouping label is added.
# Reference: ISO 3166 country codes and regional groupings
ISO_CONTINENT = {
    # Europe
    'AND':'Europe','AUT':'Europe','BEL':'Europe','BGR':'Europe',
    'CHE':'Europe','CYP':'Europe','CZE':'Europe','DEU':'Europe',
    'DNK':'Europe','ESP':'Europe','EST':'Europe','FIN':'Europe',
    'FRA':'Europe','GBR':'Europe','GIB':'Europe','GRC':'Europe',
    'HRV':'Europe','HUN':'Europe','IRL':'Europe','ISL':'Europe',
    'ITA':'Europe','LIE':'Europe','LTU':'Europe','LUX':'Europe',
    'LVA':'Europe','MCO':'Europe','MLT':'Europe','NLD':'Europe',
    'NOR':'Europe','POL':'Europe','PRT':'Europe','ROU':'Europe',
    'RUS':'Europe','SMR':'Europe','SVK':'Europe','SVN':'Europe',
    'SWE':'Europe',
    # America
    'ABW':'America','ATG':'America','BHS':'America','CAN':'America',
    'CUW':'America','CYM':'America','DMA':'America','GRD':'America',
    'KNA':'America','PRI':'America','SXM':'America','USA':'America',
    'VCT':'America','VGB':'America',
    # Asia/Pacific
    'ARE':'Asia/Pacific','AUS':'Asia/Pacific','BHR':'Asia/Pacific',
    'BRN':'Asia/Pacific','FSM':'Asia/Pacific','HKG':'Asia/Pacific',
    'ISR':'Asia/Pacific','KOR':'Asia/Pacific','LKA':'Asia/Pacific',
    'MAC':'Asia/Pacific','MHL':'Asia/Pacific','NRU':'Asia/Pacific',
    'NZL':'Asia/Pacific','OMN':'Asia/Pacific','PLW':'Asia/Pacific',
    'PRK':'Asia/Pacific','QAT':'Asia/Pacific','SGP':'Asia/Pacific',
    'SLB':'Asia/Pacific','SYC':'Africa',
}

# Apply fallback only where continent is still null
edu['continent'] = edu.apply(
    lambda r: ISO_CONTINENT.get(r['country_code'], r['continent'])
    if pd.isna(r['continent']) else r['continent'],
    axis=1
)

# ── STEP 5: REMOVE DUPLICATE WEALTH TO NATIONAL LEVEL ─────────────
# GDL dataset contains both national-level rows and sub-national
# remove duplication on ISO_Code + Year keeps only the national row,
# preventing duplicate country-year records after the join.
wealth_nat = wealth.drop_duplicates(subset=['ISO_Code', 'Year'])

# ── STEP 6: LEFT JOIN EDUCATION + WEALTH ─────────────────────
# Left join preserves ALL education rows even when no matching
merged = edu.merge(
    wealth_nat[['ISO_Code', 'Year', 'Wealth_Index']],
    left_on  = ['country_code', 'year'],
    right_on = ['ISO_Code', 'Year'],
    how      = 'left'
)

# ── STEP 7: RENAME COLUMNS TO CLEAN FIELD NAMES ──────────────
merged = merged.rename(columns={
    'country_code'            : 'id',
    'country'                 : 'country',
    'school_enrol_primary_pct': 'enrollment',
    'pri_comp_rate_pct'       : 'completion',
    'Wealth_Index'            : 'iwi'
})
# Keep only the columns needed by D3
merged = merged[['id','country','continent','year',
                 'enrollment','completion','iwi']].copy()

# ── STEP 8: FORWARD FILL TIME SERIES GAPS ────────────────────
# Many countries report data intermittently. So do the forward fill carries
# the most recent known value forward in time within each country's time series.
# This follows standard practice used by Our World in Data
# for temporal gaps in national statistics.
merged = merged.sort_values(['id','year'])
for col in ['enrollment','completion','iwi']:
    merged[col] = merged.groupby('id')[col].transform(lambda x: x.ffill())

# ── STEP 9: CLEAN AND CALCULATE ATTRITION GAP ────────────────
# Cap enrollment at 100% to give clear scale during visulization
merged['enrollment'] = merged['enrollment'].clip(upper=100).round(1)
merged['completion'] = pd.to_numeric(merged['completion'], errors='coerce').round(1)
merged['iwi']        = pd.to_numeric(merged['iwi'], errors='coerce').round(1)
merged['gap']        = (merged['enrollment'] - merged['completion']).round(1)

# ── STEP 10: REMOVE INVALID ROWS ─────────────────────────────
# Drop rows with null enrollment (primary display variable)
merged = merged.dropna(subset=['enrollment'])
# Drop rows where gap is negative — mathematically impossible
merged = merged[merged['gap'].isna() | (merged['gap'] >= 0)]
# One row per country per year
merged = merged.drop_duplicates(subset=['id','year'])

# ── STEP 11: EXPORT TO JSON FOR D3 ───────────────────────────
records = merged.to_dict(orient='records')
cleaned = [{k:(None if isinstance(v,float) and math.isnan(v) else v)
            for k,v in r.items()} for r in records]
with open('data.json','w') as f:
    json.dump(cleaned, f, separators=(',',':'))
print(f"\nSaved: data.json ({len(cleaned):,} records)")