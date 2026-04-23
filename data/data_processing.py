import json
import math

# ── LOAD ──────────────────────────────────────────────────────────────────────
edu    = pd.read_csv('world-education-data.csv')
wealth = pd.read_csv('GDL-Mean-International-Wealth-Index-(IWI).csv')

continent_lookup = (
    wealth.drop_duplicates(subset=['ISO_Code'])
          .set_index('ISO_Code')['Continent']
          .to_dict()
)
exclude = {
    'AFE','AFW','ARB','CEB','CSS','EAP','EAR','EAS','ECA','ECS',
    'EMU','EUU','FCS','HIC','IBD','IBT','IDA','IDB','IDX','LAC',
    'LCN','LDC','LIC','LMC','LMY','LTE','MEA','MIC','MNA','NAC',
    'OED','OSS','PRE','PSS','PST','SAS','SSA','SSF','SST','TEA',
    'TEC','TLA','TMN','TSA','TSS','UMC','WLD', 'HPC'
}
edu = edu[~edu['country_code'].isin(exclude)].copy()
edu['continent'] = edu['country_code'].map(continent_lookup)

# Fallback ISO continent map for countries not in GDL
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

wealth_nat = wealth.drop_duplicates(subset=['ISO_Code', 'Year'])

merged = edu.merge(
    wealth_nat[['ISO_Code', 'Year', 'Wealth_Index']],
    left_on  = ['country_code', 'year'],
    right_on = ['ISO_Code', 'Year'],
    how      = 'left'
)

merged = merged.rename(columns={
    'country_code'            : 'id',
    'country'                 : 'country',
    'school_enrol_primary_pct': 'enrollment',
    'pri_comp_rate_pct'       : 'completion',
    'Wealth_Index'            : 'iwi'
})
merged = merged[['id','country','continent','year',
                 'enrollment','completion','iwi']].copy()

merged = merged.sort_values(['id','year'])
for col in ['enrollment','completion','iwi']:
    merged[col] = merged.groupby('id')[col].transform(lambda x: x.ffill())

merged['enrollment'] = merged['enrollment'].clip(upper=100).round(1)
merged['completion'] = pd.to_numeric(merged['completion'], errors='coerce').round(1)
merged['iwi']        = pd.to_numeric(merged['iwi'], errors='coerce').round(1)
merged['gap']        = (merged['enrollment'] - merged['completion']).round(1)

merged = merged.dropna(subset=['enrollment'])
merged = merged[merged['gap'].isna() | (merged['gap'] >= 0)]
merged = merged.drop_duplicates(subset=['id','year'])

records = merged.to_dict(orient='records')
cleaned = [{k:(None if isinstance(v,float) and math.isnan(v) else v)
            for k,v in r.items()} for r in records]

with open('data.json','w') as f:
    json.dump(cleaned, f, separators=(',',':'))

print(f"\nSaved: data.json ({len(cleaned):,} records)")