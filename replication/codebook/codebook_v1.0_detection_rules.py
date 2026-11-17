"""Element codebook for the 29 STANDING Together items.

Part 1 elements follow Laws et al. (2025, Clinical Imaging 118:110369, Appendix 2 data extraction form), mapped from
the draft item numbering (1.1-1.20) to the final numbering (1.1a-1.4c). Part 2 elements follow the wording of the
final STANDING Together recommendations (Alderman et al., Lancet Digit Health 2025;7:e64-88).

Each element: (id, label, regex, extra fields searched, applicability condition or None).
Score per source and item: 0 = no element reported; 1 = some applicable elements; 2 = all applicable elements.
Text searched: the verbatim quotes for the item (always) plus the extraction's value with negated/meta clauses removed,
plus any extra fields listed (other items or Table 1 data points of the same source).
"""
import re

I = re.IGNORECASE
NUM = r"\d[\d,\.]*\s*(k|thousand|lakh|million|crore)?\s*"
PEOPLE = r"(patients|participants|women|men|individuals|subjects|people|persons|adults|children|volunteers|cases|controls|households)"
UNITS = r"(images|photographs|x-?rays|radiographs|scans|videos|frames|slides|smears|samples|lesions|polyps|studies|exams|examinations|mammograms|cxrs|records|colonoscopies|specimens)"
ATTR = {
    "age": r"\b(age[sd]?|aged|years? old|mean age|median age|age group|\d{2}\s*[-–]\s*\d{2}\s*(y|yrs|years))\b",
    "sex": r"\b(male|female|males|females|sex)\b|\b\d+[\d,\.]*\s*%?\s*\(?\s*(men|women)\b|\b(men|women)\s*\(?\s*\d",
    "gender identity": r"(gender identity|transgender|non-?binary)",
    "race": r"\b(race|racial|african american|caucasian)\b|\b(black|white) (patients|women|men|participants|individuals)",
    "ethnicity": r"(ethnicity|ethnic group|hispanic|latino)",
    "socio-economic status": r"(socio-?economic|income (group|level|status)|education(al)? (level|status)|literacy|occupation|insurance|caste|below poverty|schooling|monthly income)",
    "sexual orientation": r"(sexual orientation|lgbt|lesbian|bisexual)",
}
CONTEXT_ONLY = r"(sex\s*:\s*all|minimumage|maximumage|eligib|all sexes|low[- ]and[- ]middle[- ]income countries|lmics?\b|developing countries|irrespective of|any race|broad spectrum|diverse|diversity)"
PATIENT_GROUP = r"(age group|aged|older|younger|\bage\b|women|\bmen\b|\bmale|female|\bsex\b|symptomatic|asymptomatic|hiv|density|dense breast|menopaus|smok|tobacco|diabet|prior tb|previous tb|history of tb|bmi|rural|urban|ethnic|\brace\b|insurance|income|education|pregnan|parity|skin type|fitzpatrick|skin tone|caste|children|paediatric|pediatric|key population|elderly|older adults)"

