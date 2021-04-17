from Botterino.hosterino import check
from config import pg
from Utils.utils import randomColor

# change these two lines as appropriate
answer = 41.170280504136485, 72.39233446994774
tolerance = 20
manual = False 

submission = next(iter(pg.new())) 
print(f'{randomColor()}Checking answers on https://reddit.com{submission.permalink}')
check(submission, answer, tolerance)
