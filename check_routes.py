from app import app

print('已注册的路由:')
for rule in app.url_map.iter_rules():
    print(f'  {rule.rule} -> {rule.endpoint}')
