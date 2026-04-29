
def can_convert_to_int(s):
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False