
def autores_schema(autores_id) -> list[str]:
    """
    Converts a list of author IDs to a list of string representations.

    Args:
        autores_id (list): A list of author IDs (likely MongoDB ObjectId instances)

    Returns:
        list[str]: A list of author IDs converted to strings

    Example:
    >>> autores_schema([ObjectId('abc123'), ObjectId('def456')])
    ['abc123', 'def456']
    """
    return [autor_id.__str__() for autor_id in autores_id]
