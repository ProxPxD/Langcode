# Langcode

## Idea

### Objects
- Units
- Features
- Rules

### Relations
- **Units** have **Features**
- **Rules** describe how to change one **feature** into another within a **Unit**

### Units Division
- Graphemes
- Morphemes

Units are organized hierarchically, which is: the **morphemes** use **graphemes** and therefore **graphemes** are **subunits** of **morphemes**. By a logical extension, 
**morphemes** are the **superunits** of **graphemes**.

### Features
**Features** can be arbitrary strings (or ints?). They are used as information for **units** that can be used for the **rules** or displayed for the user.
**Features** should be used to mark the morpheme representations like the form of a morpheme in a particular script (can be the only one) or the pronunciation (like IPA).
**Features** can be composed from **subunits** when it's specified by the corresponding category (#todo:name like in special features) 

#### Special Features
Some **Features** are special for program working
- #todo:name -- describe the category the unit belongs to For a **grapheme** it is the script. For the **Morpheme** it is a language (#todo: compare with directories or allow both),

### Graphemes
**Graphemes** are symbols used to represent a **morpheme**. Usually one set of **graphemes** (script) will be used as a base one and the other ones can be generated using **rules**.
**Features** can be used to describe **graphemes**' characteristics that can be used during the generation of the other scripts or morphological forms. 
One of such characteristics may be devocalization in the coda. (#todo:extend examples or link to a future page about it)

### Rules
**Rules** describe how **features** can be generated from already existing ones or **subunits**.
**Rules** can take into consideration the environment of the **units** such as next or previous **units**, location in onset, coda, in open or closed syllable, etc.