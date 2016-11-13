from parsers import MobileDeParser

parsers = []

mits_search_url = 'http://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&scopeId=C&sortOption.sortOrder=DESCENDING&sortOption.sortBy=creationTime&damageUnrepaired=NO_DAMAGE_UNREPAIRED&minFirstRegistrationDate=2010-01-01&maxPrice=12000&makeModelVariant1.makeId=17700&makeModelVariant1.modelId=18&fuels=DIESEL&maxPowerAsArray=KW&minPowerAsArray=KW'
filter_params = {
    'power': 177,
}
parser = MobileDeParser(
    search_name='mitsubishi_out',
    search_url=mits_search_url,
    max_pages=10,
    **filter_params,
)
parsers.append(parser)

skoda_search_url = 'http://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&scopeId=C&damageUnrepaired=NO_DAMAGE_UNREPAIRED&minFirstRegistrationDate=2010-01-01&makeModelVariant1.makeId=22900&makeModelVariant1.modelId=10&makeModelVariant1.modelDescription=scout&fuels=DIESEL&maxPowerAsArray=KW&minPowerAsArray=KW&transmissions=MANUAL_GEAR'

parser = MobileDeParser(
    search_name='octavia_scout',
    search_url=skoda_search_url,
    max_pages=10,
)

parsers.append(parser)

for parser in parsers:
    parser.start()
