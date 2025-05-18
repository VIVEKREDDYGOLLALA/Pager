import os
import collections
import glob
import re

# Define character sets for different languages
# These are reference sets to check for coverage

# Telugu script reference
telugu_chars = {
    "base_consonants": [
        'క', 'ఖ', 'గ', 'ఘ', 'ఙ', 
        'చ', 'ఛ', 'జ', 'ఝ', 'ఞ', 
        'ట', 'ఠ', 'డ', 'ఢ', 'ణ', 
        'త', 'థ', 'ద', 'ధ', 'న', 
        'ప', 'ఫ', 'బ', 'భ', 'మ', 
        'య', 'ర', 'ల', 'వ', 'శ', 
        'ష', 'స', 'హ', 'ళ', 'క్ష', 'ఱ'
    ],
    "vowels": ['అ', 'ఆ', 'ఇ', 'ఈ', 'ఉ', 'ఊ', 'ఋ', 'ౠ', 'ఎ', 'ఏ', 'ఐ', 'ఒ', 'ఓ', 'ఔ'],
    "matras": ['ా', 'ి', 'ీ', 'ు', 'ూ', 'ృ', 'ౄ', 'ె', 'ే', 'ై', 'ొ', 'ో', 'ౌ', '్'],
    "digits": ['౦', '౧', '౨', '౩', '౪', '౫', '౬', '౭', '౮', '౯'],
    "special": ['ం', 'ః', '઼']
}

# Hindi/Devanagari script reference
hindi_chars = {
    "base_consonants": [
        'क', 'ख', 'ग', 'घ', 'ङ', 
        'च', 'छ', 'ज', 'झ', 'ञ', 
        'ट', 'ठ', 'ड', 'ढ', 'ण', 
        'त', 'थ', 'द', 'ध', 'न', 
        'प', 'फ', 'ब', 'भ', 'म', 
        'य', 'र', 'ल', 'व', 'श', 
        'ष', 'स', 'ह', 'क्ष', 'ज्ञ'
    ],
    "vowels": ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ए', 'ऐ', 'ओ', 'औ'],
    "matras": ['ा', 'ि', 'ी', 'ु', 'ू', 'ृ', 'ॄ', 'ॢ', 'ॣ', 'े', 'ै', 'ो', 'ौ', '्'],
    "digits": ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'],
    "special": ['ं', 'ः', '़', 'ँ', '॑']
}

# Tamil script reference
tamil_chars = {
    "base_consonants": [
        'க', 'ங', 'ச', 'ஞ', 'ட', 
        'ண', 'த', 'ந', 'ப', 'ம', 
        'ய', 'ர', 'ல', 'வ', 'ழ', 
        'ள', 'ற', 'ன'
    ],
    "vowels": ['அ', 'ஆ', 'இ', 'ஈ', 'உ', 'ஊ', 'எ', 'ஏ', 'ஐ', 'ஒ', 'ஓ', 'ஔ'],
    "matras": ['ா', 'ி', 'ீ', 'ு', 'ூ', 'ெ', 'ே', 'ை', 'ொ', 'ோ', 'ௌ', '்'],
    "digits": ['௦', '௧', '௨', '௩', '௪', '௫', '௬', '௭', '௮', '௯'],
    "special": ['ஂ', 'ஃ']
}
#sha ha

# Kannada script reference
kannada_chars = {
    "base_consonants": [
        'ಕ', 'ಖ', 'ಗ', 'ಘ', 'ಙ', 
        'ಚ', 'ಛ', 'ಜ', 'ಝ', 'ಞ', 
        'ಟ', 'ಠ', 'ಡ', 'ಢ', 'ಣ', 
        'ತ', 'ಥ', 'ದ', 'ಧ', 'ನ', 
        'ಪ', 'ಫ', 'ಬ', 'ಭ', 'ಮ', 
        'ಯ', 'ರ', 'ಲ', 'ವ', 'ಶ', 
        'ಷ', 'ಸ', 'ಹ', 'ಳ'
    ],
    "vowels": ['ಅ', 'ಆ', 'ಇ', 'ಈ', 'ಉ', 'ಊ', 'ಋ', 'ೠ', 'ಎ', 'ಏ', 'ಐ', 'ಒ', 'ಓ', 'ಔ'],
    "matras": ['ಾ', 'ಿ', 'ೀ', 'ು', 'ೂ', 'ೃ', 'ೄ', 'ೆ', 'ೇ', 'ೈ', 'ೊ', 'ೋ', 'ೌ', '್'],
    "digits": ['೦', '೧', '೨', '೩', '೪', '೫', '೬', '೭', '೮', '೯'],
    "special": ['ಂ', 'ಃ']
}

