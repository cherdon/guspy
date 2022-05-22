import logging


def equals(field=None, value=None):
    if field and value:
        return f"{field} = '{value}'"
    else:
        logging.error(f"[Filter] Equals Error: Missing {'field' if not field else 'value'}")
        return None


def is_in(field=None, value=None):
    if field and value:
        return f"{field} IN {value}"
    else:
        logging.error(f"[Filter] Is_in Error: Missing {'field' if not field else 'value'}")
        return None


def like(field=None, value=None, identifier="*"):
    if field and value:
        return f"{field} LIKE '{value.replace(identifier, '%')}'"
    else:
        logging.error(f"[Filter] Like Error: Missing {'field' if not field else 'value'}")
        return None


def incl(*args):
    if len(args) >= 2:
        return " AND ".join(args)
    else:
        logging.error(f"[Filter] Incl Error: At least 2 arguments needed, {len(args)} provided")
        return None


def excl(*args):
    if len(args) >= 2:
        return " OR ".join(args)
    else:
        logging.error(f"[Filter] Excl Error: At least 2 arguments needed, {len(args)} provided")
        return None


def quote(string):
    return f"'{string}'"


def bracket(string):
    return f"({string})"