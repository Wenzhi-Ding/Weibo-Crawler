import os

print('尝试更新代码')
os.system('git add --all')
os.system('git commit -m "update"')
os.system('git reset --hard origin/master')
os.system('git pull origin master')
print('已完成更新')