# Bengali script reference
bengali_chars = {
    "base_consonants": [
        'ক', 'খ', 'গ', 'ঘ', 'ঙ', 
        'চ', 'ছ', 'জ', 'ঝ', 'ঞ', 
        'ট', 'ঠ', 'ড', 'ঢ', 'ণ', 
        'ত', 'থ', 'দ', 'ধ', 'ন', 
        'প', 'ফ', 'ব', 'ভ', 'ম', 
        'য', 'র', 'ল', 'শ', 'ষ', 
        'স', 'হ', 'ড়', 'ঢ়', 'য়'
    ],
    "vowels": ['অ', 'আ', 'ই', 'ঈ', 'উ', 'ঊ', 'ঋ', 'ৠ', 'এ', 'ঐ', 'ও', 'ঔ'],
    "matras": ['া', 'ি', 'ী', 'ু', 'ূ', 'ৃ', 'ৄ', 'ে', 'ৈ', 'ো', 'ৌ', '্'],
    "digits": ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯'],
    "special": ['ং', 'ঃ', 'ঁ']
}

# Malayalam script reference
malayalam_chars = {
    "base_consonants": [
        'ക', 'ഖ', 'ഗ', 'ഘ', 'ങ', 
        'ച', 'ഛ', 'ജ', 'ഝ', 'ഞ', 
        'ട', 'ഠ', 'ഡ', 'ഢ', 'ണ', 
        'ത', 'ഥ', 'ദ', 'ധ', 'ന', 
        'പ', 'ഫ', 'ബ', 'ഭ', 'മ', 
        'യ', 'ര', 'ല', 'വ', 'ശ', 
        'ഷ', 'സ', 'ഹ', 'ള', 'ഴ', 'റ'
    ],
    "vowels": ['അ', 'ആ', 'ഇ', 'ഈ', 'ഉ', 'ഊ', 'ഋ', 'ൠ', 'ഌ', 'ൡ', 'എ', 'ഏ', 'ഐ', 'ഒ', 'ഓ', 'ഔ'],
    "matras": ['ാ', 'ി', 'ീ', 'ു', 'ൂ', 'ൃ', 'ൄ', 'ൢ', 'ൣ', 'െ', 'േ', 'ൈ', 'ൊ', 'ോ', 'ൌ', '്'],
    "digits": ['൦', '൧', '൨', '൩', '൪', '൫', '൬', '൭', '൮', '൯'],
    "special": ['ം', 'ഃ']
}
# 1. Assamese (uses Bengali script with some variations)
assamese_chars = {
    "base_consonants": [
        'ক', 'খ', 'গ', 'ঘ', 'ঙ', 
        'চ', 'ছ', 'জ', 'ঝ', 'ঞ', 
        'ট', 'ঠ', 'ড', 'ঢ', 'ণ', 
        'ত', 'থ', 'দ', 'ধ', 'ন', 
        'প', 'ফ', 'ব', 'ভ', 'ম', 
        'য', 'ৰ', 'ল', 'ৱ', 'শ', 
        'ষ', 'স', 'হ', 'ক্ষ', 'ড়', 'ঢ়'
    ],
    "vowels": ['অ', 'আ', 'ই', 'ঈ', 'উ', 'ঊ', 'ঋ', 'এ', 'ঐ', 'ও', 'ঔ'],
    "matras": ['া', 'ি', 'ী', 'ু', 'ূ', 'ৃ', 'ে', 'ৈ', 'ো', 'ৌ', '্'],
    "digits": ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯'],
    "special": ['ং', 'ঃ', 'ঁ']
}

# 2. Bodo (uses Devanagari script primarily)
bodo_chars = {
    "base_consonants": [
        'क', 'ख', 'ग', 'घ', 'ङ', 
        'च', 'छ', 'ज', 'झ', 'ञ', 
        'ट', 'ठ', 'ड', 'ढ', 'ण', 
        'त', 'थ', 'द', 'ध', 'न', 
        'प', 'फ', 'ब', 'भ', 'म', 
        'य', 'र', 'ल', 'व', 'श', 
        'ष', 'स', 'ह', 'क्ष', 'त्र', 'ज्ञ',
        'ड़', 'ढ़', 'य़'
    ],
    "vowels": ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ए', 'ऐ', 'ओ', 'औ'],
    "matras": ['ा', 'ि', 'ी', 'ु', 'ू', 'े', 'ै', 'ो', 'ौ', '्'],
    "digits": ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'],
    "special": ['ं', 'ः', '़', 'ँ', 'ऽ', '॑', '॒']
}

