from argparse import Namespace

from src.cli import keywords as run


class InputProcessor:
    @classmethod
    def process(cls, parsed: Namespace) -> Namespace:  # TODO: context!?
        cls.process_create(parsed.create)
        return parsed

    @classmethod
    def process_create(cls, create: Namespace):
        args: list[str] = create.args
        coords = run.create.coords

        under_idx = args.index(coords.UNDER) if coords.UNDER in args else len(args)
        over_idx = args.index(coords.OVER) if coords.OVER in args else len(args)
        name_upto_idx = min(under_idx, over_idx)

        under_upto_idx = min(over_idx, len(args)) if over_idx > under_idx else len(args)
        over_upto_idx = min(under_idx, len(args)) if under_idx > over_idx else len(args)

        # The names switch as something that a category spreads over is an under category
        names, over_cats, under_cats = args[:name_upto_idx], args[under_idx:under_upto_idx], args[over_idx:over_upto_idx]
        if len(names) != 1:
            raise ValueError(f'"{run.CREATE}" command has to have a category name specified')  # Parsing error?
        if not over_cats and under_idx < len(args):
            raise ValueError(f'"{coords.UNDER}" has to have exactly one category specified')
        if not under_cats and over_idx < len(args):
            raise ValueError(f'"{coords.OVER}" has to have at least one category specified')

        create.over_cat = over_cats
        create.under_cat = under_cats
        create.cat_name = names[0]













