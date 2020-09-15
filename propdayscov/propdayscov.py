"""
Author: Andrew J Repp
Package Name: propdayscov
Usage:
    A package to faciliate efficent calculation of the medication adherence metric
        "Proportion of Days Covered" or "PDC".

    Currently contains a single public function (calc_pdc) to calculate PDC at either the
        member level or the member-drug level as desired.  Additional detail on this function
        is available in the function docstring.
"""
import datetime as dt
import sys
import multiprocessing
import functools
import numpy as np
import pandas as pd

def _covdays(indata, druglevel):
    """
    Subfunction for internal use only.  Serves to allow parallelization of
        PDC calculation via pool mapping.  Single-process mapping also available.
    """

    # derive member-specific fields
    p_id = indata.P_ID.unique()[0]
    mbr_drugs = indata.DRUGNAME.unique()
    firstfill = indata.MBRELIGSTART.unique()[0]
    lastfill = indata.MBRELIGEND.unique()[0]

    # shift fills to handle overlaps of same drugs, truncate to end of study window
    members = []
    firstfills = []
    lastfills = []
    drugs = []
    adjfills = []
    adjends = []

    for drug_name in mbr_drugs:
        drug_clms = indata.loc[indata["DRUGNAME"] == drug_name]
        fill_dates = pd.to_datetime(drug_clms.FILLDATE).tolist()
        end_dates = pd.to_datetime(drug_clms.ENDDATE).tolist()
        days_supply = pd.to_numeric(drug_clms.DAYSSUPPLY).tolist()

        for x in range(len(fill_dates)):
            if x == 0:
                new_start = fill_dates[x]
                new_end = end_dates[x]
            else:
                if fill_dates[x] <= new_end:
                    new_start = new_end + pd.Timedelta(days=1)
                    new_end = new_start + pd.DateOffset(days=days_supply[x])
                else:
                    new_start = fill_dates[x]
                    new_end = end_dates[x]

            members.append(p_id)
            firstfills.append(firstfill)
            lastfills.append(lastfill)
            drugs.append(drug_name)
            adjfills.append(new_start)
            adjends.append(new_end)

        # store lists back into a dataframe
        adj_claims = pd.DataFrame(
            list(zip(members, firstfills, lastfills, drugs, adjfills, adjends)),
            columns=[
                "P_ID",
                "MRBELIGSTART",
                "MBRELIGEND",
                "DRUGNAME",
                "FILLDATE",
                "ENDDATE",
            ],
        ).sort_values(by=["P_ID", "DRUGNAME", "FILLDATE"], ascending=True)

    # truncate fills that end after member's eligibility ends
    adj_claims["ENDDATE"] = np.where(
        adj_claims["ENDDATE"] > adj_claims["MBRELIGEND"],
        adj_claims["MBRELIGEND"],
        adj_claims["ENDDATE"],
    )

    # recalculate days supply
    adj_claims["DAYSSUPPLY"] = (
        adj_claims["ENDDATE"] - adj_claims["FILLDATE"] + pd.Timedelta(days=1)
    )

    # calculate PDC on shifted fill dates
    if druglevel == "Y":

        members = []
        drugs = []
        numerators = []
        denominators = []
        ratios = []

        for drug_name in mbr_drugs:
            drug_clms = adj_claims.loc[adj_claims["DRUGNAME"] == drug_name]
            # create set of dates on which medication coverage is achieved
            ondates = set()
            for _, row in drug_clms.iterrows():
                start = row["FILLDATE"]
                end = row["ENDDATE"]
                dur = end - start + dt.timedelta(days=1)
                date_generated = [start + dt.timedelta(days=x) for x in range(dur.days)]

                for date in date_generated:
                    ondates.add(date)

            # calculate date coverage, begininning denominator on first date of coverage for patient
            if len(ondates) > 0:
                enddt = max(ondates)
                numer = len(ondates)
                tot_days = enddt - firstfill + pd.Timedelta(days=1)
                denom = tot_days.days
                if denom > 0:
                    pdc_ratio = numer / denom
                else:
                    pdc_ratio = 0
            else:
                numer = 0
                denom = 0
                pdc_ratio = 0

            members.append(p_id)
            drugs.append(drug_name)
            numerators.append(numer)
            denominators.append(denom)
            ratios.append(pdc_ratio)

        # store lists back into a dataframe
        mbr_pdc = pd.DataFrame(
            list(zip(members, drugs, numerators, denominators, ratios)),
            columns=["P_ID", "DRUGNAME", "COV_DAYS", "TOT_DAYS", "PDC_RATIO"],
        ).sort_values(by=["P_ID", "DRUGNAME"], ascending=True)

        return mbr_pdc

    else:
        # create set of dates on which medication coverage is achieved
        ondates = set()
        for _, row in adj_claims.iterrows():
            start = row["FILLDATE"]
            end = row["ENDDATE"]
            dur = end - start + dt.timedelta(days=1)
            date_generated = [start + dt.timedelta(days=x) for x in range(dur.days)]

            for date in date_generated:
                ondates.add(date)

        # calculate date coverage, begininning denominator on first date of coverage for patient
        if len(ondates) > 0:
            enddt = max(ondates)
            numer = len(ondates)
            tot_days = enddt - firstfill + pd.Timedelta(days=1)
            denom = tot_days.days
            if denom > 0:
                pdc_ratio = numer / denom
            else:
                pdc_ratio = 0
        else:
            numer = 0
            denom = 0
            pdc_ratio = 0

        # store values back into a dataframe
        mbr_pdc = pd.DataFrame.from_records(
            [
                {
                    "P_ID": p_id,
                    "COV_DAYS": numer,
                    "TOT_DAYS": denom,
                    "PDC_RATIO": pdc_ratio,
                }
            ]
        )

        return mbr_pdc