# 3. Dogri (uses Devanagari script primarily)
dogri_chars = {
    "base_consonants": [
        'क', 'ख', 'ग', 'घ', 'ङ', 
        'च', 'छ', 'ज', 'झ', 'ञ', 
        'ट', 'ठ', 'ड', 'ढ', 'ण', 
        'त', 'थ', 'द', 'ध', 'न', 
        'प', 'फ', 'ब', 'भ', 'म', 
        'य', 'र', 'ल', 'व', 'श', 
        'ष', 'स', 'ह', 'क्ष', 'त्र', 'ज्ञ'
    ],
    "vowels": ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ए', 'ऐ', 'ओ', 'औ'],
    "matras": ['ा', 'ि', 'ी', 'ु', 'ू', 'े', 'ै', 'ो', 'ौ', '्'],
    "digits": ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'],
    "special": ['ं', 'ः', '़', 'ँ', 'ऽ']
}

# 4. Gujarati
gujarati_chars = {
    "base_consonants": [
        'ક', 'ખ', 'ગ', 'ઘ', 'ઙ', 
        'ચ', 'છ', 'જ', 'ઝ', 'ઞ', 
        'ટ', 'ઠ', 'ડ', 'ઢ', 'ણ', 
        'ત', 'થ', 'દ', 'ધ', 'ન', 
        'પ', 'ફ', 'બ', 'ભ', 'મ', 
        'ય', 'ર', 'લ', 'વ', 'શ', 
        'ષ', 'સ', 'હ', 'ળ', 'ક્ષ', 'જ્ઞ'
    ],
    "vowels": ['અ', 'આ', 'ઇ', 'ઈ', 'ઉ', 'ઊ', 'ઋ', 'ઌ', 'એ', 'ઐ', 'ઓ', 'ઔ'],
    "matras": ['ા', 'િ', 'ી', 'ુ', 'ૂ', 'ૃ', 'ૄ', 'ૅ', 'ે', 'ૈ', 'ૉ', 'ો', 'ૌ', '્'],
    "digits": ['૦', '૧', '૨', '૩', '૪', '૫', '૬', '૭', '૮', '૯'],
    "special": ['ં', 'ઃ', 'ઁ', '઼']
}

# 5. Konkani (primarily uses Devanagari script, but also Kannada and Malayalam scripts)
konkani_devanagari_chars = {
    "base_consonants": [
        'क', 'ख', 'ग', 'घ', 'ङ', 
        'च', 'छ', 'ज', 'झ', 'ञ', 
        'ट', 'ठ', 'ड', 'ढ', 'ण', 
        'त', 'थ', 'द', 'ध', 'न', 
        'प', 'फ', 'ब', 'भ', 'म', 
        'य', 'र', 'ल', 'व', 'श', 
        'ष', 'स', 'ह', 'ळ', 'क्ष', 'ज्ञ'
    ],
    "vowels": ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ए', 'ऐ', 'ओ', 'औ', 'ॲ', 'ऑ'],
    "matras": ['ा', 'ि', 'ी', 'ु', 'ू', 'े', 'ै', 'ो', 'ौ', 'ॅ', 'ॉ', '्'],
    "digits": ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'],
    "special": ['ं', 'ः', 'ँ', 'ॐ', 'ऽ', '॰']
}

# 6. Maithili (uses Devanagari script)
maithili_chars = {
    "base_consonants": [
        'क', 'ख', 'ग', 'घ', 'ङ', 
        'च', 'छ', 'ज', 'झ', 'ञ', 
        'ट', 'ठ', 'ड', 'ढ', 'ण', 
        'त', 'थ', 'द', 'ध', 'न', 
        'प', 'फ', 'ब', 'भ', 'म', 
        'य', 'र', 'ल', 'व', 'श', 
        'ष', 'स', 'ह', 'क्ष', 'त्र', 'ज्ञ', 'ड़', 'ढ़'
    ],
    "vowels": ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ए', 'ऐ', 'ओ', 'औ'],
    "matras": ['ा', 'ि', 'ी', 'ु', 'ू', 'ृ', 'े', 'ै', 'ो', 'ौ', '्'],
    "digits": ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'],
    "special": ['ं', 'ः', '़', 'ँ', 'ऽ']
}

