# Project Pukar — Dataset Labeling & Severity Rubric

**Domain:** Crisis NLP & SOS Message Classification  
**Target Languages:** English (`en`), Hindi (`hi` - Devanagari), and Hinglish (`hinglish` - Romanized Hindi)  
**Companion File:** [`services/backend/src/ml/contracts.py`](../../services/backend/src/ml/contracts.py)

---

## 1. Severity Classification Rubric

Severity dictates tactical dispatch priority on the mesh network.

```
+-----------------------------------------------------------------------------+
| CRITICAL (Score 75 - 100) : Direct, immediate, active life threat           |
| WARN     (Score 35 - 74)  : Urgent distress, deteriorating conditions       |
| INFO     (Score 0 - 34)   : Informational, safe check-in, logistics inquiry |
+-----------------------------------------------------------------------------+
```

### 1.1 `critical` (Score 75 – 100)
**Definition:** Immediate life-threatening hazard requiring tactical intervention within minutes. Victims trapped under physical debris, active drowning/flash floods, structural fires/explosions, arterial bleeding, respiratory failure, or infants/pregnant/elderly persons in direct mortal danger.

**Examples (3 Multilingual Instances):**
1. **English:** *"Second floor collapsed in flash flood, 3 people trapped under heavy concrete slab, oxygen running out!"*
2. **Hindi (`hi`):** *"मकान की छत गिर गई है, मलबे के नीचे 4 लोग दबे हुए हैं और बहुत खून बह रहा है, तुरंत मदद भेजो!"*
3. **Hinglish (`hinglish`):** *"Pani chhat tak aa gaya hai, hum 5 log phase hue hain, bachha doob raha hai please rescue team bhejo!"*

---

### 1.2 `warn` (Score 35 – 74)
**Definition:** Urgent conditions and rising distress that do not present instantaneous mortal collapse but will rapidly escalate without relief within hours. Rapid water ingress, exhausted potable water/rationing, chronic medication exhaustion (insulin/BP), power grid failure with vulnerable residents, or blocked roads preventing movement.

**Examples (3 Multilingual Instances):**
1. **English:** *"Floodwater entering ground floor, need boat for evacuation by tomorrow morning before water reaches electrical mains."*
2. **Hindi (`hi`):** *"पीने का साफ पानी और राशन पूरी तरह खत्म हो चुका है, 2 दिन से बिजली नहीं है और दवाई चाहिए।"*
3. **Hinglish (`hinglish`):** *"Ghar ke samne 3 feet pani bhar gaya hai, dadi ki BP aur insulin ki dawai khatam ho gayi hai."*

---

### 1.3 `info` (Score 0 – 34)
**Definition:** Informational updates, safe status reports, post-evacuation check-ins, weather/camp queries, or non-urgent situational inquiries.

**Examples (3 Multilingual Instances):**
1. **English:** *"We have successfully reached the municipal relief camp at the high school; all 6 family members are safe."*
2. **Hindi (`hi`):** *"हम सब सुरक्षित ऊंचे स्थान पर पहुंच गए हैं, यहां पानी का स्तर कम हो रहा है।"*
3. **Hinglish (`hinglish`):** *"Hum log safe shelter me hain abhi, sab theek hai, koi emergency nahi hai yahan."*

---

## 2. Category Assignment Rubric

Every distress message must map to exactly one primary emergency category:

| Category | Definition | Key Indicators / Entities | Examples |
| :--- | :--- | :--- | :--- |
| **`rescue`** | Physical entrapment, flood isolation, structural collapses, evacuation assistance. | Trapped, buried, rubble, boat needed, roof, drowning, *phase hue*, *dab gaye*, *फंसे हैं* | 1. *"Trapped on roof surrounded by flood water"*<br>2. *"3 log fase hain munder par"*<br>3. *"मलबे से निकालने के लिए टीम चाहिए"* |
| **`medical`** | Injuries, burns, fractures, arterial bleeding, unconsciousness, vital drug shortages. | Blood, fracture, burn, insulin, oxygen, heart attack, ambulance, *chot*, *khoon*, *घायल*, *दवाई* | 1. *"Severe head trauma after wall collapse, unconscious"*<br>2. *"Khoon beh raha hai pair se"*<br>3. *"गंभीर चोट लगी है, एम्बुलेंस चाहिए"* |
| **`fire`** | Structural fires, gas leaks, industrial/chemical hazards, cylinder blasts. | Fire, smoke, gas leak, blast, explosion, *aag*, *dhamaka*, *धुआं*, *आग लगी है* | 1. *"Commercial warehouse on fire, 2 trapped inside"*<br>2. *"LPG cylinder blast hua hai"*<br>3. *"गैस रिसाव और आग फैल रही है"* |
| **`shelter`** | Potable drinking water exhaustion, food depletion, displaced families, temporary camp needs. | Water, food, ration, blanket, displaced, camp, *khana*, *peene ka pani*, *राशन*, *खाना नहीं है* | 1. *"Out of drinking water for 30 people in school basement"*<br>2. *"Ration aur khana khatam ho gaya"*<br>3. *"पीने के पानी की सख्त जरूरत है"* |
| **`other`** | Safe check-ins, infrastructure blockage, fallen trees, general logistics updates. | Safe, road blocked, bridge cracked, power down, *safe hain*, *rasta band*, *सब ठीक है*, *रास्ता बंद* | 1. *"Tree fell on main highway, vehicles halted"*<br>2. *"Sab theek hai hum safe location par hain"*<br>3. *"पुल में दरार आ गई है आवाजाही बंद है"* |

---

## 3. Language Identification Rubric

- **`en` (English):** Standard or colloquial English crisis text using Latin script.
- **`hi` (Hindi):** Devanagari script text (`\u0900` - `\u097F`).
- **`hinglish` (Hinglish):** Hindi / regional vernacular written in Roman/Latin script (e.g. *"pani badh gaya hai"*, *"madad bhejo"*).