# ---------------------------------------------------------------- codebook
E = {
 # ---------- Part 1 (Laws Appendix 2)
 "1.1a": ("Laws 1.1 Dataset summary", [
   ("size", "Size of the dataset stated (number of people, images or cases)", NUM + "(" + PEOPLE[1:-1] + "|" + UNITS[1:-1] + ")", ["dp:Sample size"], None),
   ("population", "Who the data come from, beyond the disease name (e.g. symptomatic women aged 30-65)", r"(symptomatic|asymptomatic|aged|age \d|adults|children|attending|undergoing|referred|screened|presenting|suspected|high-risk|healthy|eligible|consecutive|healthy volunteers|with (a )?(history|suspected|known))", [], None),
   ("contents", "Contents of the dataset described (type of data)", r"(image|photograph|x-?ray|radiograph|cxr|\bct\b|mammogra|thermal|colonoscop|endoscop|video|slide|smear|cytolog|blood|serum|plasma|breath|sample|scan|dicom|frames|cervicograph|colposcop|dermoscop|clinical (data|variables|information)|patient data|individual patient data|\bipd\b|questionnaire|records)", [], None),
   ("source", "Source / setting of the data described", r"(hospital|centre|center|clinic|phc|primary health|health cent|communit|camp|programme|program|opd|outpatient|site|district|village|registry|database|trial|cohort|screening|institut|facilit|dataset)", ["dp:Study setting"], None),
 ]),
 "1.1b": ("Laws 1.2 Dataset identity and access", [
   ("identifier", "Dataset name or identifier (registry number, dataset name, DOI)", r"(ctri/|nct\d|isrctn|drks|chictr|registration|registered|registry|accession|\bdoi\b|nlst|lidc|ddsm|inbreast|tcia|kaggle|plco|chexpert|chestx|nih |cervigram|data ?set|database|archive|repository|named)", [], None),
   ("access", "How to access / availability statement", r"(availab|on request|upon request|proprietary|confidential|restricted|open[- ]access|publicly|data shar|share|ipd|will not be|not be made|uploaded|deposited|dataverse|hosted|kaggle|downloadable)", [], None),
   ("terms", "Access route, licence or conditions (contact, repository, agreement, licence, release/version)", r"(contact|corresponding author|request (to|from)|e-?mail|@|repository|github|zenodo|figshare|dataverse|kaggle|hosted (on|by|at)|https?://|data (use|access|sharing) agreement|licen[cs]e|version|release|approval (of|from)|application)", [], None),
   ("custodian", "Data custodian (who holds the data)", r"(held by|stored (on|in|at)|custodian|owned by|property of|managed by|maintained by|hosted|server|platform|sponsor|principal investigator)", [], None),
 ]),
 "1.1c": ("Laws 1.3 Motivations for dataset creation and intended purpose(s)", [
   ("reason", "Reason the dataset was created (aim / objective)", r"(aim|objective|purpose|to evaluate|to assess|to determine|to validate|to compare|compar(e|ing)|to develop|to investigate|to train|to test|was designed|hypothes|sought to|in order to|for use in|created (for|to)|purposive)", [], None),
   ("benefit", "Intended benefit stated", r"(to (improve|enable|reduce|increase|help|support|expand|aid|facilitate|address)|benefit|potential to|could help|would allow|early detection|access to screening|useful)", [], None),
   ("avoid", "Uses to avoid stated", r"(should not be used|not intended (for|to)|not designed (for|to)|not (be )?used (for|as)|not a (substitute|replacement)|only (for|as) (research|investigational)|cannot (diagnose|replace)|not for diagnos|contraindicat)", [], None),
   ("creator", "Who created / collected the dataset", r"(conducted (at|by|in)|(collected|created|compiled|assembled|curated|acquired) (at|by|from|for)|originally collected|recruited (at|from)|enrolled (at|in)|hospital|institut|university|centre|center|college|aiims|company|sponsor|investigators)", ["it:1.1d"], None),
   ("funder", "Who funded the dataset", r"(fund|grant|sponsor|supported by|financ|birac|icmr|dst\b|nih\b)", ["it:1.4a"], None),
 ]),
 "1.1d": ("Laws 1.5 Origin and purpose of source data", [
   ("origin", "Original source of the data described (where/how generated)", r"(hospital|centre|center|clinic|site|registry|programme|program|trial|records|database|camp|community|collected (at|from|in)|recruited|phc|enrolled|india|country|district|state)", ["dp:Country/state", "dp:Study setting"], None),
   ("reason", "Reason the original data were generated (clinical care, screening, research study, trial)", r"(routine|clinical care|screening|for (the|this) study|prospective|retrospective|research|trial|archive|records|registry|diagnostic work-?up|follow-?up|validat|evaluat|study)", ["dp:Study design"], None),
   ("expectation", "What individuals expected to happen to their data (consent / information given)", r"(consent|informed|waiver|agreed|participants were (told|informed)|data (would|will) be used|opt[- ]out)", ["it:1.4a"], None),
 ]),
 "1.1e": ("Laws 1.6 Data sampling and aggregation from multiple sources", [
   ("how", "Describes how data were sampled / participants selected", r"(consecutive|random|convenience|all (eligible|patients|women|participants|cases|images)|enrol|recruit|selected|sampl|invited|attending|referred|included|subset|anyone|walk-?in|came (to|for)|volunteer|self-?referr|identified (from|through)|drawn from|retriev)", [], None),
   ("strategy", "Names / explains the sampling strategy", r"(consecutive|random(ly|ised|ized)? (sample|select|chosen)|randomly|convenience|purposive|stratified|systematic sampl|census|all (consecutive|eligible)|probability|non-?probability|snowball|sampling (method|strategy|frame))", [], None),
   ("rationale", "Gives the rationale for the sampling strategy (incl. sample size reasoning)", r"(because|to (ensure|avoid|reflect|minimi[sz]e|represent|reduce|achieve)|in order to|so that|sample size (was )?(calculat|estimat|determin)|power(ed)?\b)", [], None),
   ("selection", "If several datasets/sites combined: how they were selected", r"(selected (because|for|based)|chosen (because|for|to)|criteria for (site|dataset|centre)|sites were (selected|chosen))", [], "multi"),
   ("aggregation", "If several datasets/sites combined: how aggregation decisions were made", r"(pooled|combined (the )?(data|datasets|cohorts|sites|results)|harmoni[sz]|merged|aggregat(ed|ion)|meta-?analys|compiled together)", [], "multi"),
 ]),
 "1.1f": ("Laws 1.7 Data shifts", [
   ("shift", "Known or suspected changes over time (population, practice or data collection)", r"((changed|replaced|transition(ed)?|switched|upgraded|introduced|shift(ed)?|drift|increas(ed|ing)|decreas(ed|ing)) .{0,60}(over time|in (19|20)\d\d|from (19|20)\d\d|(january|february|march|april|may|june|july|august|september|october|november|december)|period|year|during|after)|(over time|temporal|chronolog|period(s)? (of|compared)|before and after|pre-? and post-?|later (test|data|cohort|period)[^.;]{0,60}(differ|more|less|predominant))|(differ|changed)[^.;]{0,60}(over time|between (the )?(periods|years|phases)))", [], None),
 ]),
 "1.2a": ("Laws 1.8 Composition of populations", [
   ("summary", "Summary of the populations present (distribution by at least one personal attribute, with numbers)", r"(" + ATTR["age"] + r"|" + ATTR["sex"] + r"|ethnic|race|rural|urban|income|education|menopaus|hiv|smok|bmi)[^.;]{0,80}\d|\d[^.;]{0,40}(" + ATTR["age"] + r"|male|female|women|men|rural|urban|menopaus|hiv|smok)", ["dp:Population demographics reported (age, rural/urban, socioeconomic)"], None),
   ("choice", "Explains the choice of which populations are described", r"(we (report|describe|chose|selected)|(variables|characteristics|attributes) (were )?(chosen|selected)|as (recommended|defined) by|of interest because)", [], None),
   ("categories", "Explains the population grouping / categorisation", r"(categori[sz]ed|grouped (into|as|by)|defined as|classified (as|into|according)|self-?reported|age (bands|groups|categories)|(bmi|density) categor)", [], None),
   ("missing_groups", "Highlights known missing / under-represented groups", r"(not (included|represented|enrolled)|under-?represent|excluded|no (children|men|women|pregnant)|few (men|women|children)|lack of (diversity|representation)|absence of|limited (number|representation) of|only (women|men|adults|symptomatic))", [], None),
   ("missing_why", "Explains why groups are missing", r"(because|due to|owing to|as a result|since|as (the|they)|reason)", [], "missing_groups"),
 ]),
 "1.2b": ("Laws 1.9 Recording of attributes of individuals", [
   ("how", "Describes how attributes were obtained (self-report, records, questionnaire, linkage)", r"(self-?report|reported (being|that|having)|questionnaire|interview|medical records|case (record|report) form|\bcrf\b|extracted from|recorded (by|from|in|at|on)|collected (using|through|via|by|on)|linked|history (was|were) (taken|obtained)|documented)", [], None),
   ("level", "States whether attributes are at individual or aggregate level", r"(individual|per-?patient|patient-?level|participant-?level|aggregate|summary statistics|table 1|baseline characteristics|n \(%\)|mean|median)", [], None),
   ("coded", "Explains whether attributes were coded / condensed / modified", r"(categori[sz]|coded|grouped|binned|dichotomi[sz]|collapsed|recoded|converted)", [], None),
   ("coded_why", "States why attributes were coded / condensed", r"(because|to (allow|enable|protect|simplify|ensure)|for (analysis|privacy|comparison))", [], "coded"),
   ("unknown", "Highlights proportion of attributes recorded as unknown / other", r"((unknown|other|missing|not recorded|not available|not stated)[^.;]{0,30}\d|\d[^.;]{0,30}(unknown|missing|not recorded))", [], None),
   ("unknown_why", "Explains why attributes are unknown / other", r"(because|due to|owing|reason|not (asked|collected)|declined)", [], "unknown"),
 ]),
 "1.2c": ("Laws 1.10 Groups at particular risk of harm", [
   *[(a.replace(" ", "_"), f"Has data on {a} (or states it is not available)", ATTR[a], ["it:1.2a", "it:1.2b", "dp:Population demographics reported (age, rural/urban, socioeconomic)"], None) for a in
     ["age", "gender identity", "sex", "race", "ethnicity", "socio-economic status", "sexual orientation"]],
   ("vulnerable", "Highlights vulnerable population groups in the dataset", r"(vulnerable|marginali[sz]ed|underserved|under-?served|disadvantaged|tribal|rural (indian )?(women|population|communities)|low-?income (women|families|groups)|(people|women|those|persons) (living )?with hiv|\bpwh\b|\bplhiv\b|\bwlhiv\b|pregnant|children|elderly|sex workers|migrants|prisoners|incarcerat|displaced|disab|household contacts|slum)", [], None),
 ]),
 "1.3a": ("Laws 1.12 Limitations of the dataset", [
   ("bias", "Identifies known or suspected sources of bias in the dataset", r"(bias|selection|skew|over-?represent|under-?represent|confound|preselect|pre-?selected|referral|fair comparison|mixed indications|enriched|case-?control)", [], None),
   ("error", "Identifies known or suspected sources of error", r"(error|misclassif|noise|artefact|artifact|image quality|poor quality|blur|inaccura|measurement|interobserver|inter-?observer|variab|learning curve|fatigue|deferred|inconsisten)", [], None),
   ("generalisability", "Identifies other factors affecting generalisability / applicability", r"(generali[sz]|applicab|external validity|may not (apply|reflect|represent|be)|single[- ]?(centre|center|site|institution|arm)|(small|modest|limited) (sample|number|size|cohort|lesion)|specific population|only (included|symptomatic|women|adults|one|be assessed)|retrospective|non-?randomi[sz]ed|not (externally )?validated|not powered|lack of (a )?(contemporaneous )?control|subset of sites|availability|implemented[^.;]{0,30}differently|turnout|connectivity|loss to follow)", [], None),
 ]),
 "1.3b": ("Laws 1.11 Modifications made to the data", [
   ("whether", "Describes whether data items were modified from the original source", r"(exclud|remov|crop|resiz|normali[sz]|augment|relabel|re-?label|merged|de-?identif|anonymi[sz]|convert|filter|pre-?process|clean|annotat|threshold|cut-?off|trimmed|downsampl|compress|masked|modif)", [], None),
   ("rationale", "Provides the rationale for modification", r"(to (ensure|protect|reduce|improve|remove|standardi[sz]e|balance|avoid|enable|maintain|preserve|match)|because|in order to|so that|due to|for (privacy|confidentiality|consistency|analysis))", [], None),
   ("method", "Explains the methods used for modification", r"(using|by (applying|using|removing)|software|algorithm|tool|pixel|\d+\s*[x×]\s*\d+|fps|resolution|protocol|youden|roc|manually|automatic)", [], None),
 ]),
 "1.3c": ("Laws 1.13 Missing data", [
   ("proportion", "Describes the proportion / amount of missing data (with numbers)", r"(\d[^.;]{0,60}(missing|excluded|lost|unusable|could not|not available|incomplete|did not|withdrew|drop-?out|no (biopsy|follow|histo|result|data))|(missing|excluded|lost|unusable|incomplete|withdrew)[^.;]{0,40}\d)", [], None),
   ("nature", "Describes the nature of missing data (which data are missing)", r"((missing|unavailable|not available|incomplete|lacking|absent|lost)[^.;]{0,40}(data|images|biops|follow|histo|record|result|variable|information|values|report)|(data|images|biopsy|follow-?up|histopath\w*|records|results|reports)[^.;]{0,30}(missing|unavailable|not available|incomplete|lost))", [], None),
   ("causes", "Describes causes of missing data", r"(due to|because|owing to|as (they|a result)|reason|poor (image )?quality|refus|declin|lost to follow|did not (attend|return|undergo)|not (feasible|possible)|technical|insufficient)", [], None),
   ("groups", "Describes whether missingness differs across population groups", r"((missing|excluded|lost)[^.;]{0,60}(differ|similar|compar|across|between)[^.;]{0,30}(group|age|sex|site|arm)|(differ|similar)[^.;]{0,30}(between|across) (those|participants|patients) (with|who)[^.;]{0,30}(missing|excluded|lost))", [], None),
   ("handling", "Describes how missing data were handled", r"(imput|complete[- ]case|excluded from (the )?(analys|study)|sensitivity analys|listwise|pairwise|last observation|handled|treated as (missing|negative|positive)|per[- ]protocol|intention[- ]to[- ]treat)", [], None),
 ]),
 "1.3d": ("Laws 1.15 Known or potential bias in data generation", [
   ("acquisition", "Describes how acquisition of data may have introduced bias", r"(device|camera|scanner|machine|equipment|operator|technician|acquisition|imaging condition|ambient|lighting|resolution|vendor|manufacturer|smartphone|different (devices|cameras|machines|sites)|endoscop|colonoscop|movement|debris|bowel prep|sputum|specimen|sample (collection|quality|handling)|investigator bias|performance bias|technique|masking|blinding|unblinded|open-?label)", [], None),
   ("processing", "Describes how processing of data may have introduced bias", r"(process(ing|ed)|software|compression|pre-?process|reconstruct|post-?process|image quality|format|conversion|normali[sz])", [], None),
   ("group_diff", "Highlights differences in data acquired across population groups", r"((differ|vari|heterogene)[^.;]{0,60}(groups|sites|populations|centres|centers|countries|devices|skin)|(across|between) (groups|sites|populations|centres|centers|countries|devices))", [], None),
   ("uncertainty", "Highlights uncertainty of measurements within population groups", r"(uncertain|variab|inter-?(observer|reader|rater)|intra-?(observer|reader)|reproducib|repeatab|precision|confidence interval|kappa|agreement)", [], None),
   ("mitigation", "Describes attempts to mitigate these biases", r"(standardi[sz]|calibrat|trained (technicians|staff|operators|nurses|health)|training (of|for) (technicians|staff|operators|nurses)|blind|masked|protocol|quality (check|control|assurance)|pre-?cool|harmoni[sz]|same (device|equipment|machine|operator|endoscopist)|identical|randomi[sz])", [], None),
 ]),
 "1.3e": ("Laws 1.16 Known or potential bias in data collection", [
   ("areas", "Identifies where bias may have been introduced in data collection", r"(exclu|inclusion criteria|eligib|only (included|recruited|women|adults|symptomatic|patients)|single[- ](centre|center|site|institution)|one (hospital|region|centre|center|site)|not followed|referred|selected|aged \d|tertiary|urban|convenience|volunteer)", [], None),
   ("mitigation", "Describes attempts to mitigate these biases", r"(to (minimi[sz]e|reduce|avoid|limit) (bias|selection)|consecutive|random(ly|ised|ized)?|multi-?(cent|site|country)|stratif|to ensure represent|outreach|camps|all eligible)", [], None),
 ]),
 "1.3f": ("Laws 1.17 Known or potential bias in data labels", [
   ("description", "Provides a description of data labels / reference standard", r"(label|ground truth|reference standard|reference|gold standard|annotat|categor|classified as|diagnos(is|ed)|outcome|bi-?rads|cin\s*\d|positive|negative|xpert|culture|histolog|confirmed)", ["dp:Reference standard"], None),
   ("who", "States who decided / assigned the labels", r"(expert|pathologist|radiologist|panel|consensus|clinician|annotator|reader|gyn(a)?ecologist|oncologist|endoscopist|dermatologist|physician|specialist|cytologist|colposcopist|board-?certified)", [], None),
   ("how", "States how labels were generated", r"(histopath|histolog|patholog|biopsy|culture|follow-?up|consensus|annotat|read by|reviewed by|confirmed by|xpert|sputum|microbiolog|nucleic acid|naat|smear microscopy|cytology|colposcop|pcr|by (two|three|\d) |independent(ly)? (read|review|label))", ["dp:Reference standard"], None),
   ("high_risk", "Highlights labels at high risk of bias", r"(verification bias|incorporation|imperfect (reference|gold)|subjectiv|inter-?(observer|reader|rater)|disagree|discordan|misclassif|proxy|partial verification|only (positive|referred|screen-?positive)|not (biopsied|verified|confirmed)|differential verification)", [], None),
   ("mitigation", "Describes attempts to mitigate label bias", r"(blind|independent(ly)?|consensus|adjudicat|second (reader|reviewer|opinion)|double[- ]read|kappa|arbitrat|third (reader|reviewer)|masked)", [], None),
 ]),
 "1.4a": ("Laws 1.18 Ethics, governance and quality assurance", [
   ("law", "States whether data protection laws were adhered to", r"(data protection|gdpr|dpdp|hipaa|privacy (law|act|regulation|rule)|information technology act|personal data)", [], None),
   ("identity", "Describes measures to protect the identity of individuals", r"(de-?identif|anonymi[sz]|pseudonym|confidential|identif(y|iers|iable) (removed|masked|information)|coded (id|identifier|number)|encrypt|password[- ]protected|personal (details|identifiers) (removed|were not))", [], None),
   ("permissions", "Describes permissions obtained to enable dataset curation", r"(permission|approv|authori[sz]|consent|waiver|agreement|clearance)", [], None),
   ("governance", "Describes the governance of the dataset", r"(governance|data management|steering|monitoring committee|\bdsmb\b|\bdmc\b|oversight|sponsor|registered|registration|ctri|nct\d|monitor)", [], None),
   ("irb", "References IRB / ethics committee review", r"(ethic|\birb\b|institutional review|review board|\biec\b|\bhrec\b)", [], None),
   ("standards", "References standards adhered to (e.g. ISO, FAIR, GCP, reporting guidelines)", r"(\biso\b|\bfair\b|good clinical practice|\bgcp\b|helsinki|\bstard\b|\btripod\b|\bconsort\b|\bspirit\b|\bstrobe\b|\bclaim\b|\bce[- ]mark|cdsco|fda|guideline)", [], None),
 ]),
 "1.4b": ("Laws 1.19 Patient and public involvement and engagement", [
   ("advisory", "Describes the role of advisory boards", r"(advisory (board|group|committee|panel)|steering (committee|group)|expert panel|community advisory)", [], None),
   ("ppie", "Describes the role of patient and public involvement (including stating none)", r"(patient (and|&) public|\bppi|community (involvement|engagement|members|representatives)|patients (and|or) (the )?public (were|was)|patients were (not )?(involved|consulted))", [], None),
   ("share", "Describes efforts to share data / findings with contributors", r"(disseminat|shared (with|the) (participants|community|results)|results (were|will be) (returned|communicated|shared)|participants (were|will be) informed|feedback to participants)", [], None),
   ("feedback", "Describes participant feedback relevant to interpretation", r"((feedback|interview|focus group|survey|acceptab|satisfaction|perception|preference)[^.;]{0,50}(participants|women|patients|users|community)|(participants|women|patients|users)[^.;]{0,50}(feedback|reported|preferred|found|accept))", [], None),
 ]),
 "1.4c": ("Laws 1.20 Bias and impact assessments (alternatives collapsed into: assessment stated / its results)", [
   ("assessment", "States that an assessment of bias, fairness or impact was conducted (AIA, DPIA, equality IA, risk-of-bias tool)", r"(assess(ing|ed|ment of)[^.;]{0,30}(variation|differences|bias|generali[sz]ab)|variations in (ai )?performance|bias assessment|fairness (assessment|analysis|audit)|impact assessment|\bdpia\b|algorithmic impact|equality impact|risk of bias|quadas|probast|subgroup fairness|equity (analysis|assessment)|algorithmic audit)", [], None),
   ("results", "Provides the details / results of that assessment", r"((bias|fairness|impact|risk of bias)[^.;]{0,80}(found|showed|result|low|high|moderate|no evidence|identified|judged|rated))", [], None),
 ]),
 # ---------- Part 2 (STANDING Together recommendation wording)
 "2.1a": ("ST 2.1a Documentation sufficient for traceability and auditability", [
   ("dataset_id", "Dataset(s) used are identified (name, registry, source)", r"(ctri/|nct\d|registr|dataset|database|cohort|trial|archive|repository)", [], None),
   ("version", "Version of the AI tool / software identified", r"(version|\bv\d|release|software|firmware|model (number|name))", [], None),
   ("data_access", "Access to the data stated", r"(availab|on request|upon request|proprietary|confidential|shared|sharing|ipd|open[- ]access|publicly|https?://|kaggle|dataverse|repository|public (dataset|data))", [], None),
   ("documentation", "Documentation / protocol / supplementary material available for audit", r"(protocol|supplement|appendix|statistical analysis plan|\bsap\b|published|registered|documentation|stard|tripod|consort|spirit)", [], None),
   ("code", "Code or model availability stated", r"(code|source code|github|model weights|algorithm (is|was) (available|proprietary)|proprietary (algorithm|software|model))", [], None),
 ]),
 "2.2a": ("ST 2.2a Contextualised groups of interest identified in advance", [
   ("groups", "Contextualised groups of interest named", PATIENT_GROUP, [], None),
   ("advance", "Groups stated as identified in advance (pre-specified, a priori, protocol, planned)", r"(pre-?specified|a priori|in advance|planned|protocol|secondary (objective|outcome)|predefined|pre-?defined|registered (outcome|subgroup))", [], None),
   ("how", "How the groups were identified (evidence, experts, lived experience, data analysis)", r"(literature|previous (studies|evidence|research)|evidence|expert|clinician|lived experience|consultation|known to|because|as (they|these) (are|have)|higher risk|at risk)", [], None),
 ]),
 "2.2b": ("ST 2.2b Datasets justified for intended use population", [
   ("intended", "Intended use population / setting stated", r"(intended|target (population|users)|for use in|designed for|aimed at|to be used|screen(ing|ed)|primary care|low-?resource|community|rural|population|not seeking care|people who|adults who)", [], None),
   ("dataset_pop", "Dataset population stated", NUM + "(" + PEOPLE[1:-1] + "|" + UNITS[1:-1] + ")|(enrolled|recruited|included|study population|participants were|data (were|was) (collected|drawn))", ["dp:Sample size"], None),
   ("represented", "Representation of intended population / groups in the data stated", r"(represent|reflect|similar to|comparable to|typical of|included (women|patients|participants)|drawn from the (same|target)|real-?world|we (chose|assessed|selected) this population|since (organi[sz]ed|the|this)|local evaluation|differ from those)", [], None),
   ("under", "Areas of under-representation identified", r"(under-?represent|not (included|represented)|few (men|women|children|patients)|limited (number|representation)|lack of|absence of|only (women|men|adults|symptomatic|one))", [], None),
 ]),
 "2.2c": ("ST 2.2c Explicit and implicit use of relevant attributes", [
   ("explicit", "Attributes used as model inputs named (or stated not used)", r"((age|sex|gender|race|ethnicity|skin|clinical|demographic|history|risk factor|symptom|metadata|patient (data|information))[^.;]{0,60}(input|used|incorporat|combined|feed|feature|variable|predictor)|(input|feature|variable|predictor)s?[^.;]{0,40}(age|sex|gender|race|ethnicity|skin|clinical|demographic|history|risk|symptom)|(not|without) (use|using|including) (age|sex|race|ethnicity|demographic))", [], None),
   ("implicit", "Implicit use / proxies for attributes considered", r"(proxy|implicit|inferred|could (be )?(predict|learn|encode)|encod|correlat|confound|skin (tone|type|colou?r)|shortcut)", [], None),
 ]),
 "2.2d": ("ST 2.2d Performance evaluated for contextualised groups", [
   ("by_group", "Performance reported with numbers for a patient grouping", r"((sensitivity|specificity|auc|auroc|accuracy|ppv|npv|detection rate|adr|recall|precision|f1)[^.;]{0,120}\d[^.;]{0,120}" + PATIENT_GROUP + "|" + PATIENT_GROUP + r"[^.;]{0,120}(sensitivity|specificity|auc|auroc|accuracy|ppv|npv|detection rate|adr)[^.;]{0,60}\d)", [], None),
   ("comparison", "Group performance compared with other groups / overall", r"(compared|comparison|differ|similar|higher|lower|versus|\bvs\.?\b|p\s*[=<>]|significant|consistent|regardless|irrespective)", [], None),
 ]),
 "2.2e": ("ST 2.2e Disparate performance identified in additional groups", [
   ("stated", "Explicit statement on whether performance differs between groups", r"((differ|disparit|heterogene|varied|vary|lower|higher|worse|better|reduced|impair|consistent|similar|no (significant )?difference)[^.;]{0,80}(group|age|sex|women|men|site|device|camera|system|hiv|density|symptom|population|country|setting|endoscopist|reader|subgroup))", [], None),
   ("evidence", "Supported by numbers or a statistical test", r"(\d+(\.\d+)?\s*%|\b0\.\d+|p\s*[=<>]|95%\s*ci|confidence interval|significan|\(\d)", [], None),
 ]),
 "2.2f": ("ST 2.2f Approaches to mitigate disparate performance reported", [
   ("approach", "Approach to address group differences described (thresholds, recalibration, retraining, separate models)", r"(threshold|cut-?off|recalibrat|retrain|re-?train|fine-?tun|separate model|reweigh|adjust(ed|ment)|calibrat|stratified (model|threshold)|age-?specific|site-?specific|device-?specific)", [], None),
   ("effect", "Rationale or effect of the approach reported", r"(result(ed|s)? in|improv|reduc|increas|after|because|to (address|reduce|improve|account)|led to|achiev)", [], None),
 ]),
 "2.3a": ("ST 2.3a Limitations of datasets used reported", [
   ("limitation", "Limitation of the data used stated", r"(limitation|limited|bias|small|single|retrospective|only|lack|not (include|represent|available)|missing|selection)", [], None),
   ("implication", "Implications for groups / generalisability stated", r"(generali[sz]|applicab|may not|might not|cannot be|could (affect|limit|bias|overestimat|underestimat)|overestimat|underestimat|restrict|external validity|other (populations|settings|groups))", [], None),
 ]),
 "2.3b": ("ST 2.3b Differences between intended use population and datasets reported", [
   ("intended", "Intended use / population stated", r"(intended|screening|target|community|primary care|population|real-?world|routine|asymptomatic|for use)", [], None),
   ("difference", "Difference between data and intended use stated", r"(differ|only (on |in |among )?(included|symptomatic|women|one|tertiary|hospital)|not (representative|reflect|include|evaluated)|whereas|but (the|our)|rather than|instead of|unlike|instituti|tertiary|hospital-?based|retrospective|still images|videos)", [], None),
   ("implication", "Implication of the difference stated", r"(may|might|could|need(s|ed)? (to|further)|should|limit|affect|overestimat|underestimat|generali[sz]|before (wider|routine|implementation))", [], None),
 ]),
 "2.3c": ("ST 2.3c Findings from pre-existing assessments reported", [
   ("cited", "Pre-existing assessment of the tool (or its datasets) cited", r"(previous|prior|earlier|pilot|published|reported|validated|has been (shown|evaluated|studied)|other studies|recommend|guideline|meta-?analys|review|fda[- ]clear|clearance|ce[- ]mark)", [], None),
   ("findings", "Findings of that assessment reported (with results)", r"(\d+(\.\d+)?\s*%|\b0\.\d+|sensitivity|specificity|accuracy|auc|showed|found|demonstrat|increase|improv|reduc)", [], None),
   ("implications", "Implications for groups within the intended population stated", r"(group|population|women|patients|setting|for (our|this|the) (population|setting|context)|applicab|implication|relevan)", [], None),
 ]),
 "2.4a": ("ST 2.4a Uncertainties and risks addressed with mitigation plans", [
   ("uncertainty", "Uncertainty or variable performance stated", r"(uncertain|variab|limitation|unknown|unclear|may not|risk|false[- ](positive|negative)|low (specificity|sensitivity)|missed|generali[sz])", [], None),
   ("clinical", "Clinical implications / risks stated", r"(risk|harm|missed|false[- ](positive|negative)|overdiagnos|over-?treat|unnecessary|delay|clinical (implication|consequence|impact)|patient safety|could lead|referral)", [], None),
   ("strategy", "Strategy to monitor, manage or reduce the risks", r"(monitor|mitigat|plan(ned|s)?|will (be|conduct)|future (stud|work|research)|further (stud|research|validation|evaluation)|confirm(ation|ed)? by|follow-?up|training|randomi[sz]ed|prospective (stud|validation)|should be|need(s|ed)? to|recommend|radiologist (review|confirmation)|human (review|oversight)|trial|phase \d|validation|larger stud|multi-?cent)", [], None),
 ]),
}