# 7. Meitei/Manipuri (Meitei Mayek script)
meitei_mayek_chars = {
    "base_consonants": [
        'ꯀ', 'ꯁ', 'ꯂ', 'ꯃ', 'ꯄ', 
        'ꯅ', 'ꯆ', 'ꯇ', 'ꯈ', 'ꯉ', 
        'ꯊ', 'ꯋ', 'ꯌ', 'ꯍ', 'ꯎ', 
        'ꯏ', 'ꯐ', 'ꯑ', 'ꯒ', 'ꯓ',
        'ꯔ', 'ꯕ', 'ꯖ', 'ꯗ', 'ꯘ'
    ],
    "vowels": ['ꯤ', 'ꯥ', 'ꯦ', 'ꯧ', 'ꯨ', 'ꯩ', 'ꯪ'],
    "matras": ['ꯥ', 'ꯤ', 'ꯦ', 'ꯧ', 'ꯨ', 'ꯩ', 'ꯪ', '꯭'],
    "digits": ['꯰', '꯱', '꯲', '꯳', '꯴', '꯵', '꯶', '꯷', '꯸', '꯹'],
    "special": ['꯫', '꯬']
}

# 8. Marathi (uses Devanagari script)
marathi_chars = {
    "base_consonants": [
        'क', 'ख', 'ग', 'घ', 'ङ', 
        'च', 'छ', 'ज', 'झ', 'ञ', 
        'ट', 'ठ', 'ड', 'ढ', 'ण', 
        'त', 'थ', 'द', 'ध', 'न', 
        'प', 'फ', 'ब', 'भ', 'म', 
        'य', 'र', 'ल', 'व', 'श', 
        'ष', 'स', 'ह', 'ळ', 'क्ष', 'ज्ञ'
    ],
    "vowels": ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ए', 'ऐ', 'ओ', 'औ', 'ॲ', 'ऑ'],
    "matras": ['ा', 'ि', 'ी', 'ु', 'ू', 'ृ', 'े', 'ै', 'ो', 'ौ', 'ॅ', 'ॉ', '्'],
    "digits": ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'],
    "special": ['ं', 'ः', '़', 'ँ', 'ऽ']
}

# 9. Nepali (uses Devanagari script)
nepali_chars = {
    "base_consonants": [
        'क', 'ख', 'ग', 'घ', 'ङ', 
        'च', 'छ', 'ज', 'झ', 'ञ', 
        'ट', 'ठ', 'ड', 'ढ', 'ण', 
        'त', 'थ', 'द', 'ध', 'न', 
        'प', 'फ', 'ब', 'भ', 'म', 
        'य', 'र', 'ल', 'व', 'श', 
        'ष', 'स', 'ह', 'क्ष', 'त्र', 'ज्ञ'
    ],
    "vowels": ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ए', 'ऐ', 'ओ', 'औ'],
    "matras": ['ा', 'ि', 'ी', 'ु', 'ू', 'ृ', 'े', 'ै', 'ो', 'ौ', '्'],
    "digits": ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'],
    "special": ['ं', 'ः', 'ँ', 'ऽ']
}

# 10. Oriya/Odia
odia_chars = {
    "base_consonants": [
        'କ', 'ଖ', 'ଗ', 'ଘ', 'ଙ', 
        'ଚ', 'ଛ', 'ଜ', 'ଝ', 'ଞ', 
        'ଟ', 'ଠ', 'ଡ', 'ଢ', 'ଣ', 
        'ତ', 'ଥ', 'ଦ', 'ଧ', 'ନ', 
        'ପ', 'ଫ', 'ବ', 'ଭ', 'ମ', 
        'ଯ', 'ର', 'ଲ', 'ଳ', 'ଵ', 
        'ଶ', 'ଷ', 'ସ', 'ହ', 'କ୍ଷ', 'ଡ଼', 'ଢ଼', 'ୟ'
    ],
    "vowels": ['ଅ', 'ଆ', 'ଇ', 'ଈ', 'ଉ', 'ଊ', 'ଋ', 'ୠ', 'ଌ', 'ୡ', 'ଏ', 'ଐ', 'ଓ', 'ଔ'],
    "matras": ['ା', 'ି', 'ୀ', 'ୁ', 'ୂ', 'ୃ', 'ୄ', 'େ', 'ୈ', 'ୋ', 'ୌ', '୍'],
    "digits": ['୦', '୧', '୨', '୩', '୪', '୫', '୬', '୭', '୮', '୯'],
    "special": ['ଂ', 'ଃ', 'ଁ']
}

