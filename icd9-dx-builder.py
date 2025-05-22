import re
import pandas as pd
from tkinter import Tk, filedialog, messagebox, Button

#function to check icd9 code matches
def icd9_matches(code: str, code_list: list) -> bool:
    """
    check if a given code matches any code in code_list.
    supports:
      - exact matches (e.g., '410.01' == '410.01')
      - partial decimal matches (e.g., '410' matches '410.01')
      - numeric ranges (e.g., '430-438') if present in code_list
    """
    code = code.strip()
    for c in code_list:
        c = c.strip()
        #if c is a range like '430-438'
        if '-' in c:
            try:
                start_val = float(c.split('-')[0])
                end_val = float(c.split('-')[1])
                code_val = float(code)
                if start_val <= code_val <= end_val:
                    return True
            except ValueError:
                pass
        else:
            #exact or partial match
            if code == c or code.startswith(c + "."):
                return True
    return False

#define all categories
ALL_CATEGORIES = {
    # ------------------------ MACE Categories (Existing) ------------------------
    "Acute myocardial infarction": [
        "410", "410.01", "410.02", "410.1", "410.11", "410.12", "410.2", "410.21", "410.22",
        "410.3", "410.31", "410.32", "410.4", "410.41", "410.42", "410.5", "410.51", "410.52",
        "410.6", "410.61", "410.62", "410.7", "410.71", "410.72", "410.8", "410.81", "410.82",
        "410.9", "410.91", "410.92"
    ],
    "Heart failure": [
        "428", "428.1", "428.2", "428.21", "428.22", "428.23",
        "428.3", "428.31", "428.32", "428.33", "428.4", "428.41", "428.42",
        "428.43", "428.9", "398.91", "402.01", "402.11", "402.91",
        "404.01", "404.03", "404.11", "404.13", "404.91", "404.93"
    ],
    "Stroke/transient ischemic attack": [
        "435", "435.1", "435.2", "435.3", "435.8", "435.9",
        "433.81", "433.91", "434", "436", "437", "437.1",
        "433.31", "433.01", "434.01", "434.1", "434.11", "434.9",
        "434.91", "437.2", "437.3", "437.4", "437.5", "437.6",
        "437.7", "437.8", "437.9", "430", "431", "432",
        "432.1", "432.9"
    ],

    # ------------------------ Additional Categories (Existing) ------------------------
    "Atrial fibrillation": ["427.31"],
    "Atrial flutter": ["427.32"],
    "Ventricular tachycardia": ["427.1"],
    "Ventricular fibrillation": ["427.0"], # Note: ICD-9 427.0 is Cardiac arrest, 427.4 is Ventricular fibrillation
    "Cerebral embolism": ["434.1"], # This is already in Stroke/TIA, "434.1" = Cerebral embolism
    "Pulmonary embolism and infarction": ["415.1"], # Can be expanded: "415.11", "415.12", "415.13", "415.19"
    "Chronic pulmonary embolism": ["416.2"],
    "Phlebitis and thrombophlebitis of deep veins of lower extremities": ["451.1"], # Can be expanded: "451.11", "451.19"
    "Phlebitis and thrombophlebitis of lower extremities, unspecified": ["451.2"],
    "Phlebitis and thrombophlebitis of iliac vein": ["451.81"],
    "Phlebitis and thrombophlebitis of deep veins of upper extremities": ["451.83"],
    "Phlebitis and thrombophlebitis of other sites": ["451.89"],
    "Phlebitis and thrombophlebitis of unspecified site": ["451.9"],
    "Thrombophlebitis migrans": ["453.1"],
    "Other venous embolism and thrombosis of inferior vena cava": ["453.2"],
    "Acute venous embolism and thrombosis of deep vessels of lower extremity": ["453.4", "453.40", "453.41", "453.42"], # Expanded
    "Chronic venous embolism and thrombosis of deep vessels of lower extremity": ["453.5", "453.50", "453.51", "453.52"], # Expanded
    "Chronic venous embolism and thrombosis of other specified vessels": ["453.7"],
    "Acute venous embolism and thrombosis of other specified veins": ["453.8"],
    "Acute venous embolism and thrombosis of unspecified site": ["453.9"],
    "Old myocardial infarction": ["412"],
    "Occlusion and stenosis of basilar artery with cerebral infarction": ["433.01"],
    "Occlusion and stenosis of carotid artery with cerebral infarction": ["433.11"],
    "Occlusion and stenosis of vertebral artery with cerebral infarction": ["433.21"],
    "Occlusion and stenosis of multiple and bilateral precerebral arteries with cerebral infarction": ["433.31"],
    "Occlusion and stenosis of other specified precerebral artery with cerebral infarction": ["433.81"],
    "Occlusion and stenosis of unspecified precerebral artery with cerebral infarction": ["433.91"],
    "Cerebral thrombosis": ["434"], # Can be expanded: "434.0", "434.00", "434.01", "434.9", "434.90", "434.91"
    "Acute but ill-defined cerebrovascular disease": ["436"],
    "Cerebral atherosclerosis": ["437.0"],
    "Other generalized ischemic cerebrovascular disease": ["437.1"],
    "Cerebrovascular disease (430-438)": ["430-438"], # This is a range, specific codes are often more useful for analysis.
    "Transient cerebral ischemia": ["435"], # Covered in Stroke/TIA
    "Diabetes mellitus": ["250", "250.0", "250.00", "250.01", "250.02", "250.03", "250.1", "250.10", "250.11", "250.12", "250.13", "250.2", "250.3", "250.4", "250.5", "250.6", "250.7", "250.8", "250.9"], # Expanded
    "Hyperlipidaemia": ["272.0", "272.1", "272.2", "272.3", "272.4"],
    "Unspecified essential hypertension": ["401.9"], # Consider also "401.0" Malignant, "401.1" Benign
    "Essential hypertension": ["401", "401.0", "401.1", "401.9"], # Added broader and specified
    "Aortic aneurysm and dissection": ["441", "441.0", "441.00", "441.01", "441.02", "441.03", "441.1", "441.2", "441.3", "441.4", "441.5", "441.6", "441.7", "441.9"], # Expanded
    "Peripheral vascular disease, unspecified": ["443.9"], # Consider specific PVDs like "440.2" Atherosclerosis of native arteries of the extremities
    "Atherosclerosis of extremities": ["440.2", "440.20", "440.21", "440.22", "440.23", "440.24", "440.29"],
    "Gangrene": ["785.4"],
    "Blood vessel replaced by other means": ["V43.4"],
    "Arterial embolism and thrombosis": ["444", "444.0", "444.1", "444.2", "444.21", "444.22", "444.8", "444.81", "444.89", "444.9"], # Expanded
    "Atheroembolism": ["445", "445.0", "445.01", "445.02", "445.8", "445.81", "445.82", "445.89"], # Expanded
    "Chronic kidney disease": ["585", "585.1", "585.2", "585.3", "585.4", "585.5", "585.6", "585.9"], # Expanded to stages
    "Chronic glomerulonephritis": ["582", "582.0", "582.1", "582.2", "582.4", "582.8", "582.81", "582.89", "582.9"],
    "Nephritis and nephropathy not specified as acute or chronic": ["583", "583.0", "583.1", "583.2", "583.4", "583.8", "583.81", "583.89", "583.9"],
    "Renal failure, unspecified": ["586"],
    "Disorders resulting from impaired renal function": ["588", "588.0", "588.1", "588.8", "588.81", "588.89", "588.9"],
    "Tetralogy of Fallot": ["745.2"],
    "The heart chambers including univentricular heart": ["745.3"],
    "Truncus arteriosus": ["745.0"],
    "Transposition": ["745.1"],
    "Ventricular septal defect": ["745.4"],
    "Atrial septal defect": ["745.5"],
    "Atrioventricular septal defect": ["745.6", "745.8"],
    "Pulmonary or tricuspid valve": ["746.0", "746.1"],
    "Aortic or mitral valve": ["746.3", "746.4", "746.5", "746.6"],
    "The aorta or pulmonary arteries or great arteries/veins": ["747"],
    "Other cardiac malformation": ["746.9", "746.7", "746.8", "745.7", "745.9"],

    # ------------------------ NEW Common Respiratory Conditions ------------------------
    "Acute nasopharyngitis (Common Cold)": ["460"],
    "Acute sinusitis": ["461", "461.0", "461.1", "461.2", "461.3", "461.8", "461.9"],
    "Acute pharyngitis": ["462"],
    "Acute tonsillitis": ["463"],
    "Acute laryngitis and tracheitis (incl Croup, Epiglottitis)": [
        "464", "464.0", "464.00", "464.01", "464.1", "464.10", "464.11", "464.2", "464.20", "464.21",
        "464.3", "464.30", "464.31", "464.4", "464.5", "464.50", "464.51"
    ],
    "Acute upper respiratory infections, multiple/unspecified": ["465", "465.0", "465.8", "465.9"],
    "Acute bronchitis and bronchiolitis": ["466", "466.0", "466.1", "466.11", "466.19"],
    "Influenza": ["487", "487.0", "487.1", "487.8"], # Can be "488" for novel influenza
    "Pneumonia, organism unspecified": ["486"],
    "Other bacterial pneumonia": ["482", "482.0", "482.1", "482.2", "482.3", "482.4", "482.8", "482.9"],
    "Viral pneumonia": ["480", "480.0", "480.1", "480.2", "480.3", "480.8", "480.9"],
    "Chronic sinusitis": ["473", "473.0", "473.1", "473.2", "473.3", "473.8", "473.9"],
    "Chronic bronchitis": ["491", "491.0", "491.1", "491.2", "491.20", "491.21", "491.8", "491.9"],
    "Emphysema": ["492", "492.0", "492.8"],
    "Asthma": [
        "493", "493.0", "493.00", "493.01", "493.02", "493.1", "493.10", "493.11", "493.12",
        "493.2", "493.20", "493.21", "493.22", "493.8", "493.81", "493.82", "493.9", "493.90",
        "493.91", "493.92"
    ],
    "Chronic obstructive pulmonary disease (COPD)": ["496"], # NEC; often primary codes 491.x, 492.x are used

    # ------------------------ NEW Common Infections (Non-Respiratory) ------------------------
    "Intestinal infectious diseases": ["008.45", "008.8", "009.0", "009.1", "009.2", "009.3"], # 008.45 C.diff
    "Septicemia": [
        "038", "038.0", "038.1", "038.10", "038.11", "038.12", "038.19", "038.2", "038.3", "038.4",
        "038.40", "038.41", "038.42", "038.43", "038.44", "038.49", "038.8", "038.9"
    ],
    "Human Immunodeficiency Virus (HIV) infection and AIDS": ["042", "V08"], # V08 Asymptomatic HIV
    "Viral hepatitis": ["070", "070.0", "070.1", "070.2", "070.20", "070.21", "070.22", "070.23", "070.3", "070.30", "070.31", "070.32", "070.33", "070.4", "070.41", "070.44", "070.5", "070.51", "070.54", "070.70", "070.71", "070.9"],
    "Urinary tract infection, site not specified": ["599.0"],
    "Candidiasis (Thrush, Yeast Infection)": ["112", "112.0", "112.1", "112.2", "112.3", "112.4", "112.5", "112.8", "112.9"],
    "Herpes zoster (Shingles)": ["053", "053.0", "053.1", "053.10", "053.11", "053.12", "053.13", "053.19", "053.2", "053.7", "053.8", "053.9"],
    "Cellulitis and abscess": [
        "681", "681.0", "681.00", "681.01", "681.02", "681.1", "681.10", "681.11", "681.9", # Finger and toe
        "682", "682.0", "682.1", "682.2", "682.3", "682.4", "682.5", "682.6", "682.7", "682.8", "682.9" # Other sites
    ],

    # ------------------------ NEW Common Mental Health Disorders ------------------------
    "Dementia (incl Alzheimer's)": ["290", "290.0", "290.1", "290.10", "290.11", "290.12", "290.13", "290.2", "290.20", "290.21", "290.3", "290.4", "290.40", "290.41", "290.42", "290.43", "331.0"], # 331.0 Alzheimer's
    "Schizophrenia spectrum disorders": [
        "295", "295.0", "295.00", "295.1", "295.10", "295.2", "295.20", "295.3", "295.30", "295.4", "295.40",
        "295.6", "295.60", "295.7", "295.70", "295.8", "295.80", "295.9", "295.90"
    ],
    "Major Depressive Disorder": [
        "296.2", "296.20", "296.21", "296.22", "296.23", "296.24", "296.25", "296.26",
        "296.3", "296.30", "296.31", "296.32", "296.33", "296.34", "296.35", "296.36"
    ],
    "Bipolar Disorder": [
        "296.0", "296.00", "296.01", "296.02", "296.03", "296.04", "296.05", "296.06",
        "296.1", "296.10", "296.11", "296.12", "296.13", "296.14", "296.15", "296.16",
        "296.4", "296.40", "296.41", "296.42", "296.43", "296.44", "296.45", "296.46",
        "296.5", "296.50", "296.51", "296.52", "296.53", "296.54", "296.55", "296.56",
        "296.6", "296.60", "296.61", "296.62", "296.63", "296.64", "296.65", "296.66",
        "296.7", "296.8", "296.80", "296.81", "296.82", "296.89", "296.9", "296.90", "296.99"
    ],
    "Anxiety Disorders (Generalized, Panic, Phobias)": [
        "300.0", "300.00", "300.01", "300.02", "300.09", # Anxiety states
        "300.2", "300.20", "300.21", "300.22", "300.23", "300.29"  # Phobic disorders
    ],
    "Obsessive-compulsive disorder": ["300.3"],
    "Post-traumatic stress disorder (PTSD)": ["309.81"],
    "Adjustment disorders": ["309", "309.0", "309.1", "309.2", "309.24", "309.28", "309.3", "309.4", "309.8", "309.89", "309.9"],
    "Attention deficit disorder (ADD/ADHD)": ["314", "314.0", "314.00", "314.01", "314.1", "314.2", "314.8", "314.9"],
    "Substance use disorders (Alcohol, Opioids, etc.)": [ # General categories, can be much more specific
        "303", "303.0", "303.00", "303.9", "303.90", # Alcohol dependence
        "304", "304.0", "304.00", "304.1", "304.10", "304.2", "304.20", # Drug dependence (Opioid, Cocaine, etc.)
        "305", "305.0", "305.00", "305.2", "305.20", "305.5", "305.50", "305.6", "305.60" # Non-dependent abuse
    ],

    # ------------------------ NEW Common Digestive System Disorders ------------------------
    "Gastroesophageal reflux disease (GERD)": ["530.11", "530.81"], # 530.11 Reflux esophagitis, 530.81 GERD
    "Gastritis and duodenitis": [
        "535", "535.0", "535.00", "535.01", "535.1", "535.10", "535.11", "535.3", "535.30", "535.31",
        "535.4", "535.40", "535.41", "535.5", "535.50", "535.51", "535.6", "535.60", "535.61", "535.7"
    ],
    "Peptic ulcer disease": ["531", "531.0", "531.1", "531.2", "531.3", "531.4", "531.5", "531.6", "531.7", "531.9", # Gastric
                              "532", "532.0", "532.1", "532.2", "532.3", "532.4", "532.5", "532.6", "532.7", "532.9", # Duodenal
                              "533", # Peptic, site unspecified
                              "534"], # Gastrojejunal
    "Irritable bowel syndrome (IBS)": ["564.1"],
    "Diverticulosis and Diverticulitis of colon": [
        "562.00", "562.01", "562.02", "562.03", # Diverticulosis of small intestine
        "562.10", "562.11", "562.12", "562.13"  # Diverticulosis/itis of colon
    ],
    "Constipation": ["564.0", "564.00", "564.01", "564.02", "564.09"],
    "Hemorrhoids": ["455", "455.0", "455.2", "455.3", "455.5", "455.6", "455.8"],
    "Appendicitis": ["540", "540.0", "540.1", "540.9", "541", "542"],
    "Cholelithiasis and Cholecystitis (Gallstones)": [
        "574", "574.0", "574.00", "574.01", "574.1", "574.10", "574.11", "574.2", "574.20", "574.21", # Cholelithiasis
        "575.0", "575.1", "575.10", "575.11", "575.12" # Cholecystitis
    ],
    "Non-infectious gastroenteritis and colitis": ["558.9"],
    "Chronic liver disease and cirrhosis": ["571", "571.0", "571.1", "571.2", "571.3", "571.4", "571.40", "571.41", "571.49", "571.5", "571.6", "571.8", "571.9"],

    # ------------------------ NEW Common Musculoskeletal Conditions ------------------------
    "Rheumatoid arthritis": ["714", "714.0", "714.1", "714.2", "714.30", "714.31", "714.32", "714.33", "714.4", "714.8", "714.89", "714.9"],
    "Osteoarthritis": [
        "715", "715.0", "715.00", "715.04", "715.09", "715.1", "715.10", "715.11", "715.12", "715.13", "715.14", "715.15", "715.16", "715.17", "715.18",
        "715.2", "715.3", "715.8", "715.9", "715.90", "715.91", "715.92", "715.93", "715.94", "715.95", "715.96", "715.97", "715.98"
    ],
    "Low back pain (Lumbago)": ["724.2"],
    "Sciatica": ["724.3"],
    "Intervertebral disc disorders (Herniated disc, Degeneration)": [
        "722", "722.0", "722.1", "722.10", "722.11", "722.2", # Cervical, Thoracic, Lumbar
        "722.3", "722.30", "722.31", "722.32", "722.39", # Schmorl's nodes
        "722.4", "722.5", "722.51", "722.52", # Degeneration
        "722.6", # Postlaminectomy syndrome
        "722.7", "722.70", "722.71", "722.72", "722.73", # Disc disorder with myelopathy
        "722.8", "722.80", "722.81", "722.82", "722.83", # Other specified
        "722.9", "722.90", "722.91", "722.92", "722.93"  # Unspecified
    ],
    "Osteoporosis": ["733.0", "733.00", "733.01", "733.02", "733.03", "733.09"],
    "Gout": ["274", "274.0", "274.00", "274.01", "274.02", "274.03", "274.1", "274.8", "274.9"], # This is metabolic
    "Carpal tunnel syndrome": ["354.0"],

    # ------------------------ NEW Common Cancers ------------------------
    "Malignant neoplasm of bronchus and lung": ["162", "162.0", "162.2", "162.3", "162.4", "162.5", "162.8", "162.9"],
    "Malignant neoplasm of female breast": ["174", "174.0", "174.1", "174.2", "174.3", "174.4", "174.5", "174.6", "174.8", "174.9"],
    "Malignant neoplasm of male breast": ["175", "175.0", "175.9"],
    "Malignant neoplasm of prostate": ["185"],
    "Malignant neoplasm of colon": ["153", "153.0", "153.1", "153.2", "153.3", "153.4", "153.5", "153.6", "153.7", "153.8", "153.9"],
    "Malignant neoplasm of rectum, rectosigmoid, and anus": ["154", "154.0", "154.1", "154.2", "154.3", "154.8"],
    "Malignant melanoma of skin": ["172", "172.0", "172.1", "172.2", "172.3", "172.4", "172.5", "172.6", "172.7", "172.8", "172.9"],
    "Other malignant neoplasm of skin (Non-melanoma)": ["173", "173.0", "173.1", "173.2", "173.3", "173.4", "173.5", "173.6", "173.7", "173.8", "173.9"],
    "Malignant neoplasm of bladder": ["188", "188.0", "188.1", "188.2", "188.3", "188.4", "188.5", "188.6", "188.7", "188.8", "188.9"],
    "Malignant neoplasm of kidney and other urinary organs": ["189", "189.0", "189.1", "189.2", "189.3", "189.4", "189.8", "189.9"],
    "Malignant neoplasm of thyroid gland": ["193"],
    "Malignant neoplasm of brain": ["191", "191.0", "191.1", "191.2", "191.3", "191.4", "191.5", "191.6", "191.7", "191.8", "191.9"],
    "Non-Hodgkin's lymphomas": [
        "200", "200.0", "200.00", "200.1", "200.10", "200.2", "200.20", "200.8", "200.80",
        "202", "202.0", "202.00", "202.1", "202.10", "202.2", "202.20", "202.8", "202.80", "202.9", "202.90"
    ],
    "Hodgkin's disease": ["201", "201.0", "201.00", "201.1", "201.10", "201.2", "201.20", "201.4", "201.40", "201.5", "201.50", "201.6", "201.60", "201.7", "201.70", "201.9", "201.90"],
    "Leukemias": [
        "204", "204.0", "204.00", "204.1", "204.10", "204.8", "204.9", # Lymphoid
        "205", "205.0", "205.00", "205.1", "205.10", "205.3", "205.8", "205.9", # Myeloid
        "206", # Monocytic
        "207", # Other specified
        "208", "208.0", "208.00", "208.1", "208.10", "208.8", "208.9"  # Unspecified cell type
    ],
    "Multiple Myeloma": ["203", "203.0", "203.00", "203.01", "203.8", "203.80", "203.81"],
    "Secondary malignant neoplasm (Metastasis)": [ # General categories
        "196", # Lymph nodes
        "197", # Respiratory and digestive
        "198", # Other specified sites (bone, brain, liver etc)
        "199"  # Unspecified site
    ],

    # ------------------------ NEW Other Common Conditions ------------------------
    "Anemias (Iron deficiency, other unspecified)": [
        "280", "280.0", "280.1", "280.8", "280.9", # Iron deficiency
        "281", # Other deficiency anemias (B12, Folate)
        "285.1", # Acute posthemorrhagic anemia
        "285.2", # Anemia in chronic disease
        "285.8", # Other specified anemias
        "285.9"  # Anemia, unspecified
    ],
    "Thyroid disorders (Hypothyroidism, Hyperthyroidism)": [
        "242", "242.0", "242.00", "242.01", "242.1", "242.2", "242.3", "242.4", "242.8", "242.9", "242.90", "242.91", # Thyrotoxicosis
        "244", "244.0", "244.1", "244.2", "244.3", "244.8", "244.9"  # Acquired hypothyroidism
    ],
    "Migraine": ["346", "346.0", "346.00", "346.01", "346.1", "346.10", "346.11", "346.2", "346.20", "346.21", "346.8", "346.80", "346.81", "346.9", "346.90", "346.91"],
    "Other headache syndromes": ["784.0", "307.81", "339.0", "339.1", "339.2", "339.3", "339.4", "339.8"], # 784.0 Headache, 307.81 Tension headache
    "Allergic rhinitis": ["477", "477.0", "477.1", "477.2", "477.8", "477.9"],
    "Obesity": ["278.00", "278.01", "278.03"], # 278.00 Obesity NOS, 278.01 Morbid obesity, 278.03 Overweight
    "Sleep apnea": ["327.23", "780.51", "780.53", "780.57"], # 327.23 Obstructive sleep apnea, others are symptoms like hypersomnia with sleep apnea
    "Vertigo and Dizziness": ["780.4", "386.0", "386.1", "386.10", "386.11", "386.12", "386.19", "386.2"], # 780.4 Dizziness, 386 Meniere's disease etc.
    "Syncope and collapse": ["780.2"],
    "Edema": ["782.3"], # Generalized edema
    "Peripheral neuropathies": ["356.9", "357.9"], # Unspecified polyneuropathy, Unspecified inflammatory and toxic neuropathy
    "Glaucoma": ["365", "365.0", "365.1", "365.10", "365.11", "365.12", "365.2", "365.9"],
    "Cataract": ["366", "366.0", "366.1", "366.10", "366.15", "366.16", "366.17", "366.9"],
    "Benign prostatic hyperplasia (BPH)": ["600", "600.0", "600.00", "600.01", "600.1", "600.2", "600.9"]
}

