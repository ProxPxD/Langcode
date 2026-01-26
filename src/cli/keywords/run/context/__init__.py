DIRECTION = 'direction'
DIR_TO_ALIASES = {
    (SET:='set'): [ENTER:='enter'],
    (OUT:='out'): [LEAVE:='leave'],
}
DIR_MAP = {form: main for main, aliases in DIR_TO_ALIASES.items() for form in (main, *aliases)}