# 11. Punjabi (Gurmukhi script)
punjabi_chars = {
    "base_consonants": [
        'ਕ', 'ਖ', 'ਗ', 'ਘ', 'ਙ', 
        'ਚ', 'ਛ', 'ਜ', 'ਝ', 'ਞ', 
        'ਟ', 'ਠ', 'ਡ', 'ਢ', 'ਣ', 
        'ਤ', 'ਥ', 'ਦ', 'ਧ', 'ਨ', 
        'ਪ', 'ਫ', 'ਬ', 'ਭ', 'ਮ', 
        'ਯ', 'ਰ', 'ਲ', 'ਵ', 'ੜ', 
        'ਸ', 'ਹ', 'ਖ਼', 'ਗ਼', 'ਜ਼', 'ਫ਼', 'ਲ਼'
    ],
    "vowels": ['ਅ', 'ਆ', 'ਇ', 'ਈ', 'ਉ', 'ਊ', 'ਏ', 'ਐ', 'ਓ', 'ਔ'],
    "matras": ['ਾ', 'ਿ', 'ੀ', 'ੁ', 'ੂ', 'ੇ', 'ੈ', 'ੋ', 'ੌ', '੍'],
    "digits": ['੦', '੧', '੨', '੩', '੪', '੫', '੬', '੭', '੮', '੯'],
    "special": ['ਂ', 'ਃ', 'ੰ', 'ੱ', 'ੴ']
}

# 12. Sanskrit (primarily uses Devanagari, but can be written in any Indian script)
sanskrit_chars = {
    "base_consonants": [
        'क', 'ख', 'ग', 'घ', 'ङ', 
        'च', 'छ', 'ज', 'झ', 'ञ', 
        'ट', 'ठ', 'ड', 'ढ', 'ण', 
        'त', 'थ', 'द', 'ध', 'न', 
        'प', 'फ', 'ब', 'भ', 'म', 
        'य', 'र', 'ल', 'व', 'श', 
        'ष', 'स', 'ह', 'क्ष', 'त्र', 'ज्ञ'
    ],
    "vowels": ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ॠ', 'ऌ', 'ॡ', 'ए', 'ऐ', 'ओ', 'औ'],
    "matras": ['ा', 'ि', 'ी', 'ु', 'ू', 'ृ', 'ॄ', 'ॢ', 'ॣ', 'े', 'ै', 'ो', 'ौ', '्'],
    "digits": ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'],
    "special": ['ं', 'ः', 'ँ', 'ॐ', 'ऽ', '॑', '॒']
}

# 13. Santali (Ol Chiki script)
santali_chars = {
    "base_consonants": [
        'ᱚ', 'ᱛ', 'ᱜ', 'ᱝ', 'ᱞ', 
        'ᱟ', 'ᱠ', 'ᱡ', 'ᱢ', 'ᱣ', 
        'ᱤ', 'ᱥ', 'ᱦ', 'ᱧ', 'ᱨ', 
        'ᱩ', 'ᱪ', 'ᱫ', 'ᱬ', 'ᱭ', 
        'ᱮ', 'ᱯ', 'ᱰ', 'ᱱ', 'ᱲ', 
        'ᱳ', 'ᱴ', 'ᱵ', 'ᱶ', 'ᱷ'
    ],
    "vowels": [],  # Ol Chiki doesn't have separate vowels
    "matras": [],  # Ol Chiki doesn't use matras
    "digits": ['᱐', '᱑', '᱒', '᱓', '᱔', '᱕', '᱖', '᱗', '᱘', '᱙'],
    "special": ['᱿', '᱾']
}

# 14. Sindhi (uses Arabic script primarily in Pakistan, Devanagari in India)
sindhi_devanagari_chars = {
    "base_consonants": [
        'क', 'ख', 'ग', 'घ', 'ङ', 
        'च', 'छ', 'ज', 'झ', 'ञ', 
        'ट', 'ठ', 'ड', 'ढ', 'ण', 
        'त', 'थ', 'द', 'ध', 'न', 
        'प', 'फ', 'ब', 'भ', 'म', 
        'य', 'र', 'ल', 'व', 'श', 
        'ष', 'स', 'ह', 'क्ष', 'ज्ञ', 'ड़', 'ढ़',
        'ॻ', 'ॼ', 'ॾ', 'ॿ'  # Special Sindhi characters
    ],
    "vowels": ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ए', 'ऐ', 'ओ', 'औ'],
    "matras": ['ा', 'ि', 'ी', 'ु', 'ू', 'े', 'ै', 'ो', 'ौ', '्'],
    "digits": ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'],
    "special": ['ं', 'ः', '़', 'ँ', 'ॱ']
}