META = re.compile(r"(scored|score of|calibration|as in the|matches the|like the|reference audit|example|partial\.|hence partial|\[check)", I)
NEG = re.compile(r"\b(no|not|without|none|absent|lacks?|lacking|unclear|unknown|neither|nor)\b", I)


def clean_value(v):
    """Keep only the clauses of the extraction's value that assert something (drop negated and meta clauses)."""
    if not v or v.strip().lower().startswith("not reported"):
        return ""
    out = []
    for cl in re.split(r"(?<=[.;])\s+|;\s*", re.sub(r"\[check:[^\]]*\]", "", v)):
        if cl.strip() and not META.search(cl) and not NEG.search(cl):
            out.append(cl.strip())
    return " ".join(out)


def quotes(q):
    return " ".join(re.findall(r"“(.*?)”", re.sub(r"\[check:[^\]]*\]", "", q or ""), re.S))


def item_key(src, code):
    return next(k for k in src["it"] if k.startswith(code))


def pool(src, code, extra):
    k = item_key(src, code)
    v, q = src["it"][k][0], src["it"][k][1]
    parts = [quotes(q), clean_value(v)]
    for x in extra:
        kind, name = x.split(":", 1)
        if kind == "dp":
            dv, dq = src["dp"].get(name, ["", ""])
            parts += [quotes(dq), clean_value(dv)]
        else:
            kk = item_key(src, name)
            parts += [quotes(src["it"][kk][1]), clean_value(src["it"][kk][0])]
    t = " ".join(p for p in parts if p)
    return re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2212]", "-", t).replace("\u00a0", " ")


