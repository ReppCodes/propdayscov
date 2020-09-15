The purpose of this package is to provide a python-native means to calculate a common industry metric for
medication adherence, Proportion of Days Covered (PDC).  Much of the healthcare analytics industry is 
transitioning from SAS and are working to replicate such fundametal metrics in new environments.
The goal is to offer one less thing that needs to be rebuilt from scratch, and hopefully smooth the path of 
both better healthcare and the FOSS movement.

The most comprehensive FOSS package for medication adherence is currently AdhereR, and anyone looking for a 
broader coverage of the topic would be well served to give them a look.  They can be found at
https://www.adherer.eu/ and offer a variety of adherence metrics and visualizatons.  The propdayscov package
is designed to be simpler to use, python-native, and offers a stricter focus on PDC.

A popular implementation of PDC in SAS, and my original introduction to the topic, can be found at
http://support.sas.com/resources/papers/proceedings13/168-2013.pdf
This paper describes the nuances of the metric well, and will serve as a good primer for any analyst new
to its use.

As of right now, this package consists of a single public function, calc_pdc.  Usage is described below:
  
Parameters:  
  
 - indata - A pandas dataframe containing the required columns described below.
 - druglevel - Accepts the values of "Y" or "N" to indicate whether you want to
    additionally output drug-level PDC values
 - mprocmode - Accepts the values of "Y" or "N" to indicate whether you want to run the
    analysis in multiprocessing mode or not.  Defaults to "N"
 - workers - The number of worker processes to be instantiated for multiprocessing.  If you
    aren't sure, a decent 'best guess' can be found using multiprocessing.cpu_count()
  
Input - A Pandas dataframe containing the following column:  
 - P_ID - A unique patient identifier. Format = STRING  
 - DRUGNAME - The name of the drug being filled.  Generic name, per usual PDC requirements.  
    Format = STRING  
 - FILLDATE - The date of the fill being dispensed.  Format = DATE  
 - DAYSSUPPLY - Days of supply being dispensed at fill.  Format = INTEGER  
 - MBRELIGSTART - First date of coverage eligiblity for patient.  Per URAC, can be set to  
    first known date of fill if eligibility records are not available. Format = DATE  
 - MBRELIGEND - Last date of coverage eligiblity for patient.  Per URAC, can be set to  
    last known date of fill if eligibility records are not available. Format = DATE  
  
Returns - A Pandas dataframe containing the following columns  
 - P_ID - A unique patient identifier, as provided in input. FORMAT = STRING  
 - *DRUGNAME - The name of the drug being filled, as provided in input.  Optional  
    column, only output if druglevel parameter is set to "Y".  FORMAT = STRING  
 - COV_DAYS - The number of unique days of drug coverage, after shifting coverage  
    to accommodate early refills. FORMAT = INTEGER  
 - TOT_DAYS - The total number of days in patient analysis window.  Set to 0  
    if days of coverage is 0.  FORMAT = INTEGER  
 - PDC_RATIO - The patient's PDC ratio, calculated as COV_DAYS / TOT_DAYS.  
    Set to 0 if days of coverage is 0.  FORMAT = FLOAT  