# 15. Urdu (uses Persian-Arabic script)
urdu_chars = {
    "base_consonants": [
        'ب', 'پ', 'ت', 'ٹ', 'ث', 
        'ج', 'چ', 'ح', 'خ', 'د', 
        'ڈ', 'ذ', 'ر', 'ڑ', 'ز', 
        'ژ', 'س', 'ش', 'ص', 'ض', 
        'ط', 'ظ', 'ع', 'غ', 'ف', 
        'ق', 'ک', 'گ', 'ل', 'م', 
        'ن', 'ہ', 'ھ', 'و', 'ی', 'ے'
    ],
    "vowels": ['ا', 'آ', 'ی', 'ے', 'و', 'ؤ', 'ئ'],
    "matras": ['َ', 'ِ', 'ُ', 'ّ', 'ً', 'ٍ', 'ٌ', 'ٰ', 'ٖ', 'ٗ'],
    "digits": ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'],
    "special": ['ء', 'ٔ', 'ٕ', '؟', '۔', 'ؓ', 'ؔ']
}

# 16. Kashmiri (uses Perso-Arabic script or Devanagari)
kashmiri_devanagari_chars = {
    "base_consonants": [
        'क', 'ख', 'ग', 'घ', 'ङ', 
        'च', 'छ', 'ज', 'झ', 'ञ', 
        'ट', 'ठ', 'ड', 'ढ', 'ण', 
        'त', 'थ', 'द', 'ध', 'न', 
        'प', 'फ', 'ब', 'भ', 'म', 
        'य', 'र', 'ल', 'व', 'श', 
        'ष', 'स', 'ह', 'क्ष', 'त्र', 'ज्ञ', 'ड़', 'ढ़'
    ],
    "vowels": ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ए', 'ऐ', 'ओ', 'औ'],
    "matras": ['ा', 'ि', 'ी', 'ु', 'ू', 'ृ', 'े', 'ै', 'ो', 'ौ', '्'],
    "digits": ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'],
    "special": ['ं', 'ः', '़', 'ँ', 'ऽ']
}

# Combined dictionary of all language references
language_chars = {
    "telugu": telugu_chars,
    "hindi": hindi_chars,
    "tamil": tamil_chars,
    "kannada": kannada_chars,
    "bengali": bengali_chars,
    "malayalam": malayalam_chars,
    "assamese": assamese_chars,
    "bodo": bodo_chars,
    "dogri": dogri_chars,
    "gujarati": gujarati_chars,
    "konkani": konkani_devanagari_chars,
    "maithili": maithili_chars,
    "manipuri": meitei_mayek_chars,
    "marathi": marathi_chars,
    "nepali": nepali_chars,
    "odia": odia_chars,
    "punjabi": punjabi_chars,
    "sanskrit": sanskrit_chars,
    "santali": santali_chars,
    "sindhi": sindhi_devanagari_chars,
    "urdu": urdu_chars,
    "kashmiri": kashmiri_devanagari_chars
}
def detect_language(text):
    """
    Detect which language is used in the text by counting characters.
    Not used anymore in main logic, kept for fallback/reference.
    """
    lang_scores = {}
    
    for lang_name, char_groups in language_chars.items():
        all_chars = set()
        for group in char_groups.values():
            all_chars.update(group)
        
        count = sum(1 for char in text if char in all_chars)
        lang_scores[lang_name] = count
    
    if not lang_scores:
        return None
    
    max_lang = max(lang_scores.items(), key=lambda x: x[1])
    if max_lang[1] > 10:
        return max_lang[0]
    
    return None

