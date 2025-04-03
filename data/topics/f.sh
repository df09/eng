#!/bin/bash
mkdir 1_LGG-Referentials-Nouns
touch 1_LGG-Referentials-Nouns/theory.wiki
tree='
Lexico-Grammatical Groups (LGG)
├── Referentials (обозначают предмет, лицо, идею)
│   ├── Nouns:
│   │   ├── Proper (John, London)
│   │   ├── Concrete (apple, chair)
│   │   ├── Abstract (freedom, love)
│   │   ├── Collective (team, family)
│   │   ├──(mLGG) Gerunds (swimming)
│   │   ├──(mLGG) Infinitives (to go)
│   │   └──(mLGG) Numerals (one, two, a dozen) — как самостоятельные именные единицы
'
echo -e "$tree" > 1_LGG-Referentials-Nouns/theory.wiki