MULTI = re.compile(r"(multi-?(cent|site|national|country)|multiple (sites|datasets|centres|centers|sources|hospitals|countries)|\b(two|three|four|five|six|seven|eight|nine|ten|\d+) (sites|centres|centers|hospitals|countries|datasets|cohorts)|pooled|combined (data|datasets|cohorts))", I)


def code_source(src, code):
    """Return (score, present, missing, applicable) for one source and one item."""
    label, elems = E[code]
    k = item_key(src, code)
    if src["it"][k][0].strip().lower().startswith("not reported") and not src["it"][k][1]:
        own_empty = True
    else:
        own_empty = False
    present, missing = [], []
    found = {}
    for eid, elabel, rx, extra, cond in elems:
        text = pool(src, code, extra)
        hit = bool(re.search(rx, text, I))
        if hit and code == "1.2c" and eid != "vulnerable":
            # attribute must be about the study's own participants, not context
            m = re.search(r".{0,60}(" + rx + r").{0,60}", text, I)
            hit = bool(m) and not re.search(CONTEXT_ONLY, m.group(0), I)
        if hit and code == "1.1f":
            m = re.search(r"[^.;]*(" + rx + r")[^.;]*", text, I)
            hit = bool(m) and not re.search(r"(planned|will be|to be (done|performed)|analysis for|we will)", m.group(0), I)
        if hit and code == "2.2e" and eid == "stated":
            m = re.search(r"[^.;]*(" + rx + r")[^.;]*", text, I)
            hit = bool(m) and not re.search(r"(needed|need to|would be|should|future|warrant|further (stud|research)|larger (stud|prospective))", m.group(0), I)
        found[eid] = hit
    for eid, elabel, rx, extra, cond in elems:
        if cond == "multi":
            applicable = bool(MULTI.search(pool(src, code, extra) + " " + pool(src, "1.1d", ["dp:Study setting"])))
        elif cond:
            applicable = found.get(cond, False)
        else:
            applicable = True
        if not applicable:
            continue
        (present if found[eid] else missing).append((eid, elabel))
    # an item whose own extraction is 'Not reported' cannot draw elements only from other items/fields
    if own_empty and code not in ("1.2c",):
        own_pool = pool(src, code, [])
        if not own_pool.strip():
            missing = present + missing
            present = []
    n_app = len(present) + len(missing)
    score = 0 if not present else (2 if not missing else 1)
    return score, present, missing, n_app