def analyze_file(file_path, output_dir=None):
    """
    Analyze a text file for character coverage compared to a reference character set.
    
    Args:
        file_path: Path to the input text file
        output_dir: Directory to save the output files
    """
    # Set default output directory if not provided
    if output_dir is None:
        output_dir = os.path.dirname(file_path)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Try to read the file with different encodings
    encodings = ['utf-8', 'utf-16', 'latin-1']
    text = None
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                text = file.read()
                break
        except UnicodeDecodeError:
            continue
    
    if text is None:
        with open(file_path, 'rb') as file:
            text = file.read().decode('utf-8', errors='replace')
    
    # Use filename as language
    base_name = os.path.basename(file_path)
    file_name_without_ext = os.path.splitext(base_name)[0]
    detected_lang = file_name_without_ext.lower()

    # Count character frequencies
    char_counts = collections.Counter(text)

    # Count words
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)
    unique_word_count = len(set(words))

    coverage_info = {}
    missing_chars = {}
    
    if detected_lang in language_chars:
        lang_ref = language_chars[detected_lang]
        chars_in_text = set(char_counts.keys())
        
        for category, char_set in lang_ref.items():
            found_chars = [c for c in char_set if c in chars_in_text]
            missing = [c for c in char_set if c not in chars_in_text]
            coverage_pct = (len(found_chars) / len(char_set)) * 100 if char_set else 100
            
            coverage_info[category] = {
                "total": len(char_set),
                "found": len(found_chars),
                "missing": len(missing),
                "coverage_pct": coverage_pct
            }
            missing_chars[category] = missing

    output_file = os.path.join(output_dir, f"{file_name_without_ext}_coverage.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Character Coverage Analysis for: {base_name}\n")
        f.write(f"Detected Language: {detected_lang.upper()}\n")
        f.write(f"Total characters: {len(text)}\n")
        f.write(f"Unique characters: {len(char_counts)}\n")
        f.write(f"Total words: {word_count}\n")
        f.write(f"Unique words: {unique_word_count}\n\n")
        
        f.write("CHARACTER FREQUENCIES (top 50):\n")
        f.write("-----------------------------------------\n")
        for char, count in sorted(char_counts.items(), key=lambda x: x[1], reverse=True)[:50]:
            char_repr = char
            if char == '\n':
                char_repr = "\\n"
            elif char == '\r':
                char_repr = "\\r"
            elif char == '\t':
                char_repr = "\\t"
            elif char == ' ':
                char_repr = "space"
            
            percentage = (count / len(text)) * 100
            f.write(f"{char_repr}: {count} ({percentage:.2f}%)\n")

        if detected_lang in language_chars:
            f.write("\nCHARACTER COVERAGE SUMMARY:\n")
            f.write("-----------------------------------------\n")
            overall_found = sum(info["found"] for info in coverage_info.values())
            overall_total = sum(info["total"] for info in coverage_info.values())
            overall_pct = (overall_found / overall_total) * 100 if overall_total else 100
            
            f.write(f"Overall coverage: {overall_found}/{overall_total} characters ({overall_pct:.1f}%)\n\n")
            
            for category, info in coverage_info.items():
                f.write(f"{category.upper()}: {info['found']}/{info['total']} ({info['coverage_pct']:.1f}%)\n")
            
            f.write("\nMISSING CHARACTERS:\n")
            f.write("-----------------------------------------\n")
            for category, missing in missing_chars.items():
                if missing:
                    f.write(f"\n{category.upper()} ({len(missing)} missing):\n")
                    for i in range(0, len(missing), 10):
                        f.write("  " + " ".join(missing[i:i+10]) + "\n")
                else:
                    f.write(f"\n{category.upper()}: None missing (100% coverage)\n")
        else:
            f.write("\nNote: Language not fully supported for character coverage analysis.\n")
    
    print(f"Analysis complete. Results saved to: {output_file}")
    return output_file, detected_lang

