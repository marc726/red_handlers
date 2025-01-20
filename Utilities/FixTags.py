def format_tags(tags):
    return ",".join(tags.values()) if tags else ""


def manual_format_tags(tags): #individual request GET calls on RED for tags return a list instead of dict
    return ",".join(tags) if tags else ""