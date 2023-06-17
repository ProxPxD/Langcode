from langcode import languages, Language

esp = Language('Spanish')

print(languages['Spanish'])


'''
inf       := INF          						        # gehen/ schüttern
dop       := (-a|-o?-)>(-a?+y:+a) 						# piotr -> piotra / mama -> mamy / okno -> okna
dop       := (-a|-o?-),(-a?+y:+a) 						# piotr -> piotra / mama -> mamy / okno -> okna
interfix  := (W1-a?-),W1+o+W2     						# myśl, zbrodnia -> myślozbrodnia
interfix  := (W1-a?-),+o+         						#
infix     := VV1CC1-~(CC1#1?VV1+r+CC1:VV1+re+CC1)       # amat -> armat / armat -> arermat
                     #CC1 == 1?   
mut       := X: k>cz [...]
> - later cond
, - cond at the beginning

C, V - consonants and vowels
inf    := +e^n
inf_1  := +en  -- is inf
inf_2  := +Cn  -- is inf
# inf  := inf_1 | inf_2
ung    := -e^n+ung         # üben  -> übung 
ge_t   := -e^n,ge+t        # sagen -> gesagt
ge_t   := -inf+'ge+t'  

umlaut :=  X:u>ü|o>ö|a>ä

comp   :=  '-V1CC*~' + umlaut['V1'] + '?umlaut(V1)+er' # groß -> größer
comp   :=  '-V1CC*~' + umlaut + '(V1)?umlaut(V1)+er'   # groß -> größer

'''