def analyze_folder(folder_path, output_dir=None):
    """
    Analyze all text files in a folder and generate a summary for missing characters.
    
    Args:
        folder_path: Path to the folder containing text files
        output_dir: Directory to save output files
    """
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        return
    
    if output_dir is None:
        output_dir = folder_path
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Find all text files in the folder
    txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
    
    if not txt_files:
        print(f"No text files found in {folder_path}")
        return
    
    print(f"Found {len(txt_files)} text files in {folder_path}")
    
    # Process each file and keep track of detected languages
    detected_langs = {}
    chars_by_lang = {}
    
    for file_path in txt_files:
        print(f"Processing: {os.path.basename(file_path)}")
        _, lang = analyze_file(file_path, output_dir)
        
        detected_langs[file_path] = lang
        
        # Initialize language counter if not already present
        if lang not in chars_by_lang:
            chars_by_lang[lang] = collections.Counter()
        
        # Read the file and count characters for this language
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='utf-16') as f:
                    text = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'rb') as f:
                    text = f.read().decode('utf-8', errors='replace')
        
        # Update character counts for this language
        chars_by_lang[lang].update(text)
    
    # For each detected language, generate a combined coverage report
    for lang, char_counter in chars_by_lang.items():
        if lang in language_chars:
            lang_ref = language_chars[lang]
            chars_found = set(char_counter.keys())
            
            # Calculate coverage metrics
            coverage_info = {}
            missing_chars = {}
            
            for category, char_set in lang_ref.items():
                found_chars = [c for c in char_set if c in chars_found]
                missing = [c for c in char_set if c not in chars_found]
                
                coverage_pct = (len(found_chars) / len(char_set)) * 100 if char_set else 100
                
                coverage_info[category] = {
                    "total": len(char_set),
                    "found": len(found_chars),
                    "missing": len(missing),
                    "coverage_pct": coverage_pct
                }
                
                missing_chars[category] = missing
            
            # Write combined report for this language
            lang_report_file = os.path.join(output_dir, f"combined_{lang}_coverage.txt")
            with open(lang_report_file, 'w', encoding='utf-8') as f:
                f.write(f"Combined Character Coverage Analysis for {lang.upper()}\n")
                f.write(f"Total files analyzed: {sum(1 for l in detected_langs.values() if l == lang)}\n\n")
                
                # Overall coverage summary
                overall_found = sum(info["found"] for info in coverage_info.values())
                overall_total = sum(info["total"] for info in coverage_info.values())
                overall_pct = (overall_found / overall_total) * 100 if overall_total else 100
                
                f.write(f"OVERALL COVERAGE: {overall_found}/{overall_total} characters ({overall_pct:.1f}%)\n\n")
                
                f.write("COVERAGE BY CATEGORY:\n")
                f.write("-----------------------------------------\n")
                for category, info in coverage_info.items():
                    f.write(f"{category.upper()}: {info['found']}/{info['total']} ({info['coverage_pct']:.1f}%)\n")
                
                # Character frequency list (top 50)
                f.write("\nMOST FREQUENT CHARACTERS:\n")
                f.write("-----------------------------------------\n")
                for char, count in char_counter.most_common(50):
                    if char in ['\n', '\r', '\t', ' ']:
                        continue
                    
                    # Identify which category this character belongs to
                    char_category = "Other"
                    for category, char_set in lang_ref.items():
                        if char in char_set:
                            char_category = category
                            break
                    
                    f.write(f"{char} ({char_category}): {count}\n")
                
                # List missing characters by category
                f.write("\nMISSING CHARACTERS:\n")
                f.write("-----------------------------------------\n")
                
                any_missing = False
                for category, missing in missing_chars.items():
                    if missing:
                        any_missing = True
                        f.write(f"\n{category.upper()} ({len(missing)} missing):\n")
                        # Format with 10 characters per line for readability
                        for i in range(0, len(missing), 10):
                            f.write("  " + " ".join(missing[i:i+10]) + "\n")
                
                if not any_missing:
                    f.write("\nNo missing characters! 100% coverage across all categories.\n")
                else:
                    # Generate synthetic text suggestion with missing characters
                    f.write("\nSYNTHETIC DATA SUGGESTION:\n")
                    f.write("-----------------------------------------\n")
                    f.write("Include the following text in your training data to cover missing characters:\n\n")
                    
                    for category, missing in missing_chars.items():
                        if missing:
                            if category == "base_consonants":
                                f.write(" ".join(missing) + "\n")
                            elif category == "vowels":
                                f.write(" ".join(missing) + "\n")
                            elif category == "matras" and "base_consonants" in lang_ref:
                                # For matras, combine with a common consonant (first one) if available
                                if lang_ref["base_consonants"]:
                                    base = lang_ref["base_consonants"][0]
                                    matra_examples = []
                                    for matra in missing:
                                        if matra == '्' or matra == '్':  # Special case for virama
                                            continue
                                        matra_examples.append(base + matra)
                                    f.write(" ".join(matra_examples) + "\n")
                            elif category == "special" or category == "digits":
                                f.write(" ".join(missing) + "\n")
            
            print(f"Combined {lang} analysis complete. Results saved to: {lang_report_file}")

if __name__ == "__main__":
    # Change these paths to your actual folder paths
    input_folder = "output_texts"
    output_folder = "txt_files_outpt"
    
    # Uncomment one of these lines to run the analysis
    # analyze_file("path/to/single/file.txt", output_folder)  # For single file
    analyze_folder(input_folder, output_folder)             # For folder of files