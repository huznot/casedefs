"""shared source details for the tonelli 2015 definitions."""

SOURCE_TITLE = (
    "Tonelli M, Wiebe N, Fortin M, et al. Methods for identifying 30 chronic conditions: application to "
    "administrative data. BMC Med Inform Decis Mak. 2015;15:31. Table 1 as corrected in "
    "BMC Med Inform Decis Mak. 2019 (doi 10.1186/s12911-019-0900-2)"
)
SOURCE_URL = "https://bmcmedinformdecismak.biomedcentral.com/articles/10.1186/s12911-019-0900-2/tables/1"
VERSION = "2019-correction"
LOCATION = "Table 1 (corrected), row: "

FAMILY_NOTES = (
    "alberta, canada. any diagnosis field counts unless noted. 'ACCS' records are ambulatory care "
    "(ed and clinic) records; pass them as ambulatory=. tonelli sets the index date to the first "
    "relevant claim; casedefs returns the date the rule is first met."
)
