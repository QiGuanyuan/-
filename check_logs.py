# 查看最新日志记录
print('正在查看应用程序日志...')
try:
    with open('app.log', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if lines:
            print('\n最近20条日志记录:')
            for line in lines[-20:]:
                print(line.strip())
        else:
            print('日志文件为空')
except FileNotFoundError:
    print('未找到app.log文件')
    
print('\n正在查看爬虫日志...')
try:
    with open('logs/spider.log', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if lines:
            print('\n最近20条爬虫日志记录:')
            for line in lines[-20:]:
                print(line.strip())
        else:
            print('爬虫日志文件为空')
except FileNotFoundError:
    print('未找到logs/spider.log文件')
