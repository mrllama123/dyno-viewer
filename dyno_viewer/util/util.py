def chunk(list_to_split, amount):
    """split a list into n amount"""
    for i in range(0, len(list_to_split), amount):
        yield list_to_split[i : i + amount]
