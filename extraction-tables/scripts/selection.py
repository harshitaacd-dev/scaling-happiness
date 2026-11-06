# Sources selected for each tool by the Niramai rule: a study of the tool, or a document by its company,
# with full text. (key substring of ID/DOI/title, decision, note)
SEL = {
 "Smart Scope (Periwinkle)": [
  ("apjcp.2020.21.12.3509","Include","Study of the tool"), ("diagnostics13193085","Include","Study of the tool (transvaginal device = Smart Scope)"),
  ("rs.3.rs-10502488","Include","Study of the tool (preprint)"), ("rs.3.rs-9150646","Include","Study of the tool (preprint)"),
  ("CTRI/2022/07/043993","Include","Trial registration of the tool"), ("CTRI/2022/04/041568","Include","Trial registration of the tool"),
  ("CTRI/2021/07/035164","Borderline","AI in a transvaginal device; probably Smart Scope, confirm from record"),
  ("CTRI/2022/09/045943","Borderline","AI assessment of cervix; check the record names Smart Scope/Periwinkle"),
  ("Abstracts - USICON 2020","Borderline","Abstract book; extract only Smart Scope abstract(s), as for Niramai supplements"),
  ("17th World Congress of the International Federation of Colposcopy","Borderline","Abstract book; extract only Smart Scope abstract(s)"),
  ("gore.2022.101130","Exclude","Third-party scoping review"),
 ],
 "AVE (NCI - IARC)": [
  ("jnci/djy225","Include",""),("embc44109.2020","Include",""),("diagnostics10070451","Include",""),("diagnostics10010044","Include",""),
  ("cbms52027.2021","Include",""),("jcm10050953","Include",""),("access.2021.306934","Include",""),("978-3-031-16760-7_20","Include",""),
  ("12.2610235","Include",""),("cancers14102401","Include",""),("frhs.2022.1000150","Include","Implementation study for the AVE clinical study"),
  ("s13027-023-00536-5","Include",""),("12.2651693","Include",""),("12.2651687","Include",""),("12.2653285","Include",""),
  ("jnci/djaf054","Include",""),("gatesopenres.111723","Include","Project overview by the developers"),("s2214-109x(25)00352","Include",""),
  ("Paving the Way to New Low-Cost","Include","Book chapter by the developers"),("s13027-020-00324-5","Include","Programme design pairing HPV testing with AVE"),
  ("NCT06815939","Include",""),("NCT07232355","Include",""),("NCT07461818","Include",""),
  ("mcpdig.2026.100402","Borderline","Smart speculum study; include only if it uses AVE"),
  ("ChiCTR2100046600","Borderline","Chinese 'automated visual evaluation system'; may be a different product"),
  ("jia2.26021","Exclude","Modelling study, not a study of the tool"),("fonc.2024.1382599","Exclude","Cost-effectiveness model"),
  ("jncimonographs","Exclude","Strategy paper"),("fmed.2022.945621","Exclude","Country review"),("canep.2023.102369","Exclude","Review"),
  ("langlo.2026","Exclude","Third-party commentary"),("12.2611541","Exclude","Oral cancer, not AVE cervical"),("embc48229.2022","Exclude","Oral cancer"),
 ],
 "EVA VisualCheck (MobileODT)": [
  ("CTRI/2021/08/036015","Include","Indian trial of the MobileODT AI"),("rs.3.rs-1964690","Include",""),("diagnostics12010106","Include",""),
  ("CTRI/2017/03/008128","Include","Trial registration of the EVA system"),("mhealth.2016.03.10","Include","Company case study"),
  ("go.21.00168","Borderline","Smartphone cervical images; include only if MobileODT/EVA AI"),
  ("ijph.v54i10.20134","Borderline","Include only if the AI component is used"),("bspc.2024.106948","Borderline","Image-quality AI on MobileODT images; check authors"),
  ("2024.09.27.24314466","Exclude","Third-party systematic review"),("s12033-024-01124-7","Exclude","Review"),("rs.3.rs-7254388","Exclude","Meta-analysis"),
 ],
 "iBreastExam (UE LifeSciences)": [
  ("s12957-016-1022-2","Include",""),("s40944-016-0057-1","Include",""),("sabcs16-p4-02-09","Include","Conference abstract"),("jgo.19.00205","Include",""),
  ("s2214-109x(22)00030","Include",""),("mp.15499","Include",""),("14494.003.0","Include","Book chapter on the product"),
  ("journal.pone.0284","Include","Programme using iBreastExam"),("IJCM_129A","Include","Conference abstract"),("cureus.70586","Include",""),
  ("ssrn.5383886","Include",""),("jnma.2026","Include",""),("ijc.70137","Include",""),("cancers18020281","Include",""),
  ("NCT02597452","Include",""),("NCT02814292","Include",""),("CTRI/2020/01/022727","Include","Indian trial registration"),("NCT04761055","Include",""),
  ("PMID:32362624","Borderline","Nursing awareness study; include only if it reports iBreastExam data"),
  ("go.22.00216","Borderline","Perspective piece on iBreastExam in Nepal"),("go.23.00149","Borderline","Third-party systematic review of the tool"),
  ("s2214-109x(22)00078","Exclude","Third-party commentary"),
 ],
 "uPath HER2 (Roche)": [
  ("jpi.2022.100116","Include",""),("his.15000","Include",""),("jcp-2025-210220","Include",""),
  ("s13058-024-01779-9","Borderline","Include only if uPath scoring is used"),("s10549-024-07532-2","Exclude","Pathologist survey"),
 ],
 "CanAssist Breast (OncoStem)": "ALL_INCLUDE",   # every search-1/2 include except the exclusions below
}
CANASSIST_EXCLUDE = {"s-0041-1742080": "Multi-society consensus guideline, not a study of the tool",
                     "Real-world data of CanAssist Breast-first": "Same publication as library S04/S19"}
