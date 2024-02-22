def calculate(operation: str, x: float, y: float) -> float:
    '''簡易計算機
    
    Returns:
        float: 計算結果

    Example:
    POST to http://localhost:8000/calculate
    {
        "operation": "add",
        "x": 4.4,
        "y": 5.5
    }
    '''
    if operation == 'add':
        return x+y
    elif operation == 'sub':
        return x-y
    elif operation == 'mul':
        return x*y
    elif operation == 'div':
        return x/y
    return 0