def calc_pdc(indata, druglevel="N", mprocmode="N", workers=1):
    """
    Parameters:
        indata - A pandas dataframe containing the required columns described below.
        druglevel - Accepts the values of "Y" or "N" to indicate whether you want to
            additionally output drug-level PDC values
        mprocmode - Accepts the values of "Y" or "N" to indicate whether you want to run the
            analysis in multiprocessing mode or not.  Defaults to "N"
        workers - The number of worker processes to be instantiated for multiprocessing.  If you
            aren't sure, a decent 'best guess' can be found using multiprocessing.cpu_count()

    Input - A Pandas dataframe containing the following column:
        P_ID - A unique patient identifier. Format = STRING
        DRUGNAME - The name of the drug being filled.  Generic name, per usual PDC requirements.
            Format = STRING
        FILLDATE - The date of the fill being dispensed.  Format = DATE
        DAYSSUPPLY - Days of supply being dispensed at fill.  Format = INTEGER
        MBRELIGSTART - First date of coverage eligiblity for patient.  Per URAC, can be set to
            first known date of fill if eligibility records are not available. Format = DATE
        MBRELIGEND - Last date of coverage eligiblity for patient.  Per URAC, can be set to
            last known date of fill if eligibility records are not available. Format = DATE
    Returns - A Pandas dataframe containing the following columns
        P_ID - A unique patient identifier, as provided in input. FORMAT = STRING
        *DRUGNAME - The name of the drug being filled, as provided in input.  Optional
            column, only output if druglevel parameter is set to "Y".  FORMAT = STRING
        COV_DAYS - The number of unique days of drug coverage, after shifting coverage
            to accommodate early refills. FORMAT = INTEGER
        TOT_DAYS - The total number of days in patient analysis window.  Set to 0
            if days of coverage is 0.  FORMAT = INTEGER
        PDC_RATIO - The patient's PDC ratio, calculated as COV_DAYS / TOT_DAYS.
            Set to 0 if days of coverage is 0.  FORMAT = FLOAT
    """

    # check for presence of all required columns
    if "P_ID" not in indata.columns:
        sys.exit("Input dataframe missing required column P_ID.")
    if "FILLDATE" not in indata.columns:
        sys.exit("Input dataframe missing required column FILLDATE.")
    if "DAYSSUPPLY" not in indata.columns:
        sys.exit("Input dataframe missing required column DAYSSUPPLY.")
    if "MBRELIGSTART" not in indata.columns:
        sys.exit("Input dataframe missing required column MBRELIGSTART.")
    if "MBRELIGEND" not in indata.columns:
        sys.exit("Input dataframe missing required column MBRELIGEND.")

    # check that input dataframe has data in it
    if len(indata) == 0:
        sys.exit("Input dataframe has 0 rows and cannot be processed.")

    if druglevel == "Y":
        if "DRUGNAME" not in indata.columns:
            sys.exit("Input dataframe missing required column DRUGNAME.")

    # partial function to allow mapping to single iterable for multiprocessing
    _covdayspart = functools.partial(_covdays, druglevel=druglevel)

    # derive coverage end date for each fill from FILLDATE and DAYSSUPPLY
    indata["ENDDATE"] = (
        indata.FILLDATE
        + pd.to_timedelta(pd.np.ceil(indata.DAYSSUPPLY), unit="D")
        - pd.Timedelta(days=1)
    )

    # parse each patient's data into a list of separate dataframes
    mbr_data = [x for i, x in indata.groupby(["P_ID"], sort=False)]

    if mprocmode == "Y":
        # paralellizable subfunction for calculating PDC for each member
        with multiprocessing.Pool(processes=workers) as pool:
            pdc_ratios = pd.concat(pool.map(_covdayspart, mbr_data))
    else:
        # paralellizable subfunction for calculating PDC for each member
        pdc_ratios = pd.concat(map(_covdayspart, mbr_data))

    return pdc_ratios