#MACE_CATEGORY_NAMES remains the same as per your definition
MACE_CATEGORY_NAMES = [
    "Acute myocardial infarction",
    "Heart failure",
    "Stroke/transient ischemic attack"
]


#define main app class
class ICD9App:
    def __init__(self, root):
        self.root = root
        self.root.geometry("600x300")
        self.root.title("ICD-9 DX Builder")
        
        #create select file button
        self.select_file_btn = Button(
            self.root,
            text="Select CSV File",
            command=self.select_and_process_file
        )
        self.select_file_btn.pack(pady=10)

        #create about button
        self.about_btn = Button(
            self.root,
            text="About",
            command=self.show_about
        )
        self.about_btn.pack(pady=5)

    def show_about(self):
        #display about info
        messagebox.showinfo(
            "about",
            "ICD-9 DX Builder\nDeveloped by ODAT project."
        )

    def select_and_process_file(self):
        #ask user to select a file
        file_path = filedialog.askopenfilename(
            title="Select a CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")] 
        )
        if not file_path:
            messagebox.showinfo("no file selected", "please select a csv file.")
            return

        try:
            #read the csv file
            df = pd.read_csv(file_path)
        except Exception as e:
            messagebox.showerror("error", f"could not read csv file: {e}")
            return

        #check required cols
        required_cols = ["Reference Key", "All Diagnosis Code (ICD9)", "Reference Date"]
        for rc in required_cols:
            if rc not in df.columns:
                messagebox.showerror("missing column", f"the column '{rc}' is required but not found.")
                return

        #initialize category columns efficiently
        new_cols = pd.DataFrame(
            0,
            index=df.index,
            columns=list(ALL_CATEGORIES.keys()) + ["MACE"]
        )
        df = pd.concat([df, new_cols], axis=1)

        #process each row
        for i in range(len(df)):
            row_codes = str(df.at[i, "All Diagnosis Code (ICD9)"])
            split_codes = re.split(r"[^\w\.]", row_codes)
            split_codes = [c for c in split_codes if c]
            any_mace = False
            for cat, code_list in ALL_CATEGORIES.items():
                if any(icd9_matches(code, code_list) for code in split_codes):
                    df.at[i, cat] = 1
                    if cat in MACE_CATEGORY_NAMES:
                        any_mace = True
            df.at[i, "MACE"] = 1 if any_mace else 0

        #prepare output columns
        output_cols = ["Reference Key", "MACE", "Reference Date"] + list(ALL_CATEGORIES.keys())

        #ask where to save file
        save_path = filedialog.asksaveasfilename(
            title="Save Processed CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )
        if save_path:
            #save the processed csv
            df[output_cols].to_csv(save_path, index=False)
            messagebox.showinfo("success", f"processed csv saved to {save_path}")

#launch app
if __name__ == "__main__":
    root = Tk()
    app = ICD9App(root)
    root.mainloop()
