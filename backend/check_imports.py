with open('routers/notifications.py', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 'main' in line:
            print(f'{i}: {line.rstrip()